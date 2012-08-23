# -*- coding: utf-8 -*-

'''
Created on Jul 4, 2012

@author: bach
'''

from shotgun_replica.factories import keyvalues

class SyncomaniaSettings( dict ):
    def save( self ):
        keyvalues.setValue( keyvalues.KEY_SYNC_SETTINGS, self )

    def load( self ):
        dadict = keyvalues.getValue( keyvalues.KEY_SYNC_SETTINGS )
        self.update( dadict )
