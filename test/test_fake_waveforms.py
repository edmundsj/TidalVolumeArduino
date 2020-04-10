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
        self.honeywellZero = self.arduino.pressureToHoneywellSerial(0);
        self.honeywell30Lmin = self.arduino.flowToHoneywellSerial(30);

    # Verify that we never change the state from its initial value when we feed in nothing but zeros
    def testZeros(self):
        self.arduino.readPressureBytes = Mock(return_value = self.honeywellZero)
        self.arduino.readTempBytes = Mock(return_value = 0)

        while self.totalTime <= 100: # Run the test for 1 second
            # increment the time artificially by our sampling time
            # Verify that we never change the state from its initial value
            self.assertEqual(self.arduino.state, self.arduino.EXHALATION);

            self.arduino.runCoreLoop()
            self.totalTime += self.arduino.samplingTimeMillis

    def testUnitStepUp(self):
        stepOnset = 21; # set the step onset to 21ms
        timeMax = 250
        stepReturnValues = [self.honeywellZero for time in range(
            0, stepOnset,
            self.arduino.samplingTimeMillis)]
        stepReturnValues += [self.honeywell30Lmin for time in range(
            stepOnset,
            timeMax, self.arduino.samplingTimeMillis)]

        print(stepReturnValues)

        self.arduino.readPressureBytes = Mock(side_effect= stepReturnValues)
        self.arduino.readTempBytes = Mock(return_value = 0)
        while self.totalTime <= timeMax:
            print(f'---time: {self.totalTime}')
            self.arduino.runCoreLoop()
            #print(f'serial: {self.arduino.pressureInt}')
            #print(f'pressure: {self.arduino.pressure}')
            print(f'flow: {self.arduino.flow}')
            print(f'state: {self.arduino.stateToString()}')

            if self.totalTime < stepOnset:
                self.assertEqual(self.arduino.state, self.arduino.EXHALATION,
                        msg=f'wrong state at time {self.totalTime}')
            elif (self.totalTime > stepOnset and \
                    (self.totalTime < stepOnset + self.arduino.minimumInhalationMillis)):
                self.assertEqual(self.arduino.state, self.arduino.TRANSITION_TO_INHALATION,
                        msg=f'wrong state at time {self.totalTime}')
            elif self.totalTime > stepOnset + self.arduino.minimumInhalationMillis:
                self.assertEqual(self.arduino.state, self.arduino.INHALATION,
                        msg=f'wrong state at time {self.totalTime}')

            self.totalTime += self.arduino.samplingTimeMillis
