'''
Created on Dec 7, 2012

@author: bach
'''
import unittest
from shotgun_replica import factories, entities, thumbnails
import os
from shotgun_replica.utilities import debug
import time
from shotgun_replica_tests import testNodeID_1

class Test( unittest.TestCase ):

    def setUp( self ):
        self.testnode = factories.getObject( entities.Node._type,
                                             remote_id = testNodeID_1 )

    def tearDown( self ):
        pass

    def test_pathtrans( self ):
        localpath = thumbnails.getLocalThumbPath( self.testnode.image )
        self.assertTrue( os.path.isfile( localpath ) )

    def test_retrieval_simple( self ):
        localpath = thumbnails.saveShotgunImageLocally( self.testnode.image )
        results = os.stat( localpath )
        debug.debug(results.st_mtime)
        self.assertTrue(results.st_mtime > time.time() - 20, "file does not seem to have been written lately")

    def test_retrieval_complex( self ):
        oldurl = self.testnode.image
        newurl = thumbnails.getUrlAndStoreLocally( self.testnode.getType(),
                                                   self.testnode.getRemoteID(),
                                                   "image" )
        self.assertEqual( oldurl, newurl )

