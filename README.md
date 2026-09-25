# Valencia / 2026

Josh's static training dashboard for the 6 December 2026 marathon. Light design, six views, no build step, no frontend credentials or external CDN. The supplied Strava exporter and 10-minute schedule are preserved.

## Replace the GitHub project

1. Unzip this folder. Copy its **contents** into your existing repository, merging/replacing files of the same name. Include `.github/workflows/sync.yml` (Cmd + Shift + . reveals hidden folders in Finder).
2. **Preserve existing `docs/workouts.json`, `docs/streams/`, generated CSVs, `docs/CNAME` and repository secrets** if your repository already has them. These generated files are not in this ZIP. Do not delete them by replacing the entire `docs` directory with an empty copy. GitHub secrets live in repository settings, not these files.
3. Commit the changes. In **Settings → Pages → Build and deployment**, select **GitHub Actions** (same as the supplied project's instructions).
4. Run **Actions → Sync Strava → Run workflow**. The existing Pages URL will serve the new dashboard after both `sync` and `deploy` succeed. The workflow tests the dashboard calculations and FIT exports before pulling Strava.

Do not upload the ZIP itself as your website. Upload its extracted project contents. No `npm install` is required in the repository: the Garmin SDK is included.

## Preview before replacing

- Open **PREVIEW.html** directly from the unzipped folder. It contains the real supplied snapshots and works without a local server. FIT export and edits work; it does not fetch live data. The PDF link works relative to the project folder.
- For the exact website, run `python3 -m http.server 8000 --directory docs` from this folder, then open `http://localhost:8000`.
- `docs/index.html` is the deployed website. Keep all its companion files under `docs`.

## Views

- **Overview:** current week, due-through-yesterday distance, four-week volume, recent runs, calendar and next quality session.
- **Training plan:** the complete 11-week PDF transcription, including travel, hike, optional double, conditional goal-pace blocks and taper. Filter upcoming / quality, inspect any day, edit steps and export FIT.
- **Activities:** imported history plus Strava feed; search / sport filters; moving vs elapsed pace, nonmoving time, splits, recorded laps, plan-step comparison, distance-block inspection, stream efficiency and notes.
- **Volume:** planned/actual weekly bars, daily differences, distance-weighted pace, running/cycling/other hours and prior-volume comparison.
- **Fitness:** strict pace/HR efficiency trend, actual imported Runalyze estimates, goal-pace progression, four transparent sub-three evidence checks and a race-equivalent calculator.
- **Data & settings:** timezone / HRmax, feed status, backup/restore and all definitions.

## What is real, estimated or missing

- Source plan: `docs/training-plan.pdf`, **revised 23 September 2026**, recovered from the Marathon Training Plan conversation. Its 77 days plus one optional PM run are in `docs/plan.json`.
- The PDF has 24 September as easy. The later 2 × 3 km threshold discussion is a selectable revision, not silently substituted into the PDF baseline.
- Time-based sessions use the midpoint of target pace to estimate easy remainder. The editor recalculates totals when you extend a warm-up. Stride recoveries default to 75 seconds within the PDF's 60–90s range. Open steps end on the lap button and have unknown distance. These implementation defaults are visible in the app.
- `docs/activities.json`: 34 real runs from the supplied project, through 24 September. This older format lacks elapsed time; unknown values remain blank.
- `docs/history.json`: 567 real activities from the supplied Runalyze CSV through 3 September 2026. Imported fields are limited to activity metrics. No notes, coordinates, hashes, account IDs or original-file references were added. Runalyze `s` is active/timer duration and may differ from Strava moving time. Historical sport IDs are specific to this account.
- Same-date, near-time (under 12 minutes, accounting for the legacy UTC clock text), near-distance (within 2% / 100 m) records merge; Strava takes precedence and the Runalyze estimates remain attached. Different runs on the same day remain separate.
- The ZIP had no detailed `workouts.json`. The app falls back to its summary snapshot until your authenticated workflow creates that file. No live Strava API call was made here. Recent cycling / hiking beyond the history cutoff are incomplete until the detailed feed arrives.
- Missing elapsed time / HR / streams stays unavailable. Clean-stream metrics require 20 usable minutes. The aerobic index is not VO₂max; imported Runalyze estimates are identified separately. Weekly pace is not used to predict race performance.
- Sub-three checks are explicit dashboard heuristics and self-reported goal-work evidence, not a validated probability. Log a controlled continuous G block and subsequent recovery under an activity's Notes.
- Automatic date matches are candidates. Edit the planned warm-up if it differs, and manually link a moved workout. Recorded laps are not assumed to be planned steps. Without streams, recorded-lap overlaps are preferred, with split overlaps as fallback. Time steps use observed lap/split durations to locate boundaries; partial overlaps remain estimates.

## Garmin FIT workouts

Open a session → **Edit workout & export FIT**. Change warm-up/cool-down, pace, distance/time/open steps, add work/recovery pairs, reorder and remove steps. Save edits if they should change the dashboard; downloading alone uses the draft without saving it.

The default FIT alarm widens each printed pace range by ±5 seconds/km. Choose Printed range / ±5 / ±10 / ±15. This changes watch alerts only, not the printed targets or in-range execution metric.

The official Garmin SDK v21.217.0 encodes each workout and immediately decodes it to check CRC and step count. Tests also verify distance/time scaling, pace-to-speed conversion and all planned running sessions. Work/recovery repetitions are expanded into individual steps (no recovery after the final rep). Maximum 50 steps.

Connect the Fēnix by USB and copy a downloaded `.fit` file to **GARMIN/NewFiles**. Safely disconnect, then find it under running workouts. On a Mac, MTP access may require a compatible transfer app. **A physical watch transfer has not been tested. Start with one threshold session.** The Garmin Connect activity uploader is not an importer for structured workout FIT files. These are undated workout prescriptions with a date in the name, not automatic calendar scheduling.

Pre-generated quality FITs are provided in `garmin-workouts/`, with the PDF baseline and default ±5s alarms. Conditional sessions stay conditional; using an export does not mean you should automatically advance the goal-pace progression.

## Edits, notes and backup

Changes are stored in localStorage on this browser/origin. They do not write back to GitHub or Strava. Use **Backup** to transfer them between devices. **Export edited plan** downloads a new `plan.json` you can commit to `docs/plan.json` for a shared baseline. Preserve a browser backup before changing the baseline. Different browsers and PREVIEW.html have separate storage origins.

To update Runalyze history:

```bash
python3 scripts/import_runalyze.py /path/to/new-runalyze-export.csv
```

Commit the updated `docs/history.json`. The importer uses only the Python standard library; raw CSVs should stay outside the public website. `scripts/build_plan.py` reproduces the original PDF transcription and will overwrite `docs/plan.json`; run it only to restore that baseline.

## Data feed

Same repository secrets: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`. Exporter starts 28 July 2026, includes all activity types, reads at most five API endpoints per workflow run and progressively fills detailed history. Existing rate-limit handling, token handling and deletion behaviour are retained. See `EXPORTER.md` for original feed documentation.

The feed already requests time, distance, speed, HR, cadence, watts, altitude, grade, temperature and moving state. No additional Strava scope/field is needed for this first pass. HRV, sleep, Garmin VO₂max trend and subjective recovery are not available from these Strava endpoints; the app does not invent them.

## Verification

```bash
npm test
python3 -m unittest discover -s tests -v
```

Tests cover weekly totals, optional mileage, weighted pace, duplicate imports, stops, missing fields, mixed distance/time boundaries and all FIT exports. `tests/browser-smoke.cjs` is an optional Playwright interaction test (requires Playwright / Chromium, not needed to deploy).

## Files

`docs/` is the whole static site. `docs/js/metrics.js` holds calculations; `docs/js/fit.js` handles FIT; `docs/js/app.js` renders the interface. `docs/assets/style.css` owns design. Garmin vendor source and licence are bundled under `docs/vendor/fit/`. No web build step or third-party runtime requests.

References: [Garmin SDK](https://github.com/garmin/fit-javascript-sdk), [Strava API](https://developers.strava.com/docs/reference/), [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
