#include "BleProvisioning.h"

#include <NimBLEDevice.h>

void BleProvisioning::begin(const String& moduleId) {
  config_.moduleId = moduleId;
  config_.apSsid = "BlueMesh-" + moduleId;
  config_.apPass = "changeme123";
  config_.upstreamSsid = "CenterBackhaul";
  config_.upstreamPass = "changeme123";

  NimBLEDevice::init(("BlueMesh " + moduleId).c_str());
  configured_ = true;
}

bool BleProvisioning::hasConfig() const {
  return configured_;
}

ProvisioningConfig BleProvisioning::getConfig() const {
  return config_;
}

void BleProvisioning::loop() {
  // TODO: Expose BLE service characteristics for provisioning updates.
}
