# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''
import unittest
from shotgun_replica.utilities import entityNaming

class Test( unittest.TestCase ):

    def setUp( self ):
        pass

    def tearDown( self ):
        pass

    def testUnderScoreReplacement( self ):
        testPairs = [
            ( "shoot_days", "ShootDays", True ),
            ( "_shoot_days", "ShootDays", False ),
        ]

        for ( underscored, capitalized, needsInverse ) in testPairs:
            replacedCapitalized = entityNaming.replaceUnderscoresWithCapitals( underscored )
            self.assertEqual( replacedCapitalized, capitalized )

            if needsInverse:
                replacedUnderscored = entityNaming.replaceCapitalsWithUnderscores( capitalized )
                self.assertEqual( replacedUnderscored, underscored )

    def testConnectionEntityName( self ):
        testPairs = [
            ( "Asset", "assets", "AssetAssetConnection" ),
            ( "Asset", "sg_linked_assets", "Asset_sg_linked_assets_Connection" ),
            ( "Asset", "shoot_days", "AssetShootDayConnection" )
        ]

        for ( entityType, attrName, connectionEntityName ) in testPairs:
            connEntityNameTesting = entityNaming.getConnectionEntityName( entityType, attrName )
            self.assertEqual( connEntityNameTesting, connectionEntityName )

    def testConnectionAttrNames( self ):
        testPairs = [
            ( "Asset", "Asset", "AssetAssetConnection", "asset", "parent" ),
            ( "Asset", "Shot", "AssetShotConnection", "asset", "shot" ),
            ( "CustomEntity07", "CustomEntity05", "CustomEntity07_sg_sources_Connection", "custom_entity07", "custom_entity05" ),
            ( "Revision", "Revision", "RevisionRevisionConnection", "source_revision", "dest_revision"),
        ]

        for ( srcEntityType, destEntityType, connEntityName, srcAttrName, destAttrName ) in testPairs:
            ( srcAttrNameTest, destAttrNameTest ) = entityNaming.getConnectionEntityAttrName( srcEntityType, destEntityType, connEntityName )
            self.assertEqual( srcAttrNameTest, srcAttrName )
            self.assertEqual( destAttrNameTest, destAttrName )

    def testRetAttributeNames( self ):
        testPairs = [
            ( "Asset", "sg_linked_assets", "asset_sg_linked_assets_assets" ),
            ( "CustomEntity02", "sg_sink_tasks", "custom_entity02_sg_sink_tasks_custom_entity02s" ),
        ]
        for ( entityType, attrName, retAttrName ) in testPairs:
            retAttrNameTest = entityNaming.getReverseAttributeName( entityType, attrName )
            self.assertEqual( retAttrNameTest, retAttrName )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
