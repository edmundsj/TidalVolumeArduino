import sys
sys.path.append('src')
from arduinoSerialMonitorParser import ArduinoParser

for i in range(11):
    parser = ArduinoParser()
    filename = "Experiment5." + str(i+1) + '.csv'
    parser.readFile('raw_data/' + filename)
    parser.processLines()
    parser.interpolateTimes()
    parser.writeFile('processed_data/' + filename)
