
import datetime
import shotgun_api3
import json

from shotgun_replica.factories import getObject
from shotgun_replica import config, connectors, base_entity, UNKNOWN_SHOTGUN_ID
import shotgun_replica

import traceback
from shotgun_replica.utilities import debug

LOCALDB_FAILURE = 1
SHOTGUN_FAILURE = 2
SEVERE_FAILURE = 250

def getSgObj( dataObj ):
    if type( dataObj ) == dict:
        if dataObj.has_key( "type" ) and dataObj.has_key( "id" ):
            if dataObj["id"] == UNKNOWN_SHOTGUN_ID and dataObj.has_key( "__local_id" ) and dataObj["__local_id"] != UNKNOWN_SHOTGUN_ID:
                remoteID = connectors.getRemoteID( dataObj["type"], dataObj["__local_id"] )
                return { "type": dataObj["type"],
                         "id": remoteID }
            else:
                return { "type": dataObj["type"],
                         "id": dataObj["id"] }
        return None
    elif isinstance( dataObj, base_entity.ShotgunBaseEntity ) or type( dataObj ) == connectors.PostgresEntityType:
        return dataObj.getSgObj()



class LocalDBEventSpooler( object ):
    """ Continuously spools events from couchdb and transfers them to shotgun """

    src = None # local database connector
    cur = None
    sg = None

    def _connect( self ):
        """ establish the connections
        
        establish a connection to local server and shotgun
        """
        try:
            self.src = connectors.DatabaseModificator()
        except Exception, error: #IGNORE:W0703
            debug.error( "Unable to _connect to database server. " + unicode( error ) )
            return False

        try:
            self.sg = shotgun_api3.Shotgun( config.SHOTGUN_URL,
                                            config.SHOTGUN_BACKSYNC_SKRIPT,
                                            config.SHOTGUN_BACKSYNC_KEY )
        except Exception, error: #IGNORE:W0703
            debug.error( "Unable to _connect to Shotgun server. " + unicode( error ) )
            return False

        return True

    def queryAndProcess( self, onlyEventIDs = None ):
        """ queries and processes events from shotgun
        
        this method is mainly used from the run method but also for testing purposes
        """

        # for temporary objects only
        # query first changeEvents, and then tempObject
        # tempObjects need then to be created first

        query = "SELECT * FROM \"ChangeEventsToShotgun\" WHERE  NOT processed"
        if onlyEventIDs != None:
            query += " AND id = ANY(%s)"
            query += " ORDER BY created ASC, id ASC"
            self.cur.execute( query, (onlyEventIDs, ) )
        else:
            query += " ORDER BY created ASC, id ASC"
            self.cur.execute( query )
            
        descriptions = self.cur.description
        allOk = True
        for result in self.cur:
            eventDict = {}

            for i in range( len( descriptions ) ):
                if descriptions[i][0] == "changed_values":
                    if result[i] != None and result[i] != "" :
                        eventDict[descriptions[i][0]] = json.loads( result[i] )
                    else:
                        eventDict[descriptions[i][0]] = {}
                else:
                    eventDict[descriptions[i][0]] = result[i]

            stateOk = self._processChangeEvent( eventDict )
            if not stateOk:
                allOk = False

        return allOk

    def _processChangeEvent( self, changeEvent ):
        """ processes change-events """
        success = False
        debug.debug( changeEvent )

        corr_entity = changeEvent["corr_entity"]
        if changeEvent["task"] == "creation":
            debug.debug( "creating entity %s with local ID %d" % ( corr_entity.type,
                                                                   corr_entity.local_id ) )
            success = self._createEntity( changeEvent )
        elif changeEvent["task"] == "change":
            debug.debug( "changing entity %s with local ID %d" % ( corr_entity.type,
                                                                   corr_entity.local_id ) )
            success = self._changeEntity( changeEvent )
        elif changeEvent["task"] == "deletion":
            debug.debug( "deleting entity %s with local ID %d" % ( corr_entity.type,
                                                                   corr_entity.local_id ) )
            success = self._deleteEntity( changeEvent )
        elif changeEvent["task"] == "addLink":
            debug.debug( "adding link: %s with local ID %d" % ( corr_entity.type,
                                                                corr_entity.local_id ) )
            success = self._changeEntity( changeEvent )
        elif changeEvent["task"] == "removeLink":
            debug.debug( "removing link: %s with local ID %d" % ( corr_entity.type,
                                                                  corr_entity.local_id ) )
            success = self._changeEntity( changeEvent )

        return success

    def connectAndRun( self, onlyEventIDs = None ):
        if self._connect():
            self.cur = self.src.con.cursor()
            returner = self.queryAndProcess( onlyEventIDs )
            self.src.con.commit()
            self.cur.close()
            return returner
        else:
            return False

    def _setProcessed( self, event, exception = None ):
        query = "UPDATE \"ChangeEventsToShotgun\" SET processed = 't', exception = %s WHERE id=%s"
        if exception != None:
            exception += "\n%s" % traceback.format_exc()

        cur = self.src.con.cursor()
        debug.debug( cur.mogrify( query, ( exception, event["id"], ) ) )
        cur.execute( query, ( exception, event["id"], ) )
        cur.close()

    def _changeEntity( self, event ):
        """ process a change entity event
        """

        entity = event["corr_entity"]
        entityObj = getObject( entity.type,
                               remote_id = entity.remote_id,
                               local_id = entity.local_id,
                               includeRetireds = True )

        if entityObj == None:
            exception = "Object not available %s local:%s remote:%s\n\n" % ( str( entity.type ),
                                                                             str( entity.local_id ),
                                                                             str( entity.remote_id ) )

            self._setProcessed( event, exception = exception )
            return False

        data = event["changed_values"]

        fieldDefs = connectors.getClassOfType( entity.type ).shotgun_fields

        hasFields = True
        for attribute in data.keys():
            if not fieldDefs.has_key( attribute ):
                hasFields = False

        if not hasFields:
            exception = "some fields not available %s local:%s remote:%s" % ( str( entity.type ),
                                                                              str( entity.local_id ),
                                                                              str( entity.remote_id ) )
            self._setProcessed( event, exception = exception )
            return False
        else:
            for attribute in data.keys():
                dataType = fieldDefs[attribute]["data_type"]["value"]
                value = data[attribute]

                if dataType == "float":
                    data[attribute] = float( value )
                elif dataType == "entity":
                    data[attribute] = getSgObj( value )
                elif dataType == "multi_entity":
                    newvalue = []
                    for sgObj in value:
                        newvalue.append( getSgObj( sgObj ) )
                    data[attribute] = newvalue
                elif dataType == "date_time":
                    if type( value ) == type( u"" ):
                        data[attribute] = datetime.datetime.strptime( value, "%Y-%m-%d %H:%M:%S" )
                elif dataType == "date":
                    if type( value ) == type( u"" ):
                        data[attribute] = datetime.datetime.strptime( value, "%Y-%m-%d" ).date()
                elif dataType == "duration":
                    if type( value ) == float:
                        data[attribute] = int( value * 60 )

            if fieldDefs.has_key( "sg_remotely_updated_by" ):
                data["sg_remotely_updated_by"] = event["updated_by"].getSgObj()

            try:
                debug.debug( data )

                if entityObj.getType().endswith( "Connection" ) and entityObj.getRemoteID() == UNKNOWN_SHOTGUN_ID:
                    remoteID = connectors.getRemoteID( entityObj.getType(), entityObj.getLocalID() )
                    if remoteID == None or remoteID == UNKNOWN_SHOTGUN_ID:
                        # Connection-Entities need first the corresponding remote-id
                        # they get that by the shotgun-event triggered by the event that causes this connection-entity to be created
                        # so we simply have to wait and do nothing (hopefully ;)
                        return True

                self.sg.update( entityObj.getType(), entityObj.getRemoteID(), data )
                self._setProcessed( event )
                return True
            except shotgun_api3.Fault, fault:
                #event["type"] = "CouchdbChangeEvents"
                exception = "Error %s" % ( str( fault ) )
                self._setProcessed( event, exception = exception )
                return False


    def _createEntity( self, event ):
        """ process a create entity event """

        entity = event["corr_entity"]
        if type( entity.local_id ) == type( 1 ):
            try:
                obj = getObject( entity.type, local_id = entity.local_id, includeRetireds = True )

                if not obj:
                    exception = "Error %s with local_id %d does not exist anymore" % ( entity.type,
                                                                                       entity.local_id )
                    self._setProcessed( event, exception = exception )
                    return False

                data = obj.getShotgunDict()

                debug.debug( data )

                newdata = self.sg.create( entity.type, data )
                debug.debug( newdata )

                self.src.changeInDB( obj, "id", newdata["id"] )

                self._setProcessed( event )
                return True
            except AttributeError, fault:
                #event["type"] = "CouchdbChangeEvents"
                exception = "Error %s" % ( str( fault ) )
                self._setProcessed( event, exception = exception )
                return False
            except shotgun_api3.Fault, fault:
                #event["type"] = "CouchdbChangeEvents"
                exception = "Error %s" % ( str( fault ) )
                self._setProcessed( event, exception = exception )
                return False
        else:
            exception = "Entity %s has no local_id" % ( str( entity ) )
            self._setProcessed( event, exception = exception )
            return False

    def _deleteEntity( self, event ):
        """ process a delete entity event """

        entity = event["corr_entity"]
        obj = getObject( entity.type, local_id = entity.local_id, includeRetireds = True )


        if obj and obj.getRemoteID() != shotgun_replica.UNKNOWN_SHOTGUN_ID:
            try:
                self.src.delete( entity )
                self.sg.delete( entity.type, obj.getRemoteID() )
                self._setProcessed( event )
                return True
            except shotgun_api3.Fault, fault:
                exception = "Error %s" % ( str( fault ) )
                self._setProcessed( event, exception = exception )
                return False
        else:
            exception = "Entity %s does not exist or has no remote_id" % ( str( entity ) )
            self._setProcessed( event, exception = exception )
            return False

