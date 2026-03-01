#pragma once

#include <Arduino.h>
#include <string>

struct ProvisioningConfig {
  String moduleId;
  String apSsid;
  String apPass;
  String upstreamSsid;
  String upstreamPass;
  String enrollmentToken;
};

class BleProvisioning {
 public:
  void begin(const String& moduleId);
  bool hasConfig() const;
  ProvisioningConfig getConfig() const;
  void loop();

  // Exposed for BLE write callbacks.
  bool applyPayload(const std::string& payload);

 private:
  static String extractField(const String& data, const String& key);
  String statusPayload() const;

  bool configured_ = false;
  ProvisioningConfig config_;
  String lastStatus_ = "waiting";
};
