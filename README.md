<p align="center">
  <img src="static/logo.png" width="120" alt="WithYou logo"/>
</p>

# WithYou — AI Voice Companion

> **You don't have to go through it alone.**

A private AI companion for people navigating grief, illness, anxiety, trauma, and life transitions. Select a support type, speak freely. CE listens, responds with empathy, and speaks back.

---

## What It Does

- **12 support types** — grief, illness, trauma, anxiety, relationship, loneliness, caregiver, depression, life transition, health fear, addiction, self-worth
- **Voice-first** — speak to CE, CE speaks back. No typing required.
- **Empathic responses** — grounded in the support type you chose, never clinical
- **Private by design** — no conversation history stored. Page refresh wipes everything.

---

## How It Works

```
User selects support type
  ↓ CE plays a pre-written opener (ElevenLabs TTS)
  ↓ User speaks (browser mic)
  ↓ POST /api/transcribe → OpenAI Whisper → text
  ↓ POST /api/chat → Google Gemini 2.0 Flash → reply
  ↓ POST /api/speak → ElevenLabs → audio
  ↓ CE speaks the reply aloud
  ↓ Repeat
```

---

## Stack

Python · Flask · OpenAI Whisper · Google Gemini 2.0 Flash · ElevenLabs TTS · Vanilla JS

Deployed on Railway. Live at [empathy.creativekonsoles.com](https://empathy.creativekonsoles.com)

---

## Setup

```bash
git clone https://github.com/papjamzzz/empathybot.git
cd empathybot
cp .env.example .env
# Add OPENAI_API_KEY, GEMINI_API_KEY, ELEVENLABS_API_KEY
make setup
make run
```

Opens at `http://127.0.0.1:5564`

---

## Part of Creative Konsoles

Built by [Creative Konsoles](https://creativekonsoles.com) — tools built using thought.

**[creativekonsoles.com](https://creativekonsoles.com)** &nbsp;·&nbsp; support@creativekonsoles.com

<!-- repo maintenance: 2026-05-12 -->
