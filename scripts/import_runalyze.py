"""Usage: python scripts/import_runalyze.py export.csv
Exports only useful activity metrics, never notes, routes, account IDs or file hashes.
The CSV's sport IDs are Josh's; edit SPORT for a different account.
"""
import csv,json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
SPORT={'1772235':'Run','1772236':'Swim','1772237':'Ride','1772239':'WeightTraining','1772241':'RockClimbing','1772242':'Walk','1772243':'Hike','1772244':'Elliptical','1772245':'VirtualRide','1772246':'Yoga','1772247':'Hike','2154547':'StairStepper'}
def number(x):
 try:return float(x)
 except (ValueError,TypeError):return None
rows=[]
for r in csv.DictReader(open(sys.argv[1],encoding='utf-8-sig')):
 t=number(r.get('time'))
 if not t:continue
 local=datetime.fromtimestamp(t,timezone.utc)+timedelta(minutes=number(r.get('timezoneOffset')) or 0)
 rows.append({'id':'runalyze-'+r['id'],'source':'Runalyze CSV','type':SPORT.get(r.get('sportid'),'Other'),'name':r.get('title') or 'Activity','start_date':datetime.fromtimestamp(t,timezone.utc).isoformat(),'start_date_local':local.strftime('%Y-%m-%dT%H:%M:%S'),'distance':(number(r.get('distance')) or 0)*1000,'moving_time':number(r.get('s')),'elapsed_time':number(r.get('elapsedTime')),'average_heartrate':number(r.get('pulseAvg')),'max_heartrate':number(r.get('pulseMax')),'total_elevation_gain':number(r.get('elevationUp')),'runalyze_vo2':number(r.get('vo2max')),'garmin_vo2':number(r.get('fitVO2maxEstimate')),'runalyze_vo2_enabled':r.get('useVO2max')=='1','race_distance':number(r.get('race_officialDistance')),'race_time':number(r.get('race_officialTime'))})
Path(__file__).resolve().parents[1].joinpath('docs/history.json').write_text(json.dumps({'source':'Runalyze CSV','coverageEnd':max(a['start_date_local'][:10] for a in rows),'activities':rows},ensure_ascii=False,separators=(',',':')))
print('Imported',len(rows),'activities')
