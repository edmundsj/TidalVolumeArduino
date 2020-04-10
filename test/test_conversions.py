import unittest
import sys
sys.path.append('src')
from coreLoop import ArduinoCode
import numpy as np

class TestConversionFunctions(unittest.TestCase):
    def setUp(self):
        self.arduino = ArduinoCode()

    def testPressureToSerial(self):
        serialData = 8191
        desiredPressure = -0.00466796
        actualPressure = self.arduino.pressureFromSerial(serialData)
        np.testing.assert_allclose(actualPressure, desiredPressure, atol=1e-4, err_msg='8191')

        serialData = 8300
        desiredPressure = 1.01295
        actualPressure = self.arduino.pressureFromSerial(serialData)
        np.testing.assert_allclose(actualPressure, desiredPressure, atol=1e-4, err_msg="8300")

        serialData = 8000
        desiredPressure = -1.78783
        actualPressure = self.arduino.pressureFromSerial(serialData)
        np.testing.assert_allclose(actualPressure, desiredPressure, atol=1e-4, err_msg="8000")

    def testFlowFromPressure(self):
        pressureData = 0
        desiredFlow = 0
        actualFlow = self.arduino.flowFromPressure(pressureData)
        np.testing.assert_allclose(actualFlow, desiredFlow, atol=1e-4, err_msg="0")

        pressureData = 1.04
        desiredFlow = 31.4341
        actualFlow = self.arduino.flowFromPressure(pressureData)
        np.testing.assert_allclose(actualFlow, desiredFlow, atol=1e-4, err_msg="1.04")

        pressureData = -0.63
        desiredFlow = -24.4655
        actualFlow = self.arduino.flowFromPressure(pressureData)
        np.testing.assert_allclose(actualFlow, desiredFlow, atol=1e-4, err_msg="-0.63")

    def testFlowFromSerial(self):
        serialData = 8191
        desiredFlow = -2.10595
        actualFlow = self.arduino.flowFromPressure(self.arduino.pressureFromSerial(serialData))
        np.testing.assert_allclose(actualFlow, desiredFlow, atol=1e-4, err_msg="8191")

        serialData = 8300
        desiredFlow = 31.0226
        actualFlow = self.arduino.flowFromPressure(self.arduino.pressureFromSerial(serialData))
        np.testing.assert_allclose(actualFlow, desiredFlow, atol=1e-4, err_msg="8300")

        serialData = 8001
        desiredFlow = -41.1065
        actualFlow = self.arduino.flowFromPressure(self.arduino.pressureFromSerial(serialData))
        np.testing.assert_allclose(actualFlow, desiredFlow, atol=1e-4, err_msg="8300")


if __name__ == '__main__':
    unittest.main()
