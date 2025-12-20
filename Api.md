Absolutely. Below is the **clean English version** of the documentation, focused **only on how the system works, API contracts, and accounting logic** — no deployment or runtime steps.

---

# 📘 ASR Platform – Architecture, APIs, and Accounting

## 1. System Overview (How It Works)

The platform is composed of two main layers:

```
Client (Web / Mobile / Bot)
        |
        |  HTTP + WebSocket + JWT
        v
Django ASR Gateway (Control Plane)
        |
        |  Internal HTTP
        v
FastAPI ASR Core (GPU Worker)
```

### Responsibilities

| Component        | Responsibility                                        |
| ---------------- | ----------------------------------------------------- |
| Client           | Upload audio, receive transcript, realtime updates    |
| Django Gateway   | Authentication, limits, accounting, UI, orchestration |
| FastAPI ASR Core | Audio → Text (GPU only)                               |
| Celery           | Async job execution                                   |
| Redis            | Queue + WebSocket backend                             |

Audio files are **never stored**. Only metadata and text results are persisted.

---

## 2. User Tiers

The system supports three access levels:

### 1️⃣ Anonymous User

* No login required
* Temporary JWT token
* Strict limits

### 2️⃣ Authenticated (Free)

* Logged-in user
* No subscription
* Medium limits

### 3️⃣ Subscription Users

* **PLUS**
* **PRO**

---

## 3. JWT Token Design

### JWT Claims

```json
{
  "uid": 42,
  "plan": "plus",
  "token_version": 1,
  "exp": 1739999999
}
```

| Claim         | Description                  |
| ------------- | ---------------------------- |
| uid           | User ID (null for anonymous) |
| plan          | anon / free / plus / pro     |
| token_version | Token invalidation           |
| exp           | Expiration timestamp         |

---

## 4. API Documentation (Django Gateway)

### Base URL

```
/api/
```

---

### 4.1 Health Check

```
GET /api/health/
```

Response:

```json
{ "status": "ok" }
```

---

### 4.2 Get Anonymous Token

```
POST /api/auth/anon/token/
```

Response:

```json
{
  "access": "jwt-token",
  "plan": "anon",
  "expires_in": 600
}
```

No authentication required.

---

### 4.3 Login (JWT)

```
POST /api/auth/token/
```

Body:

```json
{
  "username": "user",
  "password": "pass"
}
```

Response:

```json
{
  "access": "jwt-token",
  "refresh": "jwt-refresh",
  "plan": "free"
}
```

---

### 4.4 Upload Audio (Create ASR Job)

```
POST /api/upload/
```

Headers:

```
Authorization: Bearer <JWT>
```

Form Data:

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| audio      | file   | yes      |
| language   | string | no       |
| model_name | string | no       |
| device     | string | no       |

Response:

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

Audio is processed in-memory and discarded.

---

### 4.5 Job Status

```
GET /api/status/{job_id}/
```

Response:

```json
{
  "id": "uuid",
  "status": "processing",
  "audio": {
    "duration_sec": 9.3,
    "sample_rate": 48000,
    "format": "webm"
  },
  "processing_seconds": 2.1
}
```

---

### 4.6 Job Result

```
GET /api/result/{job_id}/
```

Response:

```json
{
  "text": "Hello, how are you?",
  "words_count": 4,
  "chars_count": 19,
  "language": "en"
}
```

---

## 5. WebSocket API (Realtime)

### Endpoint

```
ws://HOST/ws/jobs/{job_id}/?token=<JWT>
```

### Events

```json
{ "status": "queued" }
{ "status": "processing" }
{ "status": "done", "text": "..." }
{ "status": "failed", "error": "..." }
```

WebSocket replaces polling for realtime UX.

---

## 6. Accounting Model

### Cost Metrics

The system uses a **hybrid cost model**:

> **Audio Duration + Word Count**

---

### Metrics Collected

| Metric             | Description          |
| ------------------ | -------------------- |
| audio_duration_sec | Length of audio      |
| words_count        | Number of words      |
| chars_count        | Number of characters |
| processing_time    | GPU processing time  |

---

### Cost Formula

```
cost =
    audio_duration_sec
  + (words_count × WORD_COST)
```

Example:

```
audio_duration = 12.5 sec
words = 40
WORD_COST = 0.05

cost = 12.5 + (40 × 0.05)
cost = 14.5 units
```

---

## 7. Plan Limits

| Plan | Max Audio Length |
| ---- | ---------------- |
| anon | 20 seconds       |
| free | 60 seconds       |
| plus | 10 minutes       |
| pro  | 30 minutes       |

If exceeded:

```json
HTTP 403
{ "error": "audio duration exceeds plan limit" }
```

---

## 8. Usage Ledger (Accounting Records)

Each job generates an immutable usage record:

```json
{
  "user_id": 42,
  "job_id": "uuid",
  "duration_sec": 12.5,
  "words": 40,
  "cost": 14.5,
  "plan": "plus",
  "created_at": "2025-01-12T10:12:00Z"
}
```

Used for:

* Monthly reports
* Invoices
* Quota enforcement

---

## 9. Key Architectural Decisions

| Decision                 | Reason                    |
| ------------------------ | ------------------------- |
| Do not store audio       | Privacy & security        |
| GPU isolated in FastAPI  | Stability & scaling       |
| JWT-based auth           | Stateless & scalable      |
| WebSocket updates        | Better UX                 |
| Duration + words pricing | Fairer than duration-only |

---

## 10. Abuse Prevention (Design-Level)

* Rate limits for anonymous users
* Max concurrent jobs per user
* Audio length checks before queueing
* `token_version` for immediate revocation

---

## Summary

This ASR platform is:

* API-first
* Scalable
* Privacy-preserving
* SaaS-ready
* Realtime-enabled
* Billing-aware

---

### Possible Next Docs

If you want, I can also prepare:

* 📊 Billing & invoicing design
* 🔐 Security & threat model
* 📈 Scaling (multi-GPU, multi-worker)
* 🧩 Multi-tenant extensions

Just tell me which one to continue.
