# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''
import unittest
from shotgun_replica.factories import keyvalues

class Test( unittest.TestCase ):

    def setUp( self ):
        pass

    def tearDown( self ):
        pass

    def testSyncSettingsRetrieval( self ):
        thejson = keyvalues.getValue( keyvalues.KEY_SYNC_SETTINGS )
        self.assertTrue( type( thejson ) == dict )

    def testTestValueRetrieval( self ):
        thejson = keyvalues.getValue( keyvalues.KEY_TEST_VALUE )
        self.assertTrue( type( thejson ) == type( "" ), thejson )

    def testSyncSettingsSetting( self ):
        thejson = keyvalues.getValue( keyvalues.KEY_SYNC_SETTINGS )
        thejson["newitem"] = "hallo"
        keyvalues.setValue( keyvalues.KEY_SYNC_SETTINGS, thejson )

        thenewjson = keyvalues.getValue( keyvalues.KEY_SYNC_SETTINGS )
        self.assertTrue( thenewjson.has_key( "newitem" ) )

        thejson.pop( "newitem" )
        thejson = keyvalues.setValue( keyvalues.KEY_SYNC_SETTINGS, thejson )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
