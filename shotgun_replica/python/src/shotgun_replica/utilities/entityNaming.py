'''
Created on Oct 17, 2012

@author: bach
'''
import re
import shotgun_replica
#from  import entities
from shotgun_replica.utilities import debug
from shotgun_replica import connectors

def getConnectionEntityName( entityType, attribute ):
    """ return the name of a connection-entity"""

    attributeName = replaceUnderscoresWithCapitals( attribute[:-1] )
    entityName = "%s%sConnection" % ( entityType, attributeName )

    if not shotgun_replica.entities.__dict__.has_key( entityName ):
        entityName = None
        if attribute.find( "_" ) == -1:
            entityName = "%s%sConnection" % ( entityType, attribute[0].upper() + attribute[1:] )
        else:
            entityName = "%s_%s_Connection" % ( entityType, attribute )

    debug.debug( ( entityType, attribute ) )
    debug.debug( ( entityName, attributeName ) )

    if shotgun_replica.entities.__dict__.has_key( entityName ):
        return entityName
    else:
        return None

def getConnectionEntityAttrName( baseEntityType, linkedEntityType, connEntityName ):
    """return the attribute-names of the connection-entity"""

    baseAttrName = replaceCapitalsWithUnderscores( baseEntityType )
    linkedAttrName = replaceCapitalsWithUnderscores( linkedEntityType )

    debug.debug( ( baseAttrName, linkedAttrName ) )

    if baseAttrName != linkedAttrName:
        return ( baseAttrName, linkedAttrName )
    else:
        theclass = connectors.getClassOfType( connEntityName )

        baseAttrNamePrefixed = "source_" + baseAttrName
        linkedAttrNamePrefixed = "dest_" + linkedAttrName

        if theclass.shotgun_fields.has_key( baseAttrNamePrefixed ) and theclass.shotgun_fields.has_key( linkedAttrNamePrefixed ):
            debug.debug( ( baseAttrNamePrefixed, linkedAttrNamePrefixed ) )
            return ( baseAttrNamePrefixed, linkedAttrNamePrefixed )
        elif theclass.shotgun_fields.has_key( baseAttrName ) and theclass.shotgun_fields.has_key( "parent" ):
            return ( baseAttrName, "parent" )

def replaceCapitalsWithUnderscores( name ):
    """return the name of an attribute that is a backlink"""

    result = re.sub( r'([A-Z])', r'_\1', name ).lower()
    if result[0] == "_":
        result = result[1:]
    return result


def replaceUnderscoresWithCapitals( name ):
    """return the name of an attribute that is a backlink"""
    result = re.sub( r'^_+', '', name )
    result = result[0].upper() + result[1:]
    while True:
        matchObj = re.search( r'(_([a-z]))', result )
        if matchObj:
            result = result.replace( matchObj.group( 1 ), matchObj.group( 2 ).upper() )
        else:
            break

    return result

def getReverseAttributeName( entityType, attr ):
    """return the name of an attribute that is a backlink"""

    if entityType == "Asset" and attr == "assets":
        return "parents"
    elif entityType == "Shot" and attr == "shots":
        return "parent_shots"
    else:
        entityQuoted = replaceCapitalsWithUnderscores( entityType )
        return "%s_%s_%ss" % ( entityQuoted, attr, entityQuoted )


