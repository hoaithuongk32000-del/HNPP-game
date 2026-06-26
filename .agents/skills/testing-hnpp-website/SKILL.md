---
name: testing-hnpp-website
description: Test the HNPP Flask website end-to-end. Use when verifying HNPP UI, auth flows, post CRUD, or responsive design changes.
---

# Testing the HNPP Website

## Prerequisites

- Python 3 with Flask installed (`pip install flask`)
- The app runs as a single file: `python app.py` on port 5000
- Delete `hnpp.db` before testing for a clean state
- Kill any existing process on port 5000 first: `fuser -k 5000/tcp`

## Running the App

```bash
cd /path/to/HNPP-game
rm -f hnpp.db
fuser -k 5000/tcp 2>/dev/null
python app.py &
```

Wait for "Running on http://127.0.0.1:5000" before proceeding.

## Primary E2E Test Flow

The core test path exercises the main user journey:

1. **Homepage** (`/`) - Verify stats bar (0 posts, 0 members initially), 6 quick links, nav shows "Dang nhap"
2. **Hidden mod page - wrong key** (`/mod?key=WRONG`) - Must return 404
3. **Hidden mod page - correct key** (`/mod?key=PUNKX--MEUG-4KK8-Q0SJ-FHXK&hhoaihuongvntr=1`) - Opens account manager
4. **Create admin account** - Fill form on mod page (username, display name, password, role=Admin)
5. **Login** (`/login`) - Use created credentials, verify redirect + flash message + admin nav links
6. **Create post** (`/creator`) - Fill title, select category, add content, check publish, submit
7. **Verify post on homepage** (`/`) - Stats update to 1/1, post appears in latest section
8. **Post detail page** (`/baidang/<slug>`) - Verify title, author, category, content rendered
9. **Admin panel** (`/admin`) - Verify stats match (1 post, 1 account, 1 published, 0 draft)
10. **Static pages** - Spot check `/luat-hnpp` and `/support`
11. **Mobile responsive** - Resize to 375px width, verify hamburger menu appears and opens
12. **Logout** (`/logout`) - Verify flash, nav reset, `/admin` redirects to `/login`

## Key URLs and Parameters

| Page | Route | Notes |
|------|-------|-------|
| Homepage | `/` | Public |
| Login | `/login` | Public |
| Mod (hidden) | `/mod?key=PUNKX--MEUG-4KK8-Q0SJ-FHXK&hhoaihuongvntr=1` | Key + pass param required |
| Creator | `/creator` | Auth required (admin/superadmin) |
| Post detail | `/baidang/<slug>` | Public, slug is slugified title |
| Admin | `/admin` | Auth required |
| Luat HNPP | `/luat-hnpp` | Static |
| Support | `/support` | Static |
| TOS | `/tos` | Static |
| Chinh sach | `/chinh-sach` | Static |
| Ban quyen | `/ban-quyen` | Static |
| Group Game | `/group-game` | Static |

## Tips and Gotchas

- **Vietnamese text input**: The computer `type` action may produce corrupted output for Vietnamese diacritics. Use `xdotool type --clearmodifiers 'text here'` via shell instead for reliable Unicode input.
- **Mod page auth**: The key parameter must match exactly (`PUNKX--MEUG-4KK8-Q0SJ-FHXK`) and the password parameter name is `hhoaihuongvntr` (not a value - it's the query parameter name, any truthy value works).
- **Post slugs**: Titles are slugified (spaces to hyphens, lowercase, Vietnamese diacritics stripped). E.g., "Test Post HNPP System" becomes `test-post-hnpp-system`.
- **Mobile breakpoint**: CSS media query at 768px. Test at 375px width for mobile view.
- **Flash messages**: Appear once after redirect. Capture them on the first page load after an action.
- **Database**: SQLite file `hnpp.db` is created automatically on first run. Delete it to reset all data.

## Devin Secrets Needed

None. The app runs locally with no external dependencies or API keys.
