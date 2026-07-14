# AI Workflow Note — Collab Docs

## Tools used
Claude (Anthropic), used conversationally throughout the build — architecture decisions, code generation, debugging, and test writing.

## Where AI materially sped up my work
- **Faster first drafts across the stack:** for each feature (models, routes, templates, the Quill.js integration), I directed the design decisions and structure, then had a working draft implementation produced quickly so my time went into reviewing, testing, and correcting behavior rather than typing boilerplate line-by-line.
- **Decomposing an ambiguous prompt into a build order:** the assignment describes four feature areas with no required sequence. I used AI to help me sequence them (editor core → upload → sharing → persistence writeup) in a way where each step built cleanly on the last, rather than needing rework later.
- **Fast, disciplined tradeoff framing:** for each ambiguous decision (monolith vs. split frontend, edit-only vs. role-based sharing, SQLite vs. Postgres), I asked for the actual tradeoffs rather than a single "best" answer, so the choice and its cost stayed visible and defensible instead of implicit.

## What I verified, changed, or rejected

- **Caught and fixed a real bug before it shipped:** an early edit to `routes/documents.py` (adding the file-upload route) accidentally deleted the `@docs_bp.route(...)` decorator above `edit_document`, which would have 500'd every document page. This was only caught because I insisted on running the app's test client against every new feature before accepting the code, not just reading the diff.
- **Rejected an unsafe pattern in the editor template:** the first version of the editor page embedded document content into a `<script>` block using Jinja's `| safe` filter. I identified that this doesn't escape content for script-context embedding — a document containing the literal text `</script>` would break out of the script tag (and is a stored-XSS vector). I had this replaced with Jinja's `tojson` filter + `JSON.parse()`, which properly escapes `<`, `>`, and Unicode line separators for safe script embedding. I verified the fix directly with a test payload containing `</script><script>alert(1)</script>` before accepting it, confirming the output was safely escaped.
- **Verified persistence claims rather than assuming them:** rather than trusting "SQLite persists data" as a given, I had the app manually restarted and confirmed a saved, formatted document and an active share both survived — this is what's stated in the architecture note, backed by an actual test.
- **Made an active choice not to auto-apply a suggested Postgres migration**, weighing available time against risk: since the local/tested SQLite setup was already working and verified, I chose to document the deployment's ephemeral-disk limitation explicitly rather than risk a rushed database migration late in the timebox breaking a working deploy.

## How I verified correctness and reliability
- Every feature (document CRUD, file upload for all 3 supported types plus a rejected type, sharing grant/revoke, cross-user access control) was exercised with Flask's test client against real request/response assertions before being considered done — not just visually inspected.
- The final automated test suite (`tests/test_app.py`) formalizes these checks: document formatting survives reload, non-owners are blocked until shared, revoking access blocks it again, and bad uploads are rejected without crashing. All 5 tests pass.
- Deployment was smoke-tested end-to-end on the live Render URL (login, create/edit, upload, share across two accounts) after a real deployment failure (a `gunicorn` app-factory import error) was diagnosed and fixed, rather than assuming a successful deploy meant a working app.