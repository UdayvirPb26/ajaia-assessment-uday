# Collab Docs

A lightweight collaborative document editor built for the Ajaia AI-Native Full Stack Developer assignment.

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

## What's implemented

**Document creation and editing**
- Create / rename documents
- Rich text editing (bold, italic, underline, headings, ordered/unordered lists) via Quill.js
- Autosave (debounced ~800ms) with visible save status
- Save and reopen — formatting is preserved exactly on reload

**File upload**
- Upload `.txt`, `.md`, or `.docx` files — each is converted into a new editable document
  - `.txt` — each line becomes a paragraph
  - `.md` — `#`/`##`/`###` headings map to editor headings; other Markdown syntax (bold, links, lists) is intentionally not parsed
  - `.docx` — paragraph text and heading styles are preserved; inline bold/italic formatting inside the file is not
- Unsupported file types and files over 2MB are rejected with a clear message, not a crash
- Supported types are stated in the UI

**Sharing**
- Document owner can share with another user by username
- Shared users see the document under "Shared with you" on their document list and can edit it
- Owner can revoke access at any time
- Sharing is not transitive — only the owner can share a document, even one shared with them
- Duplicate shares and shares to nonexistent usernames are handled with clear messages

**Persistence**
- SQLite via SQLAlchemy (`instance/app.db`)
- Document content stored as Quill Delta JSON, so formatting round-trips exactly on save/reload without any HTML parsing/sanitization step
- Sharing state stored in a separate `shared_access` table, independent of