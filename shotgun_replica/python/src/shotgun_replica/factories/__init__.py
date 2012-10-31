# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''

from shotgun_replica import connectors, base_entity, UNKNOWN_SHOTGUN_ID
import os
import json
from shotgun_replica.utilities import debug

def getObject( entityType, local_id = None, remote_id = None, includeRetireds = False ):
    """ return object of a specific type
    
    @return: the object or None if object not available
    """

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
    
    if includeRetireds:
        sqlFilter = " OR ".join( filters )
    else:
        sqlFilter = "NOT __retired AND " + " OR ".join( filters )

    resultList = dbc.getListOfEntities( tableName, sqlFilter, limit = "1" )

    if len( resultList ) == 1:
        return resultList[0]
    else:
        return None

def getObjects( entityType, filters, filterValues, orderby = None, limit = None, includeRetireds = False ):
    dbc = connectors.DatabaseModificator()
    for filterValue in filterValues:
        if isinstance( filterValue, base_entity.ShotgunBaseEntity ):
            filterValues.remove( filterValue )
            filterValues.append( filterValue.getPgObj() )
    
    if not includeRetireds:
        filters = "NOT __retired AND ( " + filters + " )"

    resultList = dbc.getListOfEntities( entityType,
                                        filters,
                                        variables = filterValues,
                                        order = orderby,
                                        limit = limit )
    return resultList
