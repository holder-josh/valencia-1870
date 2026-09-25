import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error

spec = importlib.util.spec_from_file_location('sync', Path(__file__).resolve().parents[1] / 'scripts/sync_strava.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

ACT = {'id': 1, 'type': 'Run', 'name': '=Workout', 'start_date': '2026-09-24T07:00:00Z',
       'start_date_local': '2026-09-24T08:00:00Z', 'distance': 3000, 'moving_time': 780, 'elapsed_time': 900}
LAP = {'distance': 3000, 'moving_time': 780, 'elapsed_time': 900, 'average_heartrate': 160, 'start_index': 0, 'end_index': 2}

class Fake:
    def __init__(self, summaries=None, fail=None):
        self.calls = 0
        self.summaries = [ACT] if summaries is None else summaries
        self.fail = fail
    def get(self, path):
        self.calls += 1
        if path.startswith('/athlete/'):
            return self.summaries
        if self.fail:
            raise self.fail
        if '/streams?' in path:
            return {'time': {'data': [0, 450, 900], 'series_type': 'time', 'original_size': 3, 'resolution': 'high'}}
        return {**ACT, 'laps': [LAP], 'splits_metric': [LAP], 'description': '2 x 3 km',
                'athlete': {'secret': 'not-exported'}, 'map': {'polyline': 'not-exported'}}

class ExportTests(unittest.TestCase):
    def test_full_export_cache_and_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            sync.sync(Fake(), docs)
            data = json.loads((docs/'workouts.json').read_text())
            a = data['activities'][0]
            self.assertEqual(a['moving_pace_s_per_km'], 260)
            self.assertEqual(a['elapsed_pace_s_per_km'], 300)
            self.assertEqual(a['nonmoving_time_s'], 120)
            self.assertEqual(a['laps'][0]['end_index'], 2)
            self.assertNotIn('athlete', a)
            self.assertNotIn('map', a)
            self.assertIn("'=Workout", (docs/'workouts.csv').read_text())
            self.assertEqual(json.loads((docs/'activities.json').read_text())['activities'][0]['splits'], [[3000,780,160]])
            client = Fake()
            sync.sync(client, docs)
            self.assertEqual(client.calls, 1)
            sync.sync(Fake([]), docs)
            self.assertEqual(list((docs/'streams').glob('*.json')), [])
    def test_budget_preserves_legacy_and_pending_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            sync.dump(docs/'activities.json', {'activities':[{'strava_id':1,'splits':[[3000,780,160]]}]})
            sync.sync(Fake(fail=sync.BudgetReached()), docs)
            self.assertEqual(json.loads((docs/'workouts.json').read_text())['sync']['pending_details'], 1)
            self.assertTrue(json.loads((docs/'activities.json').read_text())['activities'][0]['splits'])
    def test_zero_distance_and_missing_values(self):
        self.assertIsNone(sync.metrics({'distance':0})['moving_pace_s_per_km'])
        self.assertIsNone(sync.metrics({})['nonmoving_time_s'])
    def test_auth_failure_does_not_replace_public_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            sync.dump(docs/'workouts.json', {'activities':[]})
            before = (docs/'workouts.json').read_bytes()
            with self.assertRaises(urllib.error.HTTPError):
                sync.sync(Fake(fail=urllib.error.HTTPError('url',403,'Forbidden',{},None)), docs)
            self.assertEqual(before, (docs/'workouts.json').read_bytes())
    def test_no_streams_is_not_retried_every_run(self):
        class NoStreams(Fake):
            def get(self, path):
                if '/streams?' in path:
                    self.calls += 1
                    raise urllib.error.HTTPError('url',404,'Not Found',{},None)
                return super().get(path)
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            sync.sync(NoStreams(), docs)
            self.assertEqual(json.loads((docs/'workouts.json').read_text())['activities'][0]['streams_status'], 'unavailable')
            client = NoStreams()
            sync.sync(client, docs)
            self.assertEqual(client.calls, 1)

if __name__ == '__main__':
    unittest.main()
