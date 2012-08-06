
import datetime
import shotgun_api3
import time
import sys
import json

from shotgun_replica.conversions import PostgresEntityType
from shotgun_replica.factories import getObject
from shotgun_replica import config, connectors
import shotgun_replica

import logging
import traceback

LOCALDB_FAILURE = 1
SHOTGUN_FAILURE = 2
SEVERE_FAILURE = 250

class LocalDBEventSpooler( object ):
    """ Continuously spools events from couchdb and transfers them to shotgun """

    src = None # local database connector
    cur = None
    sg = None

    def connect( self ):
        """ establish the connections
        
        establish a connection to local server and shotgun
        """
        try:
            self.src = connectors.DatabaseConnector()
        except Exception, error: #IGNORE:W0703
            logging.error( "Unable to connect to database server. " + unicode( error ) )
            return False

        try:
            self.sg = shotgun_api3.Shotgun( config.SHOTGUN_URL,
                                            config.SHOTGUN_BACKSYNC_SKRIPT,
                                            config.SHOTGUN_BACKSYNC_KEY )
        except Exception, error: #IGNORE:W0703
            logging.error( "Unable to connect to Shotgun server. " + unicode( error ) )
            return False

        return True

    def queryAndProcess( self ):
        """ queries and processes events from shotgun
        
        this method is mainly used from the run method but also for testing purposes
        """

        # for temporary objects only
        # query first changeEvents, and then tempObject
        # tempObjects need then to be created first

        query = "SELECT * FROM \"ChangeEventsToShotgun\" WHERE" + \
            " NOT processed ORDER BY created ASC, id ASC"
        self.cur.execute( query )
        descriptions = self.cur.description
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

            self._processChangeEvent( eventDict )


    def _processChangeEvent( self, changeEvent ):
        """ processes change-events """
        success = False
        logging.debug( changeEvent )
        logging.debug( "HALLLO" )

        corr_entity = changeEvent["corr_entity"]
        if changeEvent["task"] == "creation":
            logging.debug( "creating entity %s with local ID %d",
                           corr_entity.type,
                           corr_entity.local_id )
            success = self._createEntity( changeEvent )
        elif changeEvent["task"] == "change":
            logging.debug( "changing entity %s with local ID %d",
                           corr_entity.type,
                           corr_entity.local_id )
            success = self._changeEntity( changeEvent )
        elif changeEvent["task"] == "deletion":
            logging.debug( "deleting entity %s with local ID %d",
                           corr_entity.type,
                           corr_entity.local_id )
            success = self._deleteEntity( changeEvent )
        elif changeEvent["task"] == "addLink":
            logging.debug( "adding link: %s with local ID %d",
                           corr_entity.type,
                           corr_entity.local_id )
            success = self._changeEntity( changeEvent )
        elif changeEvent["task"] == "removeLink":
            logging.debug( "removing link: %s with local ID %d",
                           corr_entity.type,
                           corr_entity.local_id )
            success = self._changeEntity( changeEvent )
        if success:
            self._setProcessed( changeEvent )

    def processIteration( self ):
        if self.connect():
            self.cur = self.src.con.cursor()
            self.queryAndProcess()
            self.src.con.commit()
            self.cur.close()
            time.sleep( 2 )

    def run( self ):
        """ starts the loop of quering, processing pausing """
        while True:
            self.processIteration()

    def _setProcessed( self, event, exception = None ):
        query = "UPDATE \"ChangeEventsToShotgun\" SET processed = 't', exception = %s WHERE id=%s"
        if exception != None:
            exception += "\n%s" % traceback.format_exc()

        cur = self.src.con.cursor()
        logging.debug( cur.mogrify( query, ( exception, event["id"], ) ) )
        cur.execute( query, ( exception, event["id"], ) )
        cur.close()

    def _changeEntity( self, event ):
        """ process a change entity event
        """

        entity = event["corr_entity"]
        entityObj = getObject( entity.type,
                               remote_id = entity.remote_id,
                               local_id = entity.local_id )

        if entityObj == None:
            exception = "Object not available %s local:%s remote:%s" % ( str( entity.type ),
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
                    value = float( value )
                elif dataType == "entity":
                    if type( value ) == PostgresEntityType:
                        data[attribute] = value.getSgObj()
                elif dataType == "multi_entity":
                    for sgObj in value:
                        if type( sgObj ) == PostgresEntityType:
                            sgObj = sgObj.getSgObj()
                elif dataType == "date_time":
                    if type( value ) == type( u"" ):
                        data[attribute] = datetime.datetime.strptime( value, "%Y-%m-%d %H:%M:%S" )
                elif dataType == "duration":
                    if type( value ) == float:
                        data[attribute] = int( value * 60 )

            if fieldDefs.has_key( "sg_remotely_updated_by" ):
                data["sg_remotely_updated_by"] = event["updated_by"].getSgObj()

            try:
                logging.debug( data )
                self.sg.update( entityObj.getType(), entityObj.getRemoteID(), data )
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
                obj = getObject( entity.type, local_id = entity.local_id )
                if not obj:
                    exception = "Error %s with local_id %d does not exist anymore" % ( entity.type,
                                                                                       entity.local_id )
                    self._setProcessed( event, exception = exception )
                    return False

                data = obj.getShotgunDict()

                newdata = self.sg.create( entity.type, data )
                logging.debug( newdata )

                self.src.changeInDB( obj, "id", newdata["id"] )

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
        entityObj = getObject( entity.type,
                               local_id = entity.local_id,
                               remote_id = entity.remote_id )

        if entityObj and entityObj.getRemoteID() != shotgun_replica.UNKNOWN_SHOTGUN_ID:
            try:
                self.sg.delete( entity.type, entityObj.getRemoteID() )
                return True
            except shotgun_api3.Fault, fault:
                exception = "Error %s" % ( str( fault ) )
                self._setProcessed( event, exception = exception )
                return False
        else:
            exception = "Entity %s does not exist or has no remote_id" % ( str( entity ) )
            self._setProcessed( event, exception = exception )
            return False


if __name__ == "__main__":
    spooler = LocalDBEventSpooler()
    logging.basicConfig( level = logging.DEBUG,
                         stream = sys.stdout )
    spooler.run()
