# -*- coding: utf-8 -*-

'''
handling entity manipulations that get synced back to shotgun
'''

import datetime
import json
from shotgun_replica import connectors, base_entity, factories
from shotgun_replica.utilities import debug, entityNaming
from shotgun_replica.connectors import getPgObj

CREATED_CHANGE_EVENTS = []
GENERATEEVENTS = True

def _createChangeEvent( src, task, corr_entity = None, changed_values = None ):

    global CREATED_CHANGE_EVENTS
    global GENERATEEVENTS

    if not GENERATEEVENTS:
        debug.debug( "not generating change event ( for testing purposes only )" )
        return

    updated_by = connectors.getPostgresUser()

    names = ["task", "updated_by"]
    values = [task, updated_by]

    if corr_entity != None:
        names.append( "corr_entity" )
        values.append( corr_entity )

    if changed_values != None:
        names.append( "changed_values" )
        values.append( changed_values )

    repls = ["%s"] * len( names )

    query = "INSERT INTO \"ChangeEventsToShotgun\" (%s) VALUES (%s)"
    query = query % ( ", ".join( names ), ", ".join( repls ) )

    cur = src.con.cursor()
    debug.debug( cur.mogrify( query, values ) )
    cur.execute( query, values )

    cur.execute( "SELECT currval('\"ChangeEventsToShotgun_id_seq\"')" )
    ( eventid, ) = cur.fetchone()
    CREATED_CHANGE_EVENTS.append( eventid )

    src.con.commit()

def setGenerateChangeEvents( dogenerate = True ):
    global GENERATEEVENTS
    global CREATED_CHANGE_EVENTS
    
    if dogenerate:
        message = "enabling "
    else:
        CREATED_CHANGE_EVENTS = []
        message = "disabling "

    message += "generation of change events"

    debug.info( message )
    GENERATEEVENTS = dogenerate

def removeCreatedChangeEvents():
    """
    method to get rid of change events that where created during unit and integration tests
    see tests_elefant.baseTest
    """
    global CREATED_CHANGE_EVENTS

#    debug.debug( CREATED_CHANGE_EVENTS )

    src = connectors.DatabaseModificator()
    cur = src.con.cursor()
    cur.execute( "DELETE FROM \"ChangeEventsToShotgun\" WHERE id = ANY(%s) AND task != %s", ( CREATED_CHANGE_EVENTS,
                                                                                              "deletion", ) )

    CREATED_CHANGE_EVENTS = []


def createEntity( myObj ):
    """
    create entity in local database and add corresponding change-events for shotgun-sync
    
    @return: local entity ID
    """


    src = connectors.DatabaseModificator()
    newID = src.add( myObj )

    object.__setattr__( myObj, "local_id", newID )

    _createChangeEvent( src, "creation",
                        corr_entity = myObj.getPgObj()
                        )

def changeEntity( myObj, changes ):
    """change entity in local database and add corresponding change-events for shotgun-sync"""

#    myObj.reload()

    src = connectors.DatabaseModificator()
    src.changeInDB( myObj, changes = changes )

    for ( key, value ) in changes.iteritems():
        if type( value ) == datetime.datetime:
            changes[key] = value.strftime( "%Y-%m-%d %H:%M:%S" )
        if type( value ) == datetime.date:
            changes[key] = value.strftime( "%Y-%m-%d" )
        elif type( value ) == datetime.timedelta:
            changes[key] = float( value.days ) * 24 + float( value.seconds ) / 3600
        elif type( value ) == connectors.PostgresEntityType:
            changes[key] = value.getShortDict()
        elif isinstance( value, base_entity.ShotgunBaseEntity ):
            changes[key] = value.getShortDict()
        elif type( value ) == type( [] ):
            changes[key] = []
            for entry in value:
                if isinstance( entry, base_entity.ShotgunBaseEntity ) or type( entry ) == connectors.PostgresEntityType:
                    changes[key].append( entry.getShortDict() )
                else:
                    changes[key].append( entry )




            attributeName = key
            fieldValues = value
            entityType = myObj.getType()

            connEntityName = entityNaming.getConnectionEntityName( entityType, attributeName )

            if connEntityName != None:

                reverseAttribute = entityNaming.getReverseAttributeName( entityType, attributeName )
                linkedEntityType = myObj.shotgun_fields[attributeName]["properties"]["valid_types"]["value"][0]
                baseEntityType = entityType

                ( baseAttrName, linkedAttrName ) = entityNaming.getConnectionEntityAttrName( baseEntityType,
                                                                                         linkedEntityType,
                                                                                         connEntityName )

                basePgObj = myObj.getPgObj()

                # get connections
                filters = "%s=%s" % ( baseAttrName,
                                      "%s"
                                      )
                filterValues = [ basePgObj ]
                connections = factories.getObjects( connEntityName,
                                                    filters,
                                                    filterValues )

                # create new connection entities
                for linkedDict in changes[key]:
                    linkedPostgresObj = getPgObj( linkedDict )
                    fieldNames = [ baseAttrName, linkedAttrName ]
                    fieldValues = [ basePgObj, linkedPostgresObj ]

                    # check if existing first
                    connectionExists = False
                    for i in range( len( connections ) ):
                        connection = connections[i]
                        if connection.getRawField( linkedAttrName ) == linkedPostgresObj:
                            connections.remove( connection )
                            connectionExists = True
                            break

                    if not connectionExists:
                        debug.debug( dict( zip( fieldNames, fieldValues ) ), prefix = "OOOOOOOOO" )
                        src._addToDatabase( connEntityName, fieldValues, fieldNames )

                    # setting reverse attribute as well
                    linkedObj = factories.getObject( linkedDict["type"],
                                                     local_id = linkedDict["__local_id"],
                                                     remote_id = linkedDict["id"] )
                    retValues = linkedObj.getRawField( reverseAttribute )

                    if retValues == None:
                        retValues = []

                    if basePgObj not in retValues:
                        retValues.append( basePgObj )
                        src.changeInDB( linkedObj, reverseAttribute, retValues )


                # delete unused connection entities

                for connection in connections:
                    linkedObj = connection.getField( linkedAttrName )
                    retValues = linkedObj.getRawField( reverseAttribute )

                    retValues.remove( basePgObj )
                    src.changeInDB( linkedObj, reverseAttribute, retValues )
                    src.delete( connection )


    _createChangeEvent( src, "change",
                        corr_entity = myObj.getPgObj(),
                        changed_values = json.dumps( changes )
                        )

    return myObj



def deleteEntity( myObj ):
    """delete an entity in couchdb and shotgun"""
    src = connectors.DatabaseModificator()
    src.changeInDB( myObj, "__retired", True )

    _createChangeEvent( src, "deletion",
                        corr_entity = myObj.getPgObj() )

    if myObj.getType() == "Task":
        pEntity = myObj.entity
        src.changeInDB( pEntity, "tasks", myObj.getSgObj(), doRemove = True )

    src.con.commit()
