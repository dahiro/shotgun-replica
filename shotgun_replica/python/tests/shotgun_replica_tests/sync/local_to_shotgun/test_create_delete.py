# -*- coding: utf-8 -*-

'''
Created on Jun 27, 2012

@author: bach
'''
from shotgun_replica.factories import getObject
from shotgun_replica.entities import Project, Shot
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler
from shotgun_replica import entity_manipulation, config, factories, entities

from tests_elefant import testProjectID

from shotgun_api3 import shotgun

import unittest
import uuid
import shotgun_replica
from shotgun_replica_tests import testShotID

class Test( unittest.TestCase ):

    def setUp( self ):
        self.testproject = getObject( Project().getType(),
                                      remote_id = testProjectID )
        self.eventprocessor = LocalDBEventSpooler()
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_BACKSYNC_SKRIPT,
                                   config.SHOTGUN_BACKSYNC_KEY )

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

        allOk = self.eventprocessor.connectAndRun()
        self.assertTrue( allOk, "errors while syncing " )

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
        allOk = self.eventprocessor.connectAndRun()
        self.assertTrue( allOk, "errors while syncing " )

        newshot = self.sg.find( 
                               "Shot",
                               filters = [['id', 'is', newRemoteID]],
                               fields = ['id'],
                               filter_operator = 'all',
                               limit = 100
                               )
        self.assertEqual( len( newshot ), 0 )

    def test_create_and_delete( self ):
        testshot = factories.getObject( "Shot", remote_id = testShotID )
        node = entities.Node()
        node.code = "testshot_" + str( uuid.uuid1() )[0:8]
        node.sg_link = testshot
        node.project = self.testproject
        node.save()
        newNodeID = node.getLocalID()

        output = entities.Output()
        output.sg_link = node
        output.code = str( uuid.uuid1() )[0:8] + "_" + "_SCR"
        output.sg_type = "SCR"
        output.project = self.testproject
        output.save()
        newOutputID = output.getLocalID()

        node.delete()

        ret = self.eventprocessor.connectAndRun()
        self.assertTrue( ret, "errors while syncing " )

        node = factories.getObject( entities.Node._type, local_id = newNodeID )
        self.assertEqual( node, None, "node should not exist anymore" )

        output = factories.getObject( entities.Output._type, local_id = newOutputID )
        self.assertEqual( output, None, "output should not exist anymore" )
