# -*- coding: utf-8 -*-

'''
Created on Jun 25, 2012

@author: bach
'''

from shotgun_replica.entities import Task
from shotgun_replica.sync.sync_settings import SyncomaniaSettings
from shotgun_replica.utilities import debug, entityNaming
from shotgun_replica import config, factories, connectors

from shotgun_api3.lib.httplib2 import Http
import shotgun_api3

import os
import re

COUCHDB_FAILURE = 1
SHOTGUN_FAILURE = 2
SEVERE_FAILURE = 250

EVENT_OK = 0
EVENT_ERROR = 1
EVENT_UNKNOWN = 2

FIELD_LASTEVENTID = "last_eventid"

class EventSpooler( object ):
    """Continuously spools events from shotgun"""

    src = None

    def _connect( self ):
        """ _connect to shotgun and database """
        try:
            self.src = connectors.DatabaseModificator()
        except Exception, error: #IGNORE:W0703
            debug.debug( "Unable to _connect to couchdb server. " + unicode( error ), debug.ERROR )
            return False

        try:
            self.sg = shotgun_api3.Shotgun( config.SHOTGUN_URL,
                                            config.SHOTGUN_BACKSYNC_SKRIPT,
                                            config.SHOTGUN_BACKSYNC_KEY )
        except Exception, error: #IGNORE:W0703
            debug.debug( "Unable to _connect to Shotgun server. " + unicode( error ), debug.ERROR )
            return False

        self.data = SyncomaniaSettings()
        try:
            self.data.load()

        except Exception, error: #IGNORE:W0703
            debug.debug( "no syncomania data available yet: " + unicode( error ), debug.ERROR )
            return False

        # everything is ok
        return True

    def _processIteration(self):
        current = self.data[FIELD_LASTEVENTID]
        ep = EventProcessor( self.src, self.sg )
        eventliste = []
        ANZAHL = 100
        
        doRepeat = True
        
        while doRepeat:
            try:
                eventliste = self.sg.find( 
                                "EventLogEntry",
                                filters = [['id', 'greater_than', current]],
                                fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                order = [{'column':'id', 'direction':'asc'}],
                                filter_operator = 'all',
                                limit = ANZAHL )
    
            except Exception, error: #IGNORE:W0703
                debug.debug( "Exception retrieving Events from Shotgun: ", debug.ERROR )
                debug.debug( error, debug.ERROR )
                eventliste = []
                return False
    
            doRepeat = len( eventliste ) == ANZAHL
    
            for event in eventliste:
                debug.debug( 'processing event id %d' % event['id'] )
                debug.debug( '     ' + event['event_type'] )
    
                debug.debug( event )
    
                status = ep.process( event )
                status = EVENT_OK
                if ( status in [ EVENT_OK, EVENT_UNKNOWN ] ):
                    if status == EVENT_UNKNOWN:
                        debug.debug( "ignored unknown event: " + str( event['id'] ) )
    
                    current = event['id']
    
                    self.data[FIELD_LASTEVENTID] = current
                    self.data.save()
                    self.src.con.commit()
        return True

    def connectAndRun( self ):
        """run the event process loop"""

        if self._connect():
            return self._processIteration()
        else:
            return False

class EventProcessor( object ):
    """Processes change-events of shotgun"""
    def __init__( self, src, sg ):

        regexp = 'Shotgun_([A-Za-z0-9_]+)_(New|Change|Retirement)'

        self.evtype_regexp = re.compile( regexp )
        self.src = src
        self.sg = sg
        self.event = None
        self.obj_type = None

    def process( self, event ):
        """ process an event """

        # check if we care about the event
        debug.debug( "got event of type: " + event['event_type'] )
        mobj = self.evtype_regexp.match( event['event_type'] )
        if mobj:
            self.event = event
            self.obj_type = mobj.group( 1 )

            if self.obj_type != None:
                entityDef = connectors.getClassOfType( self.obj_type )

                if entityDef == None:
                    debug.debug( "    Unknown entity: " + self.obj_type, debug.WARNING )
                    return EVENT_UNKNOWN

            obj_action = mobj.group( 2 )
            if ( obj_action == "New" ):
                return self._item_added()
            if ( obj_action == "Change" ):
                return self._item_changed()
            if ( obj_action == "Retirement" ):
                return self._item_deleted()

        return EVENT_UNKNOWN


    def _getAttribData( self, obj_type, attrib_name ):
        if self.event['meta']['attribute_name'] not in ["id", "type", "retirement_date"]:
            entityDef = connectors.getClassOfType( obj_type ).shotgun_fields
            if entityDef != None and entityDef.has_key( attrib_name ):
                return entityDef[attrib_name]
            else:
                return {}
        else:
            return {}

    def _cleanItem( self, item ):
        for key in item.keys():
            if ( key not in ["id", "type", "name"] ):
                item.pop( key )
        return item

    def _item_changed( self ):
        debug.debug( "changing object of type: " + self.obj_type )
        debug.debug( self.event )

        if self.event['entity'] == None:
            debug.debug( "no entity to work on", debug.WARNING )
            return EVENT_UNKNOWN

        entity = factories.getObject( self.obj_type, remote_id = self.event['entity']['id'] )
        if entity == None:
            self.src.con.rollback()
            debug.debug( "object does not exist in db" + \
                           str( [ self.obj_type, self.event['entity']['id'] ] ), debug.ERROR )
            return EVENT_UNKNOWN

        if self.event['meta'] == None:
            debug.debug( "   did not change unknown attrib data", debug.ERROR )
            return EVENT_UNKNOWN

        attrib_data = self._getAttribData( self.obj_type, self.event['meta']['attribute_name'] )
        debug.debug( attrib_data )

        if len( attrib_data.keys() ) > 0:
            changes = self._getChanges( entity, attrib_data, self.event )
            names = changes.keys()
            values = []
            for x in names:
                attrDef = self._getAttribData( self.obj_type, x )
                convFunc = connectors.getConversionSg2Pg( attrDef['data_type']['value'] )
                values.append( convFunc( changes[x] ) )

            changeStr = [ "\"%s\"=%s" % ( x, "%s", ) for x in names]

            query = "UPDATE \"%s\" SET %s WHERE id=%s" % ( self.obj_type,
                                                          ", ".join( changeStr ),
                                                          "%s" )
            values.append( entity.remote_id )

            cur = self.src.con.cursor()
            debug.debug( cur.mogrify( query, values ) )
            cur.execute( query, values )

            debug.debug( "   changed finnished" )
        else:
            debug.debug( "   did not change unknown attrib data", debug.WARNING )

        return EVENT_OK

    def _getChanges( self, entity, attrib_data, event ):
        changes = {}
        if attrib_data['data_type']['value'] == 'multi_entity':
            debug.debug( "   changing multi-entity: " + event['meta']['attribute_name'] )
            toadd = event['meta']['added']
            toremove = event['meta']['removed']

            changes[event['meta']['attribute_name']] = entity.__getattribute__( event['meta']['attribute_name'] )

            if changes[event['meta']['attribute_name']] == None:
                changes[event['meta']['attribute_name']] = []

            childlist = changes[event['meta']['attribute_name']]

            removeConnEntities = []

            for item in toadd:
                if item != None:
                    childlist.append( self._cleanItem( item ) )

            for item in toremove:
                if item != None:
                    remType = item['type']
                    remId = item['id']

                    for childItem in childlist:
                        if childItem == None or ( childItem.getRemoteID() == remId and childItem.getType() == remType ):
                            removeConnEntities.append( ( entity, childItem ) )
                            childlist.remove( childItem )

            for ( entity, childItem ) in removeConnEntities:

                connectionEntityName = entityNaming.getConnectionEntityName( entity.getType(),
                                                                             event['meta']['attribute_name'] )
                if connectionEntityName:
                    ( srcAttrName, dstAttrName ) = entityNaming.getConnectionEntityAttrName( entity.getType(),
                                                                                             childItem.getType() )
    
                    filters = "%s=%s and %s=%s" % ( srcAttrName,
                                                    "%s",
                                                    dstAttrName,
                                                    "%s"
                                                  )
                    filterValues = [ entity.getPgObj(), childItem.getPgObj() ]
    
                    delEntities = factories.getObjects( connectionEntityName, filters, filterValues )
    
                    for entity in delEntities:
                        self.src.delete( entity )

        elif attrib_data['data_type']['value'] == 'image':
            val = self.sg.find_one( self.obj_type,
                                   filters = [['id', 'is', self.event['entity']['id']]],
                                   fields = [event['meta']['attribute_name']] )
            imageUrl = val[event['meta']['attribute_name']]
            changes[event['meta']['attribute_name']] = imageUrl
            if imageUrl != None:
                saveShotgunImageLocally( imageUrl )
        else:
            debug.debug( "   changing attribute: " + event['meta']['attribute_name'] )
            changes[event['meta']['attribute_name']] = event['meta']['new_value']
        return changes



    def _item_deleted( self ):
        debug.debug( "deleting object of type: " + self.obj_type )
        debug.debug( "   meta: " )
        debug.debug( self.event )

        entity = factories.getObject( self.event['meta']['class_name'], remote_id = self.event['meta']['id'] )
        if entity == None:

            debug.debug( "object to delete not available", debug.WARNING )
            return EVENT_UNKNOWN

        else:
            # If task is deleted update corresponding tasks-field of parent entry
            if type( entity ) == Task:
                pEntity = None
                if entity.entity != None:
                    pEntity = entity.entity
                    self.src.changeInDB( pEntity, attribute = "tasks", value = entity, doRemove = True )
                elif entity["task_template"] != None:
                    pEntity = entity["task_template"]

            query = "DELETE FROM \"%s\" WHERE id=%s" % ( self.event['meta']['class_name'],
                                                        "%s" )
            cur = self.src.con.cursor()
            cur.execute( query, ( entity.getRemoteID(), ) )

            debug.debug( "   delete finnished" )
            return EVENT_OK

    def _item_added( self ):
        debug.debug( "adding object of type: " + self.obj_type )
        debug.debug( "   meta: " )
        debug.debug( self.event )

        detAttribs = connectors.getClassOfType( self.obj_type ).shotgun_fields

        if self.event['entity'] == None:
            debug.debug( "no entity data on newly created object - deleted already?", debug.WARNING )
            return EVENT_UNKNOWN

        # check wheater already available
        obj = factories.getObject( self.obj_type,
                                   remote_id = self.event['entity']['id'] )

        if obj:
            debug.debug( "entity already available in local database", debug.WARNING )
            return EVENT_UNKNOWN

        item = self.sg.find_one( self.obj_type,
                                filters = [['id', 'is', self.event['entity']['id']]],
                                fields = detAttribs.keys() )

        if item == None:
            debug.debug( "no entity to work on", debug.WARNING )
            return EVENT_UNKNOWN

        self.src.add( item )

        debug.debug( "retrieved object: " )
        debug.debug( item )
        debug.debug( "   added finnished" )

        return EVENT_OK


def getPathFromImageUrl( url ):
    """return path from image url"""
    url = url.replace( "https://", "" )
    url = url.replace( "http://", "" )
    pathElements = url.split( "/" )
    server = pathElements[0]
    filename = pathElements[len( pathElements ) - 1]
    path = os.sep.join( pathElements[1:( len( pathElements ) - 1 )] )
    return [server, path, filename]

def getAbsShotgunImagePath( path, filename ):
    """get shotgun image path locally"""
    thepath = os.path.join( config.SHOTGUN_LOCAL_THUMBFOLDER, path )
    if not ( os.path.isdir( thepath ) ):
        os.makedirs( thepath )
    return os.path.join( thepath, filename )

def saveShotgunImageLocally( url ):
    """save shotgun image locally"""
    http = Http()
    [response, content] = http.request( url, "GET" )
    debug.debug( response )
    [server, path, filename] = getPathFromImageUrl( url ) #IGNORE:W0612

    savedAt = getAbsShotgunImagePath( path, filename )
    debug.debug( savedAt )
    imagefile = open( savedAt, "w" )
    imagefile.write( content )
    imagefile.close()
