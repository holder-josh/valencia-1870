# Strava exporter reference

Installation instructions are in README.md. The following describes the preserved exporter.

## Files available on your website

| Path relative to your existing Pages URL | Contents |
| --- | --- |
| `workouts.json` | All activity types; detailed workout metadata, full recorded laps, kilometre/mile splits, fetch status, and links to streams |
| `workouts.csv` | One activity per row, including timing, distance, HR, cadence, power, elevation, device, description and workout type where available |
| `workout-laps.csv` | One row per recorded lap or split; `kind` distinguishes laps, kilometre splits and mile splits; don't sum across these kinds |
| `streams/<activity-id>.json` | Strava's recorded time, distance, speed, HR, cadence, power, altitude, grade, temperature and moving-state arrays, where available |
| `activities.json` | Compatible compact run data used by the original dashboard |

Exports start at 28 July 2026, matching the original project. All activity types are included so rides and hikes can be considered alongside running. Optional `STRAVA_FETCH_FROM` environment variable accepts an ISO timestamp with timezone, e.g. `2026-01-01T00:00:00+00:00`.

## How to interpret the data

- Distances are metres, durations seconds, speeds metres/second, pace seconds/km, HR bpm, power watts. Original cadence values are retained without doubling or conversion.
- `elapsed_time` is total start-to-finish time, including stops; `moving_time` is Strava's moving time. Both have separate calculated pace fields using unrounded distance.
- `nonmoving_time_s` is elapsed minus moving time. It is not an exact reconstruction of the watch's pause button history.
- Laps include original stream indices and timestamps where provided. These are recorded laps, not guaranteed Garmin planned workout steps. Warm-up, effort and recovery labels are not invented. Strava's numeric `workout_type` is preserved as metadata, not interpreted as an interval prescription.
- JSON absent fields and CSV blank cells mean unavailable, not zero. An activity can have no HR, no power, no laps or no streams.
- Streams retain their original `data`, `resolution`, `original_size` and `series_type`. Use the time stream's offsets; do not assume exactly one sample per second. Inspect array lengths before joining them.
- No GPS coordinates, route maps, athlete profiles or OAuth credentials are exported. Activity names, descriptions and workout metrics are public, including private activities accessible to the token. To publish only public activities, restrict the app's OAuth scope to `activity:read` and reauthorize.

## Caching, freshness and errors

The full activity summary list is refreshed each run. Missing detail/streams are fetched newest first. Successfully fetched details and streams refresh daily for activities from the last seven days, and weekly for older activities, subject to the request budget. Refreshing summaries does not imply every detail was refreshed: check each activity's `detail_fetched_at` and `streams_fetched_at`.

There is a hard budget of 5 read requests per run, including pagination (at most 720 reads across 144 scheduled runs/day). Response rate-limit headers can stop requests sooner. Manual runs and other apps using the same credentials consume additional capacity. HTTP 429 ends enrichment cleanly and retains pending/cached data; later runs continue. Auth failures fail the workflow rather than publishing an empty history. A failed/incomplete summary pagination does not replace the public index. A successful complete listing removes exports of deleted or out-of-window activities on the next run; previously committed data remains in Git history.

The existing `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, and `STRAVA_REFRESH_TOKEN` secrets are required. The token needs `activity:read` or `activity:read_all` depending on the intended activity visibility. As in the original project, this workflow does not automatically write GitHub secrets. If Strava rotates your refresh token, the job emits a warning; obtain/save the current token via your OAuth setup and update `STRAVA_REFRESH_TOKEN`. Tokens are never printed or committed.

## Validation

Run `python -m unittest discover -s tests -v` with Python 3.12. Tests use synthetic API responses and temporary output folders. They check distinct moving/elapsed pace, lap fields, legacy dashboard compatibility, caching, absent streams, budget interruption, deletion cleanup, and auth failure handling. The workflow runs these tests before syncing.

## References

- [Strava API reference](https://developers.strava.com/docs/reference/)
- [Strava rate limits](https://developers.strava.com/docs/rate-limits/)
- [Strava authentication and refresh tokens](https://developers.strava.com/docs/authentication/)
- [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

The new plan is in `docs/plan.json`; use the dashboard’s Data & settings view for browser preferences.
