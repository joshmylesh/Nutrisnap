# NutriTrack

A mobile-first nutrition tracking SPA with React + Tailwind CSS, a Flask REST API, JWT authentication, SQLite local storage, and a MySQL-compatible schema. The first version uses a clearly labeled mock food recognizer so the full user flow works before a real TensorFlow.js model is connected.

## Included
- Landing/auth experience, registration, login, demo account, protected app workspace, sign-out and theme toggle.
- Dashboard with calorie ring, macro bars, recent meals, weekly chart and a local water tracker.
- Food photo upload/camera capture, preview, mock analysis, portion adjustment, nutrition estimates and manual food fallback.
- Kenyan and international foods, meal logging, edit quantity / delete, date filter, voice-search dictation where browser support exists, CSV export.
- Goals/profile settings, daily/weekly meal-plan generator, history and calorie/macro charts.
- Flask REST API, hashed passwords, JWT auth, per-user data filtering, validation, CORS and database seeding.

## Requirements
- Python 3.10+ (3.11 recommended)
- Node.js 20+ and npm
- Modern browser

## Run locally (Windows PowerShell)
Open two terminals from the project folder.

### 1. Start the backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```
If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process Bypass` in that terminal, or run `.venv\Scripts\python.exe app.py` after installing requirements.

### 2. Start the frontend
```powershell
cd frontend
npm install
npm run dev
```
Open the local URL Vite prints, usually `http://localhost:5173`.

### Linux / macOS
Backend: `cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env && python app.py`
Frontend in a second terminal: `cd frontend && npm install && npm run dev`.

## Demo account
- Email: `demo@nutritrack.app`
- Password: `NutriTrack123!`

The backend creates the SQLite database, seeded food catalogue, demo account, goals, weight history and sample meal logs on first run. Demo data is local and only for development. Change the demo password and `SECRET_KEY` before deploying publicly.

## Configuration
Backend reads environment variables from the process environment. `.env.example` is a template; the current minimal setup does not auto-load `.env`, so set variables in your shell or install `python-dotenv` and add `from dotenv import load_dotenv; load_dotenv()` near the top of `app.py`.

Frontend API URL defaults to `http://localhost:5000/api`. To change it, create `frontend/.env` with `VITE_API_URL=http://localhost:5000/api` and restart Vite.

## MySQL deployment
1. Create a MySQL 8 database using `database/schema.sql` (or create an empty database and let SQLAlchemy create tables).
2. Install the driver: `pip install PyMySQL`.
3. Set `DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/nutritrack`.
4. Set a long random `SECRET_KEY`, restrict `FRONTEND_ORIGIN` to your deployed frontend URL, and run behind a production WSGI server such as Gunicorn (`pip install gunicorn; gunicorn app:app`).
5. Use HTTPS, backups, monitoring, and a migration tool such as Flask-Migrate/Alembic for schema changes.

## Main API routes
- `POST /api/auth/register`, `POST /api/auth/login`
- `GET/PUT /api/profile`
- `GET /api/foods?search=...`, `GET /api/foods/<id>`
- `POST /api/recognize` (multipart form field `image`, JWT required; returns mock result)
- `GET/POST /api/meals`, `PUT/DELETE /api/meals/<id>`
- `GET/PUT /api/goals`
- `GET /api/progress?range=week|month`, `GET /api/history` (supports `format=csv`)
- `POST /api/mealplan/generate`, `GET /api/mealplan`, `POST /api/mealplan/add`
- `GET /api/health`

Authenticated routes expect `Authorization: Bearer <token>`. The API returns JSON errors with HTTP status codes. The frontend stores the token in localStorage for the remember-me experience; for a production deployment, consider secure HttpOnly cookies and CSRF protection.

## Food data and nutrition disclaimer
Seed values are approximate demo estimates, not laboratory-verified nutrition facts. Portions and recipes vary, especially for mixed dishes. The mock recognizer returns a predictable sample food and does **not** inspect image contents. Integrate a trained TensorFlow.js classifier and validate its output before describing recognition as real AI. This application does not diagnose, treat, or prevent disease and does not replace advice from a qualified nutrition professional.

## Project structure
```
NutriTrack/
├── frontend/          # React SPA, styles, responsive UI
├── backend/           # Flask API, models, auth, seed data
└── database/
    └── schema.sql     # MySQL-compatible schema
```

## Current implementation notes
- Charts use Recharts. The initial water tracker is browser-session UI state and is not persisted yet.
- CSV export endpoint is authenticated; browser navigation to it may require a token header, so use an authenticated fetch/download flow for production. This starter UI exposes the export shortcut for the next iteration to improve.
- Password reset, account deletion, saved theme preference, true photo inference, weight chart UI, and plan swapping are future hardening/features. Do not use this starter as a clinical tool.
