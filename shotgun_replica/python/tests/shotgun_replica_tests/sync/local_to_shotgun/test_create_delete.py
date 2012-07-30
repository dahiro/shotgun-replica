# -*- coding: utf-8 -*-

'''
Created on Jun 27, 2012

@author: bach
'''
from shotgun_replica.factories import getObject
from tests_elefant import testProjectID
from shotgun_replica.entities import Project, Shot
import unittest
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler
from shotgun_replica import entity_manipulation
import uuid
from shotgun_api3 import shotgun
from elefant.utilities import config

class Test( unittest.TestCase ):

    def setUp( self ):
        self.testproject = getObject( Project().getType(), testProjectID )
        self.eventprocessor = LocalDBEventSpooler()
        self.sg = shotgun.Shotgun( config.Configuration().get( config.CONF_SHOTGUN_URL ),
                                   config.Configuration().get( config.CONF_SHOTGUN_SKRIPT ),
                                   config.Configuration().get( config.CONF_SHOTGUN_KEY ) )

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

        self.eventprocessor.processIteration()

        shot_ret = getObject( "Shot", local_id = newshotid )
        newRemoteID = shot_ret.getRemoteID()
        self.assertTrue( shot_ret.getRemoteID() != None )
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
        self.eventprocessor.processIteration()

        newshot = self.sg.find( 
                               "Shot",
                               filters = [['id', 'is', newRemoteID]],
                               fields = ['id'],
                               filter_operator = 'all',
                               limit = 100
                               )
        self.assertEqual( len( newshot ), 0 )
