# -*- coding: utf-8 -*-

'''
handling thumbnailing
'''

from shotgun_replica import config as srconfig
import shotgun_api3
import os
from shotgun_api3.lib.httplib2 import Http
from shotgun_replica.utilities import debug
from elefant.utilities import config
import uuid
import shutil

def getUrlAndStoreLocally( entity_type, entity_id, attribute_name ):

    sg = shotgun_api3.Shotgun( srconfig.SHOTGUN_URL,
                               srconfig.SHOTGUN_SYNC_SKRIPT,
                               srconfig.SHOTGUN_SYNC_KEY )
    val = sg.find_one( entity_type,
                       filters = [['id', 'is', entity_id]],
                       fields = [attribute_name] )
    imageUrl = val[attribute_name]

    if imageUrl != None:
        saveShotgunImageLocally( imageUrl )
        
    return imageUrl.split("?")[0]

def __getPathFromImageUrl( url ):
    """return path from image url"""
    url = url.replace( "https://", "" )
    url = url.replace( "http://", "" )
    pathElements = url.split( "/" )
    server = pathElements[0]
    filename = pathElements[len( pathElements ) - 1]
    filename = filename.split( "?" )[0]

    path = os.sep.join( pathElements[1:( len( pathElements ) - 1 )] )
    return [path, filename]

def __getAbsShotgunImagePath( path, filename ):
    """get shotgun image path locally"""
    thepath = os.path.join( srconfig.SHOTGUN_LOCAL_THUMBFOLDER, path )
    if not ( os.path.isdir( thepath ) ):
        oldumask = os.umask(0o002)
        os.makedirs( thepath, 0o775 )
        os.umask(oldumask)
    return os.path.join( thepath, filename )

def createTestThumbnailPath( srcImage ):
    """ store image in local thumbpath and return shotgun-url
    """

    url = config.Configuration().get( config.CONF_SHOTGUN_URL )
    url += "/files/testfiles/" + str( uuid.uuid1() ) + "/"
    url += os.path.basename( srcImage )

    localPath = getLocalThumbPath( url )
    shutil.copy( srcImage, localPath )

    return url

def getLocalThumbPath( url ):
    """ translate thumbnail url to local path """

    if url == None:
        return None
    [path, filename] = __getPathFromImageUrl( url )
    return __getAbsShotgunImagePath( path, filename )

def saveShotgunImageLocally( url ):
    """save shotgun image locally"""
    if type( url ) not in [str, unicode]:
        return None
    debug.debug( "loading: " + url )

    http = Http()
    [response, content] = http.request( url, "GET" )
    debug.debug( response )
    [path, filename] = __getPathFromImageUrl( url )

    savedAt = __getAbsShotgunImagePath( path, filename )
    debug.debug( savedAt )
    oldumask = os.umask( 0o002 )
    imagefile = open( savedAt, "w" )
    imagefile.write( content )
    imagefile.close()
    os.umask( oldumask )
    os.chmod( savedAt, 0o664 )

    return savedAt
