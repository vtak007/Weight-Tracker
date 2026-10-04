# Weight Tracker — Project Instructions

## Key Files

| File | Purpose |
|---|---|
| `weight-tracker.html` | Main app — open this in your browser |
| `weight-tracker-data_2026.json` | Live data file for 2026 (contains real personal health data) |
| `README.md` | Project readme — describes all tabs, features, and data storage |
| `Workspace Map.md` | Orientation: code map, persistence, phone site, git |
| `MEMORY.md` | Confirmed root causes and change log |
| `server/` | PHP gate for the phone site (deployed to NFO `/public/FMJfiles/weight/`) |
| `deploy/` | FTPS upload/deploy scripts, password helper, tests |
| `Blank Weight-Tracker Page.png` | Screenshot of the app with no data |

## Notes

Self-contained HTML/JavaScript app — no build step. Open `weight-tracker.html` directly in a browser. Uses the File System Access API to auto-save to a linked `.json` data file. The same file is also served read-only to a phone from NFO hosting (read-only mode applies over http/https only).

The app and its live data file live in this project folder. The previous GitHub Pages demo (and its `index.html` / `weight-tracker-demo.*` / `generate_demo_data.py` files) has been removed.

## Phone view (NFO)

Read-only site at `https://fmj.fullmetaljacket.site.nfoservers.com/weight/`, files in `/public/FMJfiles/weight/`.
Data and `auth-config.php` live in `/weight-private/` (outside the web root). The daily 10:00 task
`Upload Weight Tracker JSON to NFO` runs `deploy\upload-data.ps1`; log: `C:\Users\Perdi\Documents\upload-weighttracker.log`.

- Deploy with `deploy\deploy-web.ps1` only from a **committed** tree, in **Windows PowerShell 5.1** (the WinSCP assembly fails in PowerShell 7).
- Secrets stay outside the repo and Dropbox in `%USERPROFILE%\weight-tracker-secrets\` (FTP credentials, `auth-config.php` source).
- Creating or editing the scheduled task needs an elevated PowerShell. Paste commands one statement at a time or as a single line.
- The NFO TLS certificate is pinned in `deploy/nfo-ftp.ps1` (`$NfoFingerprint`); update it if NFO rotates it (expires 2028-11-05).

## Backup to Google Drive

A Windows scheduled task, `Rclone BackupWeight Tracker JSON to gdrive` (daily 06:20, runs as Perdi, Highest privileges), runs `D:\Dropbox\Computing1\BatchFiles_Scripts\PowershellScripts\rclone-copy_WeightTracker.ps1`. The script uses rclone to copy this whole folder (Dropbox remote `Computing1/BatchFiles_Scripts/Claude Projects/Weight Tracker`) to `Gdrive:/Weight Tracker`, excluding `.git/` and `.remember/`. Log: `C:\Users\Perdi\Documents\rclone-copy_WeightTracker.log`.

The script and task live outside this repo. Editing or deleting the task needs an elevated PowerShell. The task's action must point at the `.ps1` — it once pointed (with a doubled path) at the data `.json`, so it never ran rclone and exited with code 64.
