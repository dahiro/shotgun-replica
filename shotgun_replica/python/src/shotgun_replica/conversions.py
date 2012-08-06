
from shotgun_replica import config

import re
import psycopg2
from psycopg2.extensions import adapt, register_adapter, AsIs
import json
import logging
import shotgun_replica

con = None

def getDBConnection():
    global con
    if con == None:
        con = psycopg2.connect( host = config.DB_HOST,
                                database = config.DB_DATABASE,
                                user = config.DB_USERNAME,
                                password = config.DB_PASSWORD )
        con.set_isolation_level( psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT )

        register_adapter( PostgresEntityType, adapt_entity )
        query = """ SELECT pg_type.oid
                    FROM pg_type JOIN pg_namespace
                           ON typnamespace = pg_namespace.oid
                    WHERE typname = 'entity_sync' AND nspname = 'public'"""
        cur = con.cursor()
        cur.execute( query )
        record = cur.fetchone()
        if record != None:
            entity_oid = record[0]
            ENTITY = psycopg2.extensions.new_type( ( entity_oid, ), "entity_sync", cast_entity )
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
            ENTITIES = psycopg2.extensions.new_type( ( entities_oid, ), "entity_sync[]", cast_entities )
            psycopg2.extensions.register_type( ENTITIES )

        cur.close()

    return con

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
    elif shotgunType == "summary":
        logging.debug( "%s not yet handled" % shotgunType )
    else:
        logging.error( "%s not yet handled" % shotgunType )

def getPgObj( val ):
    if val != None:
        if type( val ) == dict:
            local_id = None

            try:
                # hier die local_id abklappern
                con = getDBConnection()
                cur = con.cursor()
                query = "SELECT __local_id FROM \"%s\" WHERE id=%s" % ( val["type"],
                                                                       "%s" )

                logging.debug( query )

                cur.execute( query,
                            ( val["id"], ) )

                record = cur.fetchone()
                if record != None:
                    local_id = record[0]
                cur.close()
            except psycopg2.ProgrammingError:
                pass

            return PostgresEntityType( val["type"],
                                      local_id = local_id,
                                      remote_id = val["id"] )
        else:
            return val.getPgObj()
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
    elif sgType == "multi_entity":
        def func( val ):
            if val != None:
                if len( val ) == 0:
                    toret = None
                else:
                    arr = []
                    for entry in val:
                        arr.append( getPgObj( entry ) )
                    toret = arr
                return toret
            else:
                return None
        return func
    elif sgType in ["pivot_column", "password", "summary", "image"]:
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
        return {"id": self.remote_id,
                "type": self.type}

def adapt_entity( entity ):
    return AsIs( "ROW(%s, %s, %s)::entity_sync" % ( adapt( entity.type ),
                                                  adapt( entity.local_id ),
                                                  adapt( entity.remote_id ) ) )

def cast_entities( value, cur ):
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
        logging.error( type( value ) )
        logging.error( value )
        raise InterfaceError( "bad entity representation: %r" % value )

class InterfaceError( Exception ):
    pass

def cast_entity( value, cur ):
    if value is None:
        return None

    m = re.match( r"\(([^),]+),([^),]+),([^),]+)\)", value )
    if m:
        return PostgresEntityType( str( m.group( 1 ) ), int( m.group( 2 ) ), int( m.group( 3 ) ) )
    else:
        raise InterfaceError( "bad entity representation: %r" % value )

