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
from shotgun_replica.restAPI import server
from shotgun_replica.sync.local_to_shotgun import LocalDBEventSpooler

class Test( unittest.TestCase ):

    def setUp( self ):
        self.serverHandler = server.Handler()
        self.eventprocessor = LocalDBEventSpooler()

    def tearDown( self ):
        pass

    def testProjectCreation( self ):

        userdict = config.getUserDict()

        nowstr = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )

        projectData = {
                       "name": "TESTPROJECTE - DELETE ME - " + str( uuid.uuid1() ),
                       "code": "0000_" + str( uuid.uuid1() ),
                       "updated_by": userdict,
                       "updated_at": nowstr,
                       "created_by": userdict,
                       "created_at": nowstr
                       }

        entityDictStr = self.serverHandler.POST( "Project", None, None, testdata = projectData )
        entityDict = json.loads( entityDictStr )
        self.assertTrue( entityDict["__local_id"] != None )
        newObj = factories.getObject( "Project", local_id = entityDict["__local_id"] )
        self.assertTrue( newObj != None )
        allOk = self.eventprocessor.connectAndRun()
        self.assertTrue( allOk, "errors on event processing" )
        newObj = factories.getObject( "Project", local_id = entityDict["__local_id"] )
        self.assertTrue( newObj.getRemoteID() )

        self.serverHandler.DELETE( "Project", entityDict["__local_id"], None, testdata = "dummy" )

        newObj = factories.getObject( "Project", local_id = entityDict["__local_id"] )
        self.assertTrue( newObj == None )

        self.eventprocessor.connectAndRun()


    def testProjectUpdate( self ):

        userdict = config.getUserDict()
        nowdt = datetime.datetime.now()
        nowstr = nowdt.strftime( "%Y-%m-%d %H:%M:%S" )

        projectData = {
                       "sg_status": "Active",
                       "sg_due": "2012-08-08"
                       }

        content = self.serverHandler.PUT( "Project", None, testProjectID, testdata = projectData )
        entityDict = json.loads( content )
        self.assertEqual( entityDict["sg_due"], "2012-08-08" )
        newObj = factories.getObject( "Project", local_id = entityDict["__local_id"] )
        self.assertEqual( newObj.sg_due, datetime.date( 2012, 8, 8 ) )

        self.eventprocessor.connectAndRun()


    def testVersionCreation( self ):
        node = factories.getObject( "Node", remote_id = testNodeID_1 )
        output = factories.getObject( "Output", remote_id = testOutputID_1 )
        project = factories.getObject( "Project", remote_id = testProjectID )

        versionData = {
                       "code": "001",
                       "description": "delete me %s" % uuid.uuid1(),
                       "entity": node.sg_link.getShortDict(),
                       "sg_source_output": output.getShortDict(),
                       "project": project.getShortDict(),
                       }

        content = self.serverHandler.POST( "Version", None, None, versionData )
        entityDict = json.loads( content )
        self.assertTrue( entityDict["__local_id"] != None )
        self.assertEqual( entityDict["entity"]["__local_id"], node.sg_link.getLocalID() )

        content = self.serverHandler.DELETE( "Version", entityDict["__local_id"], None, testdata = "dummy" )
