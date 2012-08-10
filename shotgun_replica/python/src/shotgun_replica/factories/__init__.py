# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''

from shotgun_replica import connectors, base_entity
import os
import json
import logging

def getObject( entityType, remote_id = None, local_id = None ):
    """ return object of a specific type
    
    @return: the object or None if object not available
    """

    tableName = connectors.getClassOfType( entityType )._type

    dbc = connectors.DatabaseConnector()

    filters = []

    if remote_id != None:
        filters.append( "id=%d" % remote_id )
    if local_id != None:
        filters.append( "__local_id=%d" % local_id )

    sqlFilter = " OR ".join( filters )

    resultList = dbc.getListOfEntities( tableName, sqlFilter, limit = "1" )

    if len( resultList ) == 1:
        return resultList[0]
    else:
        return None

def getObjects( entityType, filters, filterValues, orderby = None, limit = None ):
    dbc = connectors.DatabaseConnector()
    for filterValue in filterValues:
        if isinstance( filterValue, base_entity.ShotgunBaseEntity ):
            filterValues.remove( filterValue )
            filterValues.append( filterValue.getPgObj() )

    logging.debug( filterValues )
    resultList = dbc.getListOfEntities( entityType,
                                        filters,
                                        variables = filterValues,
                                        order = orderby,
                                        limit = limit )
    return resultList
