'''
Created on Oct 25, 2012

@author: bach
'''

from shotgun_replica.sync import shotgun_to_local, local_to_shotgun, \
    sync_settings
import time
from shotgun_replica.utilities import debug
import sys
import uuid
import os
import socket

OTHER_SYNCDAMEON_RUNNING = -1
SYNCED_OK = 0
SYNCED_NOT_OK = 1

class SyncDaemon( object ):
    def __init__( self ):
        self.shotgun_to_local_spooler = shotgun_to_local.EventSpooler()
        self.local_to_shotgun_spooler = local_to_shotgun.LocalDBEventSpooler()

        self.syncomaniaSettings = sync_settings.SyncomaniaSettings()
        try:
            self.syncomaniaSettings.load()
        except Exception, error: #IGNORE:W0703
            debug.debug( "no syncomania data available yet: " + unicode( error ), debug.ERROR )

        self.mycode = self._generateCode()
        self.syncomaniaSettings[sync_settings.FIELD_CURRENT_SYNCDAEMON_ID] = self.mycode
        self.syncomaniaSettings.save()

    def _generateCode(self):
        code = "%s: %s" % ( socket.gethostname(), uuid.uuid1() )
        return code
        
    def run( self ):

        while True:

            retcode = self.connectAndRun()
            if retcode == OTHER_SYNCDAMEON_RUNNING:
                break
            sys.stdout.write( "." )
            time.sleep( 2 )

    def connectAndRun( self ):
        self.syncomaniaSettings.load()
        if self.syncomaniaSettings.get( sync_settings.FIELD_CURRENT_SYNCDAEMON_ID ) != self.mycode:
            debug.error( "another daemon seems to have started running" )
            return OTHER_SYNCDAMEON_RUNNING

        state_Shotgun_to_Local = self.shotgun_to_local_spooler.connectAndRun()
        if not state_Shotgun_to_Local:
            debug.debug( "something not OK syncing Shotgun to Local", debug.ERROR )

        state_Local_to_Shotgun = self.local_to_shotgun_spooler.connectAndRun()
        if not state_Local_to_Shotgun:
            debug.debug( "something not OK syncing Local to Shotgun", debug.ERROR )
        
        if not state_Shotgun_to_Local or not state_Local_to_Shotgun:
            return SYNCED_NOT_OK
        else:
            return SYNCED_OK

if __name__ == "__main__":
    syncDaemon = SyncDaemon()
    syncDaemon.run()
