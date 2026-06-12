# Technical Work Log: Hoblix WhatsApp Automation

This document outlines all technical changes, refactors, and bug fixes implemented today to improve the CRM integration, chatbot conversational flow, and data extraction pipeline.

## 1. CRM API Migration & Fallback Handling
- **Endpoint Migration:** Updated the CRM endpoint across the application from the deprecated Cloudflare Pages URL (`cowork-space-manager.pages.dev`) to the newly deployed Render instance (`hoblix-crm-api.onrender.com`).
- **Conflict Handling (Upsert):** Verified the progressive update architecture. When a `POST /public/leads` request returns a `409 Conflict` (meaning the `externalId` already exists), the system safely catches the exception and falls back to `PATCH /public/leads/{externalId}`.
- **Testing Script:** Updated `test_crm.py` to explicitly test both the `POST` creation and the `PATCH` fallback flow to guarantee reliability.

## 2. LLM System Prompt Optimization
- **Conciseness Enforcement:** Restructured `build_system_prompt` in `backend/services/llm_service.py` with strict instructions for Aria to remain concise, eliminating conversational filler and restricting responses to 1-2 short sentences.
- **Anti-Hallucination Guardrails:** Added a `PRICING EXACTNESS` rule that explicitly forces the LLM to differentiate between the "Single Day Pass", "5-Day Pass", and "7-Day Pass". It is forbidden from guessing prices.
- **Formatting Constraints:** Instructed the LLM to stop using the em dash ("—") entirely, forcing the use of standard commas and periods.
- **Single Question Rule:** Added a strict constraint in Onboarding Mode requiring the LLM to only ask **one** question at a time. It is forbidden from asking multiple follow-up questions in the same message.

## 3. Dynamic Onboarding Refactor (State Machine Removal)
- **Previous Architecture:** The onboarding flow was a strict sequential state machine (`full_name` -> `spaceType` -> `seatRange` -> `location`). The bot could only extract the exact field it asked for, making it feel robotic.
- **New Architecture:** We ripped out the strict ordering and implemented a dynamic data extraction pipeline.
  - **`extract_missing_fields`:** Replaced the single-field extractor with a multi-field JSON extractor. If the user provides multiple details in one message (e.g., "I'm Rahul, I want a private cabin in Dwarka"), the LLM detects and extracts all of them simultaneously.
  - **Conversational Prompting:** `backend/routers/chat.py` now calculates an array of `missing_fields` and passes it to the LLM. The prompt instructs the bot to naturally steer the conversation towards these missing fields rather than demanding them in a fixed order.

## 4. Bug Fixes
- **AttributeError Fix:** Resolved a crash in `backend/routers/chat.py` (`'UserProfile' object has no attribute 'seatRange'`) caused by iterating over the virtual field `"seatRange"`. Mapped it correctly to check `profile.seatRangeMin` instead.

## 5. Knowledge Base Updates
- **Clarification:** Renamed "Day Pass" to "Single Day Pass" to prevent the LLM from confusing it with the 5-Day Pass.
- **Amenities Update:** Added information about the Hoblix on-site cafeteria (snacks, Maggie, cold drinks) and Quick Commerce delivery to `backend/knowledge_base/cowork_kb.md`.
- **Vector DB Reingestion:** Re-ran `backend/scripts/ingest_kb.py` to flush the ChromaDB instance and embed the newly updated markdown knowledge base.
