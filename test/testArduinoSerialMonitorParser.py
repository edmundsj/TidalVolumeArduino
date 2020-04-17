import unittest
import sys
sys.path.append('src')
from arduinoSerialMonitorParser import ArduinoParser
from datetime import datetime
import numpy as np

class TestParser(unittest.TestCase):

    def testProcessGoodLines(self):
        self.parser.lines = self.simpleFileLines
        self.parser.processLines()
        desiredFlows = self.simpleFlowsProcessed
        desiredTimestamps = self.simpleTimestampsProcessed
        actualFlows = self.parser.flows
        actualTimestamps = self.parser.timestamps

        self.assertEqual(desiredFlows, actualFlows, msg="flows not equal")
        self.assertEqual(desiredTimestamps, actualTimestamps, msg="timestamps not equal")

    def testProcessFaultyLines(self):
        self.parser.lines = self.faultyFileLines
        self.parser.processLines()
        actualFlows = self.parser.flows
        actualTimestamps = self.parser.timestamps
        desiredFlows = np.array([])
        desiredTimestamps = []

        np.testing.assert_allclose(desiredFlows, actualFlows, err_msg="flows not equal")
        self.assertEqual(desiredTimestamps, actualTimestamps, msg="timestamps not equal")

    def testConvertToRelativeTimes(self):
        self.parser.lines = self.simpleFileLines
        self.parser.processLines()
        self.parser.convertToRelativeTimes()
        desiredSeconds = self.simpleSeconds
        actualSeconds = self.parser.seconds
        self.assertEqual(desiredSeconds, actualSeconds, msg="simple seconds not equal")

    def setUp(self):
        self.parser = ArduinoParser()

    @classmethod
    def setUpClass(self):
        self.simpleFileLines = \
                ["15:50:09.450 -> S0.01 -0.00 -683.55 9.66"]
        self.simpleFlowsProcessed = [-0.00]
        self.simpleTimestampsProcessed = [datetime(year=1940, month=1, day=1,hour=15,minute=50, second=9,
            microsecond=450000)]
        self.simpleSeconds = [0]
        self.faultyFileLines = [
                "49:33.316 -> S0.00 0.49 678.97 3.46",
                "17:15:48.006 -> S-0.05 -S⸮S-0.05 -8.26 411.13 6.19",
                "17:15:48.006 -> S-⸮S-0.05 -8.13 0.00 0.00"]
        self.longFileLines = [
                "15:50:09.450 -> S0.01 0.00 683.55 9.66",
                "15:50:09.450 -> S0.00 0.00 683.55 9.66",
                "15:50:09.450 -> S0.00 0.00 683.55 9.66",
                "15:50:09.450 -> S0.00 0.00 683.55 9.66",
                "15:50:09.483 -> S0.00 0.00 683.55 9.66",
                "15:50:09.483 -> S0.00 0.49 683.55 9.66",
                "15:50:09.483 -> S0.00 0.49 683.55 9.66",
                "15:50:09.483 -> S0.00 0.49 683.55 9.66",
                "15:50:09.483 -> S0.00 0.00 683.55 9.66",
                "15:50:09.483 -> S0.00 0.49 683.55 9.66",
            ]

if __name__ == "__main__":
    unittest.main()
