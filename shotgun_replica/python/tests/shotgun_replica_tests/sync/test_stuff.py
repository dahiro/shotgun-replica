# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
import unittest
import os
from shotgun_replica.sync import shotgun_to_local, sync_settings
from shotgun_replica import config

class Test(unittest.TestCase):

    def setUp(self):
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