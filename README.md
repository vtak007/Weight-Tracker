# Weight & Food Tracker

A self-contained HTML/JavaScript web app for tracking daily weight and food intake. No build step, no dependencies, no server — open the file directly in any modern browser.

---

## Getting started

1. Open `weight-tracker.html` in your browser.
2. Click **Browse** to select the folder where your data file lives. The app remembers this folder permanently (stored in IndexedDB) so you only need to do this once.
3. Click **New Data File** to create a JSON file in that folder. All changes auto-save to it.
4. On future visits, click **Open Data File** — the app opens the JSON file automatically from the saved folder with no file explorer dialog.

Without linking a file, data is stored in browser `localStorage` only and will be lost if browser data is cleared.

> **First-time permission:** After reopening the app, clicking **Open Data File** will trigger a one-time Chrome permission prompt for the saved folder. Choose **Every Visit** to avoid being prompted on future reloads.

---

## Data storage

The app uses the browser **File System Access API** to link directly to a local `.json` file:

| Status | Behaviour |
|---|---|
| **Linked** (green dot) | Every change auto-saves to the file immediately |
| **Unlinked** (yellow dot) | Data lives in `localStorage` only — no file persistence |

Use **Export JSON** on the Export/Import tab as a backup at any time.

---

## Tabs

### Log Entry
The main daily entry form. Each entry records:
- **Date**
- **Weight** (lbs)
- **Foods eaten** — comma-separated, with optional quantities (e.g. `2 chicken breasts, rice, 6 cookies`)
- **Notes** — free text (e.g. workout day, felt tired)

Also contains:

**Goal Weight** — set a target weight and see a progress bar showing how far along you are.

**BMI Tracker** — enter your height once; the app calculates and displays your current BMI with a color-coded gauge (Underweight → Normal → Overweight → Obese), your BMI at goal weight, and how much weight separates you from the Normal range.

**Milestones** — add intermediate weight targets between your starting and goal weight. Each milestone shows a progress bar, remaining lbs, and an editable **Date to Complete** field. The date can be set when adding a milestone or updated at any time directly on the milestone card.

**Weight Trend Chart** — SVG line chart of daily weights with a 7-day moving average overlay and optional goal line. Filterable to 7 / 30 / 90 days, This Week (Monday–today), This Month (1st–today), or All Time. Hover over a dot for the exact weight and day-over-day change.

---

### History
Full entry table sortable by Date or Daily Change. Each row shows weight, change from the previous day (color-coded green/red), foods, and notes. Edit or delete any entry inline.

---

### Food Analyzer
Search for days where specific foods were eaten and see the next-day weight change that followed.

- **Contains mode** — finds days where all listed foods appear (extras allowed)
- **Exact match mode** — finds days where the food list matches exactly (no extras)

Results show each matching day with foods highlighted, the next-day weight change, and an **average next-day change** across all matches — useful for seeing how certain foods correlate with weight movement.

**Sorting** — results can be reordered with three buttons:
- **Date (newest)** — default chronological order, newest first
- **Loss → Gain** — sorts by next-day change: biggest losses first, then gains (losses and gains stay grouped)
- **Gain → Loss** — the reverse

Days with no following entry ("no next day") always sort to the bottom.

Leading quantities in the search input are stripped before matching (`2 fairlife` matches `fairlife`).

---

### Doctors
Log doctor office visits with:
- Date, doctor/office name
- Doctor's scale weight vs. your home scale weight
- Difference between the two readings
- Notes (e.g. afternoon appointment, shoes on)

The two most recent visits also show "Current vs. Home" — how much your weight has changed since that appointment.

---

### Yearly Records
Manually log the lowest and highest weight recorded for any year. Useful for years before you started daily tracking. Displays the year's spread (high − low) alongside the stored values.

---

### Projection
Enter a current weight, a projected daily loss rate, and a target date. The app calculates the expected weight on that date and the total projected loss over the interval.

---

### Averages
**Average Daily Rate** — shows average lbs/day change over 7 days, 30 days, 90 days, and all time, with total change and actual day count for each window.

**Weekly & Monthly Averages** — average weight by calendar week and month across your full history.

---

### Export / Import

| Action | Format | Notes |
|---|---|---|
| Export JSON | `.json` | Full data snapshot — entries, goal, doctor visits, year records, milestones, height |
| Export CSV | `.csv` | Entries only (date, weight, foods, notes) |
| Import JSON | `.json` | Merges with existing data; same-date entries are overwritten by the import |

---

## Files

| File | Purpose |
|---|---|
| `weight-tracker.html` | Main app — open this in your browser |
| `weight-tracker-data_2026.json` | Live data file for 2026 |
| `Blank Weight-Tracker Page.png` | Screenshot of the app with no data |

## Requirements

- Any modern browser with File System Access API support (Chrome 86+, Edge 86+)
- No installation, no server, no build step
