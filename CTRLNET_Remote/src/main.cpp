#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ESP8266Ping.h>
#include "secrets.h"

// --- Configuration ---
// The IP address of your laptop running the CTRLNET server (e.g., 192.168.1.100)
const char* ctrlnet_server = "http://192.168.1.100:8000/api/scan";

// Scan configurations
const int SUBNET_PREFIX = 192;
const int SUBNET_SECOND = 168;
const int SUBNET_THIRD = 1;  // Typically 1 or 0 for home networks (e.g., 192.168.1.X)
const unsigned long SCAN_INTERVAL_MS = 60000; // Wait 60 seconds between full network sweeps

// Hardware Pins
const int LED_PIN = 2; // Blue LED

void notifyCtrlnetServer(String targetIp);

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // LED off

  Serial.println("\n\n--- CTRLNET AUTONOMOUS SCOUT INITIALIZING ---");
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("Scout IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Scout is ready. Beginning autonomous network sweeps...\n");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("[*] Starting sweep of 192.168." + String(SUBNET_THIRD) + ".X...");
    
    // Sweep the local subnet from 1 to 254
    for (int i = 1; i < 255; i++) {
      // Don't scan ourselves
      if (WiFi.localIP()[3] == i) continue;

      IPAddress target(SUBNET_PREFIX, SUBNET_SECOND, SUBNET_THIRD, i);
      
      // Blink LED quickly while scanning
      digitalWrite(LED_PIN, LOW);
      bool success = Ping.ping(target, 1); // 1 ping attempt per IP for speed
      digitalWrite(LED_PIN, HIGH);

      if (success) {
        Serial.print("[+] Discovered active device at: ");
        Serial.println(target.toString());
        
        // Notify laptop server to run deep analysis
        notifyCtrlnetServer(target.toString());
      }
      
      // Tiny delay to avoid watchdog resets
      yield(); 
    }
    
    Serial.println("[*] Sweep complete. Sleeping before next sweep...");
  } else {
    Serial.println("[!] Error: WiFi disconnected. Attempting to reconnect...");
    WiFi.reconnect();
  }

  // Wait before next full network sweep
  delay(SCAN_INTERVAL_MS);
}

void notifyCtrlnetServer(String targetIp) {
  WiFiClient client;
  HTTPClient http;
  
  // Construct the URL to hit the laptop's CTRLNET API
  String url = String(ctrlnet_server) + "?target=" + targetIp;
  
  Serial.print("    -> Dispatching target to CTRLNET engine: ");
  Serial.println(url);
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST("{}");
  
  if (httpResponseCode > 0) {
    Serial.print("    -> Laptop acknowledged (HTTP ");
    Serial.print(httpResponseCode);
    Serial.println("). Deep scan initiated.");
  } else {
    Serial.print("    -> [ERROR] Failed to reach laptop server. Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}
