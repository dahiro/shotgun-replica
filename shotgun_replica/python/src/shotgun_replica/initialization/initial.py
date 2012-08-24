

from shotgun_api3.shotgun import Shotgun
from elefant.utilities import config
from shotgun_replica import cleanSysName, connectors, _create_shotgun_classes
from shotgun_replica.utilities import debug

# leave empty for every entity to be checked
UPDATE_ONLY = [ ]

def _connect():
    conf = config.Configuration()
    conn = connectors.getDBConnection()

    cur = conn.cursor()
    sg = Shotgun( conf.get( config.CONF_SHOTGUN_URL ),
                  conf.get( config.CONF_SHOTGUN_SKRIPT ),
                  conf.get( config.CONF_SHOTGUN_KEY ) )

    return ( conn, cur, sg )

def importEntities():
    debug.debug( "starting import Entities", debug.INFO )
    ( conn, cur, sg ) = _connect()

    entities = sg.schema_entity_read()

    classes = entities.keys()
    classes.sort()

    for entityType in classes:
        if entityType in ["EventLogEntry"]:
            continue

        if len( UPDATE_ONLY ) > 0 and entityType not in UPDATE_ONLY:
            continue

        entityName = cleanSysName( entities[entityType]["name"]["value"] )
        if entityType.endswith( "Connection" ):
            entityName = entityType

        debug.debug( "import entities of type " + entityType )

        fieldList = connectors.getClassOfType( entityName ).shotgun_fields

        debug.debug( "deleting entities of type " + entityType )

        query = "DELETE FROM \"%s\"" % ( entityType )
        cur.execute( query )

        debug.debug( "loading entities of type " + entityType )
        objects = sg.find( entityType, [["id", "greater_than", 0]], fieldList.keys() )

        for obj in objects:
            values = []
            names = []
            reprs = []

            for fieldName in fieldList.keys():
                sgType = fieldList[fieldName]['data_type']['value']
                convFunc = connectors.getConversionSg2Pg( sgType )
                if convFunc != None:
                    names.append( "\"%s\"" % fieldName )
                    if sgType == "multi_entity":
                        reprs.append( "%s::entity_sync[]" )
                    else:
                        reprs.append( "%s" )
                    values.append( convFunc( obj[fieldName] ) )

            query = "INSERT INTO \"%s\" (%s) VALUES (%s)" % ( entityType,
                                                         ", ".join( names ),
                                                         ", ".join( reprs ) )

            debug.debug( cur.mogrify( str( query ), values ), debug.DEBUG )
            cur.execute( query, values )

        conn.commit()
    debug.debug( "finnished import Entities", debug.INFO )

if __name__ == "__main__":
    _create_shotgun_classes.main()
    importEntities()

