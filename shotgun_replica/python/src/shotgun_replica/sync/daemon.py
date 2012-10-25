'''
Created on Oct 25, 2012

@author: bach
'''

from shotgun_replica.sync import shotgun_to_local, local_to_shotgun
import time
from shotgun_replica.utilities import debug
import sys

class SyncDaemon( object ):

    def run( self ):
        shotgun_to_local_spooler = shotgun_to_local.EventSpooler()
        local_to_shotgun_spooler = local_to_shotgun.LocalDBEventSpooler()

        while True:
            state = shotgun_to_local_spooler.connectAndRun()
            if not state:
                debug.debug("something not OK", debug.ERROR)
                
            state = local_to_shotgun_spooler.connectAndRun()
            if not state:
                debug.debug("something not OK", debug.ERROR)
            
            sys.stdout.write(".")
            
            time.sleep( 2 )

if __name__ == "__main__":
    syncDaemon = SyncDaemon()
    syncDaemon.run()
