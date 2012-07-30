# -*- coding: utf-8 -*-

from elefant.utilities import config
import os

eleconfig = config.Configuration()

SHOTGUN_URL = eleconfig.get( config.CONF_SHOTGUN_URL )
SHOTGUN_BACKSYNC_SKRIPT = eleconfig.get( config.CONF_SHOTGUN_BACKSYNC_SKRIPT )
SHOTGUN_BACKSYNC_KEY = eleconfig.get( config.CONF_SHOTGUN_BACKSYNC_KEY )

SHOTGUN_LOCAL_THUMBFOLDER = eleconfig.get( config.CONF_SHOTGUN_THUMBFOLDER )

DB_HOST = eleconfig.get( config.CONF_DB_HOST )
DB_DATABASE = eleconfig.get( config.CONF_DB_DB )
DB_USERNAME = eleconfig.get( config.CONF_DB_USERNAME )
DB_PASSWORD = eleconfig.get( config.CONF_DB_PASSWORD )

SYNCSETTINGS_FILE_PATH = os.path.join( 
                                      os.path.dirname( __file__ ),
                                      "syncomania_settings.json"
                                      )

def getUserDict():
    """ function that returns a dict describing 
    the user changes should be stored as
    """
    return {"type": "HumanUser",
            "id": eleconfig.get( "shotgun_userid" )}
