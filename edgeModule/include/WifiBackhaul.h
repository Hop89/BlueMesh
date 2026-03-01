#pragma once

#include <Arduino.h>
#include "BleProvisioning.h"

class WifiBackhaul {
 public:
  void begin(const ProvisioningConfig& config);
  void loop();
  int connectedClients() const;

 private:
  int clients_ = 0;
};
