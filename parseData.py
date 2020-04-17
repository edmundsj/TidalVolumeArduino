import sys
sys.path.append('src')

from arduinoSerialMonitorParser import ArduinoParser
parser = ArduinoParser()
experimentNumber = sys.argv[1]
filename = "Experiment5." + str(experimentNumber) + '.csv'
parser.readFile('raw_data/' + filename)
parser.processLines()
parser.interpolateTimes()
parser.writeFile('processed_data/' + filename)
