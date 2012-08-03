# -*- coding: utf-8 -*-

'''
Created on Jun 25, 2012

@author: bach
'''

from shotgun_replica.connectors import DatabaseConnector, getClassOfType
from shotgun_replica.factories import getObject
from shotgun_replica.conversions import getConversionSg2Pg
from shotgun_replica.entities import Task
from shotgun_replica.sync.sync_settings import SyncomaniaSettings
from shotgun_replica import config

from shotgun_api3.lib.httplib2 import Http
import shotgun_api3

import os
import sys
import time
import re
import logging

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

    def connect( self ):
        """ connect to shotgun and database """
        try:
            self.src = DatabaseConnector()
        except Exception, error: #IGNORE:W0703
            logging.error( "Unable to connect to couchdb server. " + unicode( error ) )
            return False

        try:
            self.sg = shotgun_api3.Shotgun( config.SHOTGUN_URL,
                                            config.SHOTGUN_BACKSYNC_SKRIPT,
                                            config.SHOTGUN_BACKSYNC_KEY )
        except Exception, error: #IGNORE:W0703
            logging.error( "Unable to connect to Shotgun server. " + unicode( error ) )
            return False

        self.data = SyncomaniaSettings()
        try:
            self.data.load()

        except Exception, error: #IGNORE:W0703
            logging.error( "no syncomania data available yet: " + unicode( error ) )
            return False

        # everything is ok
        return True

    def run( self ):
        """run the event process loop"""

        logging.debug( "starting event spooler" )

        while True:
            if self.connect():
                current = self.data[FIELD_LASTEVENTID]
                ep = EventProcessor( self.src, self.sg )
                eventliste = []
                ANZAHL = 100
                try:
                    eventliste = self.sg.find( 
                                    "EventLogEntry",
                                    filters = [['id', 'greater_than', current]],
                                    fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                    order = [{'column':'id', 'direction':'asc'}],
                                    filter_operator = 'all',
                                    limit = ANZAHL )

                except Exception, error: #IGNORE:W0703
                    logging.error( "Exception retrieving Events from Shotgun: " )
                    logging.error( error )
                    eventliste = []
                    time.sleep( 60 )
                    continue

                doSleep = len( eventliste ) < ANZAHL

                for event in eventliste:
                    logging.debug( 'processing event id %d' % event['id'] )
                    logging.debug( '     ' + event['event_type'] )

                    logging.debug( event )

                    status = ep.process(event)
                    status = EVENT_OK
                    if ( status in [ EVENT_OK, EVENT_UNKNOWN ] ):
                        if status == EVENT_UNKNOWN:
                            logging.info( "ignored unknown event: " + str( event['id'] ) )

                        current = event['id']

                        self.data[FIELD_LASTEVENTID] = current
                        self.data.save()
                        self.src.con.commit()
                    else:
                        if ( not status in [ EVENT_UNKNOWN ] ):
                            logging.info( "strange event received: " + str( event['id'] ) + \
                                          " - " + event['event_type'] + " - " + str( status ) )
                            sys.exit( SEVERE_FAILURE )

                if doSleep:
                    sys.stdout.write( "." )
                    self.src.con.commit()
                    time.sleep( 2 )

            else:
                sleeptime = 60
                logging.info( "not connected - sleeping %d" % sleeptime )
                time.sleep( sleeptime )


class EventProcessor( object ):
    """Processes change-events of shotgun"""
    def __init__( self, src, sg ):

        regexp = 'Shotgun_([A-Za-z0-9]+)_(New|Change|Retirement)'

        self.evtype_regexp = re.compile( regexp )
        self.src = src
        self.sg = sg
        self.event = None
        self.obj_type = None

    def process( self, event ):
        """ process an event """

        # check if we care about the event
        logging.debug( "got event of type: " + event['event_type'] )
        mobj = self.evtype_regexp.match( event['event_type'] )
        if mobj:
            self.event = event
            self.obj_type = mobj.group( 1 )

            if self.obj_type != None:
                entityDef = getClassOfType( self.obj_type )

                if entityDef == None:
                    logging.warning( "    Unknown entity: " + self.obj_type )
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
            entityDef = getClassOfType( obj_type ).shotgun_fields
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
        logging.info( "changing object of type: " + self.obj_type )
        logging.debug( self.event )

        if self.event['entity'] == None:
            logging.warn( "no entity to work on" )
            return EVENT_UNKNOWN

        entity = getObject( self.obj_type, remote_id = self.event['entity']['id'] )
        if entity == None:
            self.src.con.rollback()
            logging.error( "object does not exist in db" + \
                           str( [ self.obj_type, self.event['entity']['id'] ] ) )
            return EVENT_UNKNOWN

        if self.event['meta'] == None:
            logging.error( "   did not change unknown attrib data" )
            return EVENT_UNKNOWN

        attrib_data = self._getAttribData( self.obj_type, self.event['meta']['attribute_name'] )
        logging.debug( attrib_data )

        if len( attrib_data.keys() ) > 0:
            changes = self._getChanges( entity, attrib_data, self.event )
            names = changes.keys()
            values = []
            for x in names:
                attrDef = self._getAttribData( self.obj_type, x )
                convFunc = getConversionSg2Pg( attrDef['data_type']['value'] )
                values.append( convFunc( changes[x] ) )

            changeStr = [ "\"%s\"=%s" % ( x, "%s", ) for x in names]

            query = "UPDATE \"%s\" SET %s WHERE id=%s" % ( self.obj_type,
                                                          ", ".join( changeStr ),
                                                          "%s" )
            values.append( entity.remote_id )

            cur = self.src.con.cursor()
            logging.debug( cur.mogrify( query, values ) )
            cur.execute( query, values )

            logging.debug( "   changed finnished" )
        else:
            logging.warning( "   did not change unknown attrib data" )

        return EVENT_OK

    def _getChanges( self, entity, attrib_data, event ):
        changes = {}
        if attrib_data['data_type']['value'] == 'multi_entity':
            logging.info( "   changing multi-entity: " + event['meta']['attribute_name'] )
            toadd = event['meta']['added']
            toremove = event['meta']['removed']

            changes[event['meta']['attribute_name']] = entity.__getattribute__( event['meta']['attribute_name'] )

            if changes[event['meta']['attribute_name']] == None:
                changes[event['meta']['attribute_name']] = []

            childlist = changes[event['meta']['attribute_name']]

            for item in toadd:
                if item != None:
                    childlist.append( self._cleanItem( item ) )

            for item in toremove:
                if item != None:
                    remType = item['type']
                    remId = item['id']

                    for childItem in childlist:
                        if childItem == None or ( childItem.getRemoteID() == remId and childItem.getType() == remType ):
                            childlist.remove( childItem )

        elif attrib_data['data_type']['value'] == 'image':
            val = self.sg.find_one( self.obj_type,
                                   filters = [['id', 'is', self.event['entity']['id']]],
                                   fields = [event['meta']['attribute_name']] )
            imageUrl = val[event['meta']['attribute_name']]
            changes[event['meta']['attribute_name']] = imageUrl
            if imageUrl != None:
                saveShotgunImageLocally( imageUrl )
        else:
            logging.info( "   changing attribute: " + event['meta']['attribute_name'] )
            changes[event['meta']['attribute_name']] = event['meta']['new_value']
        return changes



    def _item_deleted( self ):
        logging.info( "deleting object of type: " + self.obj_type )
        logging.debug( "   meta: " )
        logging.debug( self.event )

        entity = getObject( self.event['meta']['class_name'], remote_id = self.event['meta']['id'] )
        if entity == None:

            logging.warn( "object to delete not available" )
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

            logging.debug( "   delete finnished" )
            return EVENT_OK

    def _item_added( self ):
        logging.info( "adding object of type: " + self.obj_type )
        logging.debug( "   meta: " )
        logging.debug( self.event )

        detAttribs = getClassOfType( self.obj_type ).shotgun_fields

        if self.event['entity'] == None:
            logging.warn( "no entity data on newly created object - deleted already?" )
            return EVENT_UNKNOWN

        item = self.sg.find_one( self.obj_type,
                                filters = [['id', 'is', self.event['entity']['id']]],
                                fields = detAttribs.keys() )

        # TODO: save it in couch
        if item == None:
            logging.warn( "no entity to work on" )
            return EVENT_UNKNOWN

        self.src.add( item )

        logging.debug( "retrieved object: " )
        logging.debug( item )
        logging.debug( "   added finnished" )

        return EVENT_OK


def getPathFromImageUrl( url ):
    """return path from image url"""
    url = url.replace( "https://", "" )
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
    logging.debug( response )
    [server, path, filename] = getPathFromImageUrl( url ) #IGNORE:W0612

    savedAt = getAbsShotgunImagePath( path, filename )
    logging.debug( savedAt )
    imagefile = open( savedAt, "w" )
    imagefile.write( content )
    imagefile.close()

if __name__ == "__main__":
    spooler = EventSpooler()
    logging.basicConfig( level = logging.DEBUG,
                         stream = sys.stdout )
    spooler.run()
