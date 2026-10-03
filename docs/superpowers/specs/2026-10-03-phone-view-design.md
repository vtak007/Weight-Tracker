# Weight Tracker — iPhone View-Only Access (Design)

Date: 2026-10-03 · Branch: `add-phone-view` · Status: draft for review

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
                                      data/…json       (not directly web-reachable; see Security)
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
  the app HTML. The password is stored as a `password_hash()` hash in a config file outside the
  repo; `password_verify()` checks it. Failed attempts are rate-limited (small delay + lockout counter).
- `data.php`: returns the JSON only with a valid session; otherwise 401. Sends `Cache-Control:
  no-store` and `X-Content-Type-Options: nosniff`.
- Fallback if PHP sessions misbehave on NFO: HTTP Basic Auth via `.htaccess`. To be checked during
  implementation (NFO `AllowOverride` is unconfirmed).

### 4. Data sync

- `upload-weighttracker.ps1` (outside the repo, next to `rclone-copy_WeightTracker.ps1` in
  `PowershellScripts`) uploads `weight-tracker-data_2026.json` by FTP to the `/weight/` data
  location. FTP host/user/password are read from a local untracked `.ini`.
- Windows scheduled task **daily at 10:00 AM** runs the script (same pattern as the existing rclone
  task; creating/editing the task needs elevated PowerShell). The script can also be run by hand.
- Logs to `C:\Users\Perdi\Documents\upload-weighttracker.log`.
- The app itself is deployed to NFO by FTP-uploading `weight-tracker.html` + PHP files when code
  changes (manual, like `scores.php`).

## Security

- HTTPS only; session cookie flags as above; no password or FTP credentials in the repo.
- The JSON is served only through `data.php`. If a non-web-reachable directory above the document
  root is writable via FTP, the JSON lives there; otherwise the data folder gets a deny-all
  `.htaccess` (verified by requesting the file URL directly and expecting 403/404).
- `robots.txt` / `X-Robots-Tag: noindex` on the folder.
- Phone-mode JS inserts data via existing escaping paths; no new HTML injection surface.

## Testing

No test suite; verify manually, deploying only from committed state (feature branch):
1. Desktop Chrome with `file://` still links the file and autosaves exactly as before.
2. Phone mode on desktop (served over HTTPS from NFO): all view tabs render; no write controls.
3. Direct URL to the JSON without a session → blocked. Wrong password → rejected and rate-limited.
4. iPhone Safari (cellular, off home Wi-Fi): login, all tabs, layout at phone width, "Last updated".
5. Scheduled task: manual run uploads; confirm the 10:00 trigger fires and the log updates.

## Open items to resolve during implementation

- Whether NFO allows a writable directory above the document root; whether `.htaccess` is honored.
- Phone layout of the existing tabs (only one `@media (max-width: 600px)` block exists today).
- Where the web password hash is stored on NFO.

## Docs (after tested sign-off only)

Update `README.md`, `CLAUDE.md` (Key Files + deploy notes), and `Workspace Map.md`.
