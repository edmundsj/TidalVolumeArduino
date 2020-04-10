import numpy as np
sqrt = np.sqrt
class ArduinoCode:
    timeElapsed = 0;
    numReadings = 2;

    nitrogenDensity = 1.225; # in units of g/L
    channelArea = 58.0; # area of the three channels in the D-lite
    dischargeCoefficient = 0.7; # estimate from the literature
    conversionFactor = 0.594; # converts mm^2 * sqrt(cmH2O * g/L) into L/min
    mbarTocmWater = 1.1097;

    samplingTimeMillis = 5;
    averagingTimeMillis = 200;
    averagingSamples = int(averagingTimeMillis / samplingTimeMillis);

    totalPressure = 0.0;
    pressureAverage = 0.0;
    readings = [0 for i in range(averagingSamples)]
    flowAverage = 0.0;
    tidalVolumeInhalation = 0.0;
    tidalVolumeExhalation = 0.0;
    currentlyInhaling = False;

    readIndex = 0;
    bufferIndex = 0;

    INHALATION = 0;
    EXHALATION = 1;
    TRANSITION_TO_EXHALATION = 2;
    TRANSITION_TO_INHALATION = 3;

    upwardThreshold = 15.0; # threshold in L/min
    upwardStayAbove = 10.0; # threshold we must stay above
    downwardThreshold = 5.0; # threshold we must cross going down to exit the breath
    downwardStayBelow = 5.0; # threshold we must stay below to be considered an exhalation
    minimumInhalationMillis = 200.0; # check that our breath time is at least 200ms
    minimumExhalationMillis = 200.0; # check that our breath time is at least 200ms
    minimumInhalationCounter = int(minimumInhalationMillis / samplingTimeMillis);
    minimumExhalationCounter = int(minimumExhalationMillis / samplingTimeMillis);

    state = EXHALATION;
    nextState = EXHALATION;
    thresholdCounter = 0;

    pressureInt = 0.0;
    pressure = 0.0;
    tempInt = 0.0;
    temp = 0.0;
    addedTidalVolume = 0.0;

    def updateState(self):
        self.nextState = self.state; # by default, stay in the same state.
        if(self.state == self.INHALATION):
            if(self.flowAverage < self.downwardThreshold):
                self.nextState = self.TRANSITION_TO_EXHALATION;
                self.tidalVolumeExhalation = 0;
                self.thresholdCounter = 0;
        elif(self.state == self.TRANSITION_TO_EXHALATION):
            if(self.flowAverage < self.downwardStayBelow):
                self.thresholdCounter += 1;
                if(self.thresholdCounter >= self.minimumExhalationCounter):
                    self.nextState = self.EXHALATION;
            elif(self.flowAverage >= self.downwardStayBelow): # we didn't stay below the threshold.
                self.nextState = self.INHALATION;

        elif(self.state == self.EXHALATION):
            if(self.flowAverage > self.upwardThreshold):
                self.nextState = self.TRANSITION_TO_INHALATION;
                self.tidalVolumeInhalation = 0; # reset tidal volume. Can save old tidal volume now.
                self.thresholdCounter = 0;

        elif(self.state == self.TRANSITION_TO_INHALATION):
            if(self.flowAverage > self.upwardStayAbove):
                self.thresholdCounter += 1;
                if(self.thresholdCounter >= self.minimumInhalationCounter):
                  self.nextState = self.INHALATION;
            elif(self.flowAverage <= self.upwardStayAbove): # we didn't stay above the threshold.
                self.nextState = self.EXHALATION;

    def updateTidalVolume(self):
        # ACTIONS TO TAKE BASED ONLY ON CURRENT STATE
        self.addedTidalVolume = self.flowAverage * self.samplingTimeMillis / 1000.0;
        if(self.state == self.INHALATION):
            self.tidalVolumeInhalation += self.addedTidalVolume;
        elif(self.state == self.TRANSITION_TO_EXHALATION):
            self.tidalVolumeInhalation += self.addedTidalVolume;
        elif(self.state == self.EXHALATION):
            self.tidalVolumeExhalation += self.addedTidalVolume;
        elif(self.state == self.TRANSITION_TO_INHALATION):
            self.tidalVolumeExhalation += self.addedTidalVolume;

    def resetCounters(self):
        self.readIndex += 1;
        if(self.readIndex >= self.averagingSamples):
            self.readIndex = 0;
        self.timeElapsed = 0;

    def updatePressureAndFlow(self):
        self.totalPressure = self.totalPressure - self.readings[self.readIndex];
        # put your main code here, to run repeatedly:
        pressureInt = self.readPressureBytes();
        pressure = (((pressureInt-1638)*120)/(14745-1638)-60 ) * self.mbarTocmWater;
        tempInt = self.readTempBytes();
        temp = ((tempInt/2047)*200)-50;

        self.readings[self.readIndex] = pressure;
        self.totalPressure = self.totalPressure + self.readings[self.readIndex];
        self.pressureAverage = self.totalPressure / self.averagingSamples;
        self.flowAverage = self.flowFromPressure(self.pressureAverage);

    # This is strictly intended to be mocked, although we could grab real serial data
    def readPressureBytes(self):
        return 0;

    def readTempBytes(self):
        return 0;

    def flowFromPressure(self, pressure):
        flow = 0.0;
        if (pressure < 0):
            flow = -self.conversionFactor * self.dischargeCoefficient * self.channelArea * sqrt(-2 * self.pressure / self.nitrogenDensity);
        else:
            flow = self.conversionFactor * self.dischargeCoefficient * self.channelArea * sqrt(2 * self.pressure / self.nitrogenDensity);
        return flow;

    def runCoreLoop(self):
        self.updatePressureAndFlow()
        self.updateTidalVolume()
        self.updateState()
        self.resetCounters()

    def stateToString(self):
        if(self.state == self.INHALATION):
            return 'INHALATION'
        elif(self.state == self.EXHALATION):
            return 'EXHALATION'
        elif(self.state == self.TRANSITION_TO_INHALATION):
            return 'TRANSITION_TO_INHALATION'
        elif(self.state == self.TRANSITION_TO_EXHALATION):
            return 'TRANSITION_TO_EXHALATION'
