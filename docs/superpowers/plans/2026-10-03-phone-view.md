# iPhone View-Only Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user view the Weight Tracker read-only on an iPhone from a password-protected page on their NFO web host, with the data refreshed daily at 10:00 AM.

**Architecture:** `weight-tracker.html` gains a read-only mode (active when served over http/https) that loads its data with `fetch('data.php')` into an in-memory store. Three small PHP files (`lib.php`, `index.php`, `data.php`) on NFO implement a signed-cookie password gate and serve the app and the JSON; the JSON and the password hash live in `/usr/www/titan7/weight-private/`, above the web root. A PowerShell script uploads the newest data file through a saved WinSCP session on a daily scheduled task.

**Tech Stack:** Vanilla HTML/JS (existing single file), PHP 8.4 (NFO), Python 3 + `bcrypt` (local password helper), PowerShell + WinSCP.com, bash + `curl` for tests.

**Spec:** `docs/superpowers/specs/2026-10-03-phone-view-design.md`

## Global Constraints

- The PC workflow must not change: on `file://` in Chrome/Edge the app behaves exactly as today (linked JSON, autosave, `localStorage`).
- Read-only mode never writes `localStorage` or IndexedDB and never calls `autoSaveToFile()`.
- Data is real health data: unreachable without the password; the JSON and `auth-config.php` live only in `/usr/www/titan7/weight-private/` and are never inside the web root.
- No secrets in the repo, in chat, or in any Dropbox-synced folder. The password is chosen by the user and typed only into the local helper (hidden input); only its bcrypt hash is stored. `.ini` files stay untracked.
- Web folder: `/usr/www/titan7/public/FMJfiles/weight/` → `https://fmj.fullmetaljacket.site.nfoservers.com/weight/`. Private folder: `/usr/www/titan7/weight-private/`. FTP root is `/usr/www/titan7`.
- Cookie: `HttpOnly`, `Secure` (on HTTPS), `SameSite=Strict`, ~30-day lifetime. HTTPS only. `X-Robots-Tag: noindex`.
- Scheduled upload: **daily at 10:00 AM**. Log: `C:\Users\Perdi\Documents\upload-weighttracker.log`.
- Single-file app, no build step. Reference code by symbol, not line number.
- Work on branch `add-phone-view`. Deploy only from committed state (commit first, then deploy, then test). Docs (`README.md`, `CLAUDE.md`, `Workspace Map.md`) are updated only after the user has tested and approved; merge and push wait for the user's explicit go-ahead.

## Spec deltas decided while planning

These refine the spec; Task 6 patches the spec to match.

1. **Read-only trigger** is `location.protocol` being `http:` or `https:` only. The spec's "or File System Access API missing" would break the existing localStorage fallback for Firefox/Safari opening the file from disk (`file://`), so that case is left alone.
2. **Signed token cookie** instead of PHP sessions (the shared host's `/tmp` is shared with other customers). Token = `expiry.HMAC-SHA256(expiry, secret)`; the secret is random and lives in `auth-config.php`.
3. **Upload uses a saved WinSCP session** (`WinSCP.com`), so no FTP password is stored in an `.ini`; `deploy/upload.ini` holds only the session name. This also avoids sending health data over plain FTP if the saved session uses SFTP/FTPS.
4. **`auth-config.php` is generated into `%USERPROFILE%\weight-tracker-secrets\`** (outside Dropbox and the repo), not into the repo folder, because the nightly rclone job copies the whole project folder to Google Drive.
5. **Scripts are versioned in the repo** under `deploy/` (the scheduled task points at `deploy/upload-data.ps1`) instead of living in `PowershellScripts`.

## Review Focus

- A cookie that is tampered with, expired, or malformed must be treated as logged out (never a PHP warning or a free pass). Tested in Task 3 (`lib-test.php`, `test-server.sh`).
- No data file in `weight-private/` must give a clean JSON 404, and the phone page must show "Could not load data", not a blank or broken page. Tested in Tasks 1 and 3.
- A half-uploaded JSON must never be served: upload goes to `*.part` then is renamed, and `data.php` only globs `*.json`. Task 4.
- Five wrong passwords lock that client out (HTTP 429) even if the sixth is correct. Task 3.
- The milestone due-date input is editable in the normal app, so it must be disabled in read-only mode, and a corrupt/`null` JSON body must not crash the page or leave stale data. Task 1.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `weight-tracker.html` | Modify | Read-only mode: `READ_ONLY` flag, in-memory `store`, hide-write-UI CSS/classes, `loadReadOnlyData()` |
| `server/lib.php` | Create | Config loader, token sign/verify, cookie helpers, rate-limit store, security headers |
| `server/index.php` | Create | Login form + logout + serves `app.html` when authenticated |
| `server/data.php` | Create | Authenticated JSON endpoint (newest `weight-tracker-data_*.json` from the private dir) |
| `server/.htaccess` | Create | `Options -Indexes`; deny direct access to `lib.php` and `app.html` |
| `server/robots.txt` | Create | `Disallow: /` |
| `deploy/make-auth-config.py` | Create | Prompt for password, write `auth-config.php` (bcrypt hash + random secret) |
| `deploy/test_make_auth_config.py` | Create | unittest for the helper |
| `deploy/tests/lib-test.php` | Create | PHP assertions for token validation |
| `deploy/tests/test-server.sh` | Create | Local end-to-end test of the gate using `php -S` and `curl` |
| `deploy/upload-data.ps1` | Create | Daily data upload via WinSCP (atomic `.part` rename) + logging |
| `deploy/deploy-web.ps1` | Create | Upload app + PHP files via WinSCP from a clean committed tree |
| `deploy/upload.ini` | Create (untracked) | `session=<WinSCP saved site name>` |
| `.gitignore` | Modify | Ignore `auth-config.php` as a safeguard |

---

### Task 1: Read-only mode in `weight-tracker.html`

**Files:**
- Modify: `weight-tracker.html`

**Interfaces:**
- Consumes: existing `loadAllData(data)`, `renderAll()`, `autoSaveToFile()`, `getEntries()` etc.
- Produces: global `const READ_ONLY` (boolean), global `store` (object with `getItem/setItem/removeItem`; `localStorage` when not read-only), `async function loadReadOnlyData()`. Reads `data.php` and `index.php` (relative URLs) at runtime.

- [ ] **Step 1: Create the local test harness (does not touch the repo)**

```bash
T=/c/Users/Perdi/AppData/Local/Temp/wt-phone-test
mkdir -p "$T" && cd "/d/Dropbox/Computing1/BatchFiles_Scripts/Claude Projects/Weight Tracker"
cp "weight-tracker-data_2026.json" "$T/data.php"        # a static file named data.php
echo '{"entries":[{"date":"2026-01-01","weight":200}]}' > "$T/data-small.json"
```

- [ ] **Step 2: Run the app unchanged over http to confirm the failing baseline**

```bash
cp weight-tracker.html "$T/index.html"
cd "$T" && python -m http.server 8100 --bind 127.0.0.1   # run in background
```
Open `http://127.0.0.1:8100/index.html` with the chrome-devtools MCP and evaluate `document.body.classList.contains('readonly')`.
Expected: `false`, and the Add Entry form and Export / Import tab are visible. (This is the failing baseline.)

- [ ] **Step 3: Add the read-only CSS**

In `weight-tracker.html`, immediately before the line `  @media (max-width: 600px) {`, insert:

```css
  /* Read-only (phone) mode */
  body.readonly .ro-hide,
  body.readonly .btn-edit,
  body.readonly .btn-danger { display: none !important; }
  .ro-only { display: none !important; }
  body.readonly .ro-only { display: flex !important; }
  .ro-only a { color: #7dd3fc; font-size: 0.85rem; }
```

- [ ] **Step 4: Add the read-only banner and hide the PC-only banner**

Replace `  <div class="storage-banner">` (the markup line, not the CSS rule) with:

```html
  <div class="storage-banner ro-only" id="ro-banner">
    <div>
      <div class="storage-status" id="ro-status">Loading…</div>
      <div class="last-saved" id="ro-updated"></div>
    </div>
    <a href="index.php?logout=1">Sign out</a>
  </div>

  <div class="storage-banner ro-hide">
```

- [ ] **Step 5: Mark the write-only UI as `ro-hide`**

Make these exact class additions (each `old → new`):

- `<button class="tab" onclick="showTab('data', this)">Export / Import</button>` → `<button class="tab ro-hide" onclick="showTab('data', this)">Export / Import</button>`
- `<div id="tab-data" class="section">` → `<div id="tab-data" class="section ro-hide">`
- In `tab-log`, `<div class="card">\n      <h2>Add Entry</h2>` → `<div class="card ro-hide">\n      <h2>Add Entry</h2>`
- `<h2>Goal Weight</h2>\n      <div class="form-row">` → `<h2>Goal Weight</h2>\n      <div class="form-row ro-hide">`
- `<h2>BMI Tracker</h2>\n      <div class="form-row" style="align-items:flex-end">` → `<h2>BMI Tracker</h2>\n      <div class="form-row ro-hide" style="align-items:flex-end">`
- Milestones intro paragraph: `<p style="color:#94a3b8;font-size:0.85rem;margin-bottom:14px">Set intermediate targets` → `<p class="ro-hide" style="color:#94a3b8;font-size:0.85rem;margin-bottom:14px">Set intermediate targets`
- `<div class="form-row" style="margin-bottom:16px">\n        <div class="form-group">\n          <label>Label (optional)</label>` → `<div class="form-row ro-hide" style="margin-bottom:16px">\n        <div class="form-group">\n          <label>Label (optional)</label>`
- `<div id="tab-doctors" class="section">\n    <div class="card">\n      <h2>Doctor Visits</h2>` → `<div id="tab-doctors" class="section">\n    <div class="card ro-hide">\n      <h2>Doctor Visits</h2>`
- `<div id="tab-records" class="section">\n    <div class="card">\n      <h2>Yearly Low / High</h2>` → `<div id="tab-records" class="section">\n    <div class="card ro-hide">\n      <h2>Yearly Low / High</h2>`

(Edit/Delete buttons rendered by `renderHistory`, `renderDoctorVisits`, `renderYearRecords`, `renderMilestones` carry `btn-edit` / `btn-danger` and are hidden by the CSS in Step 3.)

- [ ] **Step 6: Add the `READ_ONLY` flag and in-memory `store`**

Immediately after the line `const HEIGHT_KEY = 'weightTrackerHeight';` insert:

```js
// Read-only (phone) mode: served over http(s). On file:// the app behaves exactly as before.
const READ_ONLY = location.protocol === 'http:' || location.protocol === 'https:';
const store = READ_ONLY
  ? (() => {
      const m = new Map();
      return {
        getItem: k => (m.has(k) ? m.get(k) : null),
        setItem: (k, v) => { m.set(k, String(v)); },
        removeItem: k => { m.delete(k); }
      };
    })()
  : localStorage;
```

- [ ] **Step 7: Route all accessor storage calls through `store`**

```bash
cd "/d/Dropbox/Computing1/BatchFiles_Scripts/Claude Projects/Weight Tracker"
sed -i '/^function getEntries()/,/^async function autoSaveToFile/ s/localStorage\./store./g' weight-tracker.html
grep -n "localStorage" weight-tracker.html
```
Expected: exactly one match (the `: localStorage;` line in Step 6). If any `localStorage.` call remains, repeat the `sed` for that range.

- [ ] **Step 8: Guard autosave and disable the milestone due-date input in read-only mode**

Replace `async function autoSaveToFile() {\n  if (!fileHandle) return;` with:

```js
async function autoSaveToFile() {
  if (READ_ONLY || !fileHandle) return;
```

Replace `          onchange="updateMilestoneDue(${m.id}, this.value)">` with:

```js
          onchange="updateMilestoneDue(${m.id}, this.value)" ${READ_ONLY ? 'disabled' : ''}>
```

- [ ] **Step 9: Add `loadReadOnlyData()` and switch the boot sequence**

Insert this function immediately before the `// ── Init ──` comment:

```js
async function loadReadOnlyData() {
  const status = document.getElementById('ro-status');
  const updated = document.getElementById('ro-updated');
  try {
    const res = await fetch('data.php', { credentials: 'same-origin', cache: 'no-store' });
    if (res.status === 401) { location.href = 'index.php'; return; }
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    loadAllData(data);
    renderAll();
    status.innerHTML = '<span class="dot dot-linked"></span> Read-only view';
    updated.textContent = data.savedAt ? 'Data last saved: ' + new Date(data.savedAt).toLocaleString() : '';
  } catch (err) {
    status.innerHTML = '<span class="dot dot-unlinked"></span> Could not load data';
    updated.textContent = String(err && err.message ? err.message : err);
  }
}
```

Replace the last two init lines `updateStorageStatus(false);\nrestoreDirHandle();` with:

```js
if (READ_ONLY) {
  document.body.classList.add('readonly');
  loadReadOnlyData();
} else {
  updateStorageStatus(false);
  restoreDirHandle();
}
```

- [ ] **Step 10: Verify read-only mode over http**

```bash
cd /c/Users/Perdi/AppData/Local/Temp/wt-phone-test
cp "/d/Dropbox/Computing1/BatchFiles_Scripts/Claude Projects/Weight Tracker/weight-tracker.html" index.html
```
(server from Step 2 still running). Reload `http://127.0.0.1:8100/index.html` and evaluate in the chrome-devtools MCP:

- `document.body.classList.contains('readonly')` → `true`
- `Object.keys(localStorage).length` → `0` and `indexedDB.databases ? (await indexedDB.databases()).length : 0` → `0`
- `[...document.querySelectorAll('.tab')].filter(t => t.offsetParent).map(t => t.textContent)` → no "Export / Import"
- `!!document.querySelector('#tab-log .card.ro-hide') && document.querySelector('#tab-log .card.ro-hide').offsetParent === null` → `true`
- `document.querySelectorAll('.btn-edit, .btn-danger')` all have `offsetParent === null` (open History first)
- `document.getElementById('ro-updated').textContent` starts with `Data last saved:`
- A screenshot at 390px width shows the chart, History, Doctors, Records, Projection, Averages tabs populated.

Failure-path checks (Review Focus): replace `data.php` with `echo 'not json' > data.php` → reload → `#ro-status` text contains `Could not load data`; replace with `echo 'null' > data.php` → same message and the page does not throw (check `list_console_messages` for uncaught errors). Restore with `cp weight-tracker-data_2026.json data.php` (from the repo folder).

- [ ] **Step 11: Verify the PC path is unchanged**

Open `file:///D:/Dropbox/Computing1/BatchFiles_Scripts/Claude%20Projects/Weight%20Tracker/weight-tracker.html` in the chrome-devtools MCP (if the MCP blocks `file://`, skip this and rely on the user's PC test in Task 5). Evaluate `READ_ONLY` → `false`; `typeof store.getItem` and `store === localStorage` → `true`; the Add Entry form and the data-directory banner are visible.

- [ ] **Step 12: Stop the test server and commit**

Stop the background `python -m http.server`. Then:

```bash
cd "/d/Dropbox/Computing1/BatchFiles_Scripts/Claude Projects/Weight Tracker"
git add weight-tracker.html
git commit -m "Add read-only phone mode (served over http/https)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Password helper

**Files:**
- Create: `deploy/make-auth-config.py`
- Test: `deploy/test_make_auth_config.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `deploy/make-auth-config.py` — `build_config_php(password: str) -> str` returns the PHP source (`<?php return ['hash' => '$2y$…', 'secret' => '<64 hex>'];`); `main()` prompts twice with `getpass`, enforces 12–72 bytes and matching entries, writes to `$WT_SECRETS_DIR` or `%USERPROFILE%\weight-tracker-secrets\auth-config.php`.
- Consumed by: `lib.php` `wt_config()` (Task 3) via `$cfg['hash']`, `$cfg['secret']`.

- [ ] **Step 1: Write the failing test**

Create `deploy/test_make_auth_config.py`:

```python
import importlib.util, os, pathlib, re, tempfile, unittest
from unittest import mock

import bcrypt

HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("mac", HERE / "make-auth-config.py")
mac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mac)


class BuildConfig(unittest.TestCase):
    def test_hash_is_php_compatible_and_verifies(self):
        php = mac.build_config_php("correct horse battery")
        m = re.search(r"'hash' => '(\$2y\$12\$[./A-Za-z0-9]{53})'", php)
        self.assertIsNotNone(m, php)
        self.assertTrue(bcrypt.checkpw(b"correct horse battery", m.group(1).encode()))
        self.assertFalse(bcrypt.checkpw(b"wrong", m.group(1).encode()))

    def test_secret_is_64_hex_and_random(self):
        a = re.search(r"'secret' => '([0-9a-f]{64})'", mac.build_config_php("x" * 12))
        b = re.search(r"'secret' => '([0-9a-f]{64})'", mac.build_config_php("x" * 12))
        self.assertTrue(a and b)
        self.assertNotEqual(a.group(1), b.group(1))

    def test_password_not_present_in_output(self):
        self.assertNotIn("correct horse battery", mac.build_config_php("correct horse battery"))


class Main(unittest.TestCase):
    def run_main(self, answers):
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.dict(os.environ, {"WT_SECRETS_DIR": d}), \
             mock.patch("getpass.getpass", side_effect=answers):
            try:
                mac.main()
                return (pathlib.Path(d) / "auth-config.php").exists()
            except SystemExit:
                return False

    def test_writes_file_when_passwords_match(self):
        self.assertTrue(self.run_main(["a-long-password-1", "a-long-password-1"]))

    def test_rejects_mismatch(self):
        self.assertFalse(self.run_main(["a-long-password-1", "a-long-password-2"]))

    def test_rejects_short(self):
        self.assertFalse(self.run_main(["short", "short"]))

    def test_rejects_over_72_bytes(self):
        self.assertFalse(self.run_main(["x" * 73, "x" * 73]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python deploy/test_make_auth_config.py`
Expected: FAIL/ERROR — `make-auth-config.py` does not exist (`FileNotFoundError`).

- [ ] **Step 3: Write the helper**

Create `deploy/make-auth-config.py`:

```python
"""Create auth-config.php (bcrypt hash + random cookie secret) for the Weight Tracker phone site.

The password is typed here (hidden) and never stored; only its hash is written. Output goes to
%USERPROFILE%\\weight-tracker-secrets\\auth-config.php (or $WT_SECRETS_DIR), outside the repo and
outside Dropbox. Upload that one file to /weight-private/ on NFO.
"""
import getpass
import os
import pathlib
import secrets
import sys

import bcrypt


def build_config_php(password: str) -> str:
    h = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("ascii")
    h = h.replace("$2b$", "$2y$", 1)  # PHP's password_verify accepts $2y$
    secret = secrets.token_hex(32)
    # bcrypt output uses only [./A-Za-z0-9$], so single-quoted PHP strings need no escaping.
    return "<?php\nreturn [\n    'hash' => '%s',\n    'secret' => '%s',\n];\n" % (h, secret)


def secrets_dir() -> pathlib.Path:
    env = os.environ.get("WT_SECRETS_DIR")
    if env:
        return pathlib.Path(env)
    return pathlib.Path(os.environ["USERPROFILE"]) / "weight-tracker-secrets"


def main() -> None:
    pw = getpass.getpass("New password (12-72 bytes): ")
    pw2 = getpass.getpass("Repeat password: ")
    if pw != pw2:
        sys.exit("Passwords do not match.")
    size = len(pw.encode("utf-8"))
    if size < 12 or size > 72:
        sys.exit("Password must be 12-72 bytes.")
    out = secrets_dir()
    out.mkdir(parents=True, exist_ok=True)
    target = out / "auth-config.php"
    target.write_text(build_config_php(pw), encoding="utf-8", newline="\n")
    print("Wrote", target)
    print("Upload it to /weight-private/ on NFO. Do not commit or share it.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python deploy/test_make_auth_config.py -v`
Expected: 7 tests, all `ok`.

- [ ] **Step 5: Add the safeguard ignore and commit**

Append to `.gitignore`:

```
# Secrets (live outside the repo; ignored here as a safeguard)
auth-config.php
```

```bash
git add deploy/make-auth-config.py deploy/test_make_auth_config.py .gitignore
git commit -m "Add password helper that writes a bcrypt auth-config.php" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: PHP login gate and data endpoint

**Files:**
- Create: `server/lib.php`, `server/index.php`, `server/data.php`, `server/.htaccess`, `server/robots.txt`
- Test: `deploy/tests/lib-test.php`, `deploy/tests/test-server.sh`

**Interfaces:**
- Consumes: `auth-config.php` returning `['hash' => string, 'secret' => string]` from `wt_private_dir()`; `app.html` next to `index.php` (the deployed copy of `weight-tracker.html`).
- Produces (`lib.php`): `wt_private_dir(): string` (env `WT_PRIVATE_DIR` override for tests, default `dirname(__DIR__, 3) . '/weight-private'`), `wt_security_headers(): void`, `wt_config(): array`, `wt_token(string $secret, int $expires): string`, `wt_token_valid(string $token, string $secret, int $now): bool`, `wt_authed(array $cfg): bool`, `wt_set_cookie(array $cfg): void`, `wt_clear_cookie(): void`, `wt_lock_remaining(): int`, `wt_record_fail(): void`, `wt_clear_fails(): void`. HTTP: `GET data.php` → 200 JSON / 401 `{"error":"auth"}` / 404 `{"error":"no data"}`; `POST index.php` password → 302 + cookie / 401 / 429.

- [ ] **Step 1: Get a throwaway local PHP (test tool only, outside the repo)**

```bash
D=/c/Users/Perdi/AppData/Local/Temp/wt-php && mkdir -p "$D" && cd "$D"
curl -s https://windows.php.net/downloads/releases/releases.json | python -c "import json,sys; d=json.load(sys.stdin)['8.4']; print(d['version'], d['nts-vs17-x64']['zip']['path'])"
```
Download the printed zip path with `curl -o php.zip https://windows.php.net/downloads/releases/<path>`, unzip it here (`powershell -c "Expand-Archive php.zip -DestinationPath ."`), and confirm `./php.exe -v` prints `PHP 8.4.x`. If the download or run fails, stop and ask the user (they may prefer testing on NFO only; then run Steps 2–9 against the live host in Task 5 instead).

- [ ] **Step 2: Write the failing token test**

Create `deploy/tests/lib-test.php`:

```php
<?php
declare(strict_types=1);
require __DIR__ . '/../../server/lib.php';

$fail = 0;
function check(string $name, bool $ok): void {
    global $fail;
    echo ($ok ? "PASS " : "FAIL ") . $name . "\n";
    if (!$ok) $fail = 1;
}

$secret = str_repeat('a', 64);
$now = 1_000_000;
$good = wt_token($secret, $now + 100);

check('valid token accepted', wt_token_valid($good, $secret, $now));
check('expired token rejected', !wt_token_valid(wt_token($secret, $now - 1), $secret, $now));
check('tampered expiry rejected', !wt_token_valid(($now + 99999) . '.' . explode('.', $good)[1], $secret, $now));
check('tampered mac rejected', !wt_token_valid($now + 100 . '.' . str_repeat('0', 64), $secret, $now));
check('wrong secret rejected', !wt_token_valid($good, str_repeat('b', 64), $now));
foreach (['', '.', 'abc', '123', '123.', '.abc', 'x.y', '123.abc.def', "12\x003.abc"] as $bad) {
    check('malformed rejected: ' . json_encode($bad), !wt_token_valid($bad, $secret, $now));
}
exit($fail);
```

- [ ] **Step 3: Run it to verify it fails**

Run: `"$D/php.exe" deploy/tests/lib-test.php`
Expected: fatal error — `server/lib.php` not found.

- [ ] **Step 4: Write `server/lib.php`**

```php
<?php
declare(strict_types=1);

const WT_COOKIE   = 'wt_auth';
const WT_TTL      = 2592000;   // 30 days
const WT_MAX_FAIL = 5;
const WT_LOCK_SEC = 600;       // 10 minutes

function wt_private_dir(): string {
    $env = getenv('WT_PRIVATE_DIR');
    return ($env !== false && $env !== '') ? $env : dirname(__DIR__, 3) . '/weight-private';
}

function wt_security_headers(): void {
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    header('X-Robots-Tag: noindex, nofollow');
    header('Referrer-Policy: no-referrer');
}

function wt_config(): array {
    $file = wt_private_dir() . '/auth-config.php';
    $cfg = is_file($file) ? include $file : null;
    if (!is_array($cfg) || !isset($cfg['hash'], $cfg['secret']) || !is_string($cfg['hash'])
        || !is_string($cfg['secret']) || $cfg['secret'] === '') {
        http_response_code(500);
        exit('Server not configured.');
    }
    return $cfg;
}

function wt_token(string $secret, int $expires): string {
    return $expires . '.' . hash_hmac('sha256', (string)$expires, $secret);
}

function wt_token_valid(string $token, string $secret, int $now): bool {
    $parts = explode('.', $token, 2);
    if (count($parts) !== 2 || $parts[0] === '' || !ctype_digit($parts[0]) || $parts[1] === '') {
        return false;
    }
    if ((int)$parts[0] < $now) {
        return false;
    }
    return hash_equals(hash_hmac('sha256', $parts[0], $secret), $parts[1]);
}

function wt_authed(array $cfg): bool {
    return isset($_COOKIE[WT_COOKIE]) && is_string($_COOKIE[WT_COOKIE])
        && wt_token_valid($_COOKIE[WT_COOKIE], $cfg['secret'], time());
}

function wt_cookie_opts(int $expires): array {
    $path = rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? '/'), '/') . '/';
    $https = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    return ['expires' => $expires, 'path' => $path, 'secure' => $https,
            'httponly' => true, 'samesite' => 'Strict'];
}

function wt_set_cookie(array $cfg): void {
    $exp = time() + WT_TTL;
    setcookie(WT_COOKIE, wt_token($cfg['secret'], $exp), wt_cookie_opts($exp));
}

function wt_clear_cookie(): void {
    setcookie(WT_COOKIE, '', wt_cookie_opts(1));
}

// ── Login rate limiting (state in the private dir, one JSON file, flock-protected) ──

function wt_attempts(callable $fn) {
    $fh = fopen(wt_private_dir() . '/login-attempts.json', 'c+');
    if ($fh === false) {
        http_response_code(500);
        exit('Server error.');
    }
    flock($fh, LOCK_EX);
    $data = json_decode((string)stream_get_contents($fh), true);
    if (!is_array($data)) $data = [];
    $now = time();
    foreach ($data as $k => $v) {
        if (($v['last'] ?? 0) < $now - 86400) unset($data[$k]);
    }
    $result = $fn($data, $now);
    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, json_encode($data));
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);
    return $result;
}

function wt_client_key(): string {
    return hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'unknown');
}

function wt_lock_remaining(): int {
    $key = wt_client_key();
    return wt_attempts(function (array &$d, int $now) use ($key): int {
        $until = $d[$key]['locked_until'] ?? 0;
        return $until > $now ? $until - $now : 0;
    });
}

function wt_record_fail(): void {
    $key = wt_client_key();
    wt_attempts(function (array &$d, int $now) use ($key): void {
        $e = $d[$key] ?? ['fails' => 0, 'locked_until' => 0];
        $e['fails']++;
        $e['last'] = $now;
        if ($e['fails'] >= WT_MAX_FAIL) {
            $e['locked_until'] = $now + WT_LOCK_SEC;
            $e['fails'] = 0;
        }
        $d[$key] = $e;
    });
}

function wt_clear_fails(): void {
    $key = wt_client_key();
    wt_attempts(function (array &$d, int $now) use ($key): void {
        unset($d[$key]);
    });
}
```

- [ ] **Step 5: Run the token test to verify it passes**

Run: `"$D/php.exe" deploy/tests/lib-test.php`
Expected: every line `PASS …`, exit code 0.

- [ ] **Step 6: Write `server/index.php`**

```php
<?php
declare(strict_types=1);
require __DIR__ . '/lib.php';

wt_security_headers();
$cfg = wt_config();

if (isset($_GET['logout'])) {
    wt_clear_cookie();
    header('Location: index.php');
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !wt_authed($cfg)) {
    $wait = wt_lock_remaining();
    if ($wait > 0) {
        http_response_code(429);
        $error = 'Too many attempts. Try again in ' . (int)ceil($wait / 60) . ' min.';
    } else {
        $pw = (string)($_POST['password'] ?? '');
        if (strlen($pw) <= 1024 && password_verify($pw, $cfg['hash'])) {
            wt_clear_fails();
            wt_set_cookie($cfg);
            header('Location: index.php');
            exit;
        }
        wt_record_fail();
        sleep(1);
        http_response_code(401);
        $error = 'Wrong password.';
    }
}

header('Content-Type: text/html; charset=utf-8');

if (wt_authed($cfg)) {
    readfile(__DIR__ . '/app.html');
    exit;
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Weight Tracker</title>
<style>
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
         background: #0f172a; color: #e2e8f0; font-family: system-ui, sans-serif; }
  form { width: min(320px, 90vw); background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; }
  h1 { font-size: 1.2rem; margin: 0 0 16px; }
  input, button { width: 100%; box-sizing: border-box; font-size: 1rem; padding: 10px; border-radius: 6px; border: 1px solid #334155; }
  input { background: #0f172a; color: #e2e8f0; margin-bottom: 12px; }
  button { background: #0284c7; color: #fff; border: 0; cursor: pointer; }
  .err { color: #f87171; font-size: 0.9rem; margin-bottom: 12px; }
</style>
</head>
<body>
<form method="post" action="index.php">
  <h1>Weight Tracker</h1>
  <?php if ($error !== ''): ?><div class="err"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div><?php endif; ?>
  <input type="password" name="password" autocomplete="current-password" autofocus required placeholder="Password">
  <button type="submit">Sign in</button>
</form>
</body>
</html>
```

- [ ] **Step 7: Write `server/data.php`**

```php
<?php
declare(strict_types=1);
require __DIR__ . '/lib.php';

wt_security_headers();
header('Content-Type: application/json; charset=utf-8');
$cfg = wt_config();

if (!wt_authed($cfg)) {
    http_response_code(401);
    echo '{"error":"auth"}';
    exit;
}

$files = glob(wt_private_dir() . '/weight-tracker-data_*.json') ?: [];
usort($files, fn($a, $b) => filemtime($b) <=> filemtime($a));
if (!$files) {
    http_response_code(404);
    echo '{"error":"no data"}';
    exit;
}
readfile($files[0]);
```

- [ ] **Step 8: Write `server/.htaccess` and `server/robots.txt`**

`server/.htaccess`:

```apache
Options -Indexes
<FilesMatch "^(lib\.php|app\.html)$">
  Require all denied
</FilesMatch>
```

`server/robots.txt`:

```
User-agent: *
Disallow: /
```

- [ ] **Step 9: Write the end-to-end local test**

Create `deploy/tests/test-server.sh`:

```bash
#!/usr/bin/env bash
# Local end-to-end test of the login gate. Requires PHP_BIN (php.exe) and python+bcrypt.
set -u
PHP="${PHP_BIN:?set PHP_BIN to the full path of php.exe}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
T="$(mktemp -d)"
mkdir -p "$T/web" "$T/private"
cp "$ROOT"/server/index.php "$ROOT"/server/data.php "$ROOT"/server/lib.php "$T/web/"
cp "$ROOT/weight-tracker.html" "$T/web/app.html"
export WT_PRIVATE_DIR="$(cygpath -m "$T/private")"
export WT_SECRETS_DIR="$WT_PRIVATE_DIR"
PW='test-password-12345'
PW="$PW" ROOT_PY="$(cygpath -m "$ROOT")" python - <<'PY'
import getpass, importlib.util, os, pathlib
getpass.getpass = lambda prompt="": os.environ["PW"]
spec = importlib.util.spec_from_file_location("mac", pathlib.Path(os.environ["ROOT_PY"]) / "deploy" / "make-auth-config.py")
mac = importlib.util.module_from_spec(spec); spec.loader.exec_module(mac); mac.main()
PY
echo '{"entries":[{"date":"2026-02-01","weight":250}],"savedAt":"2026-02-01T00:00:00Z"}' > "$T/private/weight-tracker-data_2026.json"
echo '{"entries":[{"date":"2025-02-01","weight":999}]}' > "$T/private/weight-tracker-data_2025.json"
touch -d '2025-01-01' "$T/private/weight-tracker-data_2025.json"

PORT=8099
"$PHP" -S 127.0.0.1:$PORT -t "$(cygpath -m "$T/web")" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; rm -rf "$T"' EXIT
curl -s --retry 15 --retry-connrefused --retry-delay 1 -o /dev/null "http://127.0.0.1:$PORT/data.php"

fail=0
check() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 (got '$2', want '$3')"; fail=1; fi; }
B="http://127.0.0.1:$PORT"
code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

check "data.php without cookie -> 401" "$(code $B/data.php)" 401
check "login page is served" "$(curl -s $B/index.php | grep -c 'type="password"')" 1
check "tampered cookie -> 401" "$(code -H 'Cookie: wt_auth=9999999999.deadbeef' $B/data.php)" 401
check "malformed cookie -> 401" "$(code -H 'Cookie: wt_auth=garbage' $B/data.php)" 401
check "no-store header on data.php" "$(curl -si $B/data.php | grep -ci '^cache-control: no-store')" 1
check "noindex header on login" "$(curl -si $B/index.php | grep -ci '^x-robots-tag: noindex')" 1

check "wrong password -> 401" "$(code -d 'password=nope' $B/index.php)" 401
check "wrong password sets no cookie" "$(curl -si -d 'password=nope' $B/index.php | grep -ci 'set-cookie: wt_auth')" 0

JAR="$T/jar"
check "right password -> 302" "$(code -c $JAR -d "password=$PW" $B/index.php)" 302
check "cookie flags HttpOnly+SameSite" "$(curl -si -d "password=$PW" $B/index.php | grep -i 'set-cookie: wt_auth' | grep -ci 'httponly.*samesite=strict\|samesite=strict.*httponly')" 1
check "data.php with cookie -> 200" "$(code -b $JAR $B/data.php)" 200
check "serves newest data file" "$(curl -s -b $JAR $B/data.php | python -c 'import json,sys;print(json.load(sys.stdin)["entries"][0]["weight"])')" 250
check "index.php with cookie serves app" "$(curl -s -b $JAR $B/index.php | grep -c 'Weight & Food Tracker')" 1
check "logout clears cookie" "$(curl -si -b $JAR "$B/index.php?logout=1" | grep -ci 'set-cookie: wt_auth=deleted\|set-cookie: wt_auth=;')" 1

rm "$T"/private/weight-tracker-data_*.json
check "no data file -> 404 json" "$(curl -s -b $JAR -o /dev/null -w '%{http_code}' $B/data.php)" 404
check "404 body is json" "$(curl -s -b $JAR $B/data.php)" '{"error":"no data"}'

# Lockout last: 5 wrong passwords, then even the right one is refused.
for i in 1 2 3 4 5; do code -d 'password=nope' $B/index.php >/dev/null; done
check "6th attempt (wrong) -> 429" "$(code -d 'password=nope' $B/index.php)" 429
check "right password during lockout -> 429" "$(code -d "password=$PW" $B/index.php)" 429

exit $fail
```


- [ ] **Step 10: Run the end-to-end test**

Run: `PHP_BIN="$D/php.exe" bash deploy/tests/test-server.sh`
Expected: every line `PASS …`, exit code 0. Fix any `FAIL` before continuing (re-run until green). If a cookie-flag check fails only because of header ordering, adjust the `grep` in the test, not the server.

- [ ] **Step 11: Commit**

```bash
git add server deploy/tests
git commit -m "Add PHP login gate and data endpoint with local tests" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Upload scripts and scheduled task

**Files:**
- Create: `deploy/upload-data.ps1`, `deploy/deploy-web.ps1`, `deploy/upload.ini` (untracked)

**Interfaces:**
- Consumes: a WinSCP saved site (name in `deploy/upload.ini` as `session=<name>`), `C:\Program Files (x86)\WinSCP\WinSCP.com`, remote paths `/weight-private/` and `/public/FMJfiles/weight/` (FTP root `/usr/www/titan7`).
- Produces: `deploy/upload-data.ps1` (no parameters needed; exit code 0 on success, non-zero on failure; appends to `C:\Users\Perdi\Documents\upload-weighttracker.log`); `deploy/deploy-web.ps1` (refuses to run if tracked deploy files are dirty or uncommitted).

- [ ] **Step 1: Confirm the WinSCP session and remote root with the user**

Ask the user for the **saved site name** they use in WinSCP for NFO and confirm that, when connected, the remote root shows `public` and `weight-private` side by side (so the paths above are correct). If the saved site uses plain FTP rather than SFTP/FTPS, tell the user the data and password would cross the internet unencrypted and ask whether NFO offers SFTP/FTPS. Create `deploy/upload.ini` (untracked via the global `.ini` rule):

```
session=<the saved site name>
```

Verify it is ignored: `git check-ignore -v deploy/upload.ini` prints a rule.

- [ ] **Step 2: Write `deploy/upload-data.ps1`**

```powershell
# upload-data.ps1
# Uploads the newest weight-tracker-data_YYYY.json to NFO /weight-private/ via a saved WinSCP session.
# Uploads to a .part name then renames, so the phone page never sees a half-written file.
$ErrorActionPreference = 'Stop'
$logPath = 'C:\Users\Perdi\Documents\upload-weighttracker.log'
$winscp  = 'C:\Program Files (x86)\WinSCP\WinSCP.com'
$iniPath = Join-Path $PSScriptRoot 'upload.ini'
$dataDir = Split-Path $PSScriptRoot -Parent

function Write-Log([string]$m) {
    Add-Content -Path $logPath -Value ("{0} {1}" -f (Get-Date -Format 's'), $m)
}

try {
    if (-not (Test-Path $winscp)) { throw "WinSCP.com not found at $winscp" }
    if (-not (Test-Path $iniPath)) { throw "Missing $iniPath (needs: session=<WinSCP saved site name>)" }
    $session = $null
    foreach ($line in Get-Content $iniPath) {
        if ($line -match '^\s*session\s*=\s*(.+?)\s*$') { $session = $Matches[1] }
    }
    if (-not $session) { throw "upload.ini has no session= line" }

    $src = Get-ChildItem -Path $dataDir -File |
        Where-Object { $_.Name -match '^weight-tracker-data_\d{4}\.json$' } |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $src) { throw "No weight-tracker-data_YYYY.json found in $dataDir" }
    try { Get-Content $src.FullName -Raw | ConvertFrom-Json | Out-Null }
    catch { throw "$($src.Name) is not valid JSON; not uploading" }

    $remote = "/weight-private/$($src.Name)"
    $script = Join-Path ([IO.Path]::GetTempPath()) ("wt-upload-{0}.txt" -f [guid]::NewGuid())
    @(
        'option batch abort'
        'option confirm off'
        ('open "{0}"' -f $session)
        ('put -transfer=binary "{0}" "{1}.part"' -f $src.FullName, $remote)
        ('mv "{0}.part" "{0}"' -f $remote)
        'exit'
    ) | Set-Content -Path $script -Encoding ASCII

    & $winscp /script=$script /log="$env:TEMP\wt-winscp.log" | Out-Null
    $code = $LASTEXITCODE
    Remove-Item $script -ErrorAction SilentlyContinue
    if ($code -ne 0) { throw "WinSCP exited with code $code (see $env:TEMP\wt-winscp.log)" }

    Write-Log ("OK uploaded {0} ({1} bytes) to {2}" -f $src.Name, $src.Length, $remote)
} catch {
    Write-Log ("ERROR {0}" -f $_)
    Write-Error $_
    exit 1
}
```

- [ ] **Step 3: Dry-run the failure paths, then run it for real**

```powershell
# a) missing ini -> must fail, log an ERROR, and exit 1
Rename-Item deploy\upload.ini upload.ini.bak
powershell -NoProfile -File deploy\upload-data.ps1; $LASTEXITCODE    # expect 1
Rename-Item deploy\upload.ini.bak upload.ini
# b) real run
powershell -NoProfile -File deploy\upload-data.ps1; $LASTEXITCODE    # expect 0
Get-Content C:\Users\Perdi\Documents\upload-weighttracker.log -Tail 3
```
Expected: the log shows an `ERROR` line for (a) and `OK uploaded weight-tracker-data_2026.json (… bytes) to /weight-private/weight-tracker-data_2026.json` for (b). In WinSCP, confirm the file is in `weight-private` and no `.part` file is left behind.

- [ ] **Step 4: Write `deploy/deploy-web.ps1`**

```powershell
# deploy-web.ps1
# Uploads the phone site (PHP files + app.html) to NFO /public/FMJfiles/weight/ via a saved WinSCP session.
# Refuses to deploy anything that is not committed (deploy-discipline).
$ErrorActionPreference = 'Stop'
$repo    = Split-Path $PSScriptRoot -Parent
$winscp  = 'C:\Program Files (x86)\WinSCP\WinSCP.com'
$session = $null
foreach ($line in Get-Content (Join-Path $PSScriptRoot 'upload.ini')) {
    if ($line -match '^\s*session\s*=\s*(.+?)\s*$') { $session = $Matches[1] }
}
if (-not $session) { throw "upload.ini has no session= line" }

Push-Location $repo
try {
    $dirty = git status --porcelain -- server weight-tracker.html
    if ($dirty) { throw "Uncommitted changes in deployable files:`n$dirty`nCommit first, then deploy." }
    $sha = git rev-parse --short HEAD
} finally { Pop-Location }

$remote = '/public/FMJfiles/weight'
$script = Join-Path ([IO.Path]::GetTempPath()) ("wt-deploy-{0}.txt" -f [guid]::NewGuid())
@(
    'option batch abort'
    'option confirm off'
    ('open "{0}"' -f $session)
    ('put -transfer=binary "{0}\server\index.php" "{1}/index.php"' -f $repo, $remote)
    ('put -transfer=binary "{0}\server\data.php" "{1}/data.php"' -f $repo, $remote)
    ('put -transfer=binary "{0}\server\lib.php" "{1}/lib.php"' -f $repo, $remote)
    ('put -transfer=binary "{0}\server\.htaccess" "{1}/.htaccess"' -f $repo, $remote)
    ('put -transfer=binary "{0}\server\robots.txt" "{1}/robots.txt"' -f $repo, $remote)
    ('put -transfer=binary "{0}\weight-tracker.html" "{1}/app.html"' -f $repo, $remote)
    'exit'
) | Set-Content -Path $script -Encoding ASCII

& $winscp /script=$script | Out-Null
$code = $LASTEXITCODE
Remove-Item $script -ErrorAction SilentlyContinue
if ($code -ne 0) { throw "WinSCP exited with code $code" }
Write-Host "Deployed commit $sha to $remote"
```

(The remote folder `/public/FMJfiles/weight/` is created once by hand in Task 5 Step 2.)

- [ ] **Step 5: Verify the dirty-tree guard**

```powershell
Add-Content weight-tracker.html ' '          # make the app dirty
powershell -NoProfile -File deploy\deploy-web.ps1; $LASTEXITCODE   # expect an error about uncommitted changes, non-zero
git checkout -- weight-tracker.html
```
Expected: the script stops with "Uncommitted changes in deployable files" before any WinSCP call.

- [ ] **Step 6: Commit**

```bash
git add deploy/upload-data.ps1 deploy/deploy-web.ps1
git commit -m "Add WinSCP-based data upload and web deploy scripts" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Create the daily 10:00 AM scheduled task (user runs this in an elevated PowerShell)**

Give the user this block to paste into an **elevated** PowerShell (creating tasks needs elevation); do not run it yourself:

```powershell
$script = 'D:\Dropbox\Computing1\BatchFiles_Scripts\Claude Projects\Weight Tracker\deploy\upload-data.ps1'
$action    = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger   = New-ScheduledTaskTrigger -Daily -At 10:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName 'Upload Weight Tracker JSON to NFO' -Action $action -Trigger $trigger -Principal $principal -Settings $settings
Start-ScheduledTask -TaskName 'Upload Weight Tracker JSON to NFO'
```
Then verify: `Get-ScheduledTaskInfo -TaskName 'Upload Weight Tracker JSON to NFO' | Select LastTaskResult, NextRunTime` shows `LastTaskResult 0` and a `NextRunTime` of tomorrow 10:00, and the log has a fresh `OK uploaded` line.

---

### Task 5: Deploy and live verification

**Files:** none changed (deploy from the committed branch).

**Interfaces:**
- Consumes: everything above; the user's chosen password.

- [ ] **Step 1: Confirm a clean, committed tree**

Run: `git status --short` and `git log --oneline -6`
Expected: only the untracked `weight-tracker-data_2026 - Copy.json`; the Task 1–4 commits are present.

- [ ] **Step 2: Create the web folder by hand**

In WinSCP create `/public/FMJfiles/weight/` (the deploy script uploads into it but does not create it).

- [ ] **Step 3: User creates the password and uploads it (never in chat)**

Ask the user to run, in this session's prompt: `! python deploy/make-auth-config.py` and type a password of 12+ characters twice. Then have them upload `%USERPROFILE%\weight-tracker-secrets\auth-config.php` to `/weight-private/` in WinSCP. Verify without reading the file: it exists remotely and `https://fmj.fullmetaljacket.site.nfoservers.com/weight-private/auth-config.php` returns 404.

- [ ] **Step 4: Deploy the site and the data**

```powershell
powershell -NoProfile -File deploy\deploy-web.ps1
powershell -NoProfile -File deploy\upload-data.ps1
```
Expected: "Deployed commit <sha>" and an `OK uploaded` log line. Remove the leftover probe items on NFO (the user deletes `probe.php`, `probe2.php`, `webroot-zz-test` in `/public/FMJfiles/`, and `test.txt` in `weight-private`).

- [ ] **Step 5: Unauthenticated checks from here (read-only `curl`)**

```bash
B=https://fmj.fullmetaljacket.site.nfoservers.com/weight
for p in data.php lib.php app.html robots.txt index.php weight-private/auth-config.php; do printf '%s -> ' "$p"; curl -s -o /dev/null -w '%{http_code}\n' "$B/$p"; done
curl -sI "$B/index.php" | grep -i 'x-robots-tag\|cache-control'
curl -s -o /dev/null -w '%{http_code}\n' https://fmj.fullmetaljacket.site.nfoservers.com/weight-private/weight-tracker-data_2026.json
```
Expected: `data.php` → 401; `lib.php` and `app.html` → 403; `robots.txt` → 200; `index.php` → 200 (login form) with `X-Robots-Tag: noindex, nofollow` and `Cache-Control: no-store`; the two private URLs → 404. Do **not** run wrong-password attempts against the live site (the lockout would block the user's own IP for 10 minutes); the lockout is covered by `test-server.sh`.

- [ ] **Step 6: Desktop browser check (user logs in)**

Ask the user to open `https://fmj.fullmetaljacket.site.nfoservers.com/weight/`, sign in, and confirm: all view tabs render with their data; there is no Add Entry form, no Export / Import tab, no Edit/Delete buttons; the banner shows "Read-only view" and a plausible "Data last saved" time; Sign out returns to the login page.

- [ ] **Step 7: PC regression check (user)**

Ask the user to open the local `weight-tracker.html` in Chrome from disk and confirm it still auto-relinks the data file, logs an entry, and autosaves as before (spec Testing item 1).

- [ ] **Step 8: iPhone check (user, off home Wi-Fi)**

Ask the user to open the URL in iPhone Safari on cellular: login works, all tabs usable at phone width, the chart is readable, the "Data last saved" stamp appears, and the login survives closing and reopening Safari. Record any layout problems found; fix them as small follow-up commits on this branch (CSS only inside the existing `@media (max-width: 600px)` block or a new one), redeploy with `deploy-web.ps1`, and re-test.

- [ ] **Step 9: Scheduled task check (next morning)**

After 10:00 AM the next day: `Get-ScheduledTaskInfo -TaskName 'Upload Weight Tracker JSON to NFO'` shows `LastRunTime` ≈ 10:00 and `LastTaskResult 0`, and the log has a new `OK uploaded` line.

---

### Task 6: Docs and spec patch (only after the user has tested and approved)

**Files:**
- Modify: `docs/superpowers/specs/2026-10-03-phone-view-design.md`, `README.md`, `CLAUDE.md`, `Workspace Map.md`

- [ ] **Step 1: Do not start until the user says the phone view works and approves.** Per the global rules, docs are the last step before merge.

- [ ] **Step 2: Patch the spec** with the five "Spec deltas" listed near the top of this plan (read-only trigger, signed cookie, WinSCP saved session, secrets directory, scripts in `deploy/`), and set its status to "implemented".

- [ ] **Step 3: Update docs** — `README.md` (phone view: URL, read-only, login, daily 10:00 upload, how to change the password), `CLAUDE.md` Key Files table (`server/`, `deploy/`, the scheduled task, NFO paths) and a Notes entry for the deploy/upload commands, `Workspace Map.md` (new folders, data flow diagram, external pieces: NFO paths, scheduled task, secrets folder). Show the user the diffs and wait for approval before committing.

- [ ] **Step 4: Stop.** Merging to `main` and pushing wait for the user's explicit go-ahead.
