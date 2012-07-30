# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
from shotgun_replica.connectors import DatabaseConnector
from shotgun_replica.sync.shotgun_to_local import EventProcessor
from shotgun_replica.entities import InOut

from tests_elefant import testProjectID, testShotID, testTaskID, testTaskID_2

from shotgun_api3 import shotgun
import unittest
from shotgun_replica import config
import logging

NEWVALUE = "rdy"
OLDVALUE = "wtg"

class Test( unittest.TestCase ):

    def setUp( self ):
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.src = DatabaseConnector()
        self.ep = EventProcessor( self.src, self.sg )

    def tearDown( self ):
        pass

    def testAddOutput( self ):
        lastevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]
        logging.debug( lastevent )

        lastID = lastevent["id"]

        data = {
                "project": {"type": "Project",
                            "id": testProjectID
                            },
                "code": "newoutput",
                "sg_link": {"type": "Task",
                            "id": testTaskID
                            },
                }

        newOutputDict = self.sg.create( InOut().getType(), data, [] )
        logging.debug( newOutputDict )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        logging.debug( newevents )

        self.assertEqual( newevents[0]["event_type"], "Shotgun_CustomEntity02_New", "event not as expected" )
        self.assertEqual( newevents[1]["event_type"], "Shotgun_CustomEntity02_Change", "event not as expected" )
        self.assertEqual( newevents[2]["event_type"], "Shotgun_CustomEntity02_Change", "event not as expected" )
        self.assertEqual( newevents[3]["event_type"], "Shotgun_CustomEntity02_Change", "event not as expected" )

        for newevent in newevents:
            self.ep.process( newevent )

        lastID = newevents[len( newevents ) - 1]["id"]

        changedData = {
                       'sg_sink_tasks': [
                                         {
                                          "type": "Task",
                                          "id": testTaskID
                                          },
                                         {
                                          "type": "Task",
                                          "id": testTaskID_2
                                          },
                                         ]
                       }

        self.sg.update( newOutputDict["type"], newOutputDict["id"], changedData )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        logging.debug( newevents )

        self.assertEqual( len( newevents ), 5 )
        self.assertEqual( newevents[0]["event_type"], "Shotgun_CustomEntity02_sg_sink_tasks_Connection_New" )
        self.assertEqual( newevents[1]["event_type"], "Shotgun_CustomEntity02_sg_sink_tasks_Connection_New" )
        self.assertEqual( newevents[2]["event_type"], "Shotgun_CustomEntity02_Change" )
        self.assertEqual( newevents[3]["event_type"], "Shotgun_Task_Change" )
        self.assertEqual( newevents[4]["event_type"], "Shotgun_Task_Change" )

        for newevent in newevents:
            self.ep.process( newevent )

        lastID = newevents[len( newevents ) - 1]["id"]

        changedData["sg_sink_tasks"] = []

        self.sg.update( newOutputDict["type"], newOutputDict["id"], changedData )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        logging.debug( newevents )

        # unfortunately there are two events missing:
        # see: https://support.shotgunsoftware.com/requests/7380
        self.assertEqual( len( newevents ), 3 )
        self.assertEqual( newevents[0]["event_type"], "Shotgun_CustomEntity02_Change" )
        self.assertEqual( newevents[1]["event_type"], "Shotgun_Task_Change" )
        self.assertEqual( newevents[2]["event_type"], "Shotgun_Task_Change" )


        for newevent in newevents:
            self.ep.process( newevent )

        lastID = newevents[len( newevents ) - 1]["id"]

        self.sg.delete( newOutputDict["type"], newOutputDict["id"] )

        for newevent in newevents:
            self.ep.process( newevent )

    def testAddTask( self ):
        lastevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]
        logging.debug( lastevent )

        lastID = lastevent["id"]
        data = {
                "project": {"type": "Project",
                            "id": testProjectID
                            },
                "content": "TEST TASK (delete me)"
                }
        newTaskDict = self.sg.create( "Task", data, [] )
        logging.debug( newTaskDict )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        logging.debug( newevents )

#        self.assertEqual(len(newevents), 4, "not the same amount of events uppon creation of Task")
        self.assertEqual( newevents[0]["event_type"], "Shotgun_Task_New", "event not as expected" )

        for newevent in newevents:
            self.ep.process( newevent )

        lastID = newevents[len( newevents ) - 1]["id"]

        self.sg.update( "Task", newTaskDict["id"], {"entity": {"type": "Shot",
                                                                "id": testShotID}} )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )
        logging.debug( newevents )

        self.assertTrue( newevents[0]["event_type"] in ["Shotgun_Task_Change",
                                                       "Shotgun_Shot_Change"] )

        self.assertTrue( newevents[1]["event_type"] in ["Shotgun_Task_Change",
                                                       "Shotgun_Shot_Change"] )

        for newevent in newevents:
            self.ep.process( newevent )

        lastID = newevents[len( newevents ) - 1]["id"]

        self.sg.delete( "Task", newTaskDict["id"] )

        newevents = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [['id', 'greater_than', lastID]],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'asc'}],
                                 filter_operator = 'all',
                                 limit = 100
                                 )

        logging.debug( newevents )

        self.assertTrue( newevents[0]["event_type"] == "Shotgun_Task_Retirement" )
        self.assertTrue( newevents[1]["event_type"] == "Shotgun_Task_Change" )

        for newevent in newevents:
            self.ep.process( newevent )


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
