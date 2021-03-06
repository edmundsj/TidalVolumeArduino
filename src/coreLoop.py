import numpy as np
sqrt = np.sqrt
class ArduinoCode:
    timeElapsed = 0;
    numReadings = 2;

    nitrogenDensity = 1.225; # in units of g/L
    channelArea = 58.0; # area of the three channels in the D-lite
    dischargeCoefficient = 0.7; # estimate from the literature
    conversionFactor = 0.5941712; # converts mm^2 * sqrt(cmH2O * g/L) into L/min
    mbarTocmWater = 1.019716;

    samplingTimeMillis = 5;
    averagingTimeMillis = 200;
    averagingSamples = int(averagingTimeMillis / samplingTimeMillis);

    flow= 0.0;
    tidalVolumeInhalation = 0.0;
    tidalVolumeExhalation = 0.0;
    currentlyInhaling = False;

    readIndex = 0;
    bufferIndex = 0;

    INHALATION = 0;
    EXHALATION = 1;
    TRANSITION_TO_EXHALATION = 2;
    TRANSITION_TO_INHALATION = 3;

    upwardThreshold = 10.0; # threshold in L/min
    upwardStayAbove = 8.0; # threshold we must stay above
    downwardThreshold = 0.0; # threshold we must cross going down to exit the breath
    downwardStayBelow = 0.0; # threshold we must stay below to be considered an exhalation
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

    def runCoreLoop(self):
        self.updatePressureAndFlow()
        self.updateState()
        self.updateTidalVolume()
        self.resetCounters()

    def updateState(self):
        self.nextState = self.state; # by default, stay in the same state.
        if(self.state == self.INHALATION):
            if(self.flow< self.downwardThreshold):
                self.nextState = self.TRANSITION_TO_EXHALATION;
                self.tidalVolumeExhalation = 0;
                self.thresholdCounter = 0;
        elif(self.state == self.TRANSITION_TO_EXHALATION):
            if(self.flow< self.downwardStayBelow):
                self.thresholdCounter += 1;
                if(self.thresholdCounter >= self.minimumExhalationCounter):
                    self.nextState = self.EXHALATION;
            elif(self.flow>= self.downwardStayBelow): # we didn't stay below the threshold.
                self.nextState = self.INHALATION;

        elif(self.state == self.EXHALATION):
            if(self.flow > self.upwardThreshold):
                self.nextState = self.TRANSITION_TO_INHALATION;
                self.tidalVolumeInhalation = 0; # reset tidal volume. Can save old tidal volume now.
                self.thresholdCounter = 0;

        elif(self.state == self.TRANSITION_TO_INHALATION):
            if(self.flow> self.upwardStayAbove):
                self.thresholdCounter += 1;
                if(self.thresholdCounter >= self.minimumInhalationCounter):
                  self.nextState = self.INHALATION;
            elif(self.flow<= self.upwardStayAbove): # we didn't stay above the threshold.
                self.nextState = self.EXHALATION;

        self.state = self.nextState

    def updateTidalVolume(self):
        # ACTIONS TO TAKE BASED ONLY ON CURRENT STATE
        self.addedTidalVolume = self.flow / 60.0 * self.samplingTimeMillis / 1000.0;
        if(self.state == self.INHALATION):
            self.tidalVolumeInhalation += self.addedTidalVolume;
        elif(self.state == self.TRANSITION_TO_INHALATION):
            self.tidalVolumeInhalation += self.addedTidalVolume;
        elif(self.state == self.EXHALATION):
            self.tidalVolumeExhalation += self.addedTidalVolume;
        elif(self.state == self.TRANSITION_TO_EXHALATION):
            self.tidalVolumeExhalation += self.addedTidalVolume;

    def resetCounters(self):
        self.readIndex += 1;
        if(self.readIndex >= self.averagingSamples):
            self.readIndex = 0;
        self.timeElapsed = 0;

    def updatePressureAndFlow(self):
        self.serial = self.readPressureBytes();
        self.pressure = self.pressureFromSerial(self.serial)
        self.tempInt = self.readTempBytes();
        self.temp = ((self.tempInt/2047)*200)-50;

        self.flow = self.flowFromPressure(self.pressure);

    # This is strictly intended to be mocked, although we could grab real serial data
    def readPressureBytes(self):
        return 0;

    def readTempBytes(self):
        return 0;

    def pressureFromSerial(self, serialData):
        return (((serialData - 1638)*120)/(14745-1638) - 60) * self.mbarTocmWater

    def flowFromPressure(self, pressure):
        if (pressure < 0):
            return -self.conversionFactor * self.dischargeCoefficient * self.channelArea * sqrt(-2 * pressure / self.nitrogenDensity);
        elif (pressure > 0):
            return self.conversionFactor * self.dischargeCoefficient * self.channelArea * sqrt(2 * pressure / self.nitrogenDensity);
        else:
            return 0


    def stateToString(self):
        if(self.state == self.INHALATION):
            return 'INHALATION'
        elif(self.state == self.EXHALATION):
            return 'EXHALATION'
        elif(self.state == self.TRANSITION_TO_INHALATION):
            return 'TRANSITION_TO_INHALATION'
        elif(self.state == self.TRANSITION_TO_EXHALATION):
            return 'TRANSITION_TO_EXHALATION'

    # computes the pressure from given honeywell serial
    def pressureToHoneywellSerial(self, pressureCmWater):
        return int(107.113*(76.4752 + pressureCmWater))

    # computes honeywell serial for a given flow
    def flowToHoneywellSerial(self, flowLmin):
        if(flowLmin > 0):
            return int(107.113 *(76.4752 + 0.00105252 * flowLmin * flowLmin))
        elif(flowLmin < 0):
            return int(107.113 *(76.4752 - 0.00105252 * flowLmin * flowLmin))

    def honeywellSerialToFlow(self, serial):
        pressure = self.pressureFromSerial(serial)
        return self.flowFromPressure(pressure)

