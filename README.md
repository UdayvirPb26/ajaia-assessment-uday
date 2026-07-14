# Collab Docs

A lightweight collaborative document editor 

## Setup

```bash
cd collab-docs
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

App runs at http://127.0.0.1:5000

## Demo accounts (seeded automatically on first run)

| Username | Password    |
|----------|-------------|
| alice    | password123 |
| bob      | password123 |

## What's implemented so far (Task 1)

- Create / rename documents
- Rich text editing (bold, italic, underline, headings, ordered/unordered lists) via Quill.js
- Autosave (debounced ~800ms) with visible save status
- Persistence via SQLite (document content stored as Quill Delta JSON)
- Basic auth (Flask-Login) with seeded demo users, owner-scoped document list

## Not yet implemented

- File upload (Task 2)
- Sharing between users (Task 3 — `_can_access`/`_can_edit` are already split out in `routes/documents.py` to make this a clean extension point)
- Automated tests
- Deployment

## Notes / tradeoffs

- Chose a Flask + Jinja monolith over a separate frontend/backend to maximize delivery speed within the assignment's timebox.
- Autosave instead of a manual save button, for smoother UX at the cost of no explicit "undo last save" safety net.
- Quill Delta JSON (not raw HTML) is stored, to avoid needing to sanitize/parse HTML for persistence.
