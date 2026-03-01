#include <Arduino.h>

#include "BleProvisioning.h"
#include "WifiBackhaul.h"

static BleProvisioning g_provisioning;
static WifiBackhaul g_backhaul;
static unsigned long g_lastLog = 0;

void setup() {
  Serial.begin(115200);

  String moduleId = "node-001";
  g_provisioning.begin(moduleId);

  if (g_provisioning.hasConfig()) {
    g_backhaul.begin(g_provisioning.getConfig());
  }
}

void loop() {
  g_provisioning.loop();
  g_backhaul.loop();

  if (millis() - g_lastLog > 5000) {
    g_lastLog = millis();
    Serial.printf("clients=%d\n", g_backhaul.connectedClients());
  }
}
