#!/usr/bin/env python3
"""Pull runs from the Strava API since block start and write docs/activities.json.

Requires repo secrets: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN
(refresh token must have activity:read scope).
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

BLOCK_START = datetime(2026, 8, 3, tzinfo=timezone.utc)
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "activities.json")

def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode())
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def main():
    tok = post("https://www.strava.com/oauth/token", {
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
    })["access_token"]

    after = int(BLOCK_START.timestamp())
    acts, page = [], 1
    while True:
        batch = get(f"https://www.strava.com/api/v3/athlete/activities?after={after}&per_page=100&page={page}", tok)
        if not batch:
            break
        acts += batch
        page += 1

    runs = []
    for a in acts:
        if a.get("type") != "Run":
            continue
        km = round(a["distance"] / 1000, 2)
        moving = a.get("moving_time") or 0
        runs.append({
            "date": a["start_date_local"][:10],
            "name": a.get("name", ""),
            "km": km,
            "moving_s": moving,
            "pace_s_per_km": round(moving / km) if km else None,
            "avg_hr": round(a["average_heartrate"]) if a.get("average_heartrate") else None,
            "elev_m": round(a.get("total_elevation_gain") or 0),
            "strava_id": a["id"],
        })

    runs.sort(key=lambda r: r["date"])
    payload = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "activities": runs}
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"Wrote {len(runs)} runs to activities.json")

if __name__ == "__main__":
    sys.exit(main())
