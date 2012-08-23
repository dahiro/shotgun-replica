# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
from shotgun_replica.connectors import DatabaseModificator
from shotgun_replica.sync.shotgun_to_local import EventProcessor
from shotgun_replica.factories import getObject
from shotgun_replica.entities import Shot

from tests_elefant import testProjectID, testShotID

from shotgun_api3 import shotgun
from uuid import uuid1
import unittest
from shotgun_replica import config
import logging

NEWVALUE = "rdy"
OLDVALUE = "wtg"

class Test( unittest.TestCase ):

    def setUp( self ):
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.src = DatabaseModificator()
        self.ep = EventProcessor( self.src, self.sg )

        logging.basicConfig( level = logging.DEBUG )

    def tearDown( self ):
        pass

    def testAddTask( self ):
        lastevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]
        logging.debug( lastevent )

        shotCode = "TEST SHOT (delete me) %s" % uuid1()

        lastID = lastevent["id"]
        data = {
                "project": {"type": "Project",
                            "id": testProjectID
                            },
                "code": shotCode
                }
        newShotDict = self.sg.create( "Shot", data, [] )
        logging.debug( newShotDict )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        logging.debug( newevents )

        self.assertEqual( newevents[0]["event_type"], "Shotgun_Shot_New", "event not as expected" )

        for newevent in newevents:
            self.ep.process( newevent )
            lastID = newevent["id"]

        shot = getObject( "Shot", newShotDict["id"] )
        self.assertEqual( type( shot ), Shot )
        self.assertEqual( shot.code, shotCode )

        self.sg.delete( "Shot", newShotDict["id"] )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        for newevent in newevents:
            self.ep.process( newevent )
            lastID = newevent["id"]

        shot = getObject( "Shot", newShotDict["id"] )
        self.assertEqual( shot, None )


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
