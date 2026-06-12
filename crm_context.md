# CRM Context: Coworking Hub — Public Lead API

Use this file as context when writing integrations, automation scripts, or workflows against the Coworking Hub CRM.

---

## Base URL

```
https://cowork-space-manager.pages.dev/api
```

---

## Authentication

All requests require a Bearer token in the `Authorization` header.

```
Authorization: Bearer cwk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- Keys are minted on the **API Keys** page. The plaintext is shown **once** at creation — store it immediately.
- Keys are stored as SHA-256 hashes server-side; plaintext is never recoverable.
- **Admins/agents** can mint, view, and revoke their own keys.
- **Super admins** can mint keys on behalf of any user (pass `userId`).
- Revoke keys via the UI to invalidate immediately.

---

## Rate Limit

**60 requests / minute / API key.** Exceeding returns `429 Too Many Requests`.

---

## Endpoints

### `POST /public/leads` — Create a lead

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `customerName` | string | ✅ | |
| `mobileNumber` | string | ✅ | E.164 or local format |
| `source` | enum | ✅ | `organic_website` · `meta_ads` · `google_ads` · `ads_website` · `walk_in` · `referral` · `call` · `other` |
| `spaceType` | enum | ✅ | `private_cabin` · `day_pass` · `five_days_pass` · `seven_days_pass` · `workstation` · `meeting_room` · `podcast_room` · `conference_room` |
| `seatRangeMin` | integer | ✅ | |
| `seatRangeMax` | integer | ✅ | |
| `urgency` | enum | ✅ | `low` · `medium` · `high` · `immediate` |
| `location` | string | ✅ | Customer's Current Location |
| `spaceId` | integer | ✅ | Default (1) |
| `numberVerified` | boolean | ➖ | Default: `false` |
| `stage` | enum | ➖ | Default: `not_contacted` |
| `callStatus` | enum | ➖ | Default: `not_started` |
| `leadStatus` | string | ➖ | Default: `new` |
| `campaignId` | string | ➖ | Free-form campaign reference |
| `nextFollowUpDate` | ISO date-time | ➖ | |
| `callbackScheduledDate` | ISO date-time | ➖ | |
| `callbackScheduledSlot` | string | ➖ | |
| `followUpCount` | integer | ➖ | Default: `0` |
| `externalId` | string | ➖ | Stable ID from your system — enables idempotent upserts on PATCH |
| `assignedToWhatsappNumber` | string | ➖ | WhatsApp number of agent/admin to assign; resolved server-side |

**Success response — `201 Created`**

```json
{ "id": 42, "externalId": null, "priorityScore": 73, "priority": "high" }
```

**Example**

```bash
curl -X POST https://cowork-space-manager.pages.dev/api/public/leads \
  -H "Authorization: Bearer cwk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "customerName": "Anjali Mehra",
    "mobileNumber": "9812345678",
    "source": "organic_website",
    "spaceType": "private_cabin",
    "seatRangeMin": 4,
    "seatRangeMax": 6,
    "urgency": "high",
    "location": "Indiranagar",
    "spaceId": 1,
    "campaignId": "spring-2026"
  }'
```

---

### `PATCH /public/leads/{idOrExternalId}` — Update or upsert a lead

The path parameter accepts:
- A **numeric internal `id`** (e.g. `42`)
- An **`externalId`** string you set at create time (e.g. `lp-spring2026-9812`)

**Upsert behaviour:** If no match is found AND the body contains all required-on-create fields, the endpoint creates a new lead with that `externalId`. This makes landing-page integrations safely idempotent on retries.

**Success response — `200 OK`**

```json
{ "id": 42, "externalId": "lp-spring2026-9812", "priorityScore": 73, "priority": "high", "created": false }
```

`"created": true` means a new lead was upserted (not an existing one updated).

**Example — update by internal id**

```bash
curl -X PATCH https://cowork-space-manager.pages.dev/api/public/leads/42 \
  -H "Authorization: Bearer cwk_..." \
  -H "Content-Type: application/json" \
  -d '{ "numberVerified": true, "stage": "contacted" }'
```

**Example — idempotent upsert by externalId**

```bash
curl -X PATCH https://cowork-space-manager.pages.dev/api/public/leads/lp-spring2026-9812 \
  -H "Authorization: Bearer cwk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "externalId": "lp-spring2026-9812",
    "customerName": "Anjali Mehra",
    "mobileNumber": "9812345678",
    "source": "meta_ads",
    "spaceType": "private_cabin",
    "seatRangeMin": 4,
    "seatRangeMax": 6,
    "urgency": "high",
    "location": "Indiranagar",
    "spaceId": 1,
    "numberVerified": true,
    "assignedToWhatsappNumber": "9000000002"
  }'
```

---

## Error Codes

| Code | Meaning |
|---|---|
| `400` | Invalid body or unknown `spaceId` |
| `401` | Missing or invalid bearer token |
| `404` | Lead not found (numeric id PATCH only) |
| `409` | `externalId` already exists (POST only) |
| `429` | Rate limit exceeded (60 req/min) |

---

## Enum Reference

### `source`
`organic_website` · `meta_ads` · `google_ads` · `ads_website` · `walk_in` · `referral` · `call` · `other`

### `spaceType`
`private_cabin` · `day_pass` · `five_days_pass` · `seven_days_pass` · `workstation` · `meeting_room` · `podcast_room` · `conference_room`

### `urgency`
`low` · `medium` · `high` · `immediate`

### `stage` (default: `not_contacted`)
Set via optional field on create or PATCH.

### `callStatus` (default: `not_started`)
Set via optional field on create or PATCH.

---

## Audit Trail & Scoring

- Every API write is recorded as an **activity entry** on the lead with actor `api-key:<prefix>` and the key's label — useful for tracing which integration touched a lead.
- `priorityScore` and `priority` are **auto-computed** from Score Builder rules on every write.
- Super admins can trigger a full recalculation via **Recalculate All Leads** in the UI after rule changes.

---

## Integration Patterns

### Landing page → new lead on form submit
Use `POST /public/leads` with `source: "organic_website"` (or relevant source). Pass an `externalId` tied to the form submission ID for deduplication.

### Ad campaign webhook → upsert on retry
Use `PATCH /public/leads/{externalId}` with the full required fields in the body. Safe to retry — if the lead already exists it updates; if not, it creates.

### Assign lead to agent on creation
Pass `assignedToWhatsappNumber` (agent's WhatsApp number) in the POST/PATCH body. Resolution is handled server-side.

### Update lead after number verification
`PATCH /public/leads/{id}` with `{ "numberVerified": true }`.
