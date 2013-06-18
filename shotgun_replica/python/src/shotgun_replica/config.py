# -*- coding: utf-8 -*-
import os

from elefant.utilities import config
eleconfig = config.Configuration()

SHOTGUN_URL = eleconfig.get( config.CONF_SHOTGUN_URL )

# shotgun-script that generates events
SHOTGUN_SYNC_SKRIPT = eleconfig.get( config.CONF_SHOTGUN_SYNC_SKRIPT )
SHOTGUN_SYNC_KEY = eleconfig.get( config.CONF_SHOTGUN_SYNC_KEY )

# folder to store thumbnails locally
SHOTGUN_LOCAL_THUMBFOLDER = eleconfig.get( config.CONF_SHOTGUN_THUMBFOLDER )

DB_HOST = eleconfig.get( config.CONF_DB_HOST )
DB_DATABASE = eleconfig.get( config.CONF_DB_DB )
DB_USERNAME = eleconfig.get( config.CONF_DB_USERNAME )
DB_PASSWORD = eleconfig.get( config.CONF_DB_PASSWORD )

DEBUG_LEVEL = eleconfig.get( config.CONF_DEBUGLEVEL )

SYNCSETTINGS_FILE_PATH = os.path.join( 
                                      os.path.dirname( __file__ ),
                                      "syncomania_settings.json"
                                      )

def getUserDict():
    """ function that returns a dict describing 
    the user changes should be stored as
    """
    
    shotgun_userid = eleconfig.get( "shotgun_userid" )
    if shotgun_userid == None:
        return None
    else:
        return {"type": "HumanUser",
                "id": shotgun_userid }

def getScriptDict():
    """
    get dict representing the api access
    """
    syncScript = config.getScript()
    return {"type": "ApiUser",
            "id": syncScript.getRemoteID() }
