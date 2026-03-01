#pragma once

#include <Arduino.h>

struct ProvisioningConfig {
  String moduleId;
  String apSsid;
  String apPass;
  String upstreamSsid;
  String upstreamPass;
};

class BleProvisioning {
 public:
  void begin(const String& moduleId);
  bool hasConfig() const;
  ProvisioningConfig getConfig() const;
  void loop();

 private:
  bool configured_ = false;
  ProvisioningConfig config_;
};
