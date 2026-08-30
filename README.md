<div align="center">

<pre>
 ____    _    _   _____ _  _ ___    ___  _  _ ___
/ ___|  / \  / \ |_   _| || |_ _| / _ \| \| | __|
\__ \ / _ \/ _ \  | | | __ || | | (_) | .` | _|
|___//_/ \_\/ \_\ |_| |_||_|___| \___/|_|\_|___|
</pre>

### 🎙️ *One Business · One Number · One Autonomous AI Employee*

<br/>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3-FF6B35?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

<br/>

> **SAATHI ONE** is a fully autonomous, multilingual AI voice receptionist platform for Indian small businesses.
> It handles phone calls, bookings, and customer queries — **24/7**, in **Hindi, English & Marathi** —
> with **zero human intervention**.

<br/>

[🚀 Quick Start](#-quick-start) &nbsp;·&nbsp; [✨ Features](#-features) &nbsp;·&nbsp; [🏗️ Architecture](#-architecture) &nbsp;·&nbsp; [📦 Tech Stack](#-tech-stack) &nbsp;·&nbsp; [🎯 Demo](#-demo)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎙️ Hands-Free Voice Calls
Natural phone-style conversations — no buttons, no clicks. Just talk. The AI listens, thinks, and speaks back like a real human receptionist.

</td>
<td width="50%">

### 🧠 Domain-Aware AI Brain
Restaurant AI asks about party size & dietary needs. Clinic AI asks about symptoms. Salon AI asks about stylists. Each business type has a unique AI personality.

</td>
</tr>
<tr>
<td width="50%">

### 📅 Real-Time Booking Engine
Checks live availability, prevents double-bookings, confirms reservations, and saves everything to MongoDB Atlas — all during the voice call.

</td>
<td width="50%">

### 🌐 Multilingual — Hindi First
Speaks Hindi, English, Marathi and Hinglish naturally. Uses warm Indian fillers: *"Ji haan", "Bilkul", "Ek moment", "Theek hai", "Zaroor"*.

</td>
</tr>
<tr>
<td width="50%">

### ⚡ Sub-200ms AI Responses
Powered by **Groq LLaMA** — the world's fastest LLM inference engine. Zero lag conversation — feels like a real phone call.

</td>
<td width="50%">

### 🏢 Multi-Tenant Platform
One platform, unlimited businesses. Each owner has isolated data, a dedicated AI employee, and a unique demo phone number.

</td>
</tr>
</table>

---

## 🎯 Demo

### Two-Window Architecture in Action

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│      🏢  OWNER PANEL            │     │      📞  CLIENT CALL PANEL        │
│   (Business Owner logs in)      │     │   (Customer dials demo number)    │
│                                 │     │                                   │
│  Business: Yash Royal Dine      │     │  Demo Number: [ DEMO-9001 ]       │
│  Type:     Restaurant 🍽️        │     │                 [📞 CALL]         │
│  Hours:    09:00 - 23:00        │     │                                   │
│  Services: Dinner Table ₹0      │     │  ┌─────────────────────────────┐  │
│            Party Table ₹1000    │     │  │  🎙️  Maya — AI Receptionist │  │
│            VIP Cabin   ₹2500    │     │  │  ● LIVE  ⏱ 02:34            │  │
│                                 │     │  │                             │  │
│  ┌──────────────────────────┐   │     │  │ Maya: "Namaste! Yash Royal  │  │
│  │  📞 YOUR DEMO NUMBER     │   │     │  │  Dine mein aapka swagat    │  │
│  │                          │   │     │  │  hai. Kaise help karoon?"  │  │
│  │      DEMO-9001           │   │────▶│  │                            │  │
│  │                          │   │     │  │ You: "2 logon ke liye kal  │  │
│  └──────────────────────────┘   │     │  │  table chahiye"            │  │
│                                 │     │  │                             │  │
│  📅 Today's Bookings: 12        │     │  │ 🎉 APPOINTMENT CONFIRMED!  │  │
│  👥 Total Clients: 47           │     │  │    Ref: BK-E17D7BAB        │  │
│  💬 AI Calls Today: 8           │     │  └─────────────────────────────┘  │
│                                 │     │  ████████████  HOLD TO END CALL  │
└─────────────────────────────────┘     └──────────────────────────────────┘
```

### Pre-Loaded Demo Businesses

| Demo Number | Business | Type |
|-------------|----------|------|
| `DEMO-9001` | Yash Royal Dine Restaurant | 🍽️ Restaurant |
| `DEMO-9002` | Mumbai Royal Barbers & Salon | 💇 Salon |
| `DEMO-9003` | Dr. Patil Multi-Speciality Clinic | 🏥 Clinic |

**Demo login:** `demo@saathi.ai` / `demo123`

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────────┐
                    │         Browser (Chrome/Edge)    │
                    │                                  │
                    │   ┌──────────┐  ┌─────────────┐ │
                    │   │  Owner   │  │ Phone Call  │ │
                    │   │  Panel   │  │  Panel      │ │
                    │   └────┬─────┘  └──────┬──────┘ │
                    └────────┼───────────────┼─────────┘
                             │               │
                             │        ┌──────▼──────────┐
                             │        │  Web Speech API  │ ← Customer Voice
                             │        │  SpeechSynthesis │ → AI Voice Out
                             │        └──────┬──────────┘
                             │               │ text / audio
                             │        ┌──────▼──────────┐
                             │        │  FastAPI :8000   │
                             │        │  /api/call/*    │
                             │        └──────┬──────────┘
                             │               │
                             │        ┌──────▼──────────┐
                             │        │   Groq LLaMA 3   │ ~200ms response
                             │        │   Tool Calling   │
                             │        └──────┬──────────┘
                             │               │
                    ┌────────▼───────────────▼─────────┐
                    │          MongoDB Atlas             │
                    │    businesses / bookings / users  │
                    └──────────────────────────────────┘
```

---

## 📦 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🖥️ **Web App** | Streamlit 1.x | Main UI framework |
| 🎨 **Frontend** | HTML + CSS + JavaScript | Custom phone call interface |
| 🎤 **Voice Input** | Web Speech API (browser) | Free speech-to-text, no API cost |
| 🔊 **Voice Output** | SpeechSynthesis API | Free TTS with Google hi-IN voice |
| ⚡ **AI Engine** | Groq + LLaMA 3 | World's fastest LLM inference |
| 🛠️ **Tool Calling** | OpenAI-compatible FC | check_availability, create_booking |
| 🌐 **REST API** | FastAPI + Uvicorn | Call session management |
| 🗄️ **Database** | MongoDB Atlas | Cloud multi-tenant data store |
| 🔐 **Auth** | bcrypt + Streamlit sessions | Secure owner authentication |

---

## 📂 Project Structure

```
saathi_one/
├── 📄 app.py               ← Streamlit UI + embedded phone call component
├── 📄 api.py               ← FastAPI backend (call start/message/end)
├── 📄 config.py            ← API keys, models, constants
├── 📄 database.py          ← MongoDB Atlas connection & collections
├── 📄 auth.py              ← Login / signup / session management
├── 📄 models.py            ← DB document schema helpers
│
├── 🤖 ai/
│   ├── groq_agent.py       ← AI brain: Groq LLaMA + tool calling loop
│   ├── prompts.py          ← Per-domain system prompts
│   └── tools.py            ← AI tools: availability, booking, services
│
├── 📅 booking/
│   └── engine.py           ← Slot logic, overlap detection, references
│
├── 📞 telephony/
│   └── provider.py         ← DEMO-XXXX number management
│
├── 🎨 ui/
│   ├── styles.py           ← Glassmorphism CSS, holographic animations
│   └── components.py       ← Reusable Streamlit UI components
│
└── 🧪 tests/
    ├── test_saathi.py       ← Core unit tests
    ├── test_multilingual.py ← Language detection tests
    └── test_e2e_simulation.py ← Full booking flow simulation
```

---

## 🚀 Quick Start

### Prerequisites

```
Python 3.12+        → https://python.org
MongoDB Atlas       → https://mongodb.com/atlas (free tier)
Groq API Key        → https://console.groq.com (free)
Chrome or Edge      → Required for voice features
```

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/saathi-one.git
cd saathi-one/saathi_one
pip install -r requirements.txt
```

### 2. Configure .env

```env
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/saathi_one
DATABASE_NAME=saathi_one
```

### 3. Start Backend

```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

### 4. Start Web App

```bash
streamlit run app.py --server.port 8501
```

### 5. Open Browser

```
http://localhost:8501
```

> 💡 Use **Google Chrome** or **Microsoft Edge** for best voice support.

---

## 🎭 Supported Business Domains

| Domain | What the AI Handles |
|--------|---------------------|
| 🍽️ Restaurant | Table reservations, party bookings, menu queries, dietary needs |
| 💇 Salon | Appointment slots, stylist selection, service pricing |
| 💈 Barber Shop | Haircut booking, stylist preference, wait times |
| 🏥 Clinic | Doctor consultations, specialty selection, health queries |
| 🦷 Dental | Treatment types, emergency vs routine, appointments |
| 🏨 Hotel | Room availability, check-in/out dates, amenity queries |
| 🏋️ Gym | Membership plans, trainer booking, trial sessions |
| 💼 Consultant | Topic discussion, session scheduling, rates |
| 🔧 Repair Shop | Device issues, pickup/delivery, quotes |

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `POST` | `/api/call/start` | Start a new AI call session |
| `POST` | `/api/call/message` | Send speech text, receive AI reply |
| `POST` | `/api/call/end` | End call and save transcript |

**Start a Call:**
```bash
curl -X POST http://localhost:8000/api/call/start \
  -H "Content-Type: application/json" \
  -d '{"demo_number": "DEMO-9001"}'
```

```json
{
  "call_id": "call_abc123",
  "business_name": "Yash Royal Dine Restaurant",
  "ai_name": "Maya",
  "greeting": "Namaste! Yash Royal Dine mein aapka swagat hai!",
  "language": "hi"
}
```

---

## 🔒 Security

- ✅ Passwords hashed with **bcrypt** (never stored as plaintext)
- ✅ Full **tenant isolation** — owners only see their own data
- ✅ All MongoDB queries scoped by `business_id`
- ✅ API keys stored in `.env` (git-ignored)
- ✅ No sensitive data exposed in browser JavaScript

---

## 🧪 Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Individual suites
python tests/test_saathi.py           # 6 core unit tests
python tests/test_multilingual.py     # Language detection
python tests/test_e2e_simulation.py   # End-to-end booking flow
```

---

## 🙏 Built With

| Tool | Why |
|------|-----|
| [Groq](https://groq.com) | World's fastest LLM inference — 200ms responses |
| [Streamlit](https://streamlit.io) | Rapid Python web apps with beautiful UI |
| [FastAPI](https://fastapi.tiangolo.com) | Lightning-fast async Python APIs |
| [MongoDB Atlas](https://mongodb.com/atlas) | Zero-ops cloud database |
| [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) | Free browser-native voice |

---

## 📜 License

```
MIT License — Use freely, build boldly.
Copyright (c) 2026 SAATHI ONE
```

---

<div align="center">

**Built with ❤️ for Indian small businesses**

*"Ek AI employee jo kabhi thakta nahi, kabhi chutti nahi leta, aur 24/7 kaam karta hai."*

*An AI employee who never gets tired, never takes leave, and works 24/7.*

<br/>

⭐ **If SAATHI ONE helped you, give it a star!** ⭐

</div>
