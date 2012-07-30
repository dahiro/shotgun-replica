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
from shotgun_replica import config
import thread
import time

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
                       "name": "asfasf",
                       "code": "9872",
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
        http.request


    def testProjectUpdate( self ):

        url = 'http://localhost:8080/Project/29'

        userdict = config.getUserDict()
        nowstr = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )

        projectData = {
                       "sg_status": "Active",
                       "sg_due": "2012-08-08",
                       "updated_by": userdict,
                       "updated_at": nowstr,
                       }

        putData = { 
                   "data": json.dumps(projectData)
                   }

        params = urllib.urlencode( putData )

        http = httplib2.Http()
        http.add_credentials( 'username', 'password' )

        response, content = http.request( url, "PUT", params )



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
