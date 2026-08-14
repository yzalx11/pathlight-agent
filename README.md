# Pathlight Agent

> A local-first, evidence-grounded job search strategy workbench.

Pathlight helps a single job seeker turn a resume into a user-confirmed fact archive, compare it with a job description, prepare an evidence-aware greeting, and keep a local record of applications. It is intentionally designed as an assistant for decisions and drafts, not an autonomous application bot.

The detailed product workflow, platform boundaries, and development priorities live in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## What it does today

- Upload a PDF or DOCX resume and extract editable candidate facts.
- Import up to eight BOSS job screenshots at once. OCR and original screenshots stay on this device, then become reviewable job drafts.
- Launch a dedicated recruiting browser, then let Pathlight observe only the visible BOSS job detail page and place it in a local review queue.
- Track a job from review through communication, follow-up, interview, offer, rejection, or archive. The home screen keeps the next action visible.
- Confirm, edit, or exclude facts before they are used in a match.
- Save job-search preferences locally.
- Paste a JD to get an explainable keyword-based match result, gaps, recommendation, and greeting draft.
- Save application drafts and inspect lightweight task traces.
- Keep the optional DeepSeek API key outside SQLite and source files; local development reads it from the ignored `backend/.env` file.

## Stack

- Desktop shell: Tauri 2
- Frontend: Vue 3, TypeScript, Vite, Element Plus
- Backend: FastAPI, Pydantic, SQLAlchemy, domain-oriented services
- Local storage: SQLite and local files
- Resume parsing: PyMuPDF and python-docx

## Run locally

Requirements: Python 3.11+ and Node.js 20+.

Start the API:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the workbench in a browser:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

### BOSS recruiting browser (development preview)

In the Pathlight workbench, click **打开招聘浏览器**. The app launches a dedicated
Chrome/Edge profile with a local CDP connection; log into BOSS yourself and browse
job detail pages normally. Pathlight observes only the visible BOSS job detail page,
adds a deduplicated draft to the local review queue, and waits for your confirmation
before creating a job record. It never reads cookies, account data, chat content, or
performs search, scrolling, clicking, messaging, resume sending, or application actions.

`browser-extension/` remains an optional fallback for people who prefer to import a
single current BOSS page manually from their daily browser.

### Desktop development

Pathlight now has a Tauri desktop shell. It reuses the existing Rust toolchain and
keeps the project build artifacts in `frontend/src-tauri/target/` (ignored by Git).
For this machine, the Cargo cache can remain on the D drive:

```powershell
cd frontend
$env:CARGO_HOME = 'D:\dev-tools\cargo-home'
$env:CARGO_TARGET_DIR = "$PWD\src-tauri\target"
$env:npm_config_cache = 'D:\dev-tools\npm-cache'
npm run tauri -- dev
```

For the desktop shell, build the Windows API sidecar once before starting it:

```powershell
cd backend
.\scripts\build-sidecar.ps1
```

The packaged API starts with the desktop app on `127.0.0.1:8001` (the browser
development API continues to use `8000`), stores SQLite/uploads under the operating
system's Pathlight app-data directory, and is stopped when the desktop app exits.

## Quality check

```powershell
cd backend
.\.venv\Scripts\python.exe -B -m pytest tests -q

cd frontend
npm run build
```

## Project structure

```text
backend/
  app/                 # FastAPI routes, persistence, and domain services
frontend/
  src/                 # Vue workbench
  src-tauri/           # Tauri desktop shell
```

## Product boundaries

- No automated application submission or bulk recruitment-platform scraping.
- No CAPTCHA bypass, credential collection, or platform restriction bypass.
- Every external action remains under the user's final confirmation.
- Real resumes, local databases, uploads, logs, and API secrets are intentionally ignored by Git.

## Roadmap

- Refine desktop startup, shutdown, upgrades, and Windows installer validation.
- Integrate structured LLM responses and streaming chat.
- Add resume diagnosis, versioning, and stable PDF export.
- Add a trace timeline and a richer application board.
- Build a regression set with anonymized resumes and job descriptions.
