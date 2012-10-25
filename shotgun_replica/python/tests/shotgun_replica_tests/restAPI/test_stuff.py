# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
import json
import datetime
from shotgun_replica import config, factories
from shotgun_replica_tests import testNodeID_1, testProjectID, testOutputID_1
import uuid
from shotgun_replica.utilities import debug
from shotgun_replica.restAPI import server

class Test( unittest.TestCase ):

    def setUp( self ):
        self.serverHandler = server.Handler()

    def tearDown( self ):
        pass

    def testProjectCreation( self ):

        userdict = config.getUserDict()

        nowstr = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )

        projectData = {
                       "name": "TESTPROJECTE - DELETE ME",
                       "code": "0000_" + str( uuid.uuid1() ),
                       "updated_by": userdict,
                       "updated_at": nowstr,
                       "created_by": userdict,
                       "created_at": nowstr
                       }

        entityDictStr = self.serverHandler.POST( "Project", None, None, testdata = projectData )
        entityDict = json.loads( entityDictStr )
        debug.debug( entityDict )
        self.assertTrue( entityDict["__local_id"] != None )

        entityDict = self.serverHandler.DELETE( "Project", entityDict["__local_id"], None, testdata = "dummy" )

    def testProjectUpdate( self ):

        userdict = config.getUserDict()
        nowstr = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )

        projectData = {
                       "sg_status": "Active",
                       "sg_due": "2012-08-08",
                       "updated_by": userdict,
                       "updated_at": nowstr,
                       }

        content = self.serverHandler.PUT( "Project", None, testProjectID, testdata = projectData )
        entityDict = json.loads( content )
        self.assertEqual( entityDict["sg_due"], "2012-08-08" )

    def testNodeVersionCreation( self ):
        node = factories.getObject( "Node", remote_id = testNodeID_1 )
        output = factories.getObject( "Output", remote_id = testOutputID_1 )
        project = factories.getObject( "Project", remote_id = testProjectID )

        versionData = {
                       "code": "001",
                       "description": "delete me %s" % uuid.uuid1(),
                       "entity": node.sg_link.getSgObj(),
                       "sg_source_output": output.getSgObj(),
                       "project": project.getSgObj(),
                       }

        content = self.serverHandler.POST( "Version", None, None, versionData )
        entityDict = json.loads( content )
        self.assertTrue( entityDict["__local_id"] != None )

        content = self.serverHandler.DELETE( "Version", entityDict["__local_id"], None, testdata = "dummy" )
