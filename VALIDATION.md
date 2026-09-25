# Validation · 25 September 2026

- 14 JavaScript tests passed: complete PDF week totals, time-step totals, running-only mileage, weighted pace, pending-day handling, unknown values, historical/Strava deduplication including the legacy UTC clock, stream stop boundaries, recorded-lap recovery alignment and workout validation.
- Five original Python exporter tests passed: request budget/caching, missing streams, deletion handling, authentication failures and missing fields.
- All 62 scheduled running sessions (including the optional PM run and race) encoded and decoded with the official Garmin SDK; CRC, sport, count, distance/time scaling and pace-target conversion were checked. The 17 pre-generated quality files have distinct file identities.
- Headless Chromium interactions passed: all views, PDF-to-later-session revision, distance-block inspection, notes, warm-up edit, saved totals, FIT download, reload persistence, race calculator and backup.
- A synthetic detailed-feed fixture tested stream loading, a 60-second stop, clean efficiency and distance-block calculations. It was isolated to browser request interception and is not published.
- The standalone PREVIEW.html opened from file:// and exported a valid FIT without a server.
- Desktop 1440px and mobile 390px layouts were inspected. Tables/charts scroll within their panels on narrow screens; the page does not overflow horizontally.

Not performed: live authenticated Strava API requests, GitHub deployment, physical Garmin transfer. Source timestamps and pending data are visible in the dashboard. Numeric fitness checks are heuristics, not a validated performance model.
