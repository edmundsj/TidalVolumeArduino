import sys
import re
import numpy as np
import json
from dateutil.parser import parse as parseDate
sys.path.append('raw_data')

class ArduinoParser():
    def __init__(self):
        self.lines = []
        self.processedLines = []
        self.flows = np.array([])
        self.timestamps = []
        self.seconds = np.array([])
        self.duration = 0
        self.fs = 0
        self.tidalVolumes = np.array([])
        self.minuteVolumes = np.array([])
        actualSamplingTime = 6.0009
        usedSamplingTime = 5.0;
        self.correctionFactor = actualSamplingTime / usedSamplingTime

    def readFile(self, filename):
        with open(filename) as textFile:
            self.lines = textFile.readlines()

    def writeFile(self, filename):
        totalData = np.transpose(np.array([self.seconds, self.flows, self.tidalVolumes, self.minuteVolumes]))
        np.savetxt(filename, totalData, fmt='%f', delimiter=',')
    def inputMetadata(self, metadata):
        """ add data to dictionary with keys 'targetFlowRate', 'leftPressure', 'rightPressure', 'leftTidalVolume', 'rightTidalVolume', 'compliance'
        """
        self.metadata = metadata
    def writeJSONFile(self, filename):
        dictionary = {}
        dictionary['time'] = self.seconds.tolist()
        dictionary['flow'] = self.flows.tolist()
        dictionary['tidalVolume'] = self.tidalVolumes.tolist()
        dictionary.update(self.metadata)
        with open(filename, 'w') as fp:
            json.dump(dictionary, fp)
    # Directly converts timestamps into times
    def convertToRelativeTimes(self):
        startingTime = self.timestamps[0]
        for time in self.timestamps:
            deltaTime = time - startingTime
            deltaSeconds = deltaTime.total_seconds()
            self.seconds = np.append(self.seconds, deltaSeconds)
        self.duration = self.seconds[-1]
        self.timeDelta = self.duration / len(self.seconds)

    # interpolates timestamps using the first and the last timestamp - this may not always work, but
    # it does work for the data we have
    def interpolateTimes(self):
        startingTime = self.timestamps[0]
        endingTime = self.timestamps[-1]
        deltaTime = endingTime - startingTime
        deltaSeconds = deltaTime.total_seconds()
        self.duration = deltaSeconds
        self.timeDelta = self.duration / len(self.timestamps)
        self.seconds = np.linspace(0, self.duration, len(self.timestamps))

    def processLines(self, timestampPattern="\d\d:\d\d:\d\d\.\d\d\d", headerPattern = ' -> S',
            measurementPattern = '-*\d+\.\d+', delimiter=' '):
        dataPattern = headerPattern + measurementPattern + delimiter + measurementPattern + delimiter + \
                measurementPattern + delimiter + measurementPattern + "$"

        for line in self.lines:
            line = line.replace(",", "")
            timestampMatch = re.search(timestampPattern, line)
            if timestampMatch:
                timestampString = timestampMatch.group()
                timestamp = parseDate(timestampString)
                timestamp = timestamp.replace(year=1940, month=1, day=1)

                data = re.search(dataPattern, line)
                if data:
                    dataString = data.group()
                    dataNoHeader = dataString.replace(headerPattern, "")
                    splitData = [float(measurement) for measurement in dataNoHeader.split(delimiter)]

                    self.timestamps.append(timestamp)
                    self.flows = np.append(self.flows, splitData[1])
                    # add tidal volumes and minute volumes w/ correction factor to account for
                    # using the wrong delta t
                    self.tidalVolumes = np.append(self.tidalVolumes, splitData[2]*self.correctionFactor)
                    self.minuteVolumes = np.append(self.minuteVolumes, splitData[3]*self.correctionFactor)
