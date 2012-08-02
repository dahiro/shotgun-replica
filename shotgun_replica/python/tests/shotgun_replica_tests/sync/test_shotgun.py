# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
import os
from shotgun_replica.sync import shotgun_to_local, sync_settings
from shotgun_replica import config
import shotgun_api3

class Test(unittest.TestCase):

    def setUp(self):
        
        self.sg = shotgun_api3.Shotgun( config.SHOTGUN_URL,
                                        config.SHOTGUN_BACKSYNC_SKRIPT,
                                        config.SHOTGUN_BACKSYNC_KEY )
        eventliste = self.sg.find( 
                        "Version",
                        filters = [['id', 'greater_than', current]],
                        fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                        order = [{'column':'id', 'direction':'asc'}],
                        filter_operator = 'all',
                        limit = ANZAHL )
        pass

    def tearDown(self):
        pass

    def testSyncomaniaSettingsChange(self):
        ss = shotgun_to_local.SyncomaniaSettings()
        ss.save()
        filePath = config.SYNCSETTINGS_FILE_PATH
        self.assertTrue(os.path.isfile(filePath), "%s does not exist" % filePath)
        
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()