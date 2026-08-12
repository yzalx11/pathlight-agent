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

- Frontend: Vue 3, TypeScript, Vite, Element Plus
- Backend: FastAPI, Pydantic, SQLAlchemy
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

In a second terminal, start the workbench:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Quality check

```powershell
cd frontend
npm run build
```

## Project structure

```text
backend/
  app/                 # FastAPI routes, persistence, and domain services
frontend/
  src/                 # Vue workbench
```

## Product boundaries

- No automated application submission or bulk recruitment-platform scraping.
- No CAPTCHA bypass, credential collection, or platform restriction bypass.
- Every external action remains under the user's final confirmation.
- Real resumes, local databases, uploads, logs, and API secrets are intentionally ignored by Git.

## Roadmap

- Integrate structured LLM responses and streaming chat.
- Add resume diagnosis, versioning, and stable PDF export.
- Add a trace timeline and a richer application board.
- Build a regression set with anonymized resumes and job descriptions.
