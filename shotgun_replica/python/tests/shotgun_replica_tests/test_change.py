# -*- coding: utf-8 -*-

'''
Created on 21.05.2012

@author: bach
'''
import unittest
from shotgun_replica import factories
from uuid import uuid1
from shotgun_replica.entities import Shot, Project, Task, Step
from shotgun_replica_tests import testProjectID, testShotID, testTaskID

class Test(unittest.TestCase):

    def setUp(self):
        self.testproject = factories.getObject(Project().getType(), testProjectID)
        self.testshot = factories.getObject(Shot().getType(), testShotID)
        self.testtask = factories.getObject(Task().getType(), testTaskID)
        
        self.oldcode = self.testproject.code
        pass

    def tearDown(self):
        self.testproject.code = "9996"
        self.testproject.save()
        
        step = factories.getObject(Step().getType(), 6)
        self.testtask.step = step
        self.testtask.save()

    def testScalarChange(self):
        
        newcode = str(uuid1())
        
        self.testproject.code = newcode
        self.assertFalse(self.testproject.isConsistent())
        
        self.testproject.save()
        
        refproject = factories.getObject("Project", testProjectID)
        self.assertEqual(refproject.code, newcode)

    def testLinkFieldChange(self):
        step = factories.getObject(Step().getType(), 1)
        self.testtask.step = step
        self.testtask.save()
        
        refTask = factories.getObject(Task().getType(), testTaskID)
        self.assertEqual(step, refTask.step)
    
    def testMultiLinkFieldChange(self):
        self.assertTrue(False)
        
    def testLinks(self):
        
        # TODO: add link connection
        self.assertFalse(True)
    
        # TODO: remove link connection
        self.assertFalse(True)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()