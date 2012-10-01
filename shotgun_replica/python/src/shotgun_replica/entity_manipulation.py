# -*- coding: utf-8 -*-

'''
Created on Jun 20, 2012

@author: bach
'''
import datetime
import json
import logging
from shotgun_replica import connectors, base_entity
from shotgun_replica.utilities import debug

def _createChangeEvent( src, task, corr_entity = None, changed_values = None ):

    updated_by = connectors.getPostgresUser()

    names = ["task", "updated_by"]
    values = [task, updated_by]
    
    if corr_entity != None:
        names.append("corr_entity")
        values.append(corr_entity)
    
    if changed_values != None:
        names.append("changed_values")
        values.append(changed_values)

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

    object.__setattr__(myObj, "local_id", newID)

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
            changes[key] = value.getSgObj()
        elif isinstance( value, base_entity.ShotgunBaseEntity ):
            changes[key] = value.getSgObj()

    _createChangeEvent( src, "change", 
                        corr_entity = myObj.getPgObj(),
                        changed_values = json.dumps( changes )
                        )

    return myObj


def deleteEntity( myObj ):
    """delete an entity in couchdb and shotgun"""
    src = connectors.DatabaseModificator()
    src.delete(myObj)
    
    _createChangeEvent( src, "deletion", 
                        corr_entity = myObj.getPgObj())

    if myObj.getType() == "Task":
        pEntity = myObj.entity
        src.changeInDB( pEntity, "tasks", myObj.getSgObj(), doRemove = True )

    src.con.commit()


