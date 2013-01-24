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

    if type(entityType) == str:
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

def getObjects( entityType, filters = None, filterValues = None, orderby = None, limit = None, includeRetireds = False ):
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

    resultList = dbc.getListOfEntities( entityType,
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


def getListOfClients():
    """ return list of Projects """
    return ShotgunReplicaConnector()._getListOfEntities( Client, order = "code" )

def getListOfProjects():
    """ return list of Projects """
    # return ShotgunReplicaConnector()._getListOfEntities(Project, order = "name")
    return ShotgunReplicaConnector()._getListOfEntities( Project, order = "name", filterquery = "sg_pipelineVersion IS NULL" )

def getListOfAllProjects():
    """ return list of all Projects
    @deprecated:  take care on using this method
    """
    # return ShotgunReplicaConnector()._getListOfEntities(Project, order = "name")
    return ShotgunReplicaConnector()._getListOfEntities( Project, order = "name" )

def getListOfMyProjects():
    """ return list of Projects """
    myself = Entity( "HumanUser",
                    Configuration().get( CONF_SHOTGUN_USERID ) )

    return ShotgunReplicaConnector()._getListOfEntities( Project,
                                                         filterquery = "%s = ANY(users) and sg_pipelineVersion IS NULL",
                                                         variables = ( myself, ),
                                                         order = 'name' )

def getListOfTemplates( templateType ):
    """ return list of Task Templates"""
    return ShotgunReplicaConnector()._getListOfEntities( TaskTemplate,
                                                        order = "code",
                                                        filterquery = "entity_type = %s",
                                                        variables = ( templateType, ) )

def getListOfFileFormats():
    """ return list of FileFormat-Objects"""
    return ShotgunReplicaConnector()._getListOfEntities( FileFormat,
                                                        order = "code" )

def getFileFormats( name ):
    """ return list of FileFormat-Objects with corresponding name"""
    return ShotgunReplicaConnector()._getListOfEntities( FileFormat,
                                                        order = "code",
                                                        filterquery = "code = %s",
                                                        variables = ( name, ) )

def getListOfLUTs( name ):
    """ return list of LUT-Objects with corresponding name"""
    return ShotgunReplicaConnector()._getListOfEntities( LUT,
                                                        order = "code")

def getListOfImageSizes():
    """ return list of ImageSize-Objects"""
    return ShotgunReplicaConnector()._getListOfEntities( ImageSize, order = "code" )

def getImageSizes( name ):
    """ return list of ImageSize-Objects with corresponding name"""
    return ShotgunReplicaConnector()._getListOfEntities( ImageSize,
                                                        order = "code",
                                                        filterquery = "code = %s",
                                                        variables = ( name, ) )

def getListOfSteps( type = "Shot" ):
    """ return list of Tools """
    return ShotgunReplicaConnector()._getListOfEntities( Step,
                                                        order = "list_order",
                                                        filterquery = "entity_type = %s",
                                                        variables = ( type, ) )

