#include <Arduino_FreeRTOS.h>
#include "Ultrasound.h"

// Globals for crash avoidance
boolean dangerCenter = false;
boolean dangerLeft   = false;
boolean dangerRight  = false;
boolean dangerDetected = false;
long leftDistance = 0, centerDistance = 0, rightDistance = 0;

// Ping sensor pins
const int right_ping_pin  = 5;
const int center_ping_pin = 6;
const int left_ping_pin   = 7;

// OOP Initializations
Ultrasound leftUltrasound   (left_ping_pin);
Ultrasound centerUltrasound (center_ping_pin);
Ultrasound rightUltrasound  (right_ping_pin);

void setup() {
  Serial.begin(9600); // Set baud-rate
}

void loop() {
    // Get distances
    leftDistance   = leftUltrasound.getDistance();
    centerDistance = centerUltrasound.getDistance();
    rightDistance  = rightUltrasound.getDistance();

    // Print distances
    Serial.print("Left: ");
    Serial.println(leftDistance);
    Serial.print("Center: ");
    Serial.println(centerDistance);
    Serial.print("Right: ");
    Serial.println(rightDistance);

    delay(500);
}
