# ASR Gateway Backend

## Overview
The ASR Gateway backend provides JWT-authenticated dashboard APIs and API-token
authenticated ASR endpoints. Each user can create multiple applications and issue
revocable API tokens per application. ASR jobs and usage are accounted per application.

## Authentication Model
- **JWT (Dashboard/Admin):** Use `Authorization: Bearer <jwt>` for dashboard and
  management endpoints (`/api/apps`, `/api/auth/*`).
- **API Token (ASR APIs):** Use `Authorization: Bearer <api_token>` for ASR endpoints
  (`/api/upload`, `/api/status`, `/api/result`, `/api/history`, `/api/usage`).
- API tokens are only returned once at creation time. The backend stores a secure hash.

## High-Level Architecture (Text Diagram)
```
┌─────────────┐        ┌──────────────────┐        ┌──────────────────────┐
│ Dashboard   │ JWT    │ Applications     │        │ ASR API              │
│ /api/apps   ├───────►│ Token Mgmt       ├───────►│ Upload/Jobs/Usage     │
└─────────────┘        └──────────────────┘  Token └──────────────────────┘
         │                   │                          │
         │                   └── Application + APIToken ─┘
         └── JWT Auth for UI/Admin
```

## ASR API Usage Example
```bash
curl -X POST \
  -H "Authorization: Bearer <api_token>" \
  -F "audio=@/path/to/audio.wav" \
  -F "language=fa" \
  https://<host>/api/upload/
```

Check status:
```bash
curl -H "Authorization: Bearer <api_token>" \
  https://<host>/api/status/<job_id>/
```

Fetch result:
```bash
curl -H "Authorization: Bearer <api_token>" \
  https://<host>/api/result/<job_id>/
```

## Application & Token Lifecycle
1. Create an application (`POST /api/apps/`).
2. Create an API token (`POST /api/apps/<app_id>/tokens/`).
3. Store the token value securely (only shown once).
4. Use the token for ASR API calls.
5. Revoke tokens (`POST /api/apps/<app_id>/tokens/<token_id>/revoke/`) or deactivate
   an application (`POST /api/apps/<app_id>/deactivate/`).

## Accounting / Usage Model
- Each ASR job is linked to an **Application**.
- Usage records are linked to the same application and can be queried per application
  (`GET /api/apps/<app_id>/usage/` or `GET /api/usage/` with API token).
- Plan limits (monthly seconds, max file size, history retention) are enforced based
  on the owning user’s plan.
