'''
Created on 25.02.2013

@author: gasr
'''
from tests_elefant import baseTest
from elefant.utilities import config
import os
from shotgun_replica import thumbnails
import shutil


class Test( baseTest.NonGuiElefantBaseTest ):


    def testCreateTestImage( self ):
        filename = "chuck_norris.png"
        staticFiles = config.Configuration().get( config.CONF_STATIC_FILES )
        testfile = os.path.join( staticFiles,
                                 "testing",
                                 "images",
                                 filename )
        daurl = thumbnails.createTestThumbnailPath( testfile )

        localPath = thumbnails.getLocalThumbPath( daurl )
        self.assertTrue( os.path.isfile( localPath ) )
        self.assertTrue( daurl.startswith( config.Configuration().get( config.CONF_SHOTGUN_URL ) ) )
        self.assertTrue( daurl.endswith( filename ) )

        shutil.rmtree( os.path.dirname( localPath ) )
