# Weight Tracker — Project Memory

Persistent notes for this project. Read at the start of every session.
See `CLAUDE.md` for project-specific details.

## CONFIRMED ROOT CAUSES

- Scheduled task "Rclone BackupWeight Tracker JSON to gdrive" exited 64 because its `-File` argument pointed (with a doubled `D:\Dropbox\Computing1\` path) at the data `.json` instead of a `.ps1`, so rclone never ran. Fixed by adding `rclone-copy_WeightTracker.ps1` and repointing the task.

## RULED-OUT THEORIES

- (none recorded yet)

## PROJECT CONVENTIONS

- (none recorded yet)

## CHANGE LOG

Newest first. Format: `- YYYY-MM-DD — what changed`.

- 2026-10-03 — Fixed Google Drive backup: new rclone-copy_WeightTracker.ps1 copies the whole folder to Gdrive:/Weight Tracker; stale Weight.ods task deleted.
- 2026-08-02 — Added MEMORY.md (standard project structure).
