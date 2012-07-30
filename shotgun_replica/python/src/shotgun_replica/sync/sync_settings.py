# -*- coding: utf-8 -*-

'''
Created on Jul 4, 2012

@author: bach
'''

import json
from shotgun_replica import config

class SyncomaniaSettings( dict ):
    def save( self ):
        settingsFilename = config.SYNCSETTINGS_FILE_PATH
        settings_fh = open( settingsFilename, "w" )
        json.dump( self, settings_fh )
        settings_fh.close()

    def load( self ):
        settingsFilename = config.SYNCSETTINGS_FILE_PATH
        settings_fh = open( settingsFilename, "r" )
        dadict = json.load( settings_fh )
        self.update( dadict )
        settings_fh.close()
