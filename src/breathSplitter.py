import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import json
from copy import deepcopy

# Class that takes the dictionary we generate as an input and does stuff to it
class Breaths:
    def __init__(self, inputFileName):
        ##This code loads the array from jason file and casts lists as numpy arrays.
        # We probably want to move this somewhere else 
        with open(fname) as json_file:
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
        firstPeriod = self.inputDict['flow'].sel(time=slice(0, self.inputDict['period']))
        differentiatedFirstPeriod = firstPeriod.differentiate('time')
        inspirationOnsetPosition = 0
        if(self.inputDict['inspiratoryExpiratory'] == 'inspiratory'):
            inspirationOnsetPosition = int(differentiatedFirstPeriod.argmax())-2
            print("inspiratory detected")
        else:
            expirationOnsetPosition = int(differentiatedFirstPeriod.argmin())-2
            inspirationOnsetPosition = expirationOnsetPosition + int(self.samplesInPeriod * 3.0 / 4.0)
            print("expiratory detected")

        self.flowData = self.flowData[inspirationOnsetPosition:]
        self.zeroShiftData()

    def splitBreaths(self):
        time = np.linspace(0, self.period, self.samplesInPeriod)
        flowValues = np.array([])
        self.numberBreaths = int(float(self.flowData[-1]['time']) / self.period)

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

    def __getitem__(self, key):
        return self.flowData[key]

    #def splitBreaths(inputDictionary, period, inspirationExpiration):
    #    if inspirationExpiration is 'inspiration':


