# -*- coding: utf-8 -*-

from shotgun_replica import entity_manipulation, UNKNOWN_SHOTGUN_ID, \
    factories, connectors
from shotgun_replica import base_entity

import shotgun_replica
import datetime
from shotgun_replica.utilities import debug
from shotgun_replica.connectors import PostgresEntityType

class _ShotgunEntity( base_entity.ShotgunBaseEntity ):
    """
    baseclass for shotgun-entities
    """

    _changed_values = []

    def __init__( self, *args, **kwargs ):
        self._changed_values = []

        if kwargs.has_key( "__data" ) and kwargs.has_key( "__names" ):
            data = kwargs.pop( "__data" )
            names = kwargs.pop( "__names" )

            for i in range( len( data ) ):
                if names[i] == "id":
                    object.__setattr__( self, "remote_id", data[i] )
                elif names[i] == "__local_id":
                    object.__setattr__( self, "local_id", data[i] )
                else:
                    object.__setattr__( self, names[i], data[i] )

        object.__init__( self, *args, **kwargs )

    def __str__( self ):
        return super( _ShotgunEntity, self ).__str__() + " %d,%d" % ( self.getLocalID(), self.getRemoteID() )

    def __repr__( self, *args, **kwargs ):
        return super( _ShotgunEntity, self ).__repr__() + " %d,%d" % ( self.getLocalID(), self.getRemoteID() )

    def getType( self ):
        """
        return Shotgun-Type of this entity
        """

        return self._type

    def getRemoteID( self ):
        """
        get ID that is used in shotgun
        """
        if self.remote_id:
            return self.remote_id
        else:
            return UNKNOWN_SHOTGUN_ID

    def getLocalID( self ):
        """
        get ID that is used in local database (for instant object creation)
        """
        if self.local_id:
            return self.local_id
        else:
            return UNKNOWN_SHOTGUN_ID

    def getSgObj( self ):
        """
        get minimal dict for use with shotgun (jsonable) 
        
        @return: returns None if not yet in shotgun
        """

        remote_id = self.getRemoteID()

        if remote_id == None or remote_id == shotgun_replica.UNKNOWN_SHOTGUN_ID:
            remote_id = connectors.getRemoteID( self.getType(), self.getLocalID() )

        if remote_id == None or remote_id == shotgun_replica.UNKNOWN_SHOTGUN_ID:
            return None
        else:
            return {'type': self.getType(),
                    'id': remote_id
                    }

    def getShortDict( self ):
        """
        get smallest possible dict that identifies an object
        """
        return {
            "type": self.getType(),
            "id": self.getRemoteID(),
            "__local_id": self.getLocalID(),
        }

    def getPgObj( self ):
        """
        get shortest postgres-representation of an entity
        """
        return connectors.PostgresEntityType( self.getType(),
                                               self.getLocalID(),
                                               self.getRemoteID() )

    def __setattr__( self, *args, **kwargs ):
        name = args[0]
        value = args[1]

        old_value = self.__getattribute__( name )
        if old_value != value:
            # changed values
            object.__setattr__( self, "%s__old" % name, old_value )
            self._changed_values.append( name )

        return object.__setattr__( self, *args, **kwargs )

    def getField( self, fieldname ):
        """
        get field value of this object
        """
        return self.__getattribute__( fieldname )

    def getRawField( self, fieldname ):
        """
        get raw field value and do not retrieve linked objects from db
        """
        return object.__getattribute__( self, fieldname )

    def getDict( self ):
        """
        @return: returns json-like dict for use in further json-using interfaces
        """
        dataDict = {}
        if self.getLocalID() != None:
            dataDict["__local_id"] = self.getLocalID()

        for ( fieldname, fielddef ) in self.shotgun_fields.iteritems():

            dataFieldname = fieldname

            if fieldname == "id":
                dataFieldname = "remote_id"

            if fielddef["data_type"]["value"] in ["pivot_column",
                                                  "summary"]:
                continue

            fieldvalue = object.__getattribute__( self, dataFieldname )
            if fieldvalue == None:
                pass
            elif fielddef["data_type"]["value"] == "entity":

                if type( fieldvalue ) == connectors.PostgresEntityType:
                    fieldvalue = fieldvalue.getShortDict()
                elif isinstance( fieldvalue, base_entity.ShotgunBaseEntity ):
                    fieldvalue = fieldvalue.getShortDict()

            elif fielddef["data_type"]["value"] == "multi_entity":
                storevalue = []

                for singleFieldvalue in fieldvalue:

                    if type( singleFieldvalue ) == connectors.PostgresEntityType:
                        storevalue.append( singleFieldvalue.getShortDict() )
                    elif isinstance( fieldvalue, base_entity.ShotgunBaseEntity ):
                        storevalue.append( singleFieldvalue.getShortDict() )
                fieldvalue = storevalue

            elif fielddef["data_type"]["value"] == "date_time":
                if type( fieldvalue ) == datetime.datetime:
                    fieldvalue = fieldvalue.strftime( "%Y-%m-%d %H:%M:%S" )

            elif fielddef["data_type"]["value"] == "date":
                if type( fieldvalue ) == datetime.date:
                    fieldvalue = fieldvalue.strftime( "%Y-%m-%d" )

            dataDict[fieldname] = fieldvalue

        return dataDict

    def getShotgunDict( self ):
        """
        removes all read-only-attributes
        
        @return: returns json-like dict for shotgun-storage
        """

        dataDict = {}
        removeKeys = [ "type", "id", "__local_id", "current_user_favorite" ]

        for ( fieldname, fielddef ) in self.shotgun_fields.iteritems():
            if fieldname in removeKeys:
                continue

            dataFieldname = fieldname

            if fieldname == "id":
                dataFieldname = "remote_id"

            if fielddef["data_type"]["value"] in ["pivot_column",
                                                  "summary"]:
                continue

            fieldvalue = object.__getattribute__( self, dataFieldname )
            if fieldvalue == None:
                continue

            if ( not fielddef["editable"]["value"] ):
                continue

            if fielddef["data_type"]["value"] == "entity":
                if type( fieldvalue ) == connectors.PostgresEntityType or \
                        isinstance( fieldvalue, base_entity.ShotgunBaseEntity ):
                    fieldvalue = fieldvalue.getSgObj()
                    if fieldvalue == None:
                        continue

            elif fielddef["data_type"]["value"] == "multi_entity":
                storevalue = []
                for singleFieldvalue in fieldvalue:
                    if ( type( singleFieldvalue ) == connectors.PostgresEntityType ) \
                            or isinstance( fieldvalue, base_entity.ShotgunBaseEntity ):
                        valToAppend = singleFieldvalue.getSgObj()
                        if valToAppend != None:
                            storevalue.append( valToAppend )
                fieldvalue = storevalue

            elif fielddef["data_type"]["value"] == "date_time":
                if type( fieldvalue ) == datetime.datetime:
                    fieldvalue = fieldvalue.strftime( "%Y-%m-%d %H:%M:%S" )

            elif fielddef["data_type"]["value"] == "date":
                if type( fieldvalue ) == datetime.date:
                    fieldvalue = fieldvalue.strftime( "%Y-%m-%d" )

            dataDict[fieldname] = fieldvalue

        return dataDict

    def loadFromDict( self, dataDict ):
        """
        sets attributes from a dict-object
        """

        for fieldname in dataDict.keys():

            if not self.shotgun_fields.has_key( fieldname ):
                continue

            fieldvalue = dataDict[ fieldname ]
            if type( fieldvalue ) == dict:
                try:
                    fieldvalue = PostgresEntityType( fieldvalue["type"],
                                                     fieldvalue["__local_id"],
                                                     fieldvalue["id"] )
                except KeyError:
                    pass

            self.__setattr__( fieldname, fieldvalue )

        return dataDict

    def __getattribute__( self, *args, **kwargs ):
        name = args[0]

        if name == "id":
            name = "remote_id"
        if name == "sg_local_id":
            name = "local_id"

        fieldvalue = object.__getattribute__( self, name )
        if fieldvalue == None:
            return None

        fielddef = object.__getattribute__( self, "shotgun_fields" )

        if fielddef.has_key( name ):
            if fielddef[name]["data_type"]["value"] == "entity":
                entityObj = fieldvalue

                if type( entityObj ) == connectors.PostgresEntityType:
                    return factories.getObject( entityObj.type,
                                                remote_id = entityObj.remote_id,
                                                local_id = entityObj.local_id )
                else:
                    return entityObj
            elif fielddef[name]["data_type"]["value"] == "multi_entity":
                entityObjArray = fieldvalue
                entityList = []
                for entityObj in entityObjArray:
                    if type( entityObj ) == connectors.PostgresEntityType:

                        obj = factories.getObject( entityObj.type,
                                                   remote_id = entityObj.remote_id,
                                                   local_id = entityObj.local_id )
                        if obj:
                            entityList.append( obj )
                    else:
                        entityList.append( entityObj )
                return entityList

        return fieldvalue

    def __cmp__( self, objB ):
        if objB == None:
            return -99999
        if isinstance( objB, base_entity.ShotgunBaseEntity ):
            if objB.getType() == self.getType():
                if self.getRemoteID() != UNKNOWN_SHOTGUN_ID and objB.getRemoteID() != UNKNOWN_SHOTGUN_ID:
                    return cmp( self.getRemoteID(), objB.getRemoteID() )
                else:
                    return cmp( self.getLocalID(), objB.getLocalID() )
            else:
                return cmp( self.getType(), objB.getType() )
        else:
            return -99999

    def save( self ):
        """
        save this objects state to database. creates a new record or updates the existing record 
        """
        if not self.isConsistent():

            debug.debug( "changing localID: %s" % str( self.getLocalID() ) )

            if self.getLocalID() == None or self.getLocalID() == shotgun_replica.UNKNOWN_SHOTGUN_ID:
                # insert entity in local database
                entity_manipulation.createEntity( self )
            else:
                changes = {}
                for attribute_name in self._changed_values:
                    changes[attribute_name] = object.__getattribute__( self, attribute_name )

                entity_manipulation.changeEntity( self, changes )

                self._changed_values = []
        else:
            debug.debug( "nothing changed" )
            return True

    def delete( self ):
        """ delete this object instance 
        """

        entity_manipulation.deleteEntity( self )
        return None

    def isRetired( self ):
        return self.__retired

    def isConsistent( self ):
        """ checks weather there are any changed values 
        """
        return len( self._changed_values ) == 0
