# Localy (Vynk) — Simple Setup Guide

A minimal guide to run the FastAPI backend and Next.js frontend connection.

---

## 1. Backend (FastAPI)

```bash
cd backend
python -m pip install -r requirements.txt
python main.py
```
- **Endpoint:** `http://127.0.0.1:8000/health`
- **Output:** `{"status": "connected", "message": "backend connected"}`

---

## 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```
- **App:** `http://localhost:3000`
- **Display:** `backend connected`

---

## 3. Verification

1. Start Backend in Terminal 1 (`python main.py` in `backend/`).
2. Start Frontend in Terminal 2 (`npm run dev` in `frontend/`).
3. Open `http://localhost:3000` in browser. It will fetch `/health` and display **"backend connected"** in one line.
