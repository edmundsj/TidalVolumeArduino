import sys
sys.path.append('src')
from arduinoSerialMonitorParser import ArduinoParser
parser = ArduinoParser()
experimentNumber = 1
filename = "Experiment5." + str(experimentNumber) + '.csv'
parser.readFile('raw_data/' + filename)
parser.processLines()
parser.interpolateTimes()
metadata = []
metadata.insert(experimentNumber -1, {
    'experiment': 5.1,
    'compliance' : 0.03,
    'port' : 'Inspiratory',
    'leftPressure' : [6,20],
    'rightPressure': [3,17],
    'leftTidalVolume' :[[0.05, 0.5], [0.04, 0.48]],
    'rightTidalVolume' : [[0.1,0.5],[0.12,0.05]],
    'period' : 4.005,
    'timestep' : 0.0060009,
    'targetFlowRate': 50})

parser.inputMetadata(metadata[0])
jsonfname = "processed_data_json/Experiment5." + str(experimentNumber) + '.json'
parser.writeJSONFile(jsonfname)

    # parser.writeFile('processed_data/' + filename)


