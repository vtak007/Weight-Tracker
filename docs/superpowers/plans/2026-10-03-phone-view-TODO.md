# iPhone view-only access — resume checklist

Written 2026-10-03 at a pause. Spec: `docs/superpowers/specs/2026-10-03-phone-view-design.md`.
Plan: `docs/superpowers/plans/2026-10-03-phone-view.md` (this file overrides it where they differ).

## Where things stand

- Branch `add-phone-view`, HEAD `16b8443`. **Not pushed, not merged.** Docs (`README.md`, `CLAUDE.md`,
  `Workspace Map.md`) deliberately **not updated yet** (only after you test and approve).
- **Tasks 1-4 done and committed:** read-only phone mode in `weight-tracker.html`; password helper
  (`deploy/make-auth-config.py`, 7 tests); PHP gate `server/` (14 token checks + 18 end-to-end checks,
  run with local PHP); upload scripts `deploy/*.ps1`.
- **Nothing is deployed yet.** Nothing has been uploaded to NFO except what already existed.
- NFO FTP login works over explicit TLS (port 21) with the pinned certificate. Credentials are saved
  (encrypted) in `%USERPROFILE%\weight-tracker-secrets\nfo-ftp-creds.xml` (10-character password verified).
- NFO layout confirmed: `/` has `public/` and `weight-private/` (empty); web root is `/public/FMJfiles/`.
  Probe files are already gone.

## To do, in order

1. **[You] Choose the website password.** In a normal PowerShell 7 window:
   `cd "D:\Dropbox\Computing1\BatchFiles_Scripts\Claude Projects\Weight Tracker"` then
   `python deploy\make-auth-config.py`. 12+ characters, typed twice, save it in your password manager first.
   Expect `Wrote …\weight-tracker-secrets\auth-config.php`.
2. **[Claude] Upload `auth-config.php`** to `/weight-private/` using `deploy\nfo-ftp.ps1`
   (`PutFiles`, binary). Confirm the URL `…/weight-private/auth-config.php` gives 404.
3. **[Claude] Deploy and upload data**, both under **Windows PowerShell 5.1** (`powershell.exe`, not
   PowerShell 7): `deploy\deploy-web.ps1` (refuses unless the tree is committed), then
   `deploy\upload-data.ps1`. Check `C:\Users\Perdi\Documents\upload-weighttracker.log` shows `OK uploaded`.
4. **[Claude] Live checks without logging in** (plan Task 5 Step 5). Expect `weight/data.php` 401,
   `lib.php` and `app.html` 403, `robots.txt` 200, login page 200 with `X-Robots-Tag: noindex`,
   `/weight-private/…` URLs 404. Do **not** try wrong passwords on the live site (10-minute lockout of your IP).
5. **[You] Desktop login test** at `https://fmj.fullmetaljacket.site.nfoservers.com/weight/`: all view tabs
   show data; no Add Entry, Export/Import, Edit/Delete; "Read-only view" and "Data last saved" show; Sign out works.
6. **[You] PC regression test:** open the local `weight-tracker.html` in Chrome from disk; it should still
   auto-relink the data file, log an entry and autosave.
7. **[You] iPhone test on cellular:** login, all tabs, readable chart, login survives closing Safari.
   Known layout issue to fix if it shows: the chart's range-button row (7/30/90/This Week/This Month/All Time)
   overflows sideways on narrow screens (also on the PC app); fix by letting that row wrap. Then re-deploy.
8. **[You, elevated PowerShell] Create the daily 10:00 AM task** (needs admin):
   ```powershell
   $script = 'D:\Dropbox\Computing1\BatchFiles_Scripts\Claude Projects\Weight Tracker\deploy\upload-data.ps1'
   $action    = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
   $trigger   = New-ScheduledTaskTrigger -Daily -At 10:00AM
   $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
   $settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
   Register-ScheduledTask -TaskName 'Upload Weight Tracker JSON to NFO' -Action $action -Trigger $trigger -Principal $principal -Settings $settings
   Start-ScheduledTask -TaskName 'Upload Weight Tracker JSON to NFO'
   ```
   Then `Get-ScheduledTaskInfo -TaskName 'Upload Weight Tracker JSON to NFO'` should show `LastTaskResult 0`;
   check again the next morning after 10:00.
9. **[Claude] Final whole-branch review** (executing-plans): fresh reviewer on the most capable model,
   Review Focus from the plan; one fix pass for Critical/Important findings.
10. **[You approve, then Claude] Docs, last step before merge:** patch the spec with the deltas below;
    update `README.md` (phone view: URL, login, daily upload, how to change the password), `CLAUDE.md`
    (Key Files: `server/`, `deploy/`; NFO paths; scheduled task) and `Workspace Map.md` (folders, data flow,
    external pieces). Show the diffs and wait for approval before committing.
11. **[You decide] Merge to `main` and push** (fast-forward merge, delete the branch). Only on your explicit go-ahead.

## Spec deltas to record in step 10

1. Read-only mode keys on `http:`/`https:` only (keeps the localStorage fallback for `file://` in other browsers).
2. Signed token cookie (HMAC, secret in `auth-config.php`) instead of PHP sessions.
3. Upload uses the WinSCP .NET assembly + DPAPI credential file + pinned TLS fingerprint (the saved
   WinSCP site stores no password and WinSCP.com cannot answer a prompt in batch mode). No `upload.ini`.
4. `auth-config.php` and the FTP credential file live in `%USERPROFILE%\weight-tracker-secrets\`, outside Dropbox/repo.
5. Scripts are versioned under `deploy/` (the scheduled task points at `deploy\upload-data.ps1`).
6. `deploy-web.ps1` creates the remote `weight/` folder itself.

## Gotchas learned

- WinSCP's .NET assembly works under **Windows PowerShell 5.1 only**, not PowerShell 7. The scheduled task uses 5.1.
- Hidden-prompt pasting into PowerShell produced a 66-character password once. Use
  `deploy\save-ftp-creds.ps1 -ShowTyping`; it prints the saved length (should be 10).
- NFO web FTP is `hosted10.nfoservers.com` (WinSCP site "FMJ Redirect Server", user `titan7`); the pinned
  certificate is self-signed and expires 2028-11-05. If NFO rotates it, update `$NfoFingerprint` in `deploy/nfo-ftp.ps1`.
- The Live Scores `scores.php` deploy uses this same FTP account.
- Local PHP for tests is a throwaway at `C:\Users\Perdi\AppData\Local\Temp\wt-php\php.exe`
  (run `PHP_BIN=… bash deploy/tests/test-server.sh`). Delete the folder when done. The harness here blocks
  `rm -rf` and `curl | python`, so download first, then parse.
- Optional: if you want the NFO FTP password rotated (it was typed at an unresponsive prompt earlier), do it
  in the NFO panel, re-run `save-ftp-creds.ps1 -ShowTyping`, and update WinSCP and the Live Scores deploy.
- `weight-tracker-data_2026 - Copy.json` is still untracked in the repo; decide whether to delete or ignore it.
