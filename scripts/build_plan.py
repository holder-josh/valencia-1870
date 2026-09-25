"""Transcription of Valencia_2026_Sub3_Training_Plan.pdf, revised 23 Sep 2026.
Source plan is immutable in the UI; route edits are separate browser overrides.
Unspecified jogs: 75 seconds (PDF permits 60–90). Time steps use midpoint pace
only to estimate the remaining easy distance. These assumptions are exposed.
"""
import json
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parents[1]/'docs'
P={'easy':[305,340],'recovery':[330,370],'threshold':[255,260],'interval':[238,245],'goal':[253,254],'steady':[285,295],'stride':None}
def step(kind,value,unit='km',label=None):return {'kind':kind,'label':label or kind.title(),'unit':unit,'value':value,'pace':P.get(kind)}
def km(s):return s['value'] if s['unit']=='km' else s['value']*60/(sum(s['pace'])/2 if s['pace'] else 240) if s['unit']=='min' else 0
sessions=[]
def add(day,kind,total,title=None,steps=None,note='',maxkm=None,strength=0,optional=False):
 d=date(2026,9,21)+timedelta(days=day)
 sessions.append({'id':d.isoformat()+('-pm' if optional else ''),'date':d.isoformat(),'week':day//7+1,'type':kind,'title':title or {'rest':'Rest','easy':'Easy run','recovery':'Recovery','long':'Long run','medium':'Medium-long','threshold':'Threshold','interval':'Intervals','goal':'Goal-pace long','race':'Valencia Marathon','cross':'Cross-training'}[kind],'km':total,'maxKm':maxkm or total,'steps':steps if steps is not None else ([step('recovery' if kind=='recovery' else 'easy',total)] if total else []),'note':note,'strength':strength,'optional':optional,'source':'PDF · 23 Sep 2026'})
def quality(day,total,reps,length,kind='threshold',unit='min',recovery=2,recunit='min',strength=0,note=''):
 ss=[step('easy',3,label='Warm-up')]
 for i in range(reps):
  ss.append(step(kind,length,unit,f'{kind.title()} {i+1}'))
  if i<reps-1:ss.append(step('recovery',recovery,recunit,'Jog recovery'))
 ss.append(step('easy',round(total-sum(map(km,ss)),3),label='Cool-down'))
 add(day,kind,total,f'{reps} × {length:g} {unit} {"LT" if kind=="threshold" else "intervals"}',ss,note,strength=strength)
def strides(day,total,n,seconds=20,strength=0):
 ss=[]
 for i in range(n):
  ss.append(step('stride',seconds/60,'min',f'Stride {i+1}'))
  if i<n-1:ss.append(step('recovery',1.25,'min','Jog recovery'))
 ss=[step('easy',round(total-sum(map(km,ss)),3),label='Easy running')]+ss
 add(day,'easy',total,f'Easy + {n} × {seconds}s strides',ss,'Fast and relaxed; 60–90s jog between. Export defaults to 75s. Total distance estimated for time steps.',strength=strength)
def blocks(day,total,seq,note='',title=None):add(day,'goal',total,title,[step(k,v) for k,v in seq],note)
# Week 1
add(0,'cross',0,'Long ride',note='Completed: 113.2 km cycling, 5 h 09 moving. Counts as load, not running distance.')
add(1,'easy',10,note='Completed. Also 10 km hiking.');add(2,'rest',0)
add(3,'easy',10,note='PDF: 10–12 easy, or rest if heavy. A later discussion changed this to 2 × 3 km LT; available as an explicit revision.',maxkm=12)
add(4,'easy',12,note='Easy throughout. No fast finish.');add(5,'recovery',6,note='No strides.')
blocks(6,30,[('easy',18),('steady',5),('goal',5),('easy',2)],'Only if recovered; G only if controlled at 23 km. Otherwise 20–24 km easy.','30 km progression')
# Week 2
add(7,'rest',0);quality(8,14,3,10,strength=15);add(9,'easy',12);add(10,'medium',22,maxkm=25,note='22–25 km easy. Optional distance; no fast finish.');add(11,'easy',10,note='Morning only. Flight to Seoul later.');add(12,'rest',0,note='Land in Seoul. No run.');add(13,'easy',15,note='Route scouting.')
# Week 3
add(14,'rest',0);quality(15,14,2,15,strength=20);add(16,'easy',12);add(17,'medium',18,strength=15);add(18,'recovery',6);strides(19,8,6)
blocks(20,24,[('easy',8),('goal',4),('easy',1),('goal',4),('easy',7)],'2 × 4 km G. If G feels like threshold, use sustainable marathon effort.')
# Week 4
add(21,'rest',0);quality(22,15,3,10,strength=15);add(23,'easy',12);add(24,'medium',18);add(25,'recovery',6);add(26,'recovery',8)
blocks(27,26,[('easy',6),('goal',4),('steady',1),('goal',4),('steady',1),('goal',4),('easy',6)],'Extend only after a controlled 11 Oct; otherwise repeat 2 × 4 km. Optional race replaces this session.')
# Week 5
add(28,'rest',0);add(29,'medium',18);add(30,'easy',12);quality(31,15,2,18,strength=15);add(32,'recovery',8);add(33,'long',26,note='All easy. Cap 2 h 30 elapsed. No fast finish before hike.');add(34,'rest',0,note='Hotel checkout; hard hike tomorrow.')
# Week 6
add(35,'cross',0,'Hard hike',note='Major training load. No run.');add(36,'rest',0);add(37,'recovery',10);add(38,'easy',8)
blocks(39,26,[('easy',10),('goal',12),('easy',4)],'26 km with 12 G only after controlled 18 Oct and normal Wed/Thu running after the hike. Otherwise 20–26 easy or shorter/rest. Cap 2 h 30 elapsed.');sessions[-1]['minKm']=20
add(40,'rest',0,note='Flight to London. No run.');add(41,'easy',14,note='Easy after travel.')
# Week 7
add(42,'rest',0);quality(43,14,3,2,unit='km',recovery=.5,recunit='km',strength=20);add(44,'easy',12);add(45,'medium',20,strength=15);add(46,'recovery',6);strides(47,8,4)
blocks(48,30,[('easy',12),('goal',16),('easy',2)],'Extend only after controlled 12 G on 30 Oct. If missed/laboured, use 10–12 G or sustainable M; easy to 30.')
# Week 8
add(49,'rest',0);add(50,'easy',12,strength=15);quality(51,12,4,3,kind='interval');add(51,'recovery',4,'Optional PM recovery',note='At least 6 hours after AM; first session to drop.',optional=True);add(52,'recovery',8);add(53,'medium',20);strides(54,10,6)
blocks(55,32,[('easy',10),('goal',20),('easy',2)],'Only after controlled 16 G on 8 Nov. Race kit and fuel. 21 days to race. Do not force a test.','Main rehearsal · 20 km G')
# Week 9
add(56,'rest',0);add(57,'recovery',10);add(58,'easy',12);quality(59,12,2,8,strength=10);add(60,'recovery',6);strides(61,8,4)
blocks(62,24,[('easy',14),('goal',8),('easy',2)],'Confirmed race pace. Use G only if 15 Nov supports it.')
# Week 10
add(63,'rest',0);quality(64,10,4,2,kind='interval',strength=10);add(65,'easy',8);blocks(66,10,[('easy',3),('goal',5),('easy',2)],'Comfortably controlled.','Race pace');add(67,'recovery',4);strides(68,4,4);add(69,'long',18,note='All easy. Finish with something left.')
# Week 11
add(70,'rest',0);strides(71,8,4);blocks(72,8,[('easy',3),('goal',3),('easy',2)],'Use race shoes.','Dress rehearsal');add(73,'easy',6);add(74,'recovery',3,'Brief shakeout');strides(75,3,3,15)
add(76,'race',42.195,steps=[step('goal',42.195)],note='If rehearsals support sub-3: first 3 km 4:17–4:20, then 4:13–4:14. Use official distance markers.')
phases=['Adjusted','Travel','Build','Specific','Build','Hike / fly','Specific','Peak','Taper 1','Taper 2','Race']
locations=['London','London → Seoul','Seoul','Seoul','Seoul','Seoul → London','London','London','London','London','Valencia']
ranges=[[68,70],[73,76],[82,82],[85,85],[79,79],[52,58],[90,90],[94,98],[72,72],[54,54],[28,28]]
weeks=[{'number':i+1,'start':(date(2026,9,21)+timedelta(days=7*i)).isoformat(),'phase':phases[i],'location':locations[i],'pdfRange':ranges[i]} for i in range(11)]
plan={'schema_version':2,'name':'Valencia / 2026','raceDate':'2026-12-06','startDate':'2026-09-21','goalTimeSeconds':10800,'goalPace':[253,254],'source':{'file':'training-plan.pdf','name':'Valencia_2026_Sub3_Training_Plan.pdf','revised':'2026-09-23'},'paces':P,'weeks':weeks,'sessions':sessions,'assumptions':['Time-based steps use midpoint target pace to estimate distance; actual distance varies.','Easy remainder after timed quality is estimated to reach the printed session total.','Strides have no pace alarm; estimated at 4:00/km only for distance budgeting.','Jog between strides defaults to 75 seconds within the PDF’s 60–90-second range.','Optional 11 Nov PM run is excluded until enabled.','30 Oct defaults to the full conditional 26 km session.','24 Sep PDF easy session is preserved; later 2 × 3 km discussion is an explicit selectable revision.']}
(ROOT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 for w in weeks:
  s=[s for s in sessions if s['week']==w['number'] and not s['optional'] and s['type']!='race']; print(w['number'],sum(x['km'] for x in s),w['pdfRange'])
