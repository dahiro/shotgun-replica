'''
Created on Aug 23, 2012

@author: bach
'''
from shotgun_replica import conversions, connectors
import json

KEY_SYNC_SETTINGS = "sync_settings"
KEY_TEST_VALUE = "test_value"

def getValue( key ):
    dbc = connectors.DatabaseConnector()
    dbc.cur.execute( "SELECT value FROM \"KeyValues\" WHERE key = %s", ( key, ) )
    retvals = dbc.cur.fetchone()

    try:
        obj = json.loads( retvals[0] )
        return obj
    except ValueError:
        return retvals[0]

def setValue( key, value ):
    storevalue = value
    if not type( value ) in [ type( "" ), type( u"" )]:
        storevalue = json.dumps( storevalue )

    dbc = connectors.DatabaseConnector()
    dbc.cur.execute( "UPDATE \"KeyValues\" SET value = %s WHERE key = %s", ( storevalue, key ) )
