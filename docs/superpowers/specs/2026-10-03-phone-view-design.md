# Weight Tracker — iPhone View-Only Access (Design)

Date: 2026-10-03 · Branch: `add-phone-view` · Status: built and deployed (see "As built" below)

## As built (differences from this design)

The sections below are the original design. Where they differ, this list wins.

1. **Read-only trigger:** read-only mode keys on `http:`/`https:` only (not on a missing File System
   Access API). This keeps the `localStorage` fallback for `file://` in other browsers.
2. **Login token, not PHP sessions:** a signed token cookie (HMAC; the secret is in `auth-config.php`,
   ~30-day lifetime, `HttpOnly`, `SameSite=Strict`). Changing the password regenerates the secret and signs
   everyone out. Lockout: five wrong attempts, 10 minutes, state kept in `weight-private/`.
3. **Upload method:** the WinSCP .NET assembly with a DPAPI-encrypted credential file and a pinned TLS
   fingerprint (the saved WinSCP site stores no password and `WinSCP.com` cannot answer a prompt in batch
   mode). There is no `upload.ini`. Runs under Windows PowerShell 5.1 only. Uploads go to `*.part`, then rename.
4. **Secrets location:** `auth-config.php` (source) and the FTP credential file live in
   `%USERPROFILE%\weight-tracker-secrets\`, outside Dropbox and the repo.
5. **Script location:** the scripts are versioned in the repo under `deploy/` (not in `PowershellScripts`);
   the scheduled task `Upload Weight Tracker JSON to NFO` points at `deploy\upload-data.ps1`.
6. **Remote folder:** `deploy\deploy-web.ps1` creates the remote `weight/` folder itself and refuses to
   run from an uncommitted tree.
7. **HTTPS enforced:** added after the final review — `.htaccess` redirects `http://` to `https://`
   (the original design only said "HTTPS only").
8. **Served file name:** the app is deployed as `app.html`, blocked from direct access by `.htaccess` and
   served by `index.php` after login.

## Goal

View the Weight Tracker (charts, history, doctors, records, projection, averages) on an iPhone, away
from home, from a password-protected page on the existing NFO web host. Logging stays on the PC.

## Constraints

- Data is real personal health data. It must not be reachable without the password.
- iOS Safari/Chrome have no File System Access API, so the phone cannot link a local JSON file.
- The PC workflow (Chrome/Edge, linked JSON file, autosave) must not change.
- Single-file app, no build step. `.ini` files stay local/untracked; no secrets in the repo.
- Reuse the Live Scores NFO setup: Apache + HTTPS + PHP 8.4, FTP deploy to the web root
  (`/usr/www/titan7/public/FMJfiles/`, served at `https://fmj.fullmetaljacket.site.nfoservers.com/`).

## Non-goals

Logging or editing from the phone; multi-user accounts; real-time sync; a second data store.

## Architecture

```
PC (Task Scheduler, daily 10:00)            NFO host  /weight/
  upload-weighttracker.ps1  --FTP-->  index.php        (login gate + serves the app)
  weight-tracker-data_2026.json       data.php         (gate-checked JSON endpoint)
                                      weight-tracker.html  (same file as PC, served by index.php)
PC (FTP, one-time)  auth-config.php --FTP-->  /usr/www/titan7/weight-private/  (above web root)
PC (FTP, daily)     the data .json  --FTP-->  /usr/www/titan7/weight-private/  (never web-served)
iPhone Safari --HTTPS--> index.php --(session cookie)--> app --fetch--> data.php
```

### 1. Hosting location

Subfolder `/weight/` under the NFO web root, separate from the public `scores.php`.

### 2. Read-only phone mode (`weight-tracker.html`)

- Activates when the File System Access API is unavailable (`!window.showDirectoryPicker`) or when
  the page is served over `http(s)` (not `file://`). The PC (`file://` + API present) is unaffected.
- On load, `fetch('data.php')` and pass the result to `loadAllData()`; then `renderAll()`.
- Hidden in this mode: Log Entry form, file link/Browse controls, Export/Import tab, delete/edit
  buttons. Default tab becomes History or the chart view.
- Never writes `localStorage` or IndexedDB and never calls `autoSaveToFile()`, so the phone cannot
  diverge from or overwrite anything.
- Shows a "Last updated" stamp from the JSON's `savedAt` field so staleness is visible.
- If the fetch returns 401, redirect to the login page.

### 3. Login gate (PHP)

- `index.php`: shows a password form if there is no valid session; on success sets a session cookie
  (`HttpOnly`, `Secure`, `SameSite=Strict`, ~30-day lifetime so the phone stays signed in) and serves
  the app HTML. `password_verify()` checks the password against a bcrypt hash held in
  `auth-config.php` (see "Password setup"). Failed attempts are rate-limited (small delay + lockout
  counter, state kept in `weight-private/`).
- Server paths: the web folder is `/usr/www/titan7/public/FMJfiles/weight/`; the private folder is
  `/usr/www/titan7/weight-private/` (= `dirname(__DIR__, 3) . '/weight-private'` from the web folder).
- `data.php`: returns the JSON only with a valid session; otherwise 401. Sends `Cache-Control:
  no-store` and `X-Content-Type-Options: nosniff`.
- Fallback if PHP sessions misbehave on NFO: HTTP Basic Auth via `.htaccess` (confirmed honored on
  NFO — see "Verified host facts").

#### Password setup

- You choose the password. It is never typed into the Claude chat, never stored in the repo, and
  never exists in plain text on the server.
- When: during implementation, at the deploy step, before the first live test.
- How: a local helper script prompts for the password with hidden input and writes only a bcrypt
  hash to a local, untracked, gitignored `auth-config.php` (a PHP file returning the hash).
- Where: you FTP-upload `auth-config.php` once to `/usr/www/titan7/weight-private/`. `index.php`
  and `data.php` load it from there.
- Changing it later: re-run the helper and re-upload that one file.

### 4. Data sync

- `upload-weighttracker.ps1` (outside the repo, next to `rclone-copy_WeightTracker.ps1` in
  `PowershellScripts`) uploads `weight-tracker-data_2026.json` by FTP to
  `/usr/www/titan7/weight-private/` (FTP root is `/usr/www/titan7`, so the remote path is
  `/weight-private/`). FTP host/user/password are read from a local untracked `.ini`.
- Windows scheduled task **daily at 10:00 AM** runs the script (same pattern as the existing rclone
  task; creating/editing the task needs elevated PowerShell). The script can also be run by hand.
- Logs to `C:\Users\Perdi\Documents\upload-weighttracker.log`.
- The app itself is deployed to NFO by FTP-uploading `weight-tracker.html` + PHP files when code
  changes (manual, like `scores.php`).

## Security

- HTTPS only; session cookie flags as above; no password or FTP credentials in the repo.
- The JSON and `auth-config.php` live in `/usr/www/titan7/weight-private/`, above the web root, and
  are served only through `data.php` after the login check. The folder is not web-reachable
  (verified: a URL to a file in it returns 404).
- NFO is shared hosting and PHP can list sibling customers' folder names under `/usr/www`; keep
  nothing sensitive in the web root and never expose directory listings.
- `robots.txt` / `X-Robots-Tag: noindex` on the folder.
- Phone-mode JS inserts data via existing escaping paths; no new HTML injection surface.

## Testing

No test suite; verify manually, deploying only from committed state (feature branch):
1. Desktop Chrome with `file://` still links the file and autosaves exactly as before.
2. Phone mode on desktop (served over HTTPS from NFO): all view tabs render; no write controls.
3. Direct URL to the JSON without a session → blocked. Wrong password → rejected and rate-limited.
4. iPhone Safari (cellular, off home Wi-Fi): login, all tabs, layout at phone width, "Last updated".
5. Scheduled task: manual run uploads; confirm the 10:00 trigger fires and the log updates.

## Verified host facts (probed 2026-10-03)

- `.htaccess` is honored (a `Require all denied` folder returned 403).
- PHP 8.4.24; `open_basedir` empty; FTP root is `/usr/www/titan7`.
- `/usr/www/titan7/weight-private/` exists, is readable and writable by PHP, can read a file
  uploaded over FTP, and is not reachable by URL (404).

## Open items (resolved)

- Phone layout of the existing tabs: tested on an iPhone; the chart range buttons were changed to wrap
  on narrow screens.
- Password helper: a Python script, `deploy/make-auth-config.py`, writes a PHP-compatible bcrypt hash.

## Docs

`README.md`, `CLAUDE.md` (Key Files + deploy notes) and `Workspace Map.md` were updated after tested
sign-off.
