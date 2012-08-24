# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
from shotgun_api3.lib import httplib2
import urllib
import json
import datetime
from shotgun_replica import config, factories, entities
import logging
from shotgun_replica_tests import testNodeID_1, testProjectID, testOutputID_1
import uuid
import sys
from shotgun_replica.utilities import debug

class Test( unittest.TestCase ):

    def setUp( self ):
        pass

    def tearDown( self ):
        pass

    def testProjectCreation( self ):

        url = 'http://localhost:8080/Project'

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

        params = urllib.urlencode( {
          'data': json.dumps( projectData ),
          'lastName': 'Doe'
        } )

        http = httplib2.Http()
        http.add_credentials( 'username', 'password' )

        response, content = http.request( url, "POST", params )
        debug.debug( "PROJECT CREATION - PROJECT CREATION - PROJECT CREATION - PROJECT CREATION - PROJECT CREATION" )
        debug.debug( response )
        debug.debug( content )
        self.assertEqual( response["status"], "200" )
        entityDict = json.loads( content )
        self.assertTrue( entityDict["__local_id"] != None )
        
        url = 'http://localhost:8080/Project/%d' % entityDict["__local_id"]
        response, content = http.request( url, "DELETE" )
        self.assertEqual( response["status"], "200" )
        

    def testProjectUpdate( self ):

        url = 'http://localhost:8080/Project/34'

        userdict = config.getUserDict()
        nowstr = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )

        projectData = {
                       "sg_status": "Active",
                       "sg_due": "2012-08-08",
#                       "updated_by": userdict,
#                       "updated_at": nowstr,
                       }

        putData = {
                   "data": json.dumps( projectData )
                   }

        params = urllib.urlencode( putData )

        http = httplib2.Http()
        http.add_credentials( 'username', 'password' )

        response, content = http.request( url, "PUT", params )
        debug.debug( "PROJECT UPDATE PROJECT UPDATE PROJECT UPDATE PROJECT UPDATE" )
        debug.debug( response )
        debug.debug( content )
        self.assertEqual( response["status"], "200" )
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

        putData = {
                   "data": json.dumps( versionData )
                   }

        params = urllib.urlencode( putData )

        http = httplib2.Http()
        http.add_credentials( 'username', 'password' )

        url = 'http://localhost:8080/Version'

        response, content = http.request( url, "POST", params )
        debug.debug( "NODE CREATION - NODE CREATION - NODE CREATION - NODE CREATION" )
        debug.debug( response )
        debug.debug( content )
        self.assertEqual( response["status"], "200" )
        entityDict = json.loads( content )
        self.assertTrue( entityDict["__local_id"] != None )
        
        url = 'http://localhost:8080/Version/%d' % entityDict["__local_id"]
        response, content = http.request( url, "DELETE" )
        self.assertEqual( response["status"], "200" )


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig( level = logging.DEBUG, stream = sys.stdout )
    unittest.main()
