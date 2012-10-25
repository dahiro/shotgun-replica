# -*- coding: utf-8 -*-

'''
Created on Jun 27, 2012

@author: bach
'''
from shotgun_replica.factories import getObject
from shotgun_replica.entities import Project, Shot
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler
from shotgun_replica import entity_manipulation, config

from tests_elefant import testProjectID

from shotgun_api3 import shotgun

import unittest
import uuid
import logging
import shotgun_replica

class Test( unittest.TestCase ):

    def setUp( self ):
        self.testproject = getObject( Project().getType(), 
                                      remote_id = testProjectID )
        self.eventprocessor = LocalDBEventSpooler()
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_BACKSYNC_SKRIPT,
                                   config.SHOTGUN_BACKSYNC_KEY )
        logging.basicConfig( level = logging.DEBUG )

    def tearDown( self ):
        pass

    def test_create( self ):

        shot = Shot()
        shot.code = "delete me again - " + str( uuid.uuid1() )
        shot.project = self.testproject
        shot.save()
        newshotid = shot.getLocalID()
        self.assertTrue( shot.getLocalID() != None )

        shot_ret = getObject( "Shot", local_id = newshotid )
        self.assertTrue( shot_ret != None )
        self.assertTrue( shot_ret.getSgObj() == None )

        self.eventprocessor.connectAndRun()

        shot_ret = getObject( "Shot", local_id = newshotid )
        newRemoteID = shot_ret.getRemoteID()
        self.assertTrue( newRemoteID != None and newRemoteID != shotgun_replica.UNKNOWN_SHOTGUN_ID,
                         "Shot with local ID %d has no remote id %s" % ( newshotid, newRemoteID ) )
        self.assertTrue( shot_ret.getSgObj() != None )

        entity_manipulation.deleteEntity( shot_ret )

        shot_ret = getObject( "Shot", local_id = newshotid )

        self.assertTrue( shot_ret == None )

        newshot = self.sg.find( 
                               "Shot",
                               filters = [['id', 'is', newRemoteID]],
                               fields = ['id'],
                               filter_operator = 'all',
                               limit = 100
                               )
        self.assertEqual( len( newshot ), 1 )
        self.eventprocessor.connectAndRun()

        newshot = self.sg.find( 
                               "Shot",
                               filters = [['id', 'is', newRemoteID]],
                               fields = ['id'],
                               filter_operator = 'all',
                               limit = 100
                               )
        self.assertEqual( len( newshot ), 0 )
