# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
import json
import datetime
from shotgun_replica import config, factories, entities
from shotgun_replica_tests import testNodeID_1, testProjectID, testOutputID_1
import uuid
from shotgun_replica.utilities import debug
from shotgun_replica.restAPI import server
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler
from tests_elefant import testAssetID, createTestNode

class Test( unittest.TestCase ):

    def setUp( self ):
        self.serverHandler = server.Handler()
        self.eventprocessor = LocalDBEventSpooler()

        self.asset = factories.getObject( "Asset", remote_id = testAssetID )
        self.testnode = createTestNode( self.asset )

    def tearDown( self ):
        self.testnode.delete()

    def testNodeVersionCreation( self ):

        versionData = {
            "code": "001",
            "sg_link": self.testnode.getShortDict(),
            "project": self.asset.project.getShortDict(),
        }

        content = self.serverHandler.POST( entities.NodeVersion._type, None, None, versionData )
        entityDict = json.loads( content )
        self.assertTrue( entityDict["sg_link"]["__local_id"] != -1 )

        newObj = factories.getObject( entities.NodeVersion._type,
                                      local_id = entityDict["__local_id"] )
        self.assertNotEqual( newObj.sg_link, None )

        content = self.serverHandler.DELETE( entities.NodeVersion._type, entityDict["__local_id"], None, testdata = "dummy" )
