# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
from shotgun_replica.sync.shotgun_to_local import EventProcessor
from shotgun_replica.connectors import DatabaseModificator
from shotgun_replica.factories import getObject
from shotgun_replica.entity_manipulation import changeEntity

from tests_elefant import testTaskID

from shotgun_api3 import shotgun

import unittest
from shotgun_replica import config
import logging
from shotgun_replica.utilities import debug

NEWVALUE = "rdy"
OLDVALUE = "wtg"

class Test( unittest.TestCase ):

    def setUp( self ):
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.src = DatabaseModificator()

    def tearDown( self ):
        task = getObject( "Task", testTaskID )
        changeEntity( task, {"sg_status_list": OLDVALUE} )
        self.sg.update( "Task", testTaskID, {"sg_status_list": OLDVALUE} )

    def testSyncomaniaSettingsChange( self ):
        lastevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]
        debug.debug( lastevent )

        lastID = lastevent["id"]

        ret = self.sg.update( "Task", testTaskID, {"sg_status_list": NEWVALUE} )
        debug.debug( ret )

        newevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]

        debug.debug( newevent )

        self.failUnlessEqual( newevent["entity"]["id"], testTaskID )
        self.failUnlessEqual( newevent["meta"]["new_value"], NEWVALUE )
        self.failUnlessEqual( newevent["id"], lastID + 1 )

        ep = EventProcessor( self.src, self.sg )
        ep.process( newevent )

        task = getObject( "Task", testTaskID )
        self.assertEqual( NEWVALUE, task.sg_status_list )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
