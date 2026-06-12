# Coworking Space AI Chatbot — Implementation Plan
**Stack:** FastAPI · Streamlit · OpenRouter · ChromaDB · SQLite  
**Pattern:** RAG + Stateful Onboarding + Persistent Sessions + Dummy Payment Gateway

---

## 1. Overview & Goals

| Goal | Mechanism |
|------|-----------|
| Customer Q&A (pricing, amenities, policies) | RAG over structured KB markdown |
| Zero pricing hallucination | Hard retrieval gate — pricing ONLY from context |
| Conversational onboarding (one field at a time) | State-machine in SQLite, resumed per session |
| Persistent user profile | SQLite user record + session token |
| Payment flow | Dummy gateway with mock success/fail |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend                       │
│  Login / Register · Chat UI · Onboarding progress bar          │
└─────────────────────┬───────────────────────────────────────────┘
                      │  HTTP (REST)
┌─────────────────────▼───────────────────────────────────────────┐
│                       FastAPI Backend                           │
│                                                                 │
│  /auth     /chat     /onboarding     /payment                   │
│                                                                 │
│  ┌──────────────┐  ┌────────────────────────────────────────┐  │
│  │  LLM Service │  │           RAG Service                  │  │
│  │  OpenRouter  │  │  ChromaDB  ←  KB Ingestor              │  │
│  └──────┬───────┘  └──────────────────┬─────────────────────┘  │
│         │                             │                         │
│  ┌──────▼─────────────────────────────▼─────────────────────┐  │
│  │              Session & State Service                     │  │
│  │              SQLite (users · sessions · conversations)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Project File Structure

```
cowork-assistant/
│
├── backend/
│   ├── main.py                        # FastAPI app init, CORS, router mounting
│   ├── config.py                      # Env vars (OPENROUTER_API_KEY, DB paths)
│   │
│   ├── routers/
│   │   ├── auth.py                    # POST /register, POST /login
│   │   ├── chat.py                    # POST /chat  (main conversation endpoint)
│   │   ├── onboarding.py              # GET /onboarding/status, POST /onboarding/step
│   │   └── payment.py                 # POST /payment/initiate, POST /payment/confirm
│   │
│   ├── services/
│   │   ├── rag_service.py             # Embed query → ChromaDB → return context chunks
│   │   ├── llm_service.py             # OpenRouter call, system prompt builder
│   │   ├── session_service.py         # Create/load session, conversation history
│   │   ├── onboarding_service.py      # State machine: next field, validate, save
│   │   └── payment_service.py         # Dummy gateway logic
│   │
│   ├── db/
│   │   ├── database.py                # SQLite engine + session factory (SQLAlchemy)
│   │   ├── models.py                  # ORM models (User, Session, Conversation, OnboardingState)
│   │   └── vector_store.py            # ChromaDB client init + collection setup
│   │
│   ├── knowledge_base/
│   │   └── cowork_kb.md               # ← Your 8-category WhatsApp-derived KB goes here
│   │
│   └── scripts/
│       └── ingest_kb.py               # One-time script: chunk KB → embed → upsert ChromaDB
│
├── frontend/
│   └── app.py                         # Streamlit UI (all pages)
│
├── .env
├── requirements.txt
└── README.md
```

---

## 4. Database Schema (SQLite via SQLAlchemy)

### 4.1 `users` table
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phone           TEXT UNIQUE NOT NULL,
    email           TEXT UNIQUE,
    password_hash   TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 `user_profiles` table  
*(Onboarding fields — grows as user fills them in)*
```sql
CREATE TABLE user_profiles (
    user_id             INTEGER PRIMARY KEY REFERENCES users(id),
    full_name           TEXT,
    company_name        TEXT,
    address_line1       TEXT,
    address_line2       TEXT,
    city                TEXT,
    state               TEXT,
    pincode             TEXT,
    membership_type     TEXT,       -- "Hot Desk" | "Dedicated Desk" | "Private Office"
    billing_cycle       TEXT,       -- "Monthly" | "Quarterly" | "Annual"
    start_date          DATE,
    gstin               TEXT,
    onboarding_step     TEXT DEFAULT 'full_name',  -- current pending field
    onboarding_complete BOOLEAN DEFAULT FALSE,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 `sessions` table
```sql
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,   -- UUID token
    user_id     INTEGER REFERENCES users(id),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 `conversations` table
```sql
CREATE TABLE conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    role        TEXT NOT NULL,       -- "user" | "assistant"
    content     TEXT NOT NULL,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.5 `payments` table
```sql
CREATE TABLE payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    amount          REAL,
    membership_type TEXT,
    billing_cycle   TEXT,
    status          TEXT DEFAULT 'pending',  -- "pending" | "success" | "failed"
    txn_ref         TEXT,
    initiated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Knowledge Base & RAG Pipeline

### 5.1 KB Structure Expected
Your existing markdown KB has 8 categories:
```
1. Pre-Sales (FAQs, trial visits)
2. Booking (process, lead time)
3. Pricing & Plans
4. Billing & Invoicing (GST compliance)
5. Onboarding (documentation, access)
6. Amenities & Facilities
7. Membership Management (upgrades, cancellations)
8. Escalations
```
Place the file at `backend/knowledge_base/cowork_kb.md`.

### 5.2 Ingestion Script (`ingest_kb.py`)
```
Run once (or on KB update):

1. Read cowork_kb.md
2. Split by markdown headers (##, ###) → semantic chunks
3. Each chunk gets metadata: { category, heading, source: "KB" }
4. Embed each chunk via sentence-transformers  
   (model: "all-MiniLM-L6-v2" — runs locally, free)
5. Upsert into ChromaDB collection "cowork_kb"
```
Command:
```bash
python backend/scripts/ingest_kb.py
```

### 5.3 RAG Service Logic (`rag_service.py`)
```python
def retrieve_context(query: str, top_k: int = 4) -> str:
    """
    Embed query → similarity search ChromaDB → return top_k chunks as string
    """
    results = collection.query(query_texts=[query], n_results=top_k)
    return "\n\n---\n\n".join(results["documents"][0])
```

### 5.4 Anti-Hallucination: Pricing Gate
**System prompt must include:**
```
PRICING RULE: You MUST only state prices, plans, or fees that appear 
word-for-word in the CONTEXT block below. If a price is not in the context, 
say exactly: "I'd need to double-check that — our team can confirm pricing 
for you." Never invent or estimate a price.
```
The RAG retriever will be biased toward pricing chunks when queries contain
keywords: price, cost, fee, plan, rate, charge, per month, per day.

---

## 6. LLM Service (`llm_service.py`)

### 6.1 System Prompt Builder
```python
def build_system_prompt(context: str, user_profile: dict, mode: str) -> str:
    base = """You are Aria, the friendly customer assistant for [CoworkSpace Name].
You help members with bookings, pricing, amenities, and onboarding.
Be warm, concise, and professional. Never make up information.

CONTEXT (from knowledge base):
{context}

PRICING RULE: Only state prices found verbatim in CONTEXT. If not there, 
say you'll check with the team.
""".format(context=context)

    if mode == "onboarding":
        next_field = user_profile.get("onboarding_step")
        base += f"""
ONBOARDING MODE: You are currently collecting the user's '{next_field}'.
Ask ONLY for this one field. Be conversational. Validate before moving on.
Do not ask for any other information in this turn.
"""
    return base
```

### 6.2 OpenRouter Call
```python
import httpx

OPENROUTER_API_KEY = config.OPENROUTER_API_KEY
MODEL = "mistralai/mistral-7b-instruct"   # swap freely via config

async def call_llm(messages: list, system_prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json=payload,
            timeout=30
        )
    return r.json()["choices"][0]["message"]["content"]
```

---

## 7. Onboarding State Machine

### 7.1 Field Sequence
```
full_name → email → phone → company_name → 
address_line1 → address_line2 → city → state → pincode →
membership_type → billing_cycle → start_date → 
gstin (optional) → [PAYMENT GATEWAY] → COMPLETE
```

### 7.2 Resumption Logic
On every `/chat` call:
```python
def get_chat_mode(profile: UserProfile) -> str:
    if not profile.onboarding_complete:
        return "onboarding"
    return "general"
```

When mode is `onboarding`, the bot ignores general Q&A and only asks for
the next pending field (`profile.onboarding_step`). After validation, it
updates the DB and advances `onboarding_step` to the next field.

### 7.3 Validation Rules Per Field
| Field | Validation |
|-------|-----------|
| email | regex email format |
| phone | 10-digit Indian mobile |
| pincode | 6-digit numeric |
| membership_type | must match: Hot Desk / Dedicated Desk / Private Office |
| billing_cycle | must match: Monthly / Quarterly / Annual |
| start_date | date ≥ today |
| gstin | regex `[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}` or skip |

### 7.4 Sample Conversation Flow
```
Bot:  "Welcome back! Let's continue your registration.
       What's your email address?"

User: "pranav@example.com"

Bot:  "Got it. And your company name? (or type 'Individual' if registering personally)"

User: "Antigravity Labs"

Bot:  "Great! Now your full address — starting with address line 1 (building / flat number)?"
```
*(Each turn = one field. The bot never bundles two fields in a single ask.)*

---

## 8. Dummy Payment Gateway

### 8.1 Flow
```
1. After all onboarding fields collected, bot says:
   "You're all set! Here's your plan summary: [Dedicated Desk · Monthly · ₹X]
    Shall I proceed with payment?"

2. User: "Yes"

3. Bot triggers /payment/initiate → creates payment record (status: pending)
   → returns a "mock payment link" displayed in Streamlit as a button

4. Streamlit shows: [💳 Pay ₹X — Test Mode]
   Click → POST /payment/confirm with { txn_ref, mock_result: "success" | "fail" }

5. On success → payment.status = "success", profile.onboarding_complete = True
   Bot: "🎉 Payment confirmed! Your membership starts on [date]. 
         Your welcome kit will be sent to [email]."

6. On fail  → bot: "It seems the payment didn't go through. Want to try again?"
```

### 8.2 Mock Payment Endpoint
```python
@router.post("/payment/confirm")
def confirm_payment(body: PaymentConfirmRequest, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter_by(txn_ref=body.txn_ref).first()
    # Dummy: 80% success rate or use body.mock_result directly
    result = body.mock_result or random.choice(["success", "success", "success", "fail"])
    payment.status = result
    if result == "success":
        profile = db.query(UserProfile).filter_by(user_id=payment.user_id).first()
        profile.onboarding_complete = True
    db.commit()
    return {"status": result, "txn_ref": body.txn_ref}
```

---

## 9. FastAPI Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create user, create blank profile |
| POST | `/auth/login` | Verify credentials → return session token |
| GET | `/auth/me` | Return user profile from session |
| POST | `/chat` | Main chat: RAG + LLM + session history |
| GET | `/onboarding/status` | Current step + % complete |
| POST | `/onboarding/validate` | Validate a single field value |
| POST | `/payment/initiate` | Create pending payment record |
| POST | `/payment/confirm` | Resolve dummy payment |
| GET | `/history` | Last N messages for current session |

---

## 10. Streamlit Frontend (`app.py`)

### 10.1 Pages / States
```
if "session_token" not in st.session_state:
    → Show Login / Register page

elif not profile.onboarding_complete:
    → Show Chat (onboarding mode) + progress bar

else:
    → Show full Chat (general assistant mode)
```

### 10.2 UI Components
```
┌──────────────────────────────────────────────────────┐
│  🏢 CoworkBot — Aria                      [Logout]  │
├──────────────────────────────────────────────────────┤
│  Onboarding Progress: ████████░░░░  65%             │
│  (shown only during onboarding)                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [assistant] Hi! What's your full name?              │
│  [user]      Pranav Mehta                            │
│  [assistant] Great, Pranav! What's your email?       │
│                                                      │
├──────────────────────────────────────────────────────┤
│  [ Type a message...                      ] [Send]  │
└──────────────────────────────────────────────────────┘
```

### 10.3 Payment UI
```python
if st.session_state.get("payment_pending"):
    st.info("💳 Test Payment Gateway")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Pay ₹X (Simulate Success)"):
            # call /payment/confirm with mock_result="success"
    with col2:
        if st.button("❌ Simulate Failure"):
            # call /payment/confirm with mock_result="fail"
```

---

## 11. Environment & Configuration (`.env`)

```env
OPENROUTER_API_KEY=sk-or-...
MODEL_ID=mistralai/mistral-7b-instruct       # or openai/gpt-4o-mini, etc.
SQLITE_DB_PATH=./backend/db/cowork.db
CHROMA_DB_PATH=./backend/db/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2
SECRET_KEY=your-jwt-secret-here
```

---

## 12. `requirements.txt`

```
fastapi
uvicorn
streamlit
httpx
sqlalchemy
chromadb
sentence-transformers
langchain                    # for text splitter only
python-jose[cryptography]    # JWT session tokens
passlib[bcrypt]              # password hashing
python-dotenv
pydantic
```

---

## 13. Implementation Phases

### Phase 1 — Foundation (Day 1–2)
- [ ] Set up project structure, `.env`, config
- [ ] SQLite models + Alembic migrations (or `Base.metadata.create_all`)
- [ ] `/auth/register` and `/auth/login` with bcrypt + JWT session
- [ ] Basic Streamlit login/register page

### Phase 2 — RAG Pipeline (Day 2–3)
- [ ] Place `cowork_kb.md` in `knowledge_base/`
- [ ] Write and run `ingest_kb.py` (chunk → embed → ChromaDB)
- [ ] `rag_service.py` with `retrieve_context(query)`
- [ ] Test retrieval manually with pricing queries

### Phase 3 — Chat Endpoint (Day 3–4)
- [ ] `/chat` endpoint: load history → RAG → build prompt → OpenRouter → save reply
- [ ] System prompt with pricing gate
- [ ] Session history (last 10 turns sent to LLM for context)
- [ ] Streamlit chat UI wired to backend

### Phase 4 — Onboarding State Machine (Day 4–5)
- [ ] `onboarding_service.py`: `get_next_field()`, `validate_field()`, `advance_step()`
- [ ] Bot detects onboarding mode, asks for one field at a time
- [ ] Resume logic: on login, check `onboarding_step` → resume from that field
- [ ] Progress bar in Streamlit

### Phase 5 — Dummy Payment Gateway (Day 5–6)
- [ ] `/payment/initiate` and `/payment/confirm`
- [ ] Plan summary display in chat
- [ ] Streamlit payment buttons (success/fail simulation)
- [ ] On success → `onboarding_complete = True` → unlock general chat

### Phase 6 — Polish & Testing (Day 6–7)
- [ ] Edge cases: empty messages, invalid field values, session expiry
- [ ] Test pricing retrieval — confirm no hallucinated numbers
- [ ] Test onboarding resume (quit mid-flow → re-login → resumes correctly)
- [ ] README + run instructions

---

## 14. Key Design Decisions & Rationale

| Decision | Why |
|----------|-----|
| SQLite over Postgres | Zero infra overhead for testing; swap to Postgres by changing connection string |
| ChromaDB over Pinecone | Local, persistent, no API key; production swap = 1 line change |
| `all-MiniLM-L6-v2` embeddings | Runs fully offline, fast, good quality for English text |
| OpenRouter over direct API | Model-agnostic; swap Mistral → GPT-4o → Claude with one env var |
| Onboarding as DB state (not LLM memory) | LLMs forget; DB never does. Resumption is deterministic |
| Pricing gate in system prompt | Prevents any confabulated number reaching the user |
| Session token in Streamlit `st.session_state` | Lightweight; survives tab refresh within same browser session |

---

## 15. Swap-Out Map (for Production)

| Testing Component | Production Replacement |
|-------------------|----------------------|
| SQLite | PostgreSQL (change `DATABASE_URL`) |
| ChromaDB (local) | Pinecone / Weaviate / Qdrant |
| Dummy payment | Razorpay / Stripe SDK |
| JWT in-memory sessions | Redis session store |
| `all-MiniLM-L6-v2` | OpenAI `text-embedding-3-small` or Cohere |

---

*No knowledge base file was attached to this message — place your existing 8-category cowork KB markdown at `backend/knowledge_base/cowork_kb.md` before running `ingest_kb.py`.*