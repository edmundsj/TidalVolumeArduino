import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import json
from copy import deepcopy

# Class that takes the dictionary we generate as an input and does stuff to it
class Breaths:
    def __init__(self, inputFileName):
        ##This code loads the array from json file and casts lists as numpy arrays.
        # We probably want to move this somewhere else 
        inputDict = {}
        with open(inputFileName) as json_file:
            inputDict = json.load(json_file)
            for key,value in inputDict.items():
                if isinstance(value, list):
                    inputDict[key] = np.array(value)
        time = inputDict['time']
        flow = inputDict['flow']
        flowData = xr.DataArray(flow, coords=[time], dims=['time'])

        flowData.attrs['long_name'] = 'Flow' # Sets the y-axis name
        flowData.attrs['units'] = 'L/min' # sets the x-axis units

        self.inputDict = deepcopy(inputDict)
        self.inputDict['flow'] = flowData

        # double-linked variables for ease of access - they are stored in the dict
        self.flowData = flowData
        self.period = self.inputDict['period']
        self.timestep = self.inputDict['timestep']
        self.samplesInPeriod = int(self.period / self.timestep)

        self.removeCorruptedData()
        self.alignAndClipData()
        self.flowDerivative= self.flowData.differentiate('time')
        self.splitBreaths()
        self.computeTidalVolumesAndStatistics()

    # For some reason, it looks like the first few seconds of our data is corrupted, and the period is
    # not the same as all the others
    def removeCorruptedData(self):
        self.flowData = self.flowData.sel(time=slice(4,None))
        self.zeroShiftData()

    def zeroShiftData(self, dataToShift=None):
        if(dataToShift is None):
            newCoordinates = np.array(self.flowData.coords['time'] - self.flowData.coords['time'][0])
            self.flowData = self.flowData.assign_coords(time=newCoordinates)
        else:
            newCoordinates = np.array(dataToShift.coords['time'] - dataToShift.coords['time'][0])
            return dataToShift.assign_coords(time=newCoordinates)

    def forcePeriodCoordinates(self, data):
        newCoordinates = np.linspace(0, self.period, self.samplesInPeriod)
        return data.assign_coords(time=newCoordinates)

    # align the data to the onset of inspiration or expiration
    def alignAndClipData(self):
        firstPeriodSlice = slice(0, self.period)
        firstPeriod = self.inputDict['flow'].sel(time=firstPeriodSlice)
        differentiatedFirstPeriod = firstPeriod.differentiate('time')
        inspirationOnsetPosition = 0
        if self.inputDict['port'] == 'Inspiratory' or self.inputDict['port'] == 'Patient':
            inspirationOnsetPosition = int(differentiatedFirstPeriod.argmax())-2
        elif(self.inputDict['port'] == 'Expiratory'):
            expirationOnsetPosition = int(differentiatedFirstPeriod.argmin())-2
            inspirationOnsetPosition = expirationOnsetPosition + int(self.samplesInPeriod * 3.0 / 4.0)

        if inspirationOnsetPosition < 0:
            inspirationOnsetPosition = 0
        self.flowData = self.flowData[inspirationOnsetPosition:]
        self.zeroShiftData()

    def splitBreaths(self):
        time = np.linspace(0, self.period, self.samplesInPeriod)
        flowValues = np.array([])
        endTime = float(self.flowData[-1]['time'])
        self.numberBreaths = int(endTime / self.period)

        for i in range(self.numberBreaths): # fugded - figure out the max index
            breathSlice = slice(i*self.period, (i+1 + 0.02)*self.period)
            breathData = self.flowData.sel(time=breathSlice)
            startInspiration = 0
            endBreath = startInspiration + self.samplesInPeriod

            breathData = np.array(breathData[startInspiration:endBreath].values)
            if i == 0:
                flowValues = breathData
            else:
                flowValues = np.vstack((flowValues, breathData))

        # grab all the data except the last one and package it into an N breaths x 4s array
        self.flowData = xr.DataArray(flowValues,
                coords={'breath': np.arange(0, self.numberBreaths, 1), 'time': time},
                dims=['breath', 'time'])

    def computeTidalVolumesAndStatistics(self):
        rectifiedPositiveData = np.clip(self.flowData, 0, np.inf)
        rectifiedNegativeData = np.clip(self.flowData, -np.inf, 0)
        conversionFactor = 1000.0 / 60.0 # converts from L into mL
        self.tidalVolumeInhalation = conversionFactor * rectifiedPositiveData.integrate('time')
        self.tidalVolumeExhalation = conversionFactor * rectifiedNegativeData.integrate('time')

        tidalVolumeInhalationMean = float(self.tidalVolumeInhalation.mean())
        tidalVolumeExhalationMean = float(self.tidalVolumeExhalation.mean())
        tidalVolumeInhalationStd = float(self.tidalVolumeInhalation.std())
        tidalVolumeExhalationStd = float(self.tidalVolumeExhalation.std())
        tidalVolumeInhalationMin = float(self.tidalVolumeInhalation.min())
        tidalVolumeExhalationMin = float(self.tidalVolumeExhalation.min())
        tidalVolumeInhalationMax = float(self.tidalVolumeInhalation.max())
        tidalVolumeExhalationMax = float(self.tidalVolumeExhalation.max())

        self.tidalVolumeStatistics = {
                'inhalation':
                {
                    'mean': tidalVolumeInhalationMean,
                    'std': [tidalVolumeInhalationStd, tidalVolumeInhalationStd/tidalVolumeInhalationMean],
                    'min': [tidalVolumeInhalationMin,
                        (tidalVolumeInhalationMin - tidalVolumeInhalationMean)/tidalVolumeInhalationMean],
                    'max': [tidalVolumeInhalationMax,
                        (tidalVolumeInhalationMax - tidalVolumeInhalationMean)/tidalVolumeInhalationMean]
                    },
                'exhalation':
                {
                    'mean': tidalVolumeExhalationMean,
                    'std': [tidalVolumeExhalationStd, tidalVolumeExhalationStd/tidalVolumeExhalationMean],
                    'min': [tidalVolumeExhalationMin,
                        (tidalVolumeExhalationMin-tidalVolumeExhalationMean)/tidalVolumeExhalationMean],
                    'max': [tidalVolumeExhalationMax,
                        (tidalVolumeExhalationMax - tidalVolumeExhalationMean)/tidalVolumeExhalationMean]
                }
                }

    def plot(self):
        self.flowData.plot()

    def plotEyeDiagram(self):
        # TODO: Figure out how to change figure size after it is plotted (we want to be able
        # to plot multiple things to the same figures)
        for i in range(self.numberBreaths):
            self.flowData[i].plot(linewidth=0.5, alpha=0.1, color='b')

        plt.title(f'Flow vs. Time at target flowrate of {self.inputDict["targetFlowRate"]}' + \
                f'L/min, n={self.numberBreaths}')
        plt.xlabel('time (s)')
        plt.ylabel('flow (L/min)')

    def plotAverageDiagram(self):
        averageData = 0.0
        for i in range(self.numberBreaths):
            averageData += self.flowData[i]
        averageData /= self.numberBreaths
        averageData.plot()

        plt.title(f'Average Flow vs. Time at target flowrate of {self.inputDict["targetFlowRate"]}' + \
                f'L/min')
        plt.xlabel('time (s)')
        plt.ylabel('flow (L/min)')

    def plotTidalVolumeHistogram(self):
        if self.inputDict['port'] == 'Inspiratory' or self.inputDict['port'] == 'Patient':
            self.tidalVolumeInhalation.plot.hist()
        elif self.inputDict['port'] == 'Expiratory':
            self.tidalVolumeExhalation.plot.hist()

        plt.title(f'Distribution of tidal volumes at compliance {self.inputDict["compliance"]*1000} mL/(cm water) and flow {self.inputDict["targetFlowRate"]} L/min')
        plt.xlabel('tidal volume (mL)')
        plt.ylabel('count (#)')

    def printStatistics(self):
        print(f'Mean: {self.tidalVolumeStatistics["inhalation"]["mean"]} mL, ' + \
                f'Min: {self.tidalVolumeStatistics["inhalation"]["min"]} mL')

    def __getitem__(self, key):
        return self.flowData[key]

    #def splitBreaths(inputDictionary, period, inspirationExpiration):
    #    if inspirationExpiration is 'inspiration':


