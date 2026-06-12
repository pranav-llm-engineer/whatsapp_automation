# WhatsApp Automation API Documentation

This document provides in-depth details of all FastAPI endpoints exposed by the backend for the Coworking Space AI Chatbot. The API manages user authentication, chat conversations, onboarding state, dummy payments, and incoming WhatsApp webhooks.

---

## Table of Contents
1. [Authentication (`/auth`)](#1-authentication-auth)
2. [Chat & Assistant (`/chat`)](#2-chat--assistant-chat)
3. [Payment Gateway (`/payment`)](#3-payment-gateway-payment)
4. [WhatsApp Webhook (`/webhook`)](#4-whatsapp-webhook-webhook)

---

## 1. Authentication (`/auth`)

These endpoints handle user registration, login, and fetching user profiles.

### 1.1 Register User
- **URL**: `/auth/register`
- **Method**: `POST`
- **Description**: Registers a new user with a phone number and password. It automatically creates a blank `UserProfile` linked to the user.

**Request Body** (`application/json`):
```json
{
  "phone": "+919876543210",
  "password": "secure_password_123"
}
```

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "message": "User created successfully"
}
```

**Error Responses**:
- **Code**: `400 Bad Request` (If phone number is already registered)

---

### 1.2 User Login
- **URL**: `/auth/login`
- **Method**: `POST`
- **Description**: Authenticates a user using phone and password. On success, it creates a new persistent session in the database and returns a session token (acting as a bearer token).

**Request Body** (`application/json`):
```json
{
  "phone": "+919876543210",
  "password": "secure_password_123"
}
```

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "access_token": "550e8400-e29b-41d4-a716-446655440000",
  "token_type": "bearer",
  "user_id": 1
}
```

**Error Responses**:
- **Code**: `400 Bad Request` (If incorrect phone or password)

---

### 1.3 Get Current Profile
- **URL**: `/auth/me`
- **Method**: `GET`
- **Description**: Fetches the currently authenticated user's profile and onboarding state based on their active `session_id`.

**Query Parameters**:
- `session_id` (string, required): The UUID token returned during login.

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "user_id": 1,
  "full_name": "Pranav Mehta",
  "onboarding_active": true,
  "onboarding_step": "location",
  "onboarding_complete": false,
  "spaceType": "Dedicated Desk",
  "seatRangeMin": 1,
  "seatRangeMax": 2,
  "urgency": "High",
  "location": null,
  "phone": "+919876543210"
}
```

**Error Responses**:
- **Code**: `401 Unauthorized` (If session is invalid)
- **Code**: `404 Not Found` (If user profile does not exist)

---

## 2. Chat & Assistant (`/chat`)

These endpoints handle message processing via OpenRouter (Groq), semantic search (Supabase pgvector), state-machine logic for onboarding, and CRM synchronization.

### 2.1 Chat Endpoint
- **URL**: `/chat/`
- **Method**: `POST`
- **Description**: The core conversational endpoint. It processes the user message, determines if the user is in general mode or onboarding mode, executes RAG retrieval, fetches missing onboarding fields via LLM if necessary, and returns the assistant's reply.

**Request Body** (`application/json`):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "What is the price of a dedicated desk?"
}
```

**Success Response**:
- **Code**: `200 OK`
- **Content** (varies depending on mode):
```json
{
  "reply": "A dedicated desk costs ₹8,000 per month.",
  "mode": "general", 
  "onboarding_complete": false,
  "onboarding_active": false,
  "context": "...retrieved markdown chunks..."
}
```
*Note: `mode` can be either `general` or `onboarding`.*

**Error Responses**:
- **Code**: `401 Unauthorized` (If session is invalid)
- **Code**: `404 Not Found` (If profile is missing)

---

### 2.2 Get Chat History
- **URL**: `/chat/history`
- **Method**: `GET`
- **Description**: Retrieves up to the last 50 messages of the conversation history for a specific session.

**Query Parameters**:
- `session_id` (string, required): The session token.

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
[
  {
    "role": "user",
    "content": "Hi, I need a desk",
    "timestamp": "2026-06-12T10:00:00Z"
  },
  {
    "role": "assistant",
    "content": "Great! What kind of desk are you looking for?",
    "timestamp": "2026-06-12T10:00:02Z"
  }
]
```

---

### 2.3 Transcribe Audio (Voice Notes)
- **URL**: `/chat/transcribe/`
- **Method**: `POST`
- **Description**: Receives a multi-part audio file upload and forwards it to the Sarvam AI API (or Groq Whisper) for Speech-to-Text transcription.

**Request Body** (`multipart/form-data`):
- `file`: The audio file (e.g., .ogg, .mp3, .wav)

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "transcript": "hello what is the price of an office"
}
```

**Error Responses**:
- **Code**: `500 Internal Server Error` (If API key is missing or transcription fails)

---

## 3. Payment Gateway (`/payment`)

These endpoints manage the dummy payment flow simulation.

### 3.1 Initiate Payment
- **URL**: `/payment/initiate`
- **Method**: `POST`
- **Description**: Creates a pending payment record in the database and generates a unique transaction reference (`txn_ref`).

**Request Body** (`application/json`):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 15000.0,
  "membership_type": "Dedicated Desk",
  "billing_cycle": "Monthly"
}
```

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "txn_ref": "TXN-A1B2C3D4",
  "status": "pending"
}
```

**Error Responses**:
- **Code**: `401 Unauthorized` (If session is invalid)

---

### 3.2 Confirm Payment
- **URL**: `/payment/confirm`
- **Method**: `POST`
- **Description**: Simulates the confirmation (or failure) of an initiated payment. If marked as `success`, it triggers `onboarding_complete = True` for the user's profile.

**Request Body** (`application/json`):
```json
{
  "txn_ref": "TXN-A1B2C3D4",
  "mock_result": "success" 
}
```
*Note: `mock_result` is optional. If omitted, the system randomly assigns success (75% probability) or fail (25% probability).*

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "status": "success",
  "txn_ref": "TXN-A1B2C3D4"
}
```

**Error Responses**:
- **Code**: `404 Not Found` (If payment transaction reference does not exist)

---

## 4. WhatsApp Webhook (`/webhook`)

These endpoints act as the interface between the Meta WhatsApp API and the backend.

### 4.1 Verify Webhook
- **URL**: `/webhook/`
- **Method**: `GET`
- **Description**: Used by Meta to verify the webhook URL during initial setup. It matches the `hub.verify_token` against your environment variables and returns the `hub.challenge`.

**Query Parameters**:
- `hub.mode` (string): Should be `subscribe`
- `hub.verify_token` (string): Must match `WHATSAPP_VERIFY_TOKEN` in `.env`
- `hub.challenge` (string): A random string sent by Meta

**Success Response**:
- **Code**: `200 OK`
- **Content**: `(Plain text of the hub.challenge value)`

**Error Responses**:
- **Code**: `400 Bad Request` (Missing parameters)
- **Code**: `403 Forbidden` (Token mismatch)

---

### 4.2 Receive WhatsApp Message
- **URL**: `/webhook/`
- **Method**: `POST`
- **Description**: The primary listener for incoming WhatsApp messages (text or audio). It adds tasks to FastAPI's `BackgroundTasks` to parse the message, process it through the `/chat/` logic, download/transcribe audio, and dispatch a response back to the user via WhatsApp Graph API. Also supports inline image responses using `[SEND_IMAGE: filename.png]` syntax.

**Request Body** (`application/json`):
(Follows the standard WhatsApp Business Cloud API payload schema)
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {"display_phone_number": "123", "phone_number_id": "123"},
            "contacts": [{"profile": {"name": "User"}, "wa_id": "+919876543210"}],
            "messages": [
              {
                "from": "+919876543210",
                "id": "wamid.HBg...",
                "timestamp": "1700000000",
                "type": "text",
                "text": {"body": "Hi there!"}
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Success Response**:
- **Code**: `200 OK`
- **Content**: 
```json
{
  "status": "ok"
}
```

**Error Responses**:
- **Code**: `404 Not Found` (If object is not `whatsapp_business_account`)
