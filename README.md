# NutriSnap

A webpage-first nutrition tracking SPA with React + Tailwind CSS, a Flask REST API, JWT authentication, SQLite local storage, and a MySQL-compatible schema. The first version uses a clearly labeled mock food recognizer so the full user flow works before a real TensorFlow.js model is connected.

## Included
- Landing/auth experience, registration, login, demo account, protected app workspace, sign-out and theme toggle.
- Dashboard with calorie ring, macro bars, recent meals, weekly chart and a local water tracker.
- Food photo upload/camera capture, preview, portion adjustment, nutrition estimates and manual food search. Without an `HF_TOKEN`, analysis returns a clearly labeled demo estimate that does not inspect the image.
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
Backend reads environment variables from the process environment. `.env.example` is a template; the current minimal setup does not auto-load `.env`, so set variables in your shell or install `python-dotenv` and add `from dotenv import load_dotenv; load_dotenv()` near the top of `app.py`. `HF_TOKEN` is optional: without it, food scanning uses a clearly labeled fixed demo result; set it to enable image recognition.

Frontend API URL defaults to the same-origin `/api` path. For local development, set `VITE_API_URL=http://localhost:5000/api` in `frontend/.env` and restart Vite.

## Deploy to Vercel
The root `vercel.json` configures two services: the Flask API in `backend` and the Vite SPA in `frontend`. Requests to `/api/*` go to the backend; all other paths go to the frontend. The frontend calls the API through the same-origin `/api` route, so it does not need a service binding or a Vercel API URL build variable.

In Vercel, import the repository as one project and add these project environment variables for the backend:
- `SECRET_KEY`: a long, randomly generated secret.
- `DATABASE_URL`: a connection URL for a managed, persistent MySQL database, such as `mysql+pymysql://user:password@host:3306/nutritrack`. URL-encode special characters in credentials.

The default SQLite database is local development storage and is not suitable for Vercel's serverless filesystem. The backend creates its tables and demo seed data when it initializes; database data must be on persistent managed storage. Set `FRONTEND_ORIGIN` only if you need to restrict CORS; same-origin requests through the configured rewrite do not require cross-origin access.

## MySQL deployment
1. Create a MySQL 8 database using `database/schema.sql` (or create an empty database and let SQLAlchemy create tables).
2. The PyMySQL driver is included in `backend/requirements.txt`.
3. Set `DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/nutritrack`.
4. Set a long random `SECRET_KEY`, restrict `FRONTEND_ORIGIN` to your deployed frontend URL if needed, and run behind a production WSGI server such as Gunicorn (`pip install gunicorn; gunicorn app:app`) outside Vercel.
5. Use HTTPS, backups, monitoring, and a migration tool such as Flask-Migrate/Alembic for schema changes.

## Main API routes
- `POST /api/auth/register`, `POST /api/auth/login`
- `GET/PUT /api/profile`
- `GET /api/foods?search=...`, `GET /api/foods/<id>`
- `POST /api/recognize` (multipart form field `image`, JWT required; uses the configured image model or returns a clearly labeled demo result when `HF_TOKEN` is unset)
- `GET/POST /api/meals`, `PUT/DELETE /api/meals/<id>`
- `GET/PUT /api/goals`
- `GET /api/progress?range=week|month`, `GET /api/history` (supports `format=csv`)
- `POST /api/mealplan/generate`, `GET /api/mealplan`, `POST /api/mealplan/add`
- `GET /api/health`

Authenticated routes expect `Authorization: Bearer <token>`. The API returns JSON errors with HTTP status codes. The frontend stores the token in localStorage for the remember-me experience; for a production deployment, consider secure HttpOnly cookies and CSRF protection.

## Food data and nutrition disclaimer
NutriTrack's nutritional information, food database, calorie estimates and meal analysis are based on Kenyan food profiles, locally available ingredients, common Kenyan food portions and typical preparation methods. Nutritional values are estimates and may vary depending on ingredient brands, portion sizes, recipes, cooking methods and regional differences. Where a food item or preparation method differs from the Kenyan profiles used by the application, the displayed nutritional information may not accurately represent the actual meal. NutriTrack is intended for general nutritional information and food-tracking purposes only. It does not provide medical advice, diagnosis or treatment, and its estimates should not replace advice from a qualified healthcare professional or registered nutritionist. Users acknowledge these limitations when creating an account. Seed values are approximate demo estimates, not laboratory-verified nutrition facts. The mock recognizer returns a predictable sample food and does **not** inspect image contents.

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
