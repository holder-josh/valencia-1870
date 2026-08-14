# Pfitz 18/70 — Valencia 2026

Phone-first dashboard for the Pfitzinger 18/70 block (3 Aug → 6 Dec 2026), with hourly
Strava sync so actual mileage overlays the book schedule automatically.

## Layout
- `docs/index.html` — the dashboard (GitHub Pages serves from `/docs`)
- `docs/plan.json` — the book schedule as data (weeks-to-goal numbering, km as printed)
- `docs/activities.json` — actual runs, written by the sync job
- `scripts/sync_strava.py` + `.github/workflows/sync.yml` — the automation

## Setup (one-time, ~10 minutes)
1. Create a repo, push these files. In **Settings → Pages**, set source to
   `main` branch, `/docs` folder. Bookmark the Pages URL on your phone
   (Share → Add to Home Screen makes it feel like an app).
2. Create a Strava API application at strava.com/settings/api. Note the
   **Client ID** and **Client Secret**.
3. Get a refresh token with `activity:read` scope:
   - Visit (with your client ID substituted):
     `https://www.strava.com/oauth/authorize?client_id=XXX&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all`
   - Approve, copy the `code=` value from the redirected URL.
   - Exchange it:
     `curl -X POST https://www.strava.com/oauth/token -d client_id=XXX -d client_secret=YYY -d code=ZZZ -d grant_type=authorization_code`
   - Save the `refresh_token` from the response.
4. In the repo, **Settings → Secrets and variables → Actions**, add
   `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.
5. Run the workflow once manually (Actions → Sync Strava → Run workflow) to
   check it commits `activities.json`. After that it runs hourly.

## Tuning
- Goal MP and the LT/V̇O₂max working bands are at the top of the `<script>` in
  `index.html` (`CONFIG`). Retune LT after Oxford.
- The plan itself lives in `plan.json` — edit there if a week gets rearranged.
