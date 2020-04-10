#include <SPI.h>
#include <elapsedMillis.h> // NOTE - NOT AN OFFICIAL LIBRARY. WE SHOULD IDEALLY USE INTERRUPTS.

elapsedMillis timeElapsed;
const int numReadings = 2;

const float nitrogenDensity = 1.225; // in units of g/L
const float channelArea = 58.0; // area of the three channels in the D-lite
const float dischargeCoefficient = 0.7; // estimate from the literature
const float conversionFactor = 0.594; // converts mm^2 * sqrt(cmH2O * g/L) into L/min
const float mbarTocmWater = 1.1097;

const uint16_t samplingTimeMillis = 5;
const uint16_t averagingTimeMillis = 200;
const uint16_t averagingSamples = int(averagingTimeMillis / samplingTimeMillis);

float totalPressure = 0;
float pressureAverage = 0;
float readings[averagingSamples];
float flowAverage = 0;
float tidalVolumeInhalation = 0;
float tidalVolumeExhalation = 0;
bool currentlyInhaling = false;

uint16_t readIndex = 0;
uint16_t bufferIndex = 0;

const uint8_t INHALATION = 0;
const uint8_t EXHALATION = 1;
const uint8_t TRANSITION_TO_EXHALATION = 2;
const uint8_t TRANSITION_TO_INHALATION = 3;

float upwardThreshold = 15; // threshold in L/min
float upwardStayAbove = 10; // threshold we must stay above
float downwardThreshold = 5; // threshold we must cross going down to exit the breath
float downwardStayBelow = 5; // threshold we must stay below to be considered an exhalation
float minimumInhalationMillis = 200; // check that our breath time is at least 200ms
float minimumExhalationMillis = 200; // check that our breath time is at least 200ms
uint16_t minimumInhalationCounter = uint16_t(minimumInhalationMillis / samplingTimeMillis);
uint16_t minimumExhalationCounter = uint16_t(minimumExhalationMillis / samplingTimeMillis);

uint8_t state = EXHALATION;
uint8_t nextState = EXHALATION;
uint8_t thresholdCounter = 0; 

float pressureInt = 0;
float pressure = 0;
float tempInt = 0;
float temp = 0;
float addedTidalVolume = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  digitalWrite(SS, HIGH);  // ensure SS stays high
  SPI.begin ();
  delay(100);
}

void loop() {
  if(timeElapsed > samplingTimeMillis) {
    updatePressureAndFlow();
    updateTidalVolume();
    updateState();
    resetCounters();
  }
  
}

void updatePressureAndFlow() {
  totalPressure = totalPressure - readings[readIndex];
  // put your main code here, to run repeatedly:
  pressureInt = readPressureBytes();
  pressure = ((pressureInt-1638)*(120))/(14745-1638)-60;
  tempInt = readTempBytes();
  temp = ((tempInt/2047)*200)-50;
  
  readings[readIndex] = pressure;
  

  // compute the running average (lowpass filter the data)
  totalPressure = totalPressure + readings[readIndex];
  pressureAverage = totalPressure / averagingSamples * mbarTocmWater;
  flowAverage = flowFromPressure(pressureAverage);
}

void updateTidalVolume() {
  addedTidalVolume = flowAverage * samplingTimeMillis / 1000.0;
  // ACTIONS TO TAKE BASED ONLY ON CURRENT STATE
  if(state == INHALATION) {
    tidalVolumeInhalation += addedTidalVolume;
  }
  else if(state == TRANSITION_TO_EXHALATION) {
    tidalVolumeInhalation += addedTidalVolume;
  }
  else if(state == EXHALATION) {
    tidalVolumeExhalation += addedTidalVolume;
  }
  else if(state == TRANSITION_TO_INHALATION) {
    tidalVolumeExhalation += addedTidalVolume;
  }
}

void updateState() {
  // STATE TRANSITION LOGIC AND VARIABLE RESETTING
  nextState = state; // by default, stay in the same state.
  if(state == INHALATION) {
    if(flowAverage < downwardThreshold) {
      nextState = TRANSITION_TO_EXHALATION;
      tidalVolumeExhalation = 0;
      thresholdCounter = 0;
    }
  }
  else if(state == TRANSITION_TO_EXHALATION) {
    if(flowAverage < downwardStayBelow) {
      thresholdCounter += 1;
      
      if(thresholdCounter >= minimumExhalationCounter) {
        nextState = EXHALATION;
      }
    }
    else if(flowAverage >= downwardStayBelow) { // we didn't stay below the threshold. 
      nextState = INHALATION;
    }
  }
  else if(state == EXHALATION) {
    if(flowAverage > upwardThreshold) {
      nextState = TRANSITION_TO_INHALATION;
      tidalVolumeInhalation = 0; // reset tidal volume. Can save old tidal volume now.
      thresholdCounter = 0;
    }
  }
  else if(state == TRANSITION_TO_INHALATION) {
    if(flowAverage > upwardStayAbove) {
      thresholdCounter += 1;
      if(thresholdCounter >= minimumInhalationCounter) {
        nextState = INHALATION;
      }
    }
    else if(flowAverage <= upwardStayAbove) { // we didn't stay above the threshold.
      nextState = EXHALATION;
    }
  }
}

void resetCounters() {
   readIndex += 1;
    timeElapsed = 0;
    
    // RESET COUNTERS AND ELAPSED TIME
    if (readIndex >= averagingSamples ) {
      readIndex = 0;
    }
}

double flowFromPressure(double pressure) {
  double flow = 0;
  if(pressure < 0) {
    flow = -conversionFactor * dischargeCoefficient * channelArea * sqrt(-2 * pressure / nitrogenDensity);
  }
  else {
    flow = conversionFactor * dischargeCoefficient * channelArea * sqrt(2 * pressure / nitrogenDensity);
  }
   
  return flow;
}

unsigned int readPressureBytes() {
  int bytesToRead = 2;
  byte inByte = 0;           // incoming byte from the SPI
  unsigned int result = 0;   // result to return
  // take the chip select low to select the device:
  digitalWrite(SS, LOW);
  // send a value of 0 to read the first byte returned:
  result = SPI.transfer(0x00);
  // decrement the number of bytes left to read:
  bytesToRead--;
  // if you still have another byte to read:
  if (bytesToRead > 0) {
    // shift the first byte left, then get the second byte:
    result = result << 8;
    inByte = SPI.transfer(0x00);
    // combine the byte you just got with the previous one:
    result = result | inByte;
    // decrement the number of bytes left to read:
    bytesToRead--;
  }
  // take the chip select high to de-select:
  digitalWrite(SS, HIGH);
  // return the result:
  return (result);
}

unsigned int readTempBytes() {
  int bytesToRead = 2;
  byte inByte = 0;           // incoming byte from the SPI
  unsigned int result = 0;   // result to return
  // take the chip select low to select the device:
  digitalWrite(SS, LOW);
  // discard the first 2 bytes, keep the third
  result = SPI.transfer(0x00);
  result = SPI.transfer(0x00);
  result = SPI.transfer(0x00);
  // decrement the number of bytes left to read:
  bytesToRead--;
  // if you still have another byte to read:
  if (bytesToRead > 0) {
    // bit shifting to extract the right temp bits:
    result = result << 3;
    inByte = SPI.transfer(0x00);
    inByte = inByte >> 5;
    // combine the byte you just got with the previous one:
    result = result | inByte;
    // decrement the number of bytes left to read:
    bytesToRead--;
  }
  // take the chip select high to de-select:
  digitalWrite(SS, HIGH);
  // return the result:
  return (result);
}
