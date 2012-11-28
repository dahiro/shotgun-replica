'''
Created on Nov 15, 2012

@author: bach
'''
import unittest
import tests_elefant
from shotgun_replica import factories, entities
from tests_elefant import commanda
from shotgun_replica.sync import local_to_shotgun, shotgun_to_local
from shotgun_replica.utilities import entityNaming, debug


class Test( unittest.TestCase ):
    local2shotgun = None
    testassetlibrary = None
    task = None
    testasset = None
    linkedAsset = None

    def setUp( self ):

        self.local2shotgun = local_to_shotgun.LocalDBEventSpooler()
        self.shotgun2local = shotgun_to_local.EventSpooler()

        self.testassetlibrary = factories.getObject( entities.AssetLibrary().getType(),
                                                     remote_id = commanda.TEST_ASSETLIBRARY_ID )
        self.task = factories.getObject( "Task", remote_id = tests_elefant.testTaskID )

        self.testasset = tests_elefant.createTestAsset( self.testassetlibrary )
        debug.debug( self.testasset.getLocalID() )
        self.linkedAsset = tests_elefant.createTestAsset( self.testassetlibrary )
        debug.debug( self.linkedAsset.getLocalID() )


    def tearDown( self ):
        self.testasset.delete()
        self.linkedAsset.delete()
        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )
        self.assertTrue( self.local2shotgun.connectAndRun(), "synch not successful" )

    def testLinkedAsset( self ):

        self.testasset.assets = [ self.linkedAsset ]
        self.testasset.save()

        # get connection objects from source
        connObj = factories.getConnectionObj( targetObj = self.testasset,
                                              sourceObj = self.linkedAsset,
                                              attribute = "assets" )
        self.assertNotEqual( connObj, None )

        # TODO: synch and check if not two connObj
        # 
        self.assertTrue( self.local2shotgun.connectAndRun(), "synch not successful" )
        connObj = factories.getConnectionObj( targetObj = self.testasset,
                                              sourceObj = self.linkedAsset,
                                              attribute = "assets" )
        self.assertNotEqual( type( connObj ), list, "multiple connection objects after synch" )

        # get attribute of reverse field
        reverseAttrName = entityNaming.getReverseAttributeName( "Asset", "assets" )
        linkedAsset = factories.getObject( "Asset", local_id = self.linkedAsset.getLocalID() )
        retLinks = linkedAsset.getField( reverseAttrName )
        self.assertTrue( retLinks != None and self.testasset in retLinks )

        # checking sync from shotgun to local

        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

        connObj = factories.getConnectionObj( targetObj = self.testasset,
                                              sourceObj = self.linkedAsset,
                                              attribute = "assets" )
        self.assertNotEqual( type( connObj ), list, "multiple connection objects after synch" )

        # remove connection

        self.testasset.assets = [ ]
        self.testasset.save()

        connObj = factories.getConnectionObj( targetObj = self.testasset,
                                              sourceObj = self.linkedAsset,
                                              attribute = "assets" )
        self.assertEqual( connObj, None )

        linkedAsset = factories.getObject( "Asset", local_id = self.linkedAsset.getLocalID() )
        retLinks = linkedAsset.getField( reverseAttrName )
        self.assertEqual( retLinks, [] )

        self.assertTrue( self.local2shotgun.connectAndRun(), "synch not successful" )

        connObj = factories.getConnectionObj( targetObj = self.testasset,
                                              sourceObj = self.linkedAsset,
                                              attribute = "assets" )
        self.assertEqual( connObj, None )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLinkedAsset']
    unittest.main()
