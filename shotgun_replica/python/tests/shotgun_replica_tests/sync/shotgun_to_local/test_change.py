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
from shotgun_replica.utilities import debug
from shotgun_replica.sync import shotgun_to_local

NEWVALUE = "rdy"
OLDVALUE = "wtg"

START_DATE = "2012-01-15"
END_DATE = "2012-02-16"

SPLIT_NEW = [{'start': START_DATE, 'end': '2012-02-01'},
             {'start': '2012-02-05', 'end': END_DATE}]
SPLIT_OLD = []

class Test( unittest.TestCase ):

    def setUp( self ):
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.src = DatabaseModificator()
        self.shotgun2local = shotgun_to_local.EventSpooler()

    def tearDown( self ):
        task = getObject( "Task", remote_id = testTaskID )
        # changeEntity( task, {"sg_status_list": OLDVALUE} )
        self.sg.update( "Task", testTaskID, {"sg_status_list": OLDVALUE,
                                             "splits": SPLIT_OLD,
                                             "start_date": START_DATE,
                                             "due_date": END_DATE } )
        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

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

        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

        task = getObject( "Task", remote_id = testTaskID )
        self.assertEqual( NEWVALUE, task.sg_status_list )

    def testSyncomaniaSplitsChange( self ):
        task = getObject( "Task", remote_id = testTaskID )
        self.assertEqual( 11520, task.duration.days * 24 * 60 )

        ret = self.sg.update( "Task", testTaskID, {"splits": SPLIT_NEW} )
        debug.debug( ret )

        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

        task = getObject( "Task", remote_id = testTaskID )
        self.assertEqual( 10080, task.duration.days * 24 * 60 )
        self.assertEqual( len( task.splits ), 2 )
        self.assertTrue( task.splits[0].has_key("start") )
        self.assertTrue( task.splits[0].has_key("end") )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
