# BlueMesh Protocol Draft

## Module states

- `provisioning`: booted, waiting for config or token
- `provisioned`: got config and enrolled
- `online`: active and reporting heartbeat
- `degraded`: backhaul weak or overloaded
- `offline`: missed heartbeat TTL

## Provisioning flow

1. Installer app discovers module over BLE.
2. App requests short-lived token from center: `POST /api/provision/token`.
3. App writes upstream Wi-Fi credentials and token to module GATT config characteristic.
4. Module connects upstream and registers with center: `POST /api/modules`.

## BLE contract

- Service UUID: `7f8f0100-1b22-4f6c-a133-8f0f9a2e1001`
- Config characteristic UUID (read/write): `7f8f0101-1b22-4f6c-a133-8f0f9a2e1001`
- Status characteristic UUID (read): `7f8f0102-1b22-4f6c-a133-8f0f9a2e1001`

Config payload format:

```text
moduleId=node-001;upstreamSsid=CenterBackhaul;upstreamPass=secret;token=abc123;apSsid=BlueMesh-node-001;apPass=changeme123
```

Required fields: `upstreamSsid`, `upstreamPass`, `token`.

## Heartbeat

- Endpoint: `POST /api/modules/:moduleId/heartbeat`
- Suggested interval: every 20-30 seconds
- Payload:

```json
{
  "status": "online",
  "clientCount": 7,
  "backhaulRssi": -68
}
```

## Security next steps

- Replace placeholder token with signed JWT or HMAC challenge.
- Encrypt BLE provisioning payload.
- Enforce per-module key rotation.
- Add rate-limits and audit logs on center API.
