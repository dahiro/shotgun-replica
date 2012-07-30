# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''

from shotgun_replica import connectors
import os
import json

def getObject( entityType, remote_id = None, local_id = None ):
    """ return object of a specific type
    
    @return: the object or None if object not available
    """

    dbc = connectors.DatabaseConnector()

    filters = []

    if remote_id != None:
        filters.append( "id=%d" % remote_id )
    if local_id != None:
        filters.append( "__local_id=%d" % local_id )

    sqlFilter = " OR ".join( filters )

    resultList = dbc.getListOfEntities( entityType, sqlFilter )

    if len( resultList ) == 1:
        return resultList[0]
    else:
        return None

def getObjects( entityType, filters, filterValues ):
    dbc = connectors.DatabaseConnector()
    resultList = dbc.getListOfEntities( entityType, filters, variables = filterValues )
    return resultList
