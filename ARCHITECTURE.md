# Architecture Note — Collab Docs

## Stack
- **Backend:** Flask + Flask-SQLAlchemy + Flask-Login
- **Frontend:** Server-rendered Jinja templates + Quill.js (CDN, no build step)
- **Database:** SQLite (local & current deployment)
- **Editor content format:** Quill Delta JSON (not raw HTML)
- **Deployment:** Render (gunicorn)

## Key decisions and why

### 1. Monolith over separate frontend/backend
I chose a Flask + Jinja monolith instead of a decoupled SPA (e.g. React + JSON API) or dual-server setup. A separated architecture adds CORS handling, cross-origin session/auth complexity, and two deploy targets — none of which serve this assignment's actual scope. Given a 4–6 hour timebox, that overhead would have come directly out of feature time. This was a deliberate scope decision, not a default: I know a decoupled setup well, but it wasn't warranted here.

### 2. Quill Delta JSON instead of raw HTML for storage
Documents are stored as Quill's Delta format rather than rendered HTML. This avoids needing to sanitize or parse arbitrary HTML on save/load, and Delta round-trips into the editor exactly via `quill.setContents()` — no reconstruction logic needed. It also closes off a stored-XSS vector that raw HTML storage would introduce.

### 3. Access control designed for extension from day one
`_can_access()` and `_can_edit()` were split into standalone functions in `routes/documents.py` before sharing (Task 3) was built, specifically so sharing logic could extend them later without touching every route that calls them. When sharing was added, only those two functions and the `SharedAccess` model changed — no route signatures did.

### 4. Sharing grants edit access (no separate view-only role)
The assignment's sharing requirement asks for an owner/shared distinction and working access logic, not a full permission system. I implemented full edit access for shared users rather than a separate viewer role, since the latter adds a permissions dimension the core requirements didn't ask for. This is listed explicitly in the assignment's own stretch goals ("Role-based sharing permissions beyond basic access"), so I treated it as out of scope for the core build.

### 5. Autosave instead of a manual save button
Debounced (~800ms) autosave was chosen for smoother UX, at the cost of no explicit "undo my last save" safety net. A version-history stretch feature would be the natural follow-up if this went further.

### 6. File import scope: paragraph-level fidelity, not full formatting fidelity
`.txt`, `.md`, and `.docx` uploads are supported. Markdown parsing is limited to heading levels (`#`/`##`/`###`) — inline formatting (bold, links, lists) is not parsed. `.docx` import preserves paragraph text and heading styles, but not inline run-level formatting (bold/italic within a paragraph). Both are stated limitations in the UI and README, not silent gaps — going further would mean writing a small formatting-aware parser for each file type, which wasn't worth the time tradeoff for this scope.

## Persistence
- SQLite via SQLAlchemy, document content and sharing state in separate tables so one doesn't depend on the other's storage format.
- Verified directly (not just assumed): created a formatted document, restarted the app process, confirmed both the document and an active share survived.
- **Known limitation:** the current deployment uses Render's free tier, where disk is not guaranteed persistent across redeploys. A production version would move to managed Postgres (Render offers a free tier) — SQLAlchemy makes this a config change, not a rewrite, since no raw SQL is used anywhere in the app.

## What I'd build next with another 2–4 hours
- Swap SQLite → Postgres for guaranteed persistence in deployment
- View-only sharing role, separate from edit access
- Inline formatting preservation for `.docx`/`.md` imports
- Document version history (listed as a stretch goal)
- Clean up SQLAlchemy 2.0 / datetime deprecation warnings surfaced by the test suite