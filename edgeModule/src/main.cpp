#include <Arduino.h>

#include "BleProvisioning.h"
#include "WifiBackhaul.h"

static BleProvisioning g_provisioning;
static WifiBackhaul g_backhaul;
static bool g_backhaulStarted = false;
static unsigned long g_lastLog = 0;

void setup() {
  Serial.begin(115200);

  const String moduleId = "node-001";
  g_provisioning.begin(moduleId);
}

void loop() {
  g_provisioning.loop();

  if (!g_backhaulStarted && g_provisioning.hasConfig()) {
    g_backhaul.begin(g_provisioning.getConfig());
    g_backhaulStarted = true;
  }

  if (g_backhaulStarted) {
    g_backhaul.loop();
  }

  if (millis() - g_lastLog > 5000) {
    g_lastLog = millis();
    Serial.print("configured=");
    Serial.print(g_provisioning.hasConfig() ? 1 : 0);
    Serial.print(" backhaul_clients=");
    Serial.println(g_backhaul.connectedClients());
  }
}
