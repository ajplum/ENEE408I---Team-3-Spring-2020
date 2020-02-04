 #include <Arduino_FreeRTOS.h>
#include "MotorControl.h"
#include "Ultrasound.h"

// Constants
byte PWM = 60;
const int STOP_DISTANCE_CENTER = 15; // cm
const int STOP_DISTANCE_SIDE   = 10; // cm

// Enum for Direction
enum Directions {forward, backward, left, right, halt};

// Globals for crash avoidance
boolean dangerCenter = false;
boolean dangerLeft   = false;
boolean dangerRight  = false;
boolean dangerDetected = false;
long leftDistance = 0, centerDistance = 0, rightDistance = 0;

// Globals for motor control
Directions currDir = halt;
Directions prevDir = halt;

// Ping sensor pins
const int right_ping_pin  = 4 ;
const int center_ping_pin = 3 ;
const int left_ping_pin   = 2 ;

// Motor pins
const int LeftMotorA_pin    = 11;
const int RightMotorA_pin   = 13;
const int LeftMotorB_pin    = 10;
const int RightMotorB_pin   = 12;
const int LeftMotorPWM_pin  = 6;
const int RightMotorPWM_pin = 5;

// OOP Initializations
MotorControl leftMotor  (LeftMotorA_pin,  LeftMotorB_pin,  LeftMotorPWM_pin);
MotorControl rightMotor (RightMotorA_pin, RightMotorB_pin, RightMotorPWM_pin);
Ultrasound leftUltrasound   (left_ping_pin);
Ultrasound centerUltrasound (center_ping_pin);
Ultrasound rightUltrasound  (right_ping_pin);

// Prototypes for RTOS tasks
void updateOrders  (void *pvParameters);
void updatePingData(void *pvParameters);
void driveACR      (void *pvParameters);

void setup() {
  Serial.begin(9600); // Set baud-rate
  xTaskCreate(driveACR,       (const portCHAR *) "Driving",         128, NULL, 1, NULL); // Priority 1
  // xTaskCreate(updateOrders,   (const portCHAR *) "Updating Orders", 128, NULL, 2, NULL); // Priority 2
  xTaskCreate(updatePingData, (const portCHAR *) "Updating Pings",  128, NULL, 2, NULL); // Priority 3
  go_stop(); // Guarantee that both motors are not moving at start
}

// This is supposed to be empty (lets RTOS run uninterupted)
void loop() {
}

// Basic motor commands
void set_speed(const int left_speed, const int right_speed) {
  leftMotor.setPWM(left_speed);
  rightMotor.setPWM(right_speed); 
}

void go_stop() {
  leftMotor.halt();
  rightMotor.halt();
}

void go_forward() {
  set_speed(PWM, PWM);
  leftMotor.forward();
  rightMotor.forward();
}

void go_backward() {
  set_speed(PWM, PWM);  // Compensate for difference that occurs when backing up
  leftMotor.backward();
  rightMotor.backward();
}

void go_left() {
  set_speed(PWM, PWM);
  leftMotor.backward();
  rightMotor.forward();
}

void go_right() {
  set_speed(PWM, PWM);
  leftMotor.forward();
  rightMotor.backward();
}

// Check sensors for new obstacles
void updatePingData(void *pvParameters) {
  while(1) {
    // Get distances
    leftDistance   = leftUltrasound.getDistance();
    centerDistance = centerUltrasound.getDistance();
    rightDistance  = rightUltrasound.getDistance();
    
    // Update danger booleans
    dangerLeft   = leftDistance   <= STOP_DISTANCE_SIDE;
    dangerCenter = centerDistance <= STOP_DISTANCE_CENTER;
    dangerRight  = rightDistance  <= STOP_DISTANCE_SIDE;
    dangerDetected = dangerCenter || dangerRight || dangerLeft;
    
    vTaskDelay(150 / portTICK_PERIOD_MS);
  }
}

// Respond to directions
void respondToCurrDir() {
  // Only need to act on the currDir value if it's different from the prevDir
  if (currDir != prevDir) {
    if (currDir == forward)
      go_forward();
    else if (currDir == left)
      go_left();
    else if (currDir == right)
      go_right();
    else if (currDir == backward)
      go_backward();
    else if (currDir == halt)
      go_stop();
    else
      Serial.println("Error in respondToCurrDir() - currDir not found");
  }
}

// Drives the robot accoring to the last received order
void driveACR(void *pvParameters) {
  while(1) {
    if (dangerDetected == false) {
      prevDir = currDir;
      currDir = forward;
      respondToCurrDir();
    }
    else {
      if (centerDistance <= STOP_DISTANCE_CENTER) { // If Danger at center...
        // Check whether we should go left or right
        
        if((leftDistance > STOP_DISTANCE_SIDE) && (rightDistance > STOP_DISTANCE_SIDE)){ // if you see something in the middle and nothing 
          // on the sides, go left and read again. But what if there's nothing on the side?
          go_left();
        }
        if (leftDistance <= rightDistance) { // Right has more room than left, so go right. 
          prevDir = currDir;
          currDir = right;
          respondToCurrDir();
        }
        else { // Left has more room than right, so go left.
          prevDir = currDir;
          currDir = left;
          respondToCurrDir();
        }
      }
      else if (leftDistance <= STOP_DISTANCE_SIDE) { // Issue @ left, so go right
        prevDir = currDir;
        currDir = right;
        respondToCurrDir();
      }
      else if (rightDistance <= STOP_DISTANCE_SIDE) { // Issue @ right, so go left
        prevDir = currDir;
        currDir = left;
        respondToCurrDir();
      }
      else { // No issue - this shouldn't be possible
        Serial.println("error: this shouldn't be possible"); 
      }
  }
        
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}
