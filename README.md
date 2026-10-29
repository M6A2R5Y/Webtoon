# VibeMotion AI — Short-Form AI Video Studio

A full-stack AI Short-Video Generator web application built with **Next.js (React + TypeScript + Tailwind CSS)** on the frontend and **Python FastAPI + SQLAlchemy** on the backend.

## Core Features
1. **Text-to-Video & Image-to-Video:** Generate short AI clips from scene descriptions or uploaded reference images.
2. **AI Prompt Enhancer:** Transforms simple ideas into director-grade video prompts (camera movements, lighting, subject motion, and style presets).
3. **Aspect Ratios, Durations & Styles:** Supports `9:16` (TikTok/Reels/Shorts), `16:9` (YouTube), and `1:1` (Square), `5s` and `10s` durations, and 8 visual style presets.
4. **Modular AI Provider Architecture (`BaseVideoProvider`):**
   - **Live Paid API Mode (`FalVideoProvider`):** Connects to official `fal.ai` queue endpoints (`fal-ai/wan-t2v` and `fal-ai/wan-i2v`) when `FAL_KEY` is configured in `backend/.env`.
   - **Honest Demo Mode (`DemoVideoProvider`):** Automatically activates when no `FAL_KEY` is set. Simulates asynchronous queue progression (`queued` -> `processing` -> `completed`) and returns clearly labeled sample MP4 clips at `$0.00` cost.
5. **Security & Cost Controls:** Server-side `.env` secrets, Pillow image verification, sliding-window rate limits, daily generation quotas, cost estimation before generation, explicit user consent for paid runs, and per-user history isolation.

---

## Quick Start (Windows / VS Code)

Open two terminals in VS Code (`Ctrl + Shift + ~`):

### Terminal 1: Start the Python FastAPI Backend (`http://localhost:8000`)
```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2: Start the Next.js Frontend (`http://localhost:3000`)
```powershell
cd frontend
npm run dev
```
- Open the AI Video Studio in your browser: [http://localhost:3000](http://localhost:3000)

---

## Running Automated Tests
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\pytest.exe backend/tests/test_api.py -v
```
