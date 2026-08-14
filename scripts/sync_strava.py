#!/usr/bin/env python3
"""Sync Strava runs into docs/activities.json, including per-km splits.

Summary data is refetched every run (cheap, one call per 100 activities).
Per-km splits need one API call per activity, so they're cached: an activity
that already has splits is never refetched. A per-run cap keeps us inside
Strava's 100-reads-per-15-minutes limit; on the first run it backfills what
it can and catches up on subsequent hourly runs.

Secrets required: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN
(refresh token needs activity:read_all scope).
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

# Fetch from well before the block so nothing at the boundary is lost.
FETCH_FROM = datetime(2026, 7, 28, tzinfo=timezone.utc)
DETAIL_BUDGET = 80          # max detail calls per workflow run
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "activities.json")


def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def load_existing():
    try:
        with open(OUT) as f:
            return {a["strava_id"]: a for a in json.load(f).get("activities", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    token = post("https://www.strava.com/oauth/token", {
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
    })["access_token"]

    cached = load_existing()

    # --- summaries (paginated) ---
    after = int(FETCH_FROM.timestamp())
    summaries, page = [], 1
    while True:
        batch = get(
            "https://www.strava.com/api/v3/athlete/activities"
            f"?after={after}&per_page=100&page={page}", token)
        if not batch:
            break
        summaries += batch
        page += 1
        if page > 20:
            break
    print(f"{len(summaries)} activities in window across {page-1} page(s)")

    runs = {}
    for a in summaries:
        if a.get("type") != "Run":
            continue
        aid = a["id"]
        km = round(a["distance"] / 1000, 2)
        moving = a.get("moving_time") or 0
        rec = {
            "strava_id": aid,
            "date": a["start_date_local"][:10],
            "start": a["start_date_local"][11:16],
            "name": a.get("name", ""),
            "km": km,
            "moving_s": moving,
            "pace_s_per_km": round(moving / km) if km else None,
            "avg_hr": round(a["average_heartrate"]) if a.get("average_heartrate") else None,
            "max_hr": round(a["max_heartrate"]) if a.get("max_heartrate") else None,
            "elev_m": round(a.get("total_elevation_gain") or 0),
        }
        prev = cached.get(aid)
        if prev and prev.get("splits"):
            rec["splits"] = prev["splits"]      # keep cached detail
            if prev.get("laps"):
                rec["laps"] = prev["laps"]
        runs[aid] = rec

    # --- backfill splits for activities that lack them, newest first ---
    need = [r for r in sorted(runs.values(), key=lambda r: r["date"], reverse=True)
            if "splits" not in r]
    print(f"{len(need)} activities need splits; budget {DETAIL_BUDGET}")

    fetched = 0
    for rec in need[:DETAIL_BUDGET]:
        try:
            d = get(f"https://www.strava.com/api/v3/activities/{rec['strava_id']}"
                    "?include_all_efforts=false", token)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("Rate limited — stopping detail fetch, will resume next run")
                break
            print(f"  skip {rec['strava_id']}: HTTP {e.code}")
            continue
        # splits_metric: one entry per km (final one usually partial)
        rec["splits"] = [
            [round(s["distance"]), s["moving_time"],
             round(s["average_heartrate"]) if s.get("average_heartrate") else None]
            for s in (d.get("splits_metric") or [])
        ]
        laps = d.get("laps") or []
        if len(laps) > 1:                      # only useful if you pressed lap
            rec["laps"] = [
                {"name": l.get("name", ""), "km": round(l["distance"] / 1000, 2),
                 "s": l["moving_time"],
                 "hr": round(l["average_heartrate"]) if l.get("average_heartrate") else None}
                for l in laps
            ]
        fetched += 1
        time.sleep(0.4)

    out = sorted(runs.values(), key=lambda r: (r["date"], r["start"]))
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "with_splits": sum(1 for r in out if r.get("splits")),
        "activities": out,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"Wrote {len(out)} runs, {payload['with_splits']} with splits "
          f"({fetched} detail fetches this run)")


if __name__ == "__main__":
    sys.exit(main())
