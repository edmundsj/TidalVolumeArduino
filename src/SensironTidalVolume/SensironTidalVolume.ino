// NOTE: RIGHT NOW THIS DOES NOT DEAL WELL WITH TRANSIENTS AT THE END OF A BREATH.
// NEED TO FIGURE OUT HOW TO DEAL WITH THAT. RIGHT NOW THIS IS BASICALLY USELESS VIA THE SERIAL
// MONITOR. NEED TO KEEP RUNNING LIST OF TIDAL VOLUMES, NOT JUST DISCARD THE DATA. THE TRANSIENT
// FLOW RATES CAN BE TRULY MASSIVE (>40L/min)

// Also, for some reason my control logic is completely fucked and I cannot figure out why.
// This needs to be completely rethought out.

#include <SPI.h>
#include <elapsedMillis.h> // NOTE - NOT AN OFFICIAL LIBRARY. WE SHOULD IDEALLY USE INTERRUPTS.
#include <Wire.h>

elapsedMillis timeElapsed;
elapsedMillis displayTimeElapsed;

const int numReadings = 2;

const uint16_t SENSOR_ADDRESS = 33;

const float nitrogenDensity = 1.225; // in units of g/L
const float channelArea = 58.0; // area of the three channels in the D-lite
const float dischargeCoefficient = 0.7; // estimate from the literature
const float conversionFactor = 0.5941712; // converts mm^2 * sqrt(cmH2O * g/L) into L/min
const float mbarTocmWater = 1.019716;
const float scaleFactormmWater=588.386;
const float kFactor = 6.43*0.0001;

const uint16_t samplingTimeMillis = 10;
const uint16_t averagingTimeMillis = 200;
const uint16_t averagingSamples = int(averagingTimeMillis / samplingTimeMillis);
const uint16_t displayTimeMillis = 20;

float flow = 0;
float tidalVolumeInhalation = 0;
float tidalVolumeExhalation = 0;

const uint8_t INHALATION = 0;
const uint8_t EXHALATION = 1;
const uint8_t TRANSITION_TO_EXHALATION = 2;
const uint8_t TRANSITION_TO_INHALATION = 3;
const uint8_t NO_ACTIVITY = 4;

float upwardThreshold = 2; // threshold in L/min
float downwardThreshold = -2; // threshold we must cross going down to exit the breath
float minimumInhalationMillis = 200; // check that our breath time is at least 200ms
float minimumExhalationMillis = 200; // check that our breath time is at least 200ms
uint16_t minimumInhalationCounter = uint16_t(minimumInhalationMillis / samplingTimeMillis);
uint16_t minimumExhalationCounter = uint16_t(minimumExhalationMillis / samplingTimeMillis);

uint8_t state = NO_ACTIVITY;
uint8_t nextState = NO_ACTIVITY;
uint16_t thresholdCounter = 0; 

int16_t serial = 0;
float pressuremmWater = 0;
float tempInt = 0;
float temp = 0;
float addedTidalVolume = 0;
const uint16_t tidalVolumesToKeep = 15;
uint16_t inhaledTidalVolumesCounter = 0;
uint16_t exhaledTidalVolumesCounter = 0;
float inhaledTidalVolumesPrevious[tidalVolumesToKeep];
float exhaledTidalVolumesPrevious[tidalVolumesToKeep];
const float LtomL = 1000.0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Wire.begin ();
  Wire.beginTransmission(SENSOR_ADDRESS);
  // begin continuous averaging mode command
  Wire.write(byte(0x36));
  Wire.write(byte(0x3));
  Wire.endTransmission();
}

void loop() {
  if(timeElapsed > samplingTimeMillis) {
    
    updatePressureAndFlow();
    updateState();
    updateTidalVolume(); // this needs to come after updateState so the volume gets added to the right bin
    resetCounters();
    //Serial.println(flow);
    //Serial.println("S" + String(pressure) + " " + String(flow) + 
    //  " " + String(tidalVolumeInhalation) + " " + String(tidalVolumeExhalation));
  } 
  if(displayTimeElapsed > displayTimeMillis) {
    /*Serial.print("serial: ");
    Serial.println(serial);
    Serial.print("pressure: ");
    Serial.println(pressuremmWater);
    Serial.print("flow: ");
    Serial.println(flow);
    Serial.print("added tidal volume: ");
    Serial.println(addedTidalVolume * 1000);
    Serial.println(tidalVolumeInhalation * 1000);
    */
    /*
    Serial.print("inhaled tidal volume: ");
    for(int i=0; i<10; i++) {
      Serial.print(inhaledTidalVolumesPrevious[i]);
      Serial.print(", ");
    }
    Serial.println("");
    Serial.print("exhaled tidal volume: ");
    for(int i=0; i<10; i++) {
      Serial.print(exhaledTidalVolumesPrevious[i]);
      Serial.print(", ");
    }
    Serial.println("");
    */
    Serial.println(flow);
    displayTimeElapsed = 0;
  }
}

void updatePressureAndFlow() {
  // put your main code here, to run repeatedly:
  serial = readPressureBytes();
  pressuremmWater = pressureFromSerial(serial);
  
  flow = flowFromPressure(pressuremmWater);
}

float pressureFromSerial(int serialData) {
  float pressureFromSerial = float(serialData) / scaleFactormmWater;
  return pressureFromSerial;
}

void updateTidalVolume() {
  addedTidalVolume = flow / 60.0 * samplingTimeMillis / 1000.0 * LtomL;
  // ACTIONS TO TAKE BASED ONLY ON CURRENT STATE
  if(state == INHALATION) {
    tidalVolumeInhalation += addedTidalVolume;
  }
  else if(state == TRANSITION_TO_INHALATION) {
    tidalVolumeInhalation += addedTidalVolume;
  }
  else if(state == EXHALATION) {
    tidalVolumeExhalation += addedTidalVolume;
  }
  else if(state == TRANSITION_TO_EXHALATION) {
    tidalVolumeExhalation += addedTidalVolume;
  }
  else if(state == NO_ACTIVITY) {
    // do nothing.
  }
}

void updateState() {
  // STATE TRANSITION LOGIC AND VARIABLE RESETTING
  nextState = state; // by default, stay in the same state.
  
  if(state == INHALATION) {
    if(flow < upwardThreshold) {
      //Serial.println("INHALATION > NO_ACTIVITY");
      nextState = NO_ACTIVITY;
      inhaledTidalVolumesPrevious[inhaledTidalVolumesCounter] = tidalVolumeInhalation;
      inhaledTidalVolumesCounter += 1;
    }
  }
  else if(state == EXHALATION) {
    if(flow > downwardThreshold) {
      //Serial.println("EXHALATION > NO_ACTIVITY");
      nextState = NO_ACTIVITY;
      exhaledTidalVolumesPrevious[exhaledTidalVolumesCounter] = tidalVolumeExhalation;
      exhaledTidalVolumesCounter += 1;
    }
  }
  else if(state == TRANSITION_TO_EXHALATION) {
    if(flow < downwardThreshold) {
      thresholdCounter += 1;
      
      if(thresholdCounter >= minimumExhalationCounter) {
        //Serial.println("TRANSITION_TO_EXHALATION -> EXHALATION");
        nextState = EXHALATION;
        thresholdCounter = 0;
      }
    }
    else if(flow >= downwardThreshold) { // we didn't stay below the threshold. 
      nextState = NO_ACTIVITY;
      //Serial.println("TRANSITION_TO_EXHALATION -> NO_ACTIVITY");
    }
  }
  else if(state == TRANSITION_TO_INHALATION) {
    if(flow > upwardThreshold) {
      thresholdCounter += 1;
      
      if(thresholdCounter >= minimumInhalationCounter) {
        nextState = INHALATION;
        thresholdCounter = 0;
        //Serial.println("TRANSITION_TO_INHALATION -> INHALATION");
      }
    }
    else if(flow < upwardThreshold) {
      nextState = NO_ACTIVITY;
      //Serial.println("TRANSITION TO INHALATION -> NO_ACTIVITY");
    }
  }
  else if(state == NO_ACTIVITY) {
    if(flow >= upwardThreshold) {
      nextState = TRANSITION_TO_INHALATION;
      tidalVolumeInhalation = 0;
      //Serial.println("NO_ACTIVITY -> TRANSITION_TO_INHALATION");
    }
    else if (flow <= downwardThreshold) {
      nextState = TRANSITION_TO_EXHALATION;
      //Serial.println("NO_ACTIVITY -> TRANSITION_TO_EXHALATION");
      tidalVolumeExhalation = 0;
    }
  }
  
  state = nextState;
}

void resetCounters() {
    timeElapsed = 0;
    if(inhaledTidalVolumesCounter >= tidalVolumesToKeep) {
      inhaledTidalVolumesCounter = 0;
    }
    if(exhaledTidalVolumesCounter >= tidalVolumesToKeep) {
      exhaledTidalVolumesCounter = 0;
    }
}

double flowFromPressure(double pressuremm) {
  double flow = 0;
  if(pressuremm < 0) {
    flow = - sqrt(-pressuremm / 10.0 / kFactor);
    //flow = -conversionFactor * dischargeCoefficient * channelArea * sqrt(-2 * pressuremmWater / 10.0 / nitrogenDensity);
  }
  else {
    flow = sqrt(pressuremm / 10.0 / kFactor);
    //flow = conversionFactor * dischargeCoefficient * channelArea * sqrt(2 * pressuremmWater / 10.0 / nitrogenDensity);
  }
   
  return flow;
}

unsigned int readPressureBytes() {
    Wire.requestFrom(SENSOR_ADDRESS,2);
  
    if(2 <= Wire.available())
    {
      serial = Wire.read();
      serial = serial << 8;
      serial |= Wire.read();
    }
    return serial;
}
