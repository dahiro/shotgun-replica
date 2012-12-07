'''
Created on Dec 7, 2012

@author: bach
'''
from shotgun_replica import config
import shotgun_api3
import os
from shotgun_api3.lib.httplib2 import Http
from shotgun_replica.utilities import debug

def getUrlAndStoreLocally( entity_type, entity_id, attribute_name ):

    sg = shotgun_api3.Shotgun( config.SHOTGUN_URL,
                               config.SHOTGUN_BACKSYNC_SKRIPT,
                               config.SHOTGUN_BACKSYNC_KEY )
    val = sg.find_one( entity_type,
                       filters = [['id', 'is', entity_id]],
                       fields = [attribute_name] )
    imageUrl = val[attribute_name]

    if imageUrl != None:
        saveShotgunImageLocally( imageUrl )

    return imageUrl

def __getPathFromImageUrl( url ):
    """return path from image url"""
    url = url.replace( "https://", "" )
    url = url.replace( "http://", "" )
    pathElements = url.split( "/" )
    server = pathElements[0]
    filename = pathElements[len( pathElements ) - 1]
    path = os.sep.join( pathElements[1:( len( pathElements ) - 1 )] )
    return [path, filename]

def __getAbsShotgunImagePath( path, filename ):
    """get shotgun image path locally"""
    thepath = os.path.join( config.SHOTGUN_LOCAL_THUMBFOLDER, path )
    if not ( os.path.isdir( thepath ) ):
        os.makedirs( thepath )
    return os.path.join( thepath, filename )

def getLocalThumbPath( url ):
    """ translate thumbnail url to local path """
    
    if url==None:
        return None
    [path, filename] = __getPathFromImageUrl( url )
    return __getAbsShotgunImagePath( path, filename )

def saveShotgunImageLocally( url ):
    """save shotgun image locally"""
    if type(url) not in [str, unicode]:
        return None
    debug.debug("loading: "+url)

    http = Http()
    [response, content] = http.request( url, "GET" )
    debug.debug( response )
    [path, filename] = __getPathFromImageUrl( url )

    savedAt = __getAbsShotgunImagePath( path, filename )
    debug.debug( savedAt )
    imagefile = open( savedAt, "w" )
    imagefile.write( content )
    imagefile.close()
    
    return savedAt
