# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''
from shotgun_replica.conversions import getDBConnection, PostgresEntityType, \
    getConversionSg2Pg
from shotgun_replica import base_entity
import logging
import inspect

class DatabaseConnector( object ):
    def __new__( cls, *args, **kw ):
        """overload the __new__-Method to ensure singleton-property"""
        if not hasattr( cls, '_instance' ):
            orig = super( DatabaseConnector, cls )
            cls._instance = orig.__new__( cls, *args, **kw )
            cls._instance.con = getDBConnection()
            cls._instance.cur = cls._instance.con.cursor()

        return cls._instance

    def getListOfEntities( self, entityType, queryFilter = None, order = None, variables = None, query = None ):

        cur = self.con.cursor()

        if query == None:
            query = "SELECT * FROM \"%s\"" % entityType

        if queryFilter != None:
            query += " WHERE " + queryFilter

        if order != None:
            query += " ORDER BY %s" % order

        if variables != None:
            logging.debug( query )
            logging.debug( variables )

            logging.debug( cur.mogrify( query, variables ) )
            cur.execute( query, variables )
        else:
            logging.debug( cur.mogrify( query ) )
            cur.execute( query )

        items = []

        names = [x[0] for x in cur.description]

        for values in cur:
            items.append( getClassOfType( entityType )( __data = values, __names = names ) )

        cur.close()
        return items

    def changeInDB( self, entity, attribute = None, value = None, changes = None, doAppend = False, doRemove = False ):
        """ change something in couchdb and do a reload and retry 
        if it fails due to changed doc """
        entityLocalID = None
        if type( entity ) == dict:
            entityType = entity["type"]
            entityID = entity["id"]
        elif type( entity ) == PostgresEntityType:
            entityType = entity.type
            entityID = entity.remote_id
            entityLocalID = entity.local_id
        elif isinstance( entity, base_entity.ShotgunBaseEntity ):
            entityType = entity.getType()
            entityID = entity.getRemoteID()
            entityLocalID = entity.getLocalID()

        cur = self.con.cursor()

        if changes != None:
            keys = changes.keys()
            values = []
            for attr in keys:
                sgType = getClassOfType( entityType ).shotgun_fields[attr]["data_type"]["value"]

                convFunc = getConversionSg2Pg( sgType )
                if convFunc != None:
                    values.append( convFunc( changes[attr] ) )
                else:
                    values.append( changes[attr] )

#            values = [ changes[x] for x in keys ]

            query = "UPDATE \"%s\" SET " % entityType
            changeArr = ["\"%s\" = %s" % ( x, "%s" ) for x in keys]
            query += ", ".join( changeArr )

            filters = []
            if entityLocalID != None:
                filters.append( "__local_id=%s" )
                values.append( entityLocalID )

            if entityID != None:
                filters.append( "id=%s" )
                values.append( entityID )

            query += " WHERE (" + " OR ".join( filters ) + " )"

            logging.debug( cur.mogrify( query, values ) )
            cur.execute( query, values )
        elif ( attribute != None ):
            values = []

            if doAppend:
                query = "UPDATE \"%s\" SET " % entityType
                query += "\"%s\" = \"%s\" || %s" % ( attribute, attribute, "%s" )
                if isinstance( value, PostgresEntityType ):
                    values = [value, ]
                elif isinstance( value, base_entity.ShotgunBaseEntity ):
                    values = [value.getPgObj(), ]
                else:
                    raise Exception( "unknown format for appending: %s" % type( value ) )
            elif doRemove:
                logging.debug( "removing: " )
                fieldvalue = entity.getField( attribute )
                logging.debug( entity.getField( attribute ) )
                logging.debug( value )

                if fieldvalue != None and len( fieldvalue ) > 0 \
                    and value in fieldvalue:
                    fieldvalue.remove( value )

                theList = [x.getPgObj() for x in fieldvalue]

                query = "UPDATE \"%s\" SET " % entityType
                query += "\"%s\" = %s" % ( attribute, "%s" )
                values = [theList, ]
            else:
                query = "UPDATE \"%s\" SET " % entityType
                query += "\"%s\" = %s" % ( attribute, "%s" )

                sgType = getClassOfType( entityType ).shotgun_fields[attribute]["data_type"]["value"]
                convFunc = getConversionSg2Pg( sgType )

                if convFunc != None:
                    values = [convFunc( value ), ]
                else:
                    values = [value, ]

            filters = []
            if entityLocalID != None:
                filters.append( "__local_id=%s" )
                values.append( entityLocalID )

            if entityID != None:
                filters.append( "id=%s" )
                values.append( entityID )

            query += " WHERE (" + " OR ".join( filters ) + " )"

            logging.debug( query )
            logging.debug( values )
            logging.debug( cur.mogrify( query, values ) )
            cur.execute( query, values )
        cur.close()
        self.con.commit()

    def add( self, item ):
        """
        add item to local database
        
        @param item: either dict gotten from shotgun or a instance of _ShotgunEntity 
        """
        if type( item ) == dict:
            return self._addDict( item )
        elif isinstance( item, base_entity.ShotgunBaseEntity ):
            return self._addObj( item )

    def _addDict( self, item ):
        """
        @param item: dict gotten from shotgun 
        """
        itemType = item.pop( "type" )
        entityClass = getClassOfType( itemType )
        fieldListDef = entityClass.shotgun_fields

        fieldValues = []
        fieldNames = []

        for fieldName in item.keys():
            sgType = fieldListDef[fieldName]['data_type']['value']
            convFunc = getConversionSg2Pg( sgType )
            if convFunc != None:
                fieldNames.append( "\"%s\"" % fieldName )
                fieldValues.append( convFunc( item[fieldName] ) )

        return self._addToDatabase( itemType, fieldValues, fieldNames )

    def _addObj( self, item ):
        """
        @param item: _ShotgunEntity-instance 
        """
        itemType = item.getType()
        fieldListDef = item.shotgun_fields

        fieldValues = []
        fieldNames = []

        for fieldName in item.shotgun_fields.keys():
            logging.debug( "converting field with name %s" % fieldName )
            sgType = fieldListDef[fieldName]['data_type']['value']
            convFunc = getConversionSg2Pg( sgType )
            if convFunc != None:
                fieldNames.append( "\"%s\"" % fieldName )
                fieldValues.append( convFunc( item.getField( fieldName ) ) )

        return self._addToDatabase( itemType, fieldValues, fieldNames )


    def _addToDatabase( self, itemType, fieldValues, fieldNames ):
        replacers = ["%s"] * len( fieldNames )

        for i in range( len( fieldValues ) ):
            if isinstance( fieldValues[i], base_entity.ShotgunBaseEntity ):
                fieldValues[i] = fieldValues[i].getPgObj()
            if type( fieldValues[i] ) == dict:
                local_id = None
                if fieldValues[i].has_key( "sg_local_id" ):
                    local_id = fieldValues[i]["sg_local_id"]
                fieldValues[i] = PostgresEntityType( fieldValues[i]["type"],
                    remote_id = fieldValues[i]["id"],
                    local_id = local_id )

        query = "INSERT INTO \"%s\" (%s) VALUES (%s)" % ( itemType,
            ", ".join( fieldNames ),
            ", ".join( replacers ) )

        cur = self.con.cursor()
        logging.debug( cur.mogrify( query, fieldValues ) )
        cur.execute( query, fieldValues )


        query2 = "SELECT currval('\"%s___local_id_seq\"')" % itemType
        cur.execute( query2 )
        ret = cur.fetchone()
        newID = ret[0]
        self.con.commit()
        cur.close()

        return newID

    def delete( self, myObj ):
        query = "DELETE FROM \"%s\" WHERE id=%s or __local_id=%s" % ( myObj.getType(), "%s", "%s" )
        cursor = self.con.cursor()
        logging.debug( cursor.mogrify( query, ( myObj.remote_id, myObj.local_id ) ) )
        cursor.execute( query, ( myObj.remote_id, myObj.local_id ) )

def getClassOfType( entityType ):
    """
    @return: returns class of specific entityType 
    """
    try:
        from shotgun_replica import entities
        if entities.__dict__.has_key( entityType ):
            cls = entities.__dict__[entityType]
            if type( cls ) == type:
                return cls
            else:
                return None
        else:
            return None
    except ImportError:
        return None
    except AttributeError:
        return None
