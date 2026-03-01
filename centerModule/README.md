# Center Module

This folder hosts the central control service that:
- Exposes a module registry API
- Accepts module heartbeats
- Serves a simple dashboard for operations

## Quick start

```bash
npm install
npm run dev
```

Service defaults to `http://0.0.0.0:8080`.

## API

- `GET /health`
- `GET /api/modules`
- `POST /api/modules`
- `POST /api/modules/:moduleId/heartbeat`
- `POST /api/provision/token`
