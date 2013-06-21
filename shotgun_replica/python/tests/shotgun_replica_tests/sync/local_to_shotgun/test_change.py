# -*- coding: utf-8 -*-

'''
Created on Jun 27, 2012

@author: bach
'''
from shotgun_replica.factories import getObject
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler
from shotgun_replica.entities import Project, Shot
from shotgun_replica import config, factories, entities

from tests_elefant import testProjectID

from shotgun_api3 import shotgun

import unittest
import uuid
from shotgun_replica.sync import shotgun_to_local
import shotgun_replica
from shotgun_replica_tests import testShotID

class Test( unittest.TestCase ):

    def setUp( self ):
        self.testproject = getObject( Project().getType(), remote_id = testProjectID )
        self.eventprocessor = LocalDBEventSpooler()
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.shotgun2local = shotgun_to_local.EventSpooler()
        
        self.testshot = factories.getObject( entities.Shot, 
                                             remote_id = testShotID )
        self.current_cut_in = self.testshot.sg_cut_in

    def tearDown( self ):

        self.testshot.sg_cut_in = self.current_cut_in
        self.testshot.save()
        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )


    def test_create( self ):

        shot = Shot()
        shot.code = "delete me again - " + str( uuid.uuid1() )
        shot.project = self.testproject
        shot.save()
        newshotid = shot.getLocalID()
        self.assertTrue( self.eventprocessor.connectAndRun(), "synch not successful" )

        shot_ret = getObject( "Shot", local_id = newshotid )

        newRemoteID = shot_ret.getRemoteID()

        self.assertTrue( newRemoteID != None and newRemoteID != shotgun_replica.UNKNOWN_SHOTGUN_ID )

        newCutIn = 1234
        shot_ret.sg_cut_in = newCutIn
        shot_ret.save()
        self.assertTrue( self.eventprocessor.connectAndRun(), "synch not successful" )

        newshot = self.sg.find( 
                               "Shot",
                               filters = [['id', 'is', newRemoteID]],
                               fields = ['id', 'sg_cut_in'],
                               filter_operator = 'all',
                               limit = 100
                               )

        self.assertEqual( newshot[0]['sg_cut_in'], newCutIn )

        shot_ret = shot_ret.delete()

        self.assertEqual( shot_ret, None )
        isShot = getObject( "Shot", local_id = newshotid )
        self.assertEqual( isShot, None )

        self.assertTrue( self.eventprocessor.connectAndRun(), "synch not successful" )

        newshot = self.sg.find( 
                               "Shot",
                               filters = [['id', 'is', newRemoteID]],
                               fields = ['id', 'sg_cut_in'],
                               filter_operator = 'all',
                               limit = 100
                               )
        self.assertEqual( len( newshot ), 0 )


    def test_change_Nones( self ):
        
        self.testshot.sg_cut_in = None
        self.testshot.save()

        self.assertTrue( self.eventprocessor.connectAndRun(), "synch not successful" )
        
        newshot = factories.getObject( entities.Shot, 
                                       remote_id = testShotID )
        self.assertEqual( newshot.sg_cut_in, None )
