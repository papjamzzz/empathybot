# WithYou (empathybot) — Re-Entry File
*Claude: read this before touching anything.*

---

## What This Is
**WithYou** — an AI voice companion for people going through hard times. Product was renamed from "Cognitive Empathies" to WithYou. User selects a support type (grief, anxiety, trauma, etc.) and speaks freely. The companion (named CE) listens, responds with empathy, and speaks back using text-to-speech. Built on three separate AI services.

**Live at:** https://empathy.creativekonsoles.com

## Re-Entry Phrase
> "Re-entry: empathybot"

## Current Status
✅ Private alpha baseline — FROZEN as of 2026-04-06

**DO NOT modify without explicit instruction:**
- BASE_SYSTEM prompt
- Any SUPPORT_CONTEXT entry
- Any opener line (getOpener in index.html)
- Hero copy (eyebrow, h1, subtitle)
- Brand name (WithYou) or companion name (CE)

Next step is real human QA testing, not more prompt changes.

---

## Stack

| Layer | Service | Detail |
|-------|---------|--------|
| Server | Python + Flask | Port 5564 locally, Railway in prod |
| STT | OpenAI Whisper (`whisper-1`) | Audio blob → transcript text |
| Chat | Google Gemini 2.0 Flash | Text in, text out — non-streaming JSON |
| TTS | ElevenLabs (`eleven_monolingual_v1`) | Text → audio/mpeg, voice: Rachel (`21m00Tcm4TlvDq8ikWAM`) |
| Frontend | Single HTML template | All CSS and JS inline in `templates/index.html` |

**UI:** Dark theme, Inter font, CSS variables, purple/lavender accent (`#b794f4`)

---

## File Structure

```
empathybot/
├── app.py                  ← Flask entry point: all routes, AI clients, support type data, system prompts
├── templates/index.html    ← Entire UI: HTML + all inline CSS + all inline JS (~650 lines)
├── static/
│   ├── logo.png            ← Header logo (onerror fallback if missing)
│   └── favicon.png         ← Browser tab icon
├── data/                   ← Empty, reserved for future use
├── requirements.txt        ← flask, python-dotenv, requests, google-generativeai, openai, elevenlabs, gunicorn
├── Procfile                ← Railway: `web: gunicorn app:app`
├── railway.json            ← Railway deployment config
├── runtime.txt             ← Python version pin
├── Makefile
├── launch.command          ← Mac local launcher
├── .env                    ← API keys (never commit)
└── .env.example
```

---

## Request Flow

```
1. User selects a support type (select screen)
   → CE plays a pre-written opener via ElevenLabs TTS
   → UI transitions to voice screen

2. User taps mic button
   → browser MediaRecorder captures audio (audio/webm)
   → POST /api/transcribe → OpenAI Whisper → returns transcript text

3. Transcript sent to backend
   → POST /api/chat → Gemini 2.0 Flash
   → system prompt = BASE_SYSTEM + support type context (coaching hardcoded to '')
   → returns reply text as JSON (non-streaming)

4. Reply text sent to TTS
   → POST /api/speak → ElevenLabs → returns audio/mpeg blob
   → browser plays audio via Web Audio API
   → transcript and reply text displayed on screen

5. Cycle repeats — all conversation history held in browser state only
```

---

## Environment Variables

```
OPENAI_API_KEY=sk-...          # Whisper STT
GEMINI_API_KEY=...             # Gemini 2.0 Flash chat
ELEVENLABS_API_KEY=...         # TTS
```

All three are required. App will fail silently or with 500 errors if any are missing.

---

## How to Run Locally

```bash
cd ~/empathybot && make setup && make run
```

Runs at http://127.0.0.1:5564

---

## GitHub + Deploy

- Repo: `papjamzzz/empathybot`
- Push: `make m="your message" push`
- Production: Railway, auto-deploys from `main` branch

---

## UI Flow (2 screens)

```
Screen 1 — Select
  ↓ User picks support type (12 options)

Screen 2 — Voice
  ↓ CE speaks opener
  ↓ User taps mic → speaks → taps again
  ↓ CE transcribes → thinks → responds → speaks
  ↓ Repeat
  ↓ "Start Over" returns to Screen 1
```

**Note:** A coaching screen (Screen 2 in an earlier design) was removed. The `coaching` parameter still exists in `/api/chat` but is hardcoded to `''` in the frontend JS — it does nothing currently.

---

## Support Types (12)

`grief`, `illness`, `trauma`, `anxiety`, `relationship`, `loneliness`, `caregiver`, `depression`, `transition`, `health_fear`, `addiction`, `self_worth`

Each has: a label, icon, short description (card), a context string injected into the system prompt, and a pre-written opener CE speaks on entry.

---

## Known Technical Risks

| Risk | Location | Severity |
|------|----------|----------|
| **Safari/iOS webm** — MediaRecorder outputs `audio/webm`; Safari uses a different codec. Voice input may silently fail on iPhone. | `index.html` — `startListening()` | High |
| **No session persistence** — All conversation state lives in browser JS. Page refresh wipes the entire conversation. | `index.html` — `state` object | Medium |
| **Three paid API dependencies** — Any one of Whisper, Gemini, or ElevenLabs going down breaks the core loop. No fallbacks. | `app.py` | Medium |
| **Silent API failures** — `/api/chat` and `/api/transcribe` have no retry logic. Errors surface as generic catch blocks in JS. | `index.html` — `processAudio()` | Medium |
| **TTS failure UX** — When ElevenLabs fails, the app now shows a fallback message (`"CE responded above — audio didn't load this time."`) and displays the text reply. Previously silent. | `index.html` — `speakText()` catch | Low (fixed) |
| **All CSS/JS inline** — `templates/index.html` is ~660 lines with no separation of concerns. Edits require careful attention to avoid collisions. | `index.html` | Low |
| **`coaching` dead code** — Backend accepts and processes a `coaching` parameter; frontend always sends `''`. | `app.py` `build_system_prompt()`, `index.html` line ~513 | Low |

---

## What's Done

- [x] Flask app with 3-service AI pipeline (Whisper → Gemini → ElevenLabs)
- [x] 12 support types with per-type system prompts and opener lines
- [x] 2-screen UI: support type select → voice conversation
- [x] Mic button with animated orb rings (idle / listening / speaking / processing states)
- [x] fetchWithTimeout on all 3 API calls (20s / 15s / 25s)
- [x] MAX_HISTORY = 20 message cap
- [x] Safari/iOS mime type detection (audio/mp4 fallback)
- [x] All error states surface with distinct messages (mic blocked, empty audio, timeout, TTS fail)
- [x] TTS fallback: shows text + warm pink error when audio fails
- [x] Crisis note + disclosure merged into single footer line
- [x] Renamed to WithYou (2026-04-06)
- [x] Full content quality pass: all 12 card descriptions, opener lines, support contexts (2026-04-06)
- [x] Transcript realism pass: BASE_SYSTEM explicit phrase bans, clinical vocab bans, behavior-explanation bans (2026-04-06)
- [x] Live QA over-correction fixes: restraint-announcing ban, "[X] is real" ban, somatic question ban (2026-04-06)
- [x] Manual QA checklist produced (2026-04-06)

## What's Next

**Before sharing with anyone:**
- [ ] iPhone Safari: confirm voice record + playback works on a real device
- [ ] Run Top 10 Must-Test Prompts from QA plan
- [ ] Confirm TTS fallback shows text correctly when ElevenLabs fails

**After first human feedback:**
- [ ] Session persistence (localStorage)
- [ ] V2: subscription/payment layer
- [ ] V2: more support types (roadmap: 100+)

---

*Last updated: 2026-04-06 — Renamed to WithYou; private alpha baseline frozen; QA plan complete*
