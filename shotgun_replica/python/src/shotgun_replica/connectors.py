# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''

from shotgun_replica import config, base_entity, UNKNOWN_SHOTGUN_ID
import shotgun_replica

from psycopg2.extensions import adapt, AsIs, register_adapter
import psycopg2
import re
import json
from shotgun_replica.utilities import debug

con = None

IGNORE_SHOTGUN_TYPES = [ "AppWelcome", "PermissionRuleSet", "Banner", "BannerUserConnection", "Icon" ]

def __adapt_entity( entity ):
    return AsIs( "ROW(%s, %s, %s)::entity_sync" % ( adapt( entity.type ),
                                                    adapt( entity.local_id ),
                                                    adapt( entity.remote_id ) ) )

def __cast_entities( value, cur ):
    if value is None:
        return None
    if value == "" or value == '{}':
        return []

    # Convert from (f1, f2) syntax using a regular expression.
    value = value[1:len( value ) - 1]
    regexp = r"^(\"\(([^,)]+),([^,)]+),([^,)]+)\)\",?)"
    m = re.match( regexp, value )
    if m:
        ret = []
        while m:
            found = m.groups()[1:]
            ret.append( PostgresEntityType( str( found[0] ),
                                          int( found[1] ),
                                          int( found[2] ) ) )
            value = value[len( m.group( 0 ) ):]
            m = re.match( regexp, value )

        return ret
    else:
        debug.error( type( value ) )
        debug.error( value )
        raise InterfaceError( "bad entity representation: %r" % value )

def __cast_entity( value, cur ):
    if value is None:
        return None

    m = re.match( r"\(([^),]+),([^),]+),([^),]+)\)", value )
    if m:
        return PostgresEntityType( str( m.group( 1 ) ), int( m.group( 2 ) ), int( m.group( 3 ) ) )
    else:
        raise InterfaceError( "bad entity representation: %r" % value )

class InterfaceError( Exception ):
    pass

def getPgType( shotgunType ):
    if shotgunType == "checkbox":
        return "boolean"
    elif shotgunType == "currency":
        return "money"
    elif shotgunType == "date":
        return "date"
    elif shotgunType == "date_time":
        return "timestamp with time zone"
    elif shotgunType == "duration":
        return "interval"
    elif shotgunType == "entity":
        return "entity_sync"
#        pgfields.append([attribute+"__x__type", "text"])
#        pgfields.append([attribute+"__x__id", "integer"])
    elif shotgunType == "multi_entity":
        return "entity_sync[]"
    elif shotgunType == "float":
        return "double precision"
    elif shotgunType == "file":
        return "text"
    elif shotgunType == "tag_list":
        return "varchar[]"
    elif shotgunType == "list":
        return "text"
    elif shotgunType == "number":
        return "integer"
    elif shotgunType == "percent":
        return "integer"
    elif shotgunType == "password":
        pass
        #debug("%s not yet handled" % shotgunType, ERROR)
    elif shotgunType == "query":
        return "text"
    elif shotgunType == "status_list":
        return "text"
    elif shotgunType == "text":
        return "text"
    elif shotgunType == "image":
        return "text"
    elif shotgunType == "pivot_column":
        pass
        #debug("%s not yet handled" % shotgunType, ERROR)
    elif shotgunType == "url":
        return "text"
    elif shotgunType == "color":
        return "text"
    elif shotgunType == "uuid":
        return "text"
    elif shotgunType == "entity_type":
        return "text"
    elif shotgunType == "serializable":
        return "text"
    elif shotgunType == "summary":
        debug.debug( "%s not yet handled" % shotgunType )
    else:
        debug.debug( "%s not yet handled" % shotgunType )

def getPgObj( val ):
    if val != None:
        if type( val ) == PostgresEntityType:
            return val
        elif type( val ) == dict:

            if val["type"] in IGNORE_SHOTGUN_TYPES:
                return None

            local_id = None
            # hier die local_id abklappern
            if val.has_key( "__local_id" ):
                local_id = val["__local_id"]

            if local_id == None or local_id == UNKNOWN_SHOTGUN_ID:
                # hier die local_id abklappern
                local_id = getLocalID( val["type"], val["id"] )

            return PostgresEntityType( val["type"],
                                       local_id = local_id,
                                       remote_id = val["id"] )
        elif isinstance( val, base_entity.ShotgunBaseEntity ):
            return val.getPgObj()
        elif type( val ) == list:
            retval = [ getPgObj( entry ) for entry in val ]
            return retval
        else:
            return val
    else:
        return None

def getPostgresUser():
    pgObj = getPgObj( config.getUserDict() )
    return pgObj

def getConversionSg2Pg( sgType ):
    if sgType == "duration":
        def func( val ):
            if val != None:
                return str( val ) + " minutes"
            return None
        return func
    elif sgType == "entity":
        return getPgObj
    elif sgType == "url":
        def func( val ):
            if val != None:
                return json.dumps( val )
            else:
                return None
        return func
    elif sgType == "serializable":
        def func( val ):
            if val != None:
                return json.dumps( val )
            else:
                return None
        return func
    elif sgType == "tag_list":
        def func( val ):
            if type( val ) == type( [] ):
                return val
            elif val != None:
                return [val]
            else:
                return None
        return func
    elif sgType == "number":
        def func( val ):
            if val != None and val != '':
                return int( val )
            else:
                return None
        return func
    elif sgType == "checkbox":
        def func( val ):
            if val != None and val == 1:
                return True
            else:
                return False
        return func
    elif sgType == "multi_entity":
        def func( val ):
            if val != None:
                if len( val ) == 0:
                    toret = None
                else:
                    arr = []
                    for entry in val:
                        newentry = getPgObj( entry )
                        if newentry:
                            arr.append( newentry )
                    toret = arr
                return toret
            else:
                return None
        return func
    elif sgType in ["pivot_column", "password", "summary"]:
        return None
    else:
        def func( val ):
            return val
        return func






class PostgresEntityType( object ):
    def __init__( self, sg_type, local_id = None, remote_id = None ):
        self.type = sg_type
        self.local_id = local_id
        self.remote_id = remote_id

        if self.local_id == None:
            self.local_id = shotgun_replica.UNKNOWN_SHOTGUN_ID

        if self.remote_id == None:
            self.remote_id = shotgun_replica.UNKNOWN_SHOTGUN_ID

    def __repr__( self ):
        return "%s (%d,%d) %s" % ( self.type,
                                   self.local_id,
                                   self.remote_id,
                                   super( PostgresEntityType, self ).__repr__() )

    def getSgObj( self ):

        remote_id = self.remote_id
        if remote_id == None or remote_id == shotgun_replica.UNKNOWN_SHOTGUN_ID:
            remote_id = getRemoteID( self.type, self.local_id )

        if remote_id == None or remote_id == shotgun_replica.UNKNOWN_SHOTGUN_ID:
            return None
        else:
            return {"id": remote_id,
                    "type": self.type}

    def getType( self ):
        return self.type

    def getShortDict( self ):
        """
        get smallest possible dict that identifies an object
        """
        return {
            "type": self.type,
            "id": self.remote_id,
            "__local_id": self.local_id,
        }
    
    def getLocalID(self):
        return self.local_id
    
    def getRemoteID(self):
        return self.remote_id

    def __cmp__( self, objB ):
        if objB == None:
            return -99999
        if objB.type == self.type:
            if self.remote_id != UNKNOWN_SHOTGUN_ID and objB.remote_id != UNKNOWN_SHOTGUN_ID:
                return cmp( self.remote_id, objB.remote_id )
            else:
                return cmp( self.local_id, objB.local_id )
        else:
            return cmp( self.type, objB.type )

class DatabaseConnector( object ):
    con = None
    cur = None

    def __new__( cls, *args, **kw ):
        """overload the __new__-Method to ensure singleton-property"""
        if not hasattr( cls, '_instance' ):
            orig = super( DatabaseConnector, cls )
            cls._instance = orig.__new__( cls, *args, **kw )
            cls._instance.con = getDBConnection()
            cls._instance.cur = cls._instance.con.cursor()

        return cls._instance

class DatabaseModificator( object ):
    con = None
    cur = None

    def __init__( self ):
        self.dbc = DatabaseConnector()
        self.con = self.dbc.con
        self.cur = self.dbc.cur

    def getListOfEntities( self, entityType, queryFilter = None, order = None, variables = None, limit = None ):

        cur = self.con.cursor()
        query = "SELECT * FROM \"%s\"" % entityType

        if queryFilter != None and queryFilter != "":
            queryFilter = queryFilter.replace( ";", "" )
            query += " WHERE " + queryFilter

        if order != None:
            order = order.replace( ";", "" )
            query += " ORDER BY %s" % order

        if limit != None:
            if type( limit ) != type( 1 ):
                limit = str( limit ).replace( ";", "" )
            query += " LIMIT %s" % str( limit )

        if variables != None:
            debug.debug( query )
            debug.debug( variables )
            debug.debug( cur.mogrify( query, variables ) )
            cur.execute( query, variables )
        else:
            debug.debug( cur.mogrify( query ) )
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
        classOfType = getClassOfType( entityType )

        if changes != None:
            keys = changes.keys()
            values = []
            for attr in keys:
                convFunc = None
                if classOfType.shotgun_fields.has_key( attr ):
                    sgType = classOfType.shotgun_fields[attr]["data_type"]["value"]
                    convFunc = getConversionSg2Pg( sgType )

                newValue = changes[attr]
                if convFunc != None:
                    newValue = convFunc( changes[attr] )
                values.append( newValue )

            query = "UPDATE \"%s\" SET " % entityType
            changeArr = ["\"%s\" = %s" % ( x, "%s" ) for x in keys]
            query += ", ".join( changeArr )

            filters = []
            if entityLocalID != None and entityLocalID != UNKNOWN_SHOTGUN_ID:
                filters.append( "__local_id=%s" )
                values.append( entityLocalID )

            if entityID != None and entityID != UNKNOWN_SHOTGUN_ID:
                filters.append( "id=%s" )
                values.append( entityID )

            query += " WHERE (" + " OR ".join( filters ) + " )"

            debug.debug( cur.mogrify( query, values ) )
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
                debug.debug( "removing: " )
                fieldvalue = entity.getField( attribute )
                debug.debug( entity.getField( attribute ) )
                debug.debug( value )

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

                convFunc = None
                if classOfType.shotgun_fields.has_key( attribute ):
                    sgType = classOfType.shotgun_fields[attribute]["data_type"]["value"]
                    convFunc = getConversionSg2Pg( sgType )

                if convFunc != None:
                    values = [convFunc( value ), ]
                else:
                    values = [value, ]

            filters = []
            if entityLocalID != None and entityLocalID != UNKNOWN_SHOTGUN_ID:
                filters.append( "__local_id=%s" )
                values.append( entityLocalID )

            if entityID != None and entityID != UNKNOWN_SHOTGUN_ID:
                filters.append( "id=%s" )
                values.append( entityID )

            if len( filters ) > 0:
                query += " WHERE (" + " OR ".join( filters ) + " )"

                debug.debug( query )
                debug.debug( values )
                debug.debug( cur.mogrify( query, values ) )
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
        debug.debug( cur.mogrify( query, fieldValues ) )
        cur.execute( query, fieldValues )


        query2 = "SELECT currval('\"%s___local_id_seq\"')" % itemType
        cur.execute( query2 )
        ret = cur.fetchone()
        newID = ret[0]
        self.con.commit()
        cur.close()

        return newID

    def delete( self, myObj ):
        query = "DELETE FROM \"%s\" WHERE " % ( myObj.getType() )

        filters = []
        filtervalues = []

        if myObj.local_id != UNKNOWN_SHOTGUN_ID:
            filters.append( "__local_id=%s" )
            filtervalues.append( myObj.local_id )

        if myObj.remote_id != UNKNOWN_SHOTGUN_ID:
            filters.append( "id=%s" )
            filtervalues.append( myObj.remote_id )

        query += " OR ".join( filters )

        cursor = self.con.cursor()
        debug.debug( cursor.mogrify( query, filtervalues ) )
        cursor.execute( query, filtervalues )

def getDBConnection():
    global con
    if con == None:
        con = psycopg2.connect( host = config.DB_HOST,
                                database = config.DB_DATABASE,
                                user = config.DB_USERNAME,
                                password = config.DB_PASSWORD )

        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
        
        con.set_isolation_level( psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT )

        register_adapter( PostgresEntityType, __adapt_entity )
        query = """ SELECT pg_type.oid
                    FROM pg_type JOIN pg_namespace
                           ON typnamespace = pg_namespace.oid
                    WHERE typname = 'entity_sync' AND nspname = 'public'"""
        cur = con.cursor()
        cur.execute( query )
        record = cur.fetchone()
        if record != None:
            entity_oid = record[0]
            ENTITY = psycopg2.extensions.new_type( ( entity_oid, ), "entity_sync", __cast_entity )
            psycopg2.extensions.register_type( ENTITY )

        query = ''' SELECT pg_type.oid
                    FROM pg_type JOIN pg_namespace
                           ON typnamespace = pg_namespace.oid
                    WHERE typname = '_entity_sync'
                     AND nspname = 'public'
                    '''
        cur = con.cursor()

        cur.execute( query )
        record = cur.fetchone()
        if record != None:
            entities_oid = record[0]
            ENTITIES = psycopg2.extensions.new_type( ( entities_oid, ), "entity_sync[]", __cast_entities )
            psycopg2.extensions.register_type( ENTITIES )

        cur.close()

    return con

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
    except AttributeError:
        return None

def getRemoteID( entityType, local_id ):
    """
    get remote-ID of an object for a give local_id 
    """

    dbc = DatabaseConnector()
    dbc.cur.execute( "SELECT id FROM \"%s\" WHERE __local_id = %s" % ( entityType,
                                                                       "%s" ),
                    ( local_id, ) )
    result = dbc.cur.fetchone()
    if result:
        return result[0]
    else:
        return None

def getLocalID( entityType, remote_id ):
    """
    get loca-ID of an object for a give remote_id 
    """

    dbc = DatabaseConnector()
    dbc.cur.execute( "SELECT __local_id FROM \"%s\" WHERE id = %s" % ( entityType,
                                                                       "%s" ),
                     ( remote_id, ) )
    result = dbc.cur.fetchone()
    if result:
        return result[0]
    else:
        return None
