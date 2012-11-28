# -*- coding: utf-8 -*-

'''
Created on Jun 20, 2012

@author: bach
'''
import datetime
import json
from shotgun_replica import connectors, base_entity, factories
from shotgun_replica.utilities import debug, entityNaming
from shotgun_replica.connectors import getPgObj

def _createChangeEvent( src, task, corr_entity = None, changed_values = None ):

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
    src.con.commit()

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
                targetType = myObj.shotgun_fields[attributeName]["properties"]["valid_types"]["value"][0]

                ( srcAttrName, dstAttrName ) = entityNaming.getConnectionEntityAttrName( entityType,
                                                                                         targetType,
                                                                                         connEntityName )

                tgPgObj = myObj.getPgObj()

                # get connections
                filters = "%s=%s" % ( dstAttrName,
                                      "%s"
                                      )
                filterValues = [ tgPgObj ]
                connections = factories.getObjects( connEntityName,
                                                    filters,
                                                    filterValues )

                # create new connection entities
                for targetDict in changes[key]:
                    srcPostgresObj = getPgObj( targetDict )
                    fieldNames = [ dstAttrName, srcAttrName ]
                    fieldValues = [ tgPgObj, srcPostgresObj ]

                    # check if existing first
                    connectionExists = False
                    for i in range( len( connections ) ):
                        connection = connections[i]
                        if connection.getRawField( srcAttrName ) == srcPostgresObj:
                            connections.remove( connection )
                            connectionExists = True
                            break

                    if not connectionExists:
                        src._addToDatabase( connEntityName, fieldValues, fieldNames )

                    # setting reverse attribute as well
                    targetObj = factories.getObject( targetDict["type"],
                                                     local_id = targetDict["__local_id"],
                                                     remote_id = targetDict["id"] )
                    retValues = targetObj.getRawField( reverseAttribute )

                    if retValues == None:
                        retValues = []

                    if tgPgObj not in retValues:
                        retValues.append( tgPgObj )
                        src.changeInDB( targetObj, reverseAttribute, retValues )


                # delete unused connection entities

                for connection in connections:
                    targetObj = connection.getField( srcAttrName )
                    retValues = targetObj.getRawField( reverseAttribute )
                    
                    retValues.remove( tgPgObj )
                    src.changeInDB( targetObj, reverseAttribute, retValues )
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
