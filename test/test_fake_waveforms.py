# Test that our FSM correctly transitions when we feed it nothing but zeros.

import unittest
from unittest.mock import Mock
import sys
sys.path.append('src')
from coreLoop import ArduinoCode
import numpy as np

class TestFakeWaveformsHoneywell(unittest.TestCase):
    def setUp(self):
        self.arduino = ArduinoCode()
        self.totalTime = 0
        self.honeywellZero = self.arduino.pressureToHoneywellSerial(0)
        self.honeywell30Lmin = self.arduino.flowToHoneywellSerial(30)
        self.honeywell15Lmin = self.arduino.flowToHoneywellSerial(15)
        self.honeywell15FlowActual = 14.74165410364667
        self.honeywellNegative8Lmin = self.arduino.flowToHoneywellSerial(-8)
        self.honeywellNegative8FlowActual = -8.156311548424826

    # Verify that we never change the state from its initial value when we feed in nothing but zeros
    def testZerosFSM(self):
        self.arduino.readPressureBytes = Mock(return_value = self.honeywellZero)
        self.arduino.readTempBytes = Mock(return_value = 0)

        while self.totalTime <= 100: # Run the test for 1 second
            # increment the time artificially by our sampling time
            # Verify that we never change the state from its initial value
            self.assertEqual(self.arduino.state, self.arduino.EXHALATION);

            self.arduino.runCoreLoop()
            self.totalTime += self.arduino.samplingTimeMillis

    def testUnitStepUpFSMTransitions(self):
        stepOnset = 21; # set the step onset to 21ms
        timeMax = 250
        stepReturnValues = [self.honeywellZero for time in range(
            0, stepOnset,
            self.arduino.samplingTimeMillis)]
        stepReturnValues += [self.honeywell30Lmin for time in range(
            stepOnset,
            timeMax, self.arduino.samplingTimeMillis)]

        self.arduino.readPressureBytes = Mock(side_effect= stepReturnValues)
        self.arduino.readTempBytes = Mock(return_value = 0)
        while self.totalTime <= timeMax:
            self.arduino.runCoreLoop()

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

    def testUnitStepDownFSMTransitions(self):
        stepOnset = 251;
        timeMax = 550
        stepReturnValues = [self.honeywell30Lmin for time in range(
            0, stepOnset,
            self.arduino.samplingTimeMillis)]
        stepReturnValues += [self.honeywellZero for time in range(
            stepOnset,
            timeMax, self.arduino.samplingTimeMillis)]

        self.arduino.readPressureBytes = Mock(side_effect= stepReturnValues)
        self.arduino.readTempBytes = Mock(return_value = 0)
        while self.totalTime <= timeMax:
            self.arduino.runCoreLoop()
            #print(f'---time: {self.totalTime}')
            #print(f'flow: {self.arduino.flow}')
            #print(f'state: {self.arduino.stateToString()}')

            if self.totalTime < self.arduino.minimumInhalationMillis:
                self.assertEqual(self.arduino.state, self.arduino.TRANSITION_TO_INHALATION,
                        msg=f'wrong state at time {self.totalTime}')
            elif (self.totalTime > self.arduino.minimumInhalationMillis) and \
                    (self.totalTime < stepOnset):
                self.assertEqual(self.arduino.state, self.arduino.INHALATION,
                        msg=f'wrong state at time {self.totalTime}')
            elif self.totalTime > stepOnset and \
                    (self.totalTime < stepOnset + self.arduino.minimumExhalationMillis):
                self.assertEqual(self.arduino.state, self.arduino.TRANSITION_TO_EXHALATION,
                        msg=f'wrong state at time {self.totalTime}')
            elif self.totalTime > stepOnset + self.arduino.minimumExhalationMillis:
                self.assertEqual(self.arduino.state, self.arduino.EXHALATION,
                        msg=f'wrong state at time {self.totalTime}')


            self.totalTime += self.arduino.samplingTimeMillis

    def testTidalVolumeSquareWave(self):
        inhalationTime = 2000
        exhalationTime = 4000
        inhalationSamples = int(inhalationTime / self.arduino.samplingTimeMillis)
        exhalationSamples = int(exhalationTime / self.arduino.samplingTimeMillis)
        maxTime = (inhalationTime + exhalationTime) * 3
        inhaledTidalVolumeDesired = self.honeywell15FlowActual * inhalationTime / 1000.0 / 60.0
        exhaledTidalVolumeDesired = self.honeywellNegative8FlowActual * exhalationTime / 1000.0 / 60.0

        squareUpper = self.honeywell15Lmin*np.ones(inhalationSamples)
        squareLower = self.honeywellNegative8Lmin*np.ones(exhalationSamples)
        squareTotal = np.hstack([squareLower, squareUpper, squareLower, squareUpper, squareLower, squareUpper])

        self.arduino.readPressureBytes = Mock(side_effect= squareTotal)

        while self.totalTime < maxTime:
            self.arduino.runCoreLoop()
            if self.totalTime == exhalationTime - self.arduino.samplingTimeMillis:
                tidalVolumeActual = self.arduino.tidalVolumeExhalation
                np.testing.assert_allclose(tidalVolumeActual, exhaledTidalVolumeDesired,
                        atol=1e-6, err_msg="exhaled 1")
            if self.totalTime == exhalationTime + inhalationTime - self.arduino.samplingTimeMillis:
                tidalVolumeActual = self.arduino.tidalVolumeInhalation
                np.testing.assert_allclose(tidalVolumeActual, inhaledTidalVolumeDesired,
                        atol=1e-6, err_msg="inhaled 1")
            if self.totalTime == exhalationTime*2 + inhalationTime - self.arduino.samplingTimeMillis:
                tidalVolumeActual = self.arduino.tidalVolumeExhalation
                np.testing.assert_allclose(tidalVolumeActual, exhaledTidalVolumeDesired,
                        atol=1e-6, err_msg="exhaled 2")
            if self.totalTime == exhalationTime*2 + inhalationTime*2 - self.arduino.samplingTimeMillis:
                tidalVolumeActual = self.arduino.tidalVolumeInhalation
                np.testing.assert_allclose(tidalVolumeActual, inhaledTidalVolumeDesired,
                        atol=1e-6, err_msg="inhaled 2")

            self.totalTime += self.arduino.samplingTimeMillis
