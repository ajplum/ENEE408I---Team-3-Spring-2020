#include <Arduino_FreeRTOS.h>
#include "MotorControl.h"

//constants
byte PWM = 60;

// Motor pins
const int LeftMotorA_pin    = 11;
const int LeftMotorB_pin    = 10;
const int LeftMotorPWM_pin  = 6;
const int RightMotorA_pin   = 13;
const int RightMotorB_pin   = 12;
const int RightMotorPWM_pin = 5;

// OOP Initializations
MotorControl leftMotor  (LeftMotorA_pin,  LeftMotorB_pin,  LeftMotorPWM_pin);
MotorControl rightMotor (RightMotorA_pin, RightMotorB_pin, RightMotorPWM_pin);

void setup() {
  Serial.begin(9600); // Set baud-rate
}

void loop() {
  go_stop();
  delay(1000);
  go_forward();
  delay(1000);
  go_backward();
  delay(1000);
  go_right();
  delay(1000);
  go_left();
  delay(1000);
  go_stop();
}

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
