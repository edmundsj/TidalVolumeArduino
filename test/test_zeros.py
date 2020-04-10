# Test that our FSM correctly transitions when we feed it nothing but zeros.

import unittest
from unittest.mock import Mock
import sys
sys.path.append('src')
from coreLoop import ArduinoCode
import numpy as np

class TestZeros(unittest.TestCase):
    def setUp(self):
        self.arduino = ArduinoCode()
        self.totalTime = 0;

    # Verify that we never change the state from its initial value when we feed in nothing but zeros
    def testZeros(self):
        self.arduino.readPressureBytes = Mock(return_value = 0)
        self.arduino.readTempBytes = Mock(return_value = 0)

        while self.totalTime <= 1000: # Run the test for 1 second
            # increment the time artificially by our sampling time
            # Verify that we never change the state from its initial value
            self.assertEqual(self.arduino.state, self.arduino.EXHALATION);

            self.arduino.runCoreLoop()
            self.totalTime += self.arduino.samplingTimeMillis

    def testUnitStep(self):
        stepOnset = 51; # set the step onset to 51ms
        stepReturnValues = [50*np.heaviside(time - stepOnset, 1) for time in \
                range(0,1000,self.arduino.samplingTimeMillis)]
        print(stepReturnValues)

        self.arduino.readPressureBytes = Mock(side_effect= stepReturnValues)
        self.arduino.readTempBytes = Mock(return_value = 0)
        while self.totalTime <= 500:
            self.arduino.runCoreLoop()
            print(f'time: {self.totalTime}')
            print(f'pressure: {self.arduino.pressureAverage}')
            print(f'flow: {self.arduino.flowAverage}')
            print(f'state: {self.arduino.stateToString()}')
            if(self.totalTime < stepOnset):
                self.assertEqual(self.arduino.state, self.arduino.EXHALATION)
            elif(self.totalTime - stepOnset > 0):
                self.assertEqual(self.arduino.state, self.arduino.TRANSITION_TO_INHALATION)

            self.totalTime += self.arduino.samplingTimeMillis
