#include "BleProvisioning.h"

#if defined(ARDUINO_ARCH_ESP32)

#include <NimBLEDevice.h>

namespace {
constexpr char kServiceUuid[] = "7f8f0100-1b22-4f6c-a133-8f0f9a2e1001";
constexpr char kConfigCharUuid[] = "7f8f0101-1b22-4f6c-a133-8f0f9a2e1001";
constexpr char kStatusCharUuid[] = "7f8f0102-1b22-4f6c-a133-8f0f9a2e1001";

class ConfigCallbacks : public NimBLECharacteristicCallbacks {
 public:
  explicit ConfigCallbacks(BleProvisioning* owner) : owner_(owner) {}

  void onWrite(NimBLECharacteristic* characteristic) override {
    owner_->applyPayload(characteristic->getValue());
  }

 private:
  BleProvisioning* owner_;
};

class StatusCallbacks : public NimBLECharacteristicCallbacks {
 public:
  explicit StatusCallbacks(BleProvisioning* owner) : owner_(owner) {}

  void onRead(NimBLECharacteristic* characteristic) override {
    characteristic->setValue(owner_->statusPayload().c_str());
  }

 private:
  BleProvisioning* owner_;
};
}  // namespace

void BleProvisioning::begin(const String& moduleId) {
  config_.moduleId = moduleId;
  config_.apSsid = "BlueMesh-" + moduleId;
  config_.apPass = "changeme123";

  NimBLEDevice::init(("BlueMesh " + moduleId).c_str());

  NimBLEServer* server = NimBLEDevice::createServer();
  NimBLEService* service = server->createService(kServiceUuid);

  NimBLECharacteristic* configChar =
      service->createCharacteristic(kConfigCharUuid, NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::READ);
  configChar->setCallbacks(new ConfigCallbacks(this));
  configChar->setValue("moduleId=<id>;upstreamSsid=<ssid>;upstreamPass=<pass>;token=<token>;apSsid=<ssid>;apPass=<pass>");

  NimBLECharacteristic* statusChar =
      service->createCharacteristic(kStatusCharUuid, NIMBLE_PROPERTY::READ);
  statusChar->setCallbacks(new StatusCallbacks(this));

  service->start();

  NimBLEAdvertising* advertising = NimBLEDevice::getAdvertising();
  advertising->addServiceUUID(kServiceUuid);
  advertising->setScanResponse(true);
  advertising->start();
}

void BleProvisioning::loop() {
  // NimBLE callbacks handle provisioning writes.
}

#elif defined(ARDUINO_PORTENTA_C33)

#include <ArduinoBLE.h>

namespace {
constexpr char kServiceUuid[] = "7f8f0100-1b22-4f6c-a133-8f0f9a2e1001";
constexpr char kConfigCharUuid[] = "7f8f0101-1b22-4f6c-a133-8f0f9a2e1001";
constexpr char kStatusCharUuid[] = "7f8f0102-1b22-4f6c-a133-8f0f9a2e1001";

constexpr char kRelayServiceUuid[] = "7f8f0200-1b22-4f6c-a133-8f0f9a2e1001";
constexpr char kRelayInCharUuid[] = "7f8f0201-1b22-4f6c-a133-8f0f9a2e1001";
constexpr char kRelayOutCharUuid[] = "7f8f0202-1b22-4f6c-a133-8f0f9a2e1001";

BLEService g_provisioningService(kServiceUuid);
BLEStringCharacteristic g_configChar(kConfigCharUuid, BLERead | BLEWrite, 240);
BLEStringCharacteristic g_statusChar(kStatusCharUuid, BLERead, 240);

BLEService g_relayService(kRelayServiceUuid);
BLEStringCharacteristic g_relayInChar(kRelayInCharUuid, BLEWrite, 240);
BLEStringCharacteristic g_relayOutChar(kRelayOutCharUuid, BLERead | BLENotify, 240);

uint32_t g_relaySeq = 0;
}  // namespace

void BleProvisioning::begin(const String& moduleId) {
  config_.moduleId = moduleId;
  config_.apSsid = "BlueMesh-" + moduleId;
  config_.apPass = "changeme123";

  if (!BLE.begin()) {
    lastStatus_ = "error:ble_begin_failed";
    return;
  }

  String deviceName = "BlueMesh " + moduleId;
  BLE.setLocalName(deviceName.c_str());
  BLE.setDeviceName(deviceName.c_str());

  g_provisioningService.addCharacteristic(g_configChar);
  g_provisioningService.addCharacteristic(g_statusChar);
  BLE.addService(g_provisioningService);

  g_configChar.writeValue("moduleId=<id>;upstreamSsid=<ssid>;upstreamPass=<pass>;token=<token>;apSsid=<ssid>;apPass=<pass>");
  g_statusChar.writeValue(statusPayload().c_str());

  g_relayService.addCharacteristic(g_relayInChar);
  g_relayService.addCharacteristic(g_relayOutChar);
  BLE.addService(g_relayService);
  g_relayOutChar.writeValue("seq=0;msg=");

  BLE.advertise();
}

void BleProvisioning::loop() {
  BLE.poll();

  if (g_configChar.written()) {
    String payload = g_configChar.value();
    applyPayload(std::string(payload.c_str()));
    g_statusChar.writeValue(statusPayload().c_str());
  }

  if (g_relayInChar.written()) {
    String incoming = g_relayInChar.value();
    g_relaySeq++;
    String relayPayload = "seq=" + String(g_relaySeq) + ";" + incoming;
    g_relayOutChar.writeValue(relayPayload.c_str());
  }
}

#else

void BleProvisioning::begin(const String& moduleId) {
  config_.moduleId = moduleId;
  config_.apSsid = "BlueMesh-" + moduleId;
  config_.apPass = "changeme123";
  lastStatus_ = "error:unsupported_board";
}

void BleProvisioning::loop() {}

#endif

bool BleProvisioning::hasConfig() const {
  return configured_;
}

ProvisioningConfig BleProvisioning::getConfig() const {
  return config_;
}

bool BleProvisioning::applyPayload(const std::string& payload) {
  String data(payload.c_str());

  String moduleId = extractField(data, "moduleId");
  String upstreamSsid = extractField(data, "upstreamSsid");
  String upstreamPass = extractField(data, "upstreamPass");
  String token = extractField(data, "token");
  String apSsid = extractField(data, "apSsid");
  String apPass = extractField(data, "apPass");

  if (!moduleId.isEmpty()) {
    config_.moduleId = moduleId;
  }

  if (upstreamSsid.isEmpty() || upstreamPass.isEmpty() || token.isEmpty()) {
    configured_ = false;
    lastStatus_ = "error:missing_required_fields";
    return false;
  }

  config_.upstreamSsid = upstreamSsid;
  config_.upstreamPass = upstreamPass;
  config_.enrollmentToken = token;

  if (!apSsid.isEmpty()) {
    config_.apSsid = apSsid;
  }
  if (!apPass.isEmpty()) {
    config_.apPass = apPass;
  }

  configured_ = true;
  lastStatus_ = "configured";
  return true;
}

String BleProvisioning::extractField(const String& data, const String& key) {
  String needle = key + "=";
  int start = data.indexOf(needle);
  if (start < 0) {
    return "";
  }

  start += needle.length();
  int end = data.indexOf(';', start);
  if (end < 0) {
    end = data.length();
  }

  String value = data.substring(start, end);
  value.trim();
  return value;
}

String BleProvisioning::statusPayload() const {
  return String("state=") + (configured_ ? "configured" : "waiting") +
         ";moduleId=" + config_.moduleId +
         ";apSsid=" + config_.apSsid +
         ";status=" + lastStatus_;
}
