#include "WifiBackhaul.h"

#if __has_include(<WiFiC3.h>)
#include <WiFiC3.h>
#elif __has_include(<WiFiS3.h>)
#include <WiFiS3.h>
#elif __has_include(<WiFi.h>)
#include <WiFi.h>
#else
#error "No compatible WiFi library found for this board"
#endif

void WifiBackhaul::begin(const ProvisioningConfig& config) {
#if defined(ARDUINO_ARCH_ESP32)
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(config.apSsid.c_str(), config.apPass.c_str());
  WiFi.begin(config.upstreamSsid.c_str(), config.upstreamPass.c_str());
#elif defined(ARDUINO_PORTENTA_C33)
  // Portenta C33 stack does not provide ESP32-style AP+STA APIs.
  WiFi.begin(config.upstreamSsid.c_str(), config.upstreamPass.c_str());
#else
  WiFi.begin(config.upstreamSsid.c_str(), config.upstreamPass.c_str());
#endif
}

void WifiBackhaul::loop() {
#if defined(ARDUINO_ARCH_ESP32)
  clients_ = WiFi.softAPgetStationNum();
#else
  clients_ = (WiFi.status() == WL_CONNECTED) ? 1 : 0;
#endif
}

int WifiBackhaul::connectedClients() const {
  return clients_;
}
