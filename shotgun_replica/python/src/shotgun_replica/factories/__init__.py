# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''

from shotgun_replica import connectors, base_entity, UNKNOWN_SHOTGUN_ID
import os
import json
from shotgun_replica.utilities import debug, entityNaming


def getObject( entityType, local_id = None, remote_id = None, includeRetireds = False ):
    """ return object of a specific type

    @return: the object or None if object not available
    """
    classObj = entityType

    if type( entityType ) == str or type( entityType ) == unicode:
        classObj = connectors.getClassOfType( entityType )
        if not classObj:
            return None

    tableName = classObj._type

    dbc = connectors.DatabaseModificator()

    filters = []

    if remote_id != None and remote_id != UNKNOWN_SHOTGUN_ID:
        filters.append( "id=%d" % remote_id )
    if local_id != None and local_id != UNKNOWN_SHOTGUN_ID:
        filters.append( "__local_id=%d" % local_id )

    if len( filters ) == 0:
        return None

    if includeRetireds:
        sqlFilter = " OR ".join( filters )
    else:
        sqlFilter = "NOT __retired AND " + " OR ".join( filters )

    resultList = dbc.getListOfEntities( tableName, sqlFilter, limit = "1" )

    if len( resultList ) == 1:
        return resultList[0]
    else:
        return None


def getObjects( entityType, filters = None, filterValues = None, orderby = None,
               limit = None, includeRetireds = False ):
    """ return objects of a specific type

    @return: the objects or [] if object not available
    """

    if type( entityType ) == str or type( entityType ) == unicode:
        tableName = entityType
    else:
        tableName = entityType._type

    dbc = connectors.DatabaseModificator()
    pgFilterValues = []
    if filterValues != None:
        for filterValue in filterValues:
            pgFilterValues.append( connectors.getPgObj( filterValue ) )

    if not includeRetireds:
        if filters == None:
            filters = "NOT __retired"
        else:
            filters = "NOT __retired AND ( " + filters + " )"

    resultList = dbc.getListOfEntities( tableName,
                                       filters,
                                       variables = pgFilterValues,
                                       order = orderby,
                                       limit = limit )
    return resultList


def getConnectionObj( baseObj, linkedObj, attribute ):
    """
    return the connection obj of two connected entities
    """
    connEntityName = entityNaming.getConnectionEntityName( baseObj.getType(), attribute )

    if connEntityName:
        ( baseAttrName, linkedAttrName ) = entityNaming.getConnectionEntityAttrName( baseObj.getType(),
                                                                                 linkedObj.getType(),
                                                                                 connEntityName )

        filters = "%s=%s and %s=%s" % ( baseAttrName,
                                        "%s",
                                        linkedAttrName,
                                        "%s"
                                      )
        filterValues = [ baseObj.getPgObj(), linkedObj.getPgObj() ]

        objs = getObjects( connEntityName, filters, filterValues )
        if len( objs ) == 1:
            return objs[0]
        elif len( objs ) > 1:
            return objs
    return None
