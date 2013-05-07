# -*- coding: utf-8 -*-

'''
module to retrieve entities from the database
'''

from shotgun_replica import connectors, base_entity, UNKNOWN_SHOTGUN_ID
import os
import json
from shotgun_replica.utilities import debug, entityNaming
import re


def getObject( entityType, local_id = None, remote_id = None, includeRetireds = False ):
    """ return entity of a specific type with given IDs

    :py:class:`shotgun_replica.entities.Task`

    :param entityType: either a entities-class or a string (ex. "CustomEntity22")
    :type entityType: class or str
    :param local_id: the local id of the object
    :param remote_id: the remote id (shotgun) of the object
    :param includeRetireds: include retired (deleted) objects
    
    :rtype: object or None if object not available
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
    
    :param entityType: either a entities-class or a string (ex. "CustomEntity22")
    :type entityType: class or str
    :param filters: string with SQL-style filters (example "sg_link=%s")
    :param filterValues: list with variables that are passed to the sql-statement for %x-style variables
    :param orderby: SQL-ish order-by-string
    :param limit:  SQL-ish limit-string
    :param includeRetireds: include retired (deleted) objects
    
    :rtype: array with matching entities
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
    
    :param baseObj:   entity that has the given attribute
    :param linkedObj: entity that is linked in the given attribute
    :param attribute: attribute name of baseObj-parameter
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

IDENTIFY_REGEX = r"\(\'([a-zA-Z0-9\-\_]+)\'\,(\-?\d+)\,(\-?\d+)\)"

def getObjectByIdentifier( identifier ):
    ## return object by its identifier
    # 
    # @param identifier: string à la "('CustomEntity24,-1,239)"
    # @return: object if available/found or None if not
     
    identObject = None
    mObj = re.match( IDENTIFY_REGEX, identifier )
    if mObj:
        identObject = getObject( mObj.group( 1 ),
                                 local_id = int( mObj.group( 2 ) ),
                                 remote_id = int( mObj.group( 3 ) ) )
    return identObject
