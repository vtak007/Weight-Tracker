# Weight Tracker — Project Instructions

## Key Files

| File | Purpose |
|---|---|
| `weight-tracker.html` | Main app — open this in your browser |
| `weight-tracker-data_2026.json` | Live data file for 2026 (contains real personal health data) |
| `README.md` | Project readme — describes all tabs, features, and data storage |
| `Blank Weight-Tracker Page.png` | Screenshot of the app with no data |

## Notes

Self-contained HTML/JavaScript app — no build step, no server. Open `weight-tracker.html` directly in a browser. Uses the File System Access API to auto-save to a linked `.json` data file.

The app and its live data file live in this project folder. The previous GitHub Pages demo (and its `index.html` / `weight-tracker-demo.*` / `generate_demo_data.py` files) has been removed.

## Backup to Google Drive

A Windows scheduled task, `Rclone BackupWeight Tracker JSON to gdrive` (daily 06:20, runs as Perdi, Highest privileges), runs `D:\Dropbox\Computing1\BatchFiles_Scripts\PowershellScripts\rclone-copy_WeightTracker.ps1`. The script uses rclone to copy this whole folder (Dropbox remote `Computing1/BatchFiles_Scripts/Claude Projects/Weight Tracker`) to `Gdrive:/Weight Tracker`, excluding `.git/` and `.remember/`. Log: `C:\Users\Perdi\Documents\rclone-copy_WeightTracker.log`.

The script and task live outside this repo. Editing or deleting the task needs an elevated PowerShell. The task's action must point at the `.ps1` — it once pointed (with a doubled path) at the data `.json`, so it never ran rclone and exited with code 64.
