# Pathlight Agent

> A local-first, evidence-grounded job search strategy workbench.

Pathlight helps a single job seeker turn a resume into a user-confirmed fact archive, compare it with a job description, prepare an evidence-aware greeting, and keep a local record of applications. It is intentionally designed as an assistant for decisions and drafts, not an autonomous application bot.

## What it does today

- Upload a PDF or DOCX resume and extract editable candidate facts.
- Confirm, edit, or exclude facts before they are used in a match.
- Save job-search preferences locally.
- Paste a JD to get an explainable keyword-based match result, gaps, recommendation, and greeting draft.
- Save application drafts and inspect lightweight task traces.
- Store the DeepSeek API key in the operating system credential store rather than SQLite or source files.

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

Keep the FastAPI service above running while using the desktop shell. Packaging the
Python API as a Tauri sidecar is the next milestone before a standalone installer.

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

- Package the FastAPI service as a Tauri sidecar for a standalone local app.
- Integrate structured LLM responses and streaming chat.
- Add resume diagnosis, versioning, and stable PDF export.
- Add a trace timeline and a richer application board.
- Build a regression set with anonymized resumes and job descriptions.
