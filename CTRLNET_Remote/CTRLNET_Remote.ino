#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#include "secrets.h"

// --- Configuration ---

// The IP address of your laptop running the CTRLNET server (e.g., 192.168.1.100)
// You can find your laptop's IP by opening cmd and typing `ipconfig` (Look for IPv4 Address)
const char* ctrlnet_server = "http://192.168.1.100:8000/api/scan";

// The target you want to scan when you press the button
const char* scan_target = "192.168.1.0/24";   

// Hardware Pins
const int BUTTON_PIN = 0; // GPIO 0 is usually the built-in "FLASH" button on NodeMCU
const int LED_PIN = 2;    // GPIO 2 is usually the built-in blue LED

// State tracking
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // LED off (Active LOW on most ESP8266)

  // Connect to WiFi
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("ESP8266 IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Ready to trigger CTRLNET scans.");
}

void loop() {
  int reading = digitalRead(BUTTON_PIN);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    // If the button state has changed to LOW (pressed)
    if (reading == LOW && lastButtonState == HIGH) {
      Serial.println("\n[!] Button Pressed! Triggering CTRLNET Scan...");
      triggerScan();
    }
  }

  lastButtonState = reading;
}

void triggerScan() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    
    // Turn on LED to indicate activity
    digitalWrite(LED_PIN, LOW); 
    
    // Construct the URL with query parameters
    String url = String(ctrlnet_server) + "?target=" + scan_target;
    
    Serial.print("POSTing to: ");
    Serial.println(url);
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    // Send an empty POST body since target is in query params
    int httpResponseCode = http.POST("{}");
    
    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      String payload = http.getString();
      Serial.println(payload);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
    
    // Turn off LED
    digitalWrite(LED_PIN, HIGH); 
  } else {
    Serial.println("Error: WiFi not connected");
  }
}
