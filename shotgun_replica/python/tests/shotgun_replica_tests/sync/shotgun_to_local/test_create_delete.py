# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
from tests_elefant import testProjectID, testShotID
from elefant.utilities.debug import debug
from elefant.utilities.definitions import DEBUG
from shotgun_replica.connectors import DatabaseConnector
from shotgun_replica.sync.shotgun_to_local import EventProcessor
from shotgun_replica.factories import getObject
from shotgun_replica.entities import Shot
from uuid import uuid1
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
        self.ep = EventProcessor( self.src, self.sg )

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
        debug( lastevent, DEBUG )

        shotCode = "TEST SHOT (delete me) %s" % uuid1()

        lastID = lastevent["id"]
        data = {
                "project": {"type": "Project",
                            "id": testProjectID
                            },
                "code": shotCode
                }
        newShotDict = self.sg.create( "Shot", data, [] )
        debug( newShotDict )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        debug( newevents, DEBUG, prefix = " SHOT CREATE: " )

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
