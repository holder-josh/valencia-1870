#!/usr/bin/env python3
"""Bounded, cached Strava sync. Standard library only; see README.md."""
import csv
import io
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DOCS = Path(__file__).resolve().parent.parent / 'docs'
API = 'https://www.strava.com/api/v3'
FETCH_FROM = '2026-07-28T00:00:00+00:00'
STREAM_KEYS = 'time,distance,velocity_smooth,heartrate,cadence,watts,altitude,grade_smooth,temp,moving'
# 144 scheduled runs * 5 requests = 720 reads/day at most.
READ_BUDGET = 5
FIELDS = '''id name type sport_type start_date start_date_local timezone utc_offset
 distance moving_time elapsed_time total_elevation_gain elev_high elev_low
 average_speed max_speed average_heartrate max_heartrate has_heartrate
 average_cadence average_temp average_watts max_watts weighted_average_watts kilojoules
 device_watts calories suffer_score perceived_exertion workout_type description
 gear_id device_name trainer commute manual private visibility flagged'''.split()
LAP_FIELDS = '''id name lap_index split start_index end_index start_date start_date_local
 distance moving_time elapsed_time total_elevation_gain elevation_difference
 average_speed max_speed average_heartrate max_heartrate average_cadence
 average_watts max_watts device_watts pace_zone average_grade_adjusted_speed'''.split()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def load(path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(content, encoding='utf-8')
    tmp.replace(path)


def dump(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


class BudgetReached(Exception):
    pass


class Client:
    def __init__(self, token):
        self.token = token
        self.calls = 0
        self.exhausted = False

    def get(self, path):
        if self.calls >= READ_BUDGET or self.exhausted:
            raise BudgetReached()
        self.calls += 1
        req = urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + self.token})
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                for prefix in ('X-ReadRateLimit', 'X-RateLimit'):
                    limits = response.headers.get(prefix + '-Limit')
                    usage = response.headers.get(prefix + '-Usage')
                    if limits and usage:
                        self.exhausted |= any(u >= l - 2 for u, l in zip(
                            map(int, usage.split(',')), map(int, limits.split(','))))
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise BudgetReached() from None
            raise


def authenticate():
    data = urllib.parse.urlencode({
        'client_id': os.environ['STRAVA_CLIENT_ID'],
        'client_secret': os.environ['STRAVA_CLIENT_SECRET'],
        'refresh_token': os.environ['STRAVA_REFRESH_TOKEN'],
        'grant_type': 'refresh_token',
    }).encode()
    with urllib.request.urlopen('https://www.strava.com/oauth/token', data=data, timeout=45) as response:
        result = json.load(response)
    # Never write credentials to the public export or logs.
    if result.get('refresh_token') != os.environ['STRAVA_REFRESH_TOKEN']:
        print('::warning::Strava returned a rotated refresh token. Update the STRAVA_REFRESH_TOKEN secret via your OAuth setup before the next sync.')
    return result['access_token']


def metrics(obj):
    distance = obj.get('distance')
    moving = obj.get('moving_time')
    elapsed = obj.get('elapsed_time')
    return {
        'moving_pace_s_per_km': round(moving * 1000 / distance, 3) if distance and moving is not None else None,
        'elapsed_pace_s_per_km': round(elapsed * 1000 / distance, 3) if distance and elapsed is not None else None,
        'nonmoving_time_s': max(0, elapsed - moving) if elapsed is not None and moving is not None else None,
    }


def pick(obj, fields):
    return {k: obj[k] for k in fields if k in obj}


def normalize(obj, fields=FIELDS):
    return {**pick(obj, fields), **metrics(obj)}


def expired(stamp, hours):
    return not stamp or (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds() >= hours * 3600


def csv_text(rows, headers):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        # Escape spreadsheet formulas in user-entered text.
        writer.writerow({k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r')) else v)
                         for k, v in row.items()})
    return out.getvalue()


def legacy_record(a, old):
    r = {'strava_id': a['id'], 'date': a['start_date_local'][:10],
         'start': a['start_date_local'][11:16], 'name': a.get('name', ''),
         'km': round(a.get('distance', 0) / 1000, 2), 'moving_s': a.get('moving_time', 0),
         'pace_s_per_km': a.get('moving_pace_s_per_km'), 'avg_hr': a.get('average_heartrate'),
         'max_hr': a.get('max_heartrate'), 'elev_m': a.get('total_elevation_gain', 0)}
    if 'splits_metric' in a:
        r['splits'] = [[s.get('distance'), s.get('moving_time'), s.get('average_heartrate')] for s in a['splits_metric']]
        r['laps'] = [{'name': l.get('name', ''), 'km': l.get('distance', 0)/1000,
                      's': l.get('moving_time'), 'hr': l.get('average_heartrate')} for l in a.get('laps', [])]
    else:
        for k in ('splits', 'laps'):
            if k in old:
                r[k] = old[k]
    return r


def sync(client, docs=DOCS):
    generated = now()
    previous = load(docs / 'workouts.json', {'activities': []})
    cache = {a['id']: a for a in previous['activities']}
    old_runs = {a['strava_id']: a for a in load(docs / 'activities.json', {'activities': []})['activities']}
    summaries = []
    after = int(datetime.fromisoformat(os.getenv('STRAVA_FETCH_FROM', FETCH_FROM)).timestamp())
    page = 1
    # Do not publish an incomplete activity list if pagination fails or hits budget.
    while True:
        batch = client.get(f'/athlete/activities?after={after}&per_page=100&page={page}')
        summaries.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    records = []
    for summary in summaries:
        rec = dict(cache.get(summary['id'], {}))
        rec.update(normalize(summary))
        rec['strava_url'] = f"https://www.strava.com/activities/{summary['id']}"
        rec.setdefault('detail_status', 'pending')
        rec.setdefault('streams_status', 'pending')
        records.append(rec)
    records.sort(key=lambda a: a['start_date'], reverse=True)
    # New activities first, then missing history, then refresh recent activities daily
    # and older ones weekly (oldest successful fetch first).
    def priority(a):
        missing = a.get('detail_fetched_at') is None or a.get('streams_fetched_at') is None
        if missing:
            return (0, -datetime.fromisoformat(a['start_date'].replace('Z', '+00:00')).timestamp())
        return (1, a.get('detail_fetched_at', ''))
    limited = False
    for rec in sorted(records, key=priority):
        hours = 24 if not expired(rec['start_date'].replace('Z', '+00:00'), 7*24) else 7*24
        aid = rec['id']
        try:
            if expired(rec.get('detail_fetched_at'), hours):
                detail = client.get(f'/activities/{aid}?include_all_efforts=false')
                for key in FIELDS:
                    rec.pop(key, None)
                rec.update(normalize(detail))
                for kind in ('laps', 'splits_metric', 'splits_standard'):
                    rec[kind] = [normalize(x, LAP_FIELDS) for x in detail.get(kind, [])]
                rec['gear'] = pick(detail.get('gear') or {}, ['id', 'name', 'distance'])
                rec['detail_fetched_at'] = generated
                rec['detail_status'] = 'available'
                rec.pop('detail_error', None)
            if expired(rec.get('streams_fetched_at'), hours):
                try:
                    streams = client.get(f'/activities/{aid}/streams?keys={STREAM_KEYS}&key_by_type=true')
                except urllib.error.HTTPError as exc:
                    if exc.code != 404:
                        raise
                    streams = {}
                dump(docs / 'streams' / f'{aid}.json', {
                    'schema_version': 1, 'activity_id': aid, 'fetched_at': generated,
                    'streams': streams,
                })
                rec['streams_file'] = f'streams/{aid}.json'
                rec['streams_status'] = 'available' if streams else 'unavailable'
                rec['streams_fetched_at'] = generated
                rec.pop('detail_error', None)
        except BudgetReached:
            limited = True
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise
            rec['detail_error'] = f'HTTP {exc.code}; retry on next sync'
        except (TimeoutError, urllib.error.URLError):
            rec['detail_error'] = 'Network error; retry on next sync'
    # Summary pagination is authoritative: remove exports for deleted/out-of-window activities.
    valid = {str(a['id']) for a in records}
    for path in (docs / 'streams').glob('*.json'):
        if path.stem not in valid:
            path.unlink()
    payload = {'schema_version': 1, 'updated': generated, 'fetch_from': os.getenv('STRAVA_FETCH_FROM', FETCH_FROM),
               'sync': {'read_requests': client.calls, 'budget_reached': limited,
                        'pending_details': sum(a['detail_status'] == 'pending' for a in records),
                        'pending_streams': sum(a['streams_status'] == 'pending' for a in records)},
               'units': {'distance': 'metres', 'time': 'seconds', 'speed': 'metres/second',
                         'pace': 'seconds/km', 'heartrate': 'bpm', 'power': 'watts',
                         'cadence': 'Strava native value, unconverted'},
               'notes': ['elapsed_time is total start-to-finish time, including stops.',
                         'nonmoving_time_s = elapsed_time - moving_time; not necessarily device pause time.',
                         'Laps are recorded laps, not guaranteed planned workout steps.',
                         'Missing fields are unavailable, not zero. Stream files retain Strava samples and metadata.',
                         'No GPS coordinates, maps, athlete profiles, or credentials are exported.'],
               'activities': records}
    dump(docs / 'workouts.json', payload)
    headers = FIELDS + list(metrics({})) + ['strava_url', 'detail_status', 'detail_fetched_at', 'streams_status', 'streams_file', 'streams_fetched_at']
    write(docs / 'workouts.csv', csv_text(records, headers))
    rows = []
    for a in records:
        for kind in ('laps', 'splits_metric', 'splits_standard'):
            for index, lap in enumerate(a.get(kind, []), 1):
                rows.append({'activity_id': a['id'], 'activity_name': a.get('name'), 'kind': kind, 'sequence': index, **lap})
    write(docs / 'workout-laps.csv', csv_text(rows, ['activity_id', 'activity_name', 'kind', 'sequence'] + LAP_FIELDS + list(metrics({}))))
    runs = [legacy_record(a, old_runs.get(a['id'], {})) for a in records
            if a.get('type') == 'Run' or a.get('sport_type') in ('Run', 'TrailRun', 'VirtualRun')]
    runs.sort(key=lambda r: (r['date'], r['start']))
    dump(docs / 'activities.json', {'updated': generated, 'with_splits': sum(bool(a.get('splits')) for a in runs), 'activities': runs})
    print(f'Exported {len(records)} activities, {len(runs)} runs; {client.calls} API reads; {payload["sync"]}')


if __name__ == '__main__':
    sync(Client(authenticate()))
