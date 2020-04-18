import sys
sys.path.append('src')
from arduinoSerialMonitorParser import ArduinoParser

metadata = []
metadata.insert(1, {
    'experiment': 5.1,
    'compliance' : 0.03,
    'port' : 'Inspiratory',
    'leftPressure' : [6,20],
    'rightPressure': [3,17],
    'leftTidalVolume' :[[0.05, 0.5], [0.04, 0.48]],
    'rightTidalVolume' : [[0.1,0.5],[0.12,0.5]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 50,
    'I:E': 1/3
    })
metadata.insert(2, {
    'experiment': 5.2,
    'compliance' : 0.03,
    'port' : 'Expiratory',
    'leftPressure' : [5,20],
    'rightPressure': [2.5,17],
    'leftTidalVolume' :[[0.01, 0.45], [0.0, 0.48]],
    'rightTidalVolume' : [[0.1,0.5],[0.12,0.5]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 50,
    'I:E':1/3})
metadata.insert(3, {
    'experiment': 5.3,
    'compliance' : 0.03,
    'port' : 'Patient',
    'leftPressure' : [5,20],
    'rightPressure': [2,17],
    'leftTidalVolume' :[[0.05, 0.48], [0.05, 0.5]],
    'rightTidalVolume' : [[0.12,0.5],[0.1,0.52]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 50,
    'I:E':1/3})
metadata.insert(4, {
    'experiment': 5.4,
    'compliance' : 0.01,
    'port' : 'Patient',
    'leftPressure' : [5,35],
    'rightPressure': [3,32],
    'leftTidalVolume' :[[0.05, 0.4], [0.03, 0.4]],
    'rightTidalVolume' : [[0.05,0.45],[0.05,0.45]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 50,
    'I:E':1/3})
metadata.insert(5, {
    'experiment': 5.5,
    'compliance' : 0.15,
    'port' : 'Patient',
    'leftPressure' : [8,10],
    'rightPressure': [5,7],
    'leftTidalVolume' :[[0.6, 1], [0.6, 1]],
    'rightTidalVolume' : [[0.6,1],[0.6,1]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 50,
    'I:E':1/3})
metadata.insert(6, {
    'experiment': 5.6,
    'compliance' : 0.15,
    'port' : 'Patient',
    'leftPressure' : [7,8],
    'rightPressure': [4,5],
    'leftTidalVolume' :[[0.5, 0.78], [0.5, 0.78]],
    'rightTidalVolume' : [[0.5,0.75],[0.5,0.75]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 30,
    'I:E':1/3})
metadata.insert(7, {
    'experiment': 5.7,
    'compliance' : 0.03,
    'port' : 'Patient',
    'leftPressure' : [6,14],
    'rightPressure': [2.5,12],
    'leftTidalVolume' :[[0.05, 0.3], [0.05, .3]],
    'rightTidalVolume' : [[0.1,0.35],[0.1,0.35]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 30,
    'I:E':1/3})
metadata.insert(8, {
    'experiment': 5.8,
    'compliance' : 0.01,
    'port' : 'Patient',
    'leftPressure' : [6,27],
    'rightPressure': [3,24],
    'leftTidalVolume' :[[0.05, 0.2], [0.03, .19]],
    'rightTidalVolume' : [[0.05,0.2],[0.05,0.2]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 30,
    'I:E':1/3})
    
metadata.insert(9, {
    'experiment': 5.9,
    'compliance' : 0.01,
    'port' : 'Patient',
    'leftPressure' : [6,12],
    'rightPressure': [3,9],
    'leftTidalVolume' :[[0.03, 0.08], [0.02, .08]],
    'rightTidalVolume' : [[0.03,0.1],[0.03,0.1]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 10,
    'I:E':1/3})
    
metadata.insert(10, {
    'experiment': 5.10,
    'compliance' : 0.03,
    'port' : 'Patient',
    'leftPressure' : [5,7],
    'rightPressure': [2.5,5],
    'leftTidalVolume' :[[0.05, 0.15], [0.05, .15]],
    'rightTidalVolume' : [[0.1,0.17],[0.11,0.18]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 10,
    'I:E':1/3})
metadata.insert(11, {
    'experiment': 5.11,
    'compliance' : 0.15,
    'port' : 'Patient',
    'leftPressure' : [6,6.5],
    'rightPressure': [3,3.5],
    'leftTidalVolume' :[[0.4, 0.49], [0.4, .48]],
    'rightTidalVolume' : [[0.39,0.47],[0.4,0.48]],
    'period' : 4.0045,
    'timestep' : 0.0060009,
    'targetFlowRate': 10,
    'I:E':1/3})
for i in range(11):
    parser = ArduinoParser()
    filename = "Experiment5." + str(i+1) 
    parser.readFile('raw_data/' + filename + '.csv')
    parser.processLines()
    parser.interpolateTimes()
    parser.inputMetadata(metadata[i])
    parser.writeJSONFile('processed_data_json/' + filename + '.json')
