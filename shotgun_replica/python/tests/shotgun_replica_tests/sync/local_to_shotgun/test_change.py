# -*- coding: utf-8 -*-

'''
Created on Jun 27, 2012

@author: bach
'''
from shotgun_replica.factories import getObject
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler
from shotgun_replica.entities import Project, Shot
from shotgun_replica import config

from tests_elefant import testProjectID

from shotgun_api3 import shotgun

import unittest
import uuid
from shotgun_replica.sync import shotgun_to_local

class Test( unittest.TestCase ):

    def setUp( self ):
        self.testproject = getObject( Project().getType(), remote_id = testProjectID )
        self.eventprocessor = LocalDBEventSpooler()
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_BACKSYNC_SKRIPT,
                                   config.SHOTGUN_BACKSYNC_KEY )
        self.shotgun2local = shotgun_to_local.EventSpooler()

    def tearDown( self ):
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

        self.assertTrue( newRemoteID != None )

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

