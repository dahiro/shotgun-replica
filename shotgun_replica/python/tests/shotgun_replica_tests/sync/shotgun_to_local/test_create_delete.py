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
from shotgun_replica.utilities import debug
from shotgun_replica.sync import shotgun_to_local

NEWVALUE = "rdy"
OLDVALUE = "wtg"

class Test( unittest.TestCase ):

    def setUp( self ):
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.src = DatabaseModificator()
        self.ep = EventProcessor( self.src, self.sg )
        
        self.shotgun2local = shotgun_to_local.EventSpooler()

    def tearDown( self ):
        pass

    def testAddTask( self ):

        shotCode = "TEST SHOT (delete me) %s" % uuid1()

        data = {
                "project": {"type": "Project",
                            "id": testProjectID
                            },
                "code": shotCode
                }
        newShotDict = self.sg.create( "Shot", data, [] )
        
        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

        shot = getObject( "Shot", remote_id = newShotDict["id"] )
        self.assertEqual( type( shot ), Shot )
        self.assertEqual( shot.code, shotCode )

        self.sg.delete( "Shot", newShotDict["id"] )
        
        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

        shot = getObject( "Shot", remote_id = newShotDict["id"] )
        self.assertEqual( shot, None )


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
