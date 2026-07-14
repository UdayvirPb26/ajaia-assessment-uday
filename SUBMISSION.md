# Submission — Collab Docs (Ajaia AI-Native Full Stack Developer Assignment)

## Candidate
Udayvir Singh Rai (udayvir2002@gmail.com)

## Live product URL
https://ajaia-assessment-uday.onrender.com

## Demo accounts
| Username | Password    |
|----------|-------------|
| alice    | password123 |
| bob      | password123 |

(Use both accounts in separate browser sessions/incognito windows to test sharing — log in as alice, share a document with bob, then log in as bob to see it under "Shared with you.")

## Walkthrough video
[ADD YOUR LOOM/YOUTUBE LINK HERE]

## What's included in this folder
- `/` — full source code (Flask backend, Jinja + Quill.js frontend)
- `README.md` — local setup and run instructions, feature list, known gaps
- `ARCHITECTURE.md` — architecture decisions and tradeoffs
- `AI_WORKFLOW.md` — AI tool usage, what was verified/changed/rejected
- `tests/test_app.py` — automated test suite (5 tests, all passing)
- `SUBMISSION.md` — this file

## What's working
- Document creation, renaming, rich text editing (bold/italic/underline/headings/lists), autosave, save/reopen
- File upload: `.txt`, `.md`, `.docx` → converted into new editable documents; unsupported types/oversized files rejected cleanly
- Sharing: owner grants/revokes access by username; shared users see documents under "Shared with you" and can edit them; sharing is not transitive
- Persistence: SQLite, verified to survive a full app restart (document content + sharing state both confirmed)
- Basic auth via seeded demo accounts

## What's incomplete / known limitations
- No separate view-only sharing role — shared access currently grants full edit rights (this is listed as a stretch goal in the assignment itself)
- `.docx`/`.md` imports preserve paragraph text and heading levels only, not inline formatting (bold/italic within the source file)
- Current deployment uses Render's free tier, where disk is not guaranteed persistent across redeploys — documented in `ARCHITECTURE.md` along with the Postgres migration path that would resolve it in production

## What I'd build next with another 2-4 hours
- Migrate deployment to managed Postgres for guaranteed persistence across redeploys
- View-only sharing role, separate from edit access
- Inline formatting preservation for `.docx`/`.md` imports
- Document version history