# -*- coding: utf-8 -*-

from shotgun_replica import entity_manipulation, conversions
from shotgun_replica.conversions import PostgresEntityType
from shotgun_replica import base_entity 

import logging
import shotgun_replica

class _ShotgunEntity( base_entity.ShotgunBaseEntity ):
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

    def getType( self ):
        """
        return Shotgun-Type of this entity
        """

        return self._type

    def getID( self ):
        """
        return Shotgun-ID of this entity
        @deprecated: now two ids used
        """

        return self.getRemoteID()

    def getRemoteID( self ):
        return self.remote_id

    def getLocalID( self ):
        return self.local_id

    def getSgObj( self ):
        """
        get minimal dict for use with shotgun (jsonable) 
        
        @return: returns None if not yet in shotgun
        """

        remote_id = self.getRemoteID()
        if remote_id == None or remote_id == shotgun_replica.UNKNOWN_SHOTGUN_ID:
            return None
        else:
            return {'type': self.getType(),
                    'id': remote_id
                    }

    def getShortDict( self ): 
        return {
            "type": self.getType(),
            "remote_id": self.getRemoteID(),
            "local_id": self.getLocalID(),
        }

    def getPgObj( self ):
        return conversions.PostgresEntityType( self.getType(),
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
        return self.__getattribute__( fieldname )

    def getShotgunDict( self ):
        """
        removes all read-only-attributes
        
        @return: returns json-like dict for shotgun-storage
        """
        dataDict = {}
        for ( fieldname, fielddef ) in self.shotgun_fields.iteritems():

            dataFieldname = fieldname

            if fieldname == "id":
                dataFieldname = "remote_id"

            if fielddef["data_type"]["value"] in ["pivot_column",
                                                  "image",
                                                  "summary"]:
                continue

            if not fielddef["editable"]["value"]:
                continue

            fieldvalue = object.__getattribute__( self, dataFieldname )
            if fieldvalue == None:
#                dataDict[fieldname] = None
                continue

            if fielddef["data_type"]["value"] == "entity":

                if type( fieldvalue ) == PostgresEntityType:
                    fieldvalue = fieldvalue.getSgObj()
                elif isinstance( fieldvalue, base_entity.ShotgunBaseEntity ):
                    fieldvalue = fieldvalue.getSgObj()

            elif fielddef["data_type"]["value"] == "multi_entity":
                storevalue = []

                for singleFieldvalue in fieldvalue:

                    if type( singleFieldvalue ) == PostgresEntityType:
                        storevalue.append( singleFieldvalue.getSgObj() )
                    elif isinstance( fieldvalue, base_entity.ShotgunBaseEntity ):
                        storevalue.append( singleFieldvalue.getSgObj() )
                fieldvalue = storevalue

            dataDict[fieldname] = fieldvalue

        return dataDict

    def loadFromDict( self, dataDict ):
        """
        sets attributes from a dict-object
        """
        
        for fieldname in dataDict.keys():
            
            if not self.shotgun_fields.has_key(fieldname):
                continue

            fieldvalue = dataDict[ fieldname ]
                
            self.__setattr__(fieldname, fieldvalue)

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

                if type( entityObj ) == PostgresEntityType:
                    from shotgun_replica import factories
                    return factories.getObject( entityObj.type,
                                                remote_id = entityObj.remote_id,
                                                local_id = entityObj.local_id )
                else:
                    return entityObj
            elif fielddef[name]["data_type"]["value"] == "multi_entity":
                entityObjArray = fieldvalue

                entityList = []
                for entityObj in entityObjArray:
                    if type( entityObj ) == PostgresEntityType:
                        from shotgun_replica import factories
                        entityList.append( factories.getObject( entityObj.type,
                                                                remote_id = entityObj.remote_id,
                                                                local_id = entityObj.local_id ) )
                    else:
                        entityList.append( entityObj )
                return entityList

        return fieldvalue

    def __cmp__( self, objB ):
        if objB == None:
            return -99999
        if isinstance( objB, base_entity.ShotgunBaseEntity ):
            if objB.getType() == self.getType():
                return cmp( self.getID(), objB.getID() )
            else:
                return cmp( self.getType(), objB.getType() )
        else:
            return -99999

    def save( self ):
        if not self.isConsistent():

            logging.debug( "changing localID: %s" % str( self.getLocalID() ) )

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
            logging.debug( "nothing changed" )
            return True

    def delete( self ):
        """ delete this object instance 
        """

        entity_manipulation.deleteEntity( self )
        return None

    def isConsistent( self ):
        """ checks wheater there are any changed values 
        """
        return len( self._changed_values ) == 0
