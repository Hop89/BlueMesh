#include "WifiBackhaul.h"

#include <WiFi.h>

void WifiBackhaul::begin(const ProvisioningConfig& config) {
  WiFi.mode(WIFI_AP_STA);

  WiFi.softAP(config.apSsid.c_str(), config.apPass.c_str());
  WiFi.begin(config.upstreamSsid.c_str(), config.upstreamPass.c_str());
}

void WifiBackhaul::loop() {
  clients_ = WiFi.softAPgetStationNum();
}

int WifiBackhaul::connectedClients() const {
  return clients_;
}
