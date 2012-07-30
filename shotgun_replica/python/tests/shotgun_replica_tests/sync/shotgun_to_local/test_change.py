# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
from elefant.utilities.config import Configuration
from tests_elefant import testTaskID
from elefant.utilities.debug import debug
from elefant.utilities.definitions import DEBUG
from shotgun_replica.sync.shotgun_to_local import EventProcessor
from shotgun_replica.connectors import DatabaseConnector
from shotgun_replica.factories import getObject
from shotgun_replica.entity_manipulation import changeEntity
from shotgun_api3 import shotgun
from elefant.utilities import config

NEWVALUE = "rdy"
OLDVALUE = "wtg"

class Test( unittest.TestCase ):

    def setUp( self ):
        self.sg = shotgun.Shotgun( config.Configuration().get( config.CONF_SHOTGUN_URL ),
                                   config.Configuration().get( config.CONF_SHOTGUN_SKRIPT ),
                                   config.Configuration().get( config.CONF_SHOTGUN_KEY ) )
        self.src = DatabaseConnector()

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
        debug( lastevent, DEBUG )

        lastID = lastevent["id"]

        ret = self.sg.update( "Task", testTaskID, {"sg_status_list": NEWVALUE} )
        debug( ret )

        newevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]

        debug( newevent, DEBUG )

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
