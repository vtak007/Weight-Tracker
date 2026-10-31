# Weight Tracker — Project Memory

Persistent notes for this project. Read at the start of every session.
See `CLAUDE.md` for project-specific details.

## CONFIRMED ROOT CAUSES

- Evening entries could land on tomorrow's date (and be overwritten next morning) because default dates and range cutoffs used `toISOString()`, which is UTC — after 7 pm CDT / 6 pm CST it returns tomorrow. Fixed with `localDateStr()` (9717b6e). A scan of git history found no entries actually lost.
- `deploy-web.ps1` fails with "Method not found: EventWaitHandle..ctor" when run in PowerShell 7 — WinSCP's .NET assembly needs Windows PowerShell 5.1. Run it via `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\deploy\deploy-web.ps1`.
- Git commands from a non-Windows shell failed with "unable to unlink index.lock / main.lock" because Dropbox held `.git/index` and `.git/refs/heads/main` open while syncing. Quitting Dropbox fixed it.
- Scheduled task "Rclone BackupWeight Tracker JSON to gdrive" exited 64 because its `-File` argument pointed (with a doubled `D:\Dropbox\Computing1\` path) at the data `.json` instead of a `.ps1`, so rclone never ran. Fixed by adding `rclone-copy_WeightTracker.ps1` and repointing the task.

## RULED-OUT THEORIES

- 2026-10-30: The UTC date bug did not lose any entries. No committed version has a future-dated entry; the only gap (2026-08-02) and the weight-only days are days that simply weren't logged.

## PROJECT CONVENTIONS

- Calendar dates: `localDateStr()` for "today"/cutoffs, `dayNumber()` for day differences. Never `toISOString()` for a date, never `Math.floor` on a millisecond difference (DST).
- Signed changes: always `fmtSigned()` + `changeCls()` so the sign/colour match the rounded number shown.
- Progress toward a target: `targetProgress()` — direction comes from the starting weight (loss or gain).
- Food matching: `foodNameMatches()` — whole words, simple plurals; units stay part of the food name by choice.
- Git from a non-Windows shell: `git -c core.autocrlf=true …`; quit Dropbox first.

## CHANGE LOG

Newest first. Format: `- YYYY-MM-DD — what changed`.

- 2026-10-30 — Calculation audit fixes (commits 9717b6e → 7b43c45):
  local dates instead of UTC for defaults and range cutoffs; Projection day count rounds across DST;
  Food Analyzer whole-word matching (no more "diet coke" = "coke", "corn" = "popcorn");
  chart 7-day average computed over full history and by calendar days;
  milestone progress from weight at creation (`startWeight`) instead of the first entry;
  skipped days marked "(N days)" in History and excluded from the analyzer's next-day average;
  Averages chart windows count back from the latest entry like the Daily Rate cards;
  signed values rounded before sign/colour (no "+0.0"/"-0.0");
  goals and milestones support weight-gain targets;
  BMI category / Normal max / gauge follow the displayed (1-decimal) BMI, gauge shows Obese I/II/III;
  Projection rate buttons and "Projected gain" label to avoid the loss-per-day sign trap.
  Deliberately left: units stored inside food names; heights like 5′11.6″ display as 5′12″ (on hold).

- 2026-10-03 — Fixed Google Drive backup: new rclone-copy_WeightTracker.ps1 copies the whole folder to Gdrive:/Weight Tracker; stale Weight.ods task deleted.
- 2026-08-02 — Added MEMORY.md (standard project structure).
