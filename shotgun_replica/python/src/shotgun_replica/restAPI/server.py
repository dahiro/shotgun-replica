"""
RESTful interface to database
"""

import web
import json

from shotgun_replica import connectors, factories
import urlparse

def intOrNone( value ):
    if value == None:
        return None
    else:
        return int( value )

class Handler( object ):
    def GET( self, entityType, localID, remoteID ):
        entityClass = connectors.getClassOfType( entityType )
        if not entityClass: raise web.notfound()

        userData = web.input()

        if localID:
            entity = factories.getObject( entityType,
                                          remote_id = intOrNone( remoteID ),
                                          local_id = intOrNone( localID ) )
            if entity:
                return entity.getShotgunDict()
            else:
                return web.notfound()
        else:
            #
            #userData["queryfilter"].split("=")
            filters = []
            filterValues = []
            for attribute in userData.keys():
                filters.append( "%s=%s" % ( attribute, "%s" ) )
                filterValues.append( userData[attribute] )

            entities = factories.getObjects( entityType, " AND ".join( filters ), filterValues )
            json_entities = []

            for entity in entities:
                json_entities.append( entity.getShortDict() )

            return json_entities

    def DELETE( self, entityType, localID, remoteID ):
        entityClass = connectors.getClassOfType( entityType )
        if not entityClass: raise web.notfound()

        entity = factories.getObject( entityType,
                                      remote_id = intOrNone( remoteID ),
                                      local_id = intOrNone( localID ) )

        if entity:
            return entity.delete()
        else:
            return web.notfound()

    def POST( self, entityType, localID, remoteID ):
        entityClass = connectors.getClassOfType( entityType )
        if not entityClass: raise web.notfound()

        userData = web.input()

        data = json.loads( userData["data"] )
        entity = entityClass()
        entity.loadFromDict( data )
        entity.save()

    def PUT( self, entityType, localID, remoteID ):
        entityClass = connectors.getClassOfType( entityType )
        if not entityClass: raise web.notfound()

        entity = factories.getObject( entityType,
                                      remote_id = intOrNone( remoteID ),
                                      local_id = intOrNone( localID ) )

        if not entity:
            return web.notfound()

        userData = dict( urlparse.parse_qsl( web.data() ) )
        newData = json.loads( userData["data"] )

        entity.loadFromDict( newData )
        entity.save()

def startServer():
    urls = ( 
        '/(\w*)\/?(.+)?\/?(.+)?', 'Handler'
    )
    global app
    app = web.application( urls, globals() )
    app.run()

def stopServer():
    app.stop()

if __name__ == "__main__":
    startServer()
