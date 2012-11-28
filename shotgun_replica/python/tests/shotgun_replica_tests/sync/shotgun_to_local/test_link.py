# -*- coding: utf-8 -*-

'''
Created on 25.06.2012

@author: bach
'''
from shotgun_replica.connectors import DatabaseModificator, PostgresEntityType
from shotgun_replica.sync.shotgun_to_local import EventProcessor
from shotgun_replica.entities import InOut

from tests_elefant import testProjectID, testShotID, testTaskID, testTaskID_2

from shotgun_api3 import shotgun
import unittest
from shotgun_replica import config, factories
from shotgun_replica.utilities import debug, entityNaming
import pprint
from shotgun_replica._entity_mgmt import _ShotgunEntity
from shotgun_replica.sync import shotgun_to_local

NEWVALUE = "rdy"
OLDVALUE = "wtg"

class Test( unittest.TestCase ):
    def setUp( self ):
        self.sg = shotgun.Shotgun( config.SHOTGUN_URL,
                                   config.SHOTGUN_SYNC_SKRIPT,
                                   config.SHOTGUN_SYNC_KEY )
        self.src = DatabaseModificator()
        self.ep = EventProcessor( self.src, self.sg )

        self.deleteEntities = []
        self.shotgun2local = shotgun_to_local.EventSpooler()

    def tearDown( self ):

        for entry in self.deleteEntities:
            if type( entry ) == dict:
                self.sg.delete( entry["type"],
                                entry["id"] )
            elif isinstance( entry, PostgresEntityType ):
                self.sg.delete( entry.type,
                                entry.remote_id )
            elif isinstance( entry, _ShotgunEntity ):
                self.sg.delete( entry.getType(),
                                entry.getRemoteID() )
            else:
                raise Exception( "%s not handled" % type( entry ) )

        self.assertTrue( self.shotgun2local.connectAndRun(), "synch not successful" )

    def _getNewEvents( self ):
        newevents = self.sg.find( "EventLogEntry",
            filters = [['id', 'greater_than', self.lastID]],
            fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
            order = [{'column':'id', 'direction':'asc'}],
            filter_operator = 'all',
            limit = 100 )

        debug.debug( newevents )
        return newevents

    def testAddOutput( self ):
        lastevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]

        self.lastID = lastevent["id"]

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
        self.deleteEntities.append( newOutputDict )

        newevents = self._getNewEvents()

        self.assertEqual( newevents[0]["event_type"], "Shotgun_CustomEntity02_New", "event not as expected" )
        self.assertEqual( newevents[1]["event_type"], "Shotgun_CustomEntity02_Change", "event not as expected" )
        self.assertEqual( newevents[2]["event_type"], "Shotgun_CustomEntity02_Change", "event not as expected" )
        self.assertEqual( newevents[3]["event_type"], "Shotgun_CustomEntity02_Change", "event not as expected" )

        self._processEvents( newevents )

        newOutput = factories.getObject( "CustomEntity02", remote_id = newOutputDict["id"] )

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

        newevents = self._getNewEvents()

        self.assertEqual( len( newevents ), 5 )
        self.assertEqual( newevents[0]["event_type"], "Shotgun_CustomEntity02_sg_sink_tasks_Connection_New" )
        self.assertEqual( newevents[1]["event_type"], "Shotgun_CustomEntity02_sg_sink_tasks_Connection_New" )
        self.assertEqual( newevents[2]["event_type"], "Shotgun_CustomEntity02_Change" )
        self.assertEqual( newevents[3]["event_type"], "Shotgun_Task_Change" )
        self.assertEqual( newevents[4]["event_type"], "Shotgun_Task_Change" )

        self._processEvents( newevents )

        # check if Connection-Entities are available

        filters = "custom_entity02=%s and task=ANY(%s)"
        taskSgObj1 = PostgresEntityType( "Task", remote_id = testTaskID )
        taskSgObj2 = PostgresEntityType( "Task", remote_id = testTaskID_2 )
        outputSgObj = PostgresEntityType( newOutputDict["type"], remote_id = newOutputDict["id"] )
        filterValues = [ outputSgObj, [ taskSgObj1, taskSgObj2 ] ]

        connObjs = factories.getObjects( "CustomEntity02_sg_sink_tasks_Connection", filters, filterValues )
        self.assertEqual( len( connObjs ), 2, "no conn-objs: %s" % pprint.pformat( connObjs, indent = 2 ) )

        # check if return attribute of Task contains this CustomEntity02
        retAttr = entityNaming.getReverseAttributeName( "CustomEntity02", "sg_sink_tasks" )
        for taskID in [ testTaskID, testTaskID_2 ]:
            taskTmpObj = factories.getObject( "Task", remote_id = taskID )
            retOutputs = taskTmpObj.__getattribute__( retAttr )
            self.assertTrue( newOutput in retOutputs )

        changedData["sg_sink_tasks"] = []
        self.sg.update( newOutputDict["type"], newOutputDict["id"], changedData )

        newevents = self._getNewEvents()

        # unfortunately there are two events missing:
        # see: https://support.shotgunsoftware.com/requests/7380
        self.assertEqual( len( newevents ), 3 )
        self.assertEqual( newevents[0]["event_type"], "Shotgun_CustomEntity02_Change" )
        self.assertEqual( newevents[1]["event_type"], "Shotgun_Task_Change" )
        self.assertEqual( newevents[2]["event_type"], "Shotgun_Task_Change" )

        self._processEvents( newevents )

        retAttr = entityNaming.getReverseAttributeName( "CustomEntity02", "sg_sink_tasks" )
        for taskID in [ testTaskID, testTaskID_2 ]:
            taskTmpObj = factories.getObject( "Task", remote_id = taskID )
            retOutputs = taskTmpObj.__getattribute__( retAttr )
            if retOutputs:
                self.assertFalse( newOutput in retOutputs )

        # check if Connection-Entities are deleted

        connObjs = factories.getObjects( "CustomEntity02_sg_sink_tasks_Connection", filters, filterValues )
        self.assertEqual( len( connObjs ), 0, "conn-objs still available: %s" % pprint.pformat( connObjs, indent = 2 ) )

    def _processEvents( self, newevents ):
        self.shotgun2local.connectAndRun()

        self.lastID = newevents[len( newevents ) - 1]["id"]

    def testAddTask( self ):
        lastevent = self.sg.find( 
                                 "EventLogEntry",
                                 filters = [],
                                 fields = ['id', 'event_type', 'attribute_name', 'meta', 'entity'],
                                 order = [{'column':'id', 'direction':'desc'}],
                                 filter_operator = 'all',
                                 limit = 1
                                 )[0]

        self.lastID = lastevent["id"]
        data = {
                "project": {"type": "Project",
                            "id": testProjectID
                            },
                "content": "TEST TASK (delete me)"
                }
        newTaskDict = self.sg.create( "Task", data, [] )
        self.deleteEntities.append( newTaskDict )

        newevents = self._getNewEvents()

#        self.assertEqual(len(newevents), 4, "not the same amount of events uppon creation of Task")
        self.assertEqual( newevents[0]["event_type"], "Shotgun_Task_New", "event not as expected" )

        self._processEvents( newevents )

        newTaskObj = factories.getObject( "Task", remote_id = newTaskDict["id"] )


        self.sg.update( "Task", newTaskDict["id"], {"entity": {"type": "Shot",
                                                                "id": testShotID}} )

        newevents = self._getNewEvents()

        self.assertTrue( newevents[0]["event_type"] in ["Shotgun_Task_Change",
                                                       "Shotgun_Shot_Change"] )

        self.assertTrue( newevents[1]["event_type"] in ["Shotgun_Task_Change",
                                                       "Shotgun_Shot_Change"] )

        self._processEvents( newevents )

        # check if tasks-property of Shot contains this task
        shotObj = factories.getObject( "Shot", remote_id = testShotID )
        self.assertTrue( newTaskObj in shotObj.tasks )

        self.sg.delete( "Task", newTaskDict["id"] )

        newevents = self._getNewEvents()

        self.assertTrue( newevents[0]["event_type"] == "Shotgun_Task_Retirement" )
        self.assertTrue( newevents[1]["event_type"] == "Shotgun_Task_Change" )

        self._processEvents( newevents )

        # check if tasks-property of Shot does not contain this task anymore
        shotObj = factories.getObject( "Shot", remote_id = testShotID )
        self.assertFalse( newTaskObj in shotObj.tasks )


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
