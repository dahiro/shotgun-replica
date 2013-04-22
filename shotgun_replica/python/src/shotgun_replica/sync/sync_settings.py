# -*- coding: utf-8 -*-

'''
Created on Jul 4, 2012

@author: bach
'''

from shotgun_replica.factories import keyvalues

FIELD_LASTEVENTID = "last_eventid"
FIELD_CURRENT_SYNCDAEMON_ID = "sync_daemon_id"
FIELD_SYNC_SLEEP = "sync_sleep"
FIELD_SYNC_SLEEP_YES = "yes"
FIELD_SYNC_SLEEP_NO = "no"

class SyncomaniaSettings( dict ):
    def save( self ):
        keyvalues.setValue( keyvalues.KEY_SYNC_SETTINGS, self )

    def load( self ):
        dadict = keyvalues.getValue( keyvalues.KEY_SYNC_SETTINGS )
        self.update( dadict )
