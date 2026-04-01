# empathybot — Re-Entry File
*Claude: read this before touching anything.*

---

## What This Is
Empathetic AI chatbot for grief, illness, and trauma support. Single Claude model, carefully voiced. User selects support type → coaches the bot → chats. Built to expand to 100+ support types. Subscription product roadmap.

## Re-Entry Phrase
> "Re-entry: empathybot"

## Current Status
✅ V1 complete — fully functional, ready to test and push to GitHub

## Stack
- Python + Flask, port 5564, host 127.0.0.1
- Anthropic SDK (claude-sonnet-4-6) — streaming responses via SSE
- Dark theme, Inter font, CSS variables, purple/lavender accent (#b794f4)
- Logo at /static/logo.png

## File Structure
```
empathybot/
├── app.py                  ← Flask + Anthropic API, 12 support types, streaming /api/chat
├── templates/index.html    ← Full 3-screen UI: select → coach → chat
├── static/                 ← logo.png goes here
├── data/
├── requirements.txt        ← flask, python-dotenv, requests, anthropic
├── Makefile
├── launch.command
├── .env                    ← ANTHROPIC_API_KEY
└── .env.example
```

## How to Run
```bash
cd ~/empathybot && make setup && make run
```

## Environment
```
ANTHROPIC_API_KEY=sk-ant-...
```

## GitHub
- Repo: papjamzzz/empathybot
- Push: `make m="your message" push`

## What's Done
- [x] Project scaffold created
- [x] Flask app with Anthropic streaming chat
- [x] 12 support types (grief, illness, trauma, anxiety, relationship, loneliness, caregiver, depression, transition, health fear, addiction, self-worth)
- [x] 3-screen UI: support type select → coaching → chat
- [x] Coaching chips (quick one-click voice preferences)
- [x] Streaming SSE response with typing indicator
- [x] Empathetic system prompts per support type
- [x] User coaching layered into system prompt
- [x] Crisis note (988) in chat footer
- [x] Restart flow

## What's Next
- [ ] Add logo to static/
- [ ] Push to GitHub (papjamzzz/empathybot)
- [ ] Add to Launcher hub
- [ ] V2: session memory, multiple conversations, saved preferences
- [ ] V2: subscription/payment layer

## Key Technical Decisions
- localhost only (host=127.0.0.1)
- Streaming SSE so responses feel human-paced
- System prompt = base empathy voice + support type context + user coaching (layered)
- No conversation history persisted server-side — all state in browser

---
*Last updated: 2026-04-01*
