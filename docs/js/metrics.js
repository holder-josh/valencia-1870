export const finite = x => typeof x === 'number' && Number.isFinite(x);
export const sum = (xs, f=x=>x) => xs.reduce((n,x)=>n+(finite(f(x))?f(x):0),0);
export const mean = xs => xs.length?sum(xs)/xs.length:null;
export const median = xs => {const a=xs.filter(finite).sort((a,b)=>a-b);return a.length?(a[Math.floor((a.length-1)/2)]+a[Math.ceil((a.length-1)/2)])/2:null;};
export const pace = s => !finite(s)||s<=0?'—':`${Math.floor(Math.round(s)/60)}:${String(Math.round(s)%60).padStart(2,'0')}`;
export const duration = seconds => {if(!finite(seconds))return '—';const s=Math.round(seconds);return s>=3600?`${Math.floor(s/3600)}:${String(Math.floor(s%3600/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`:`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;};
export const addDays = (d,n) => {const a=new Date(d+'T12:00:00Z');a.setUTCDate(a.getUTCDate()+n);return a.toISOString().slice(0,10);};
export const monday = d => addDays(d,-((new Date(d+'T12:00:00Z').getUTCDay()+6)%7));
export const isRun = a => ['Run','TrailRun','VirtualRun'].includes(a.sport_type||a.type);
export const isRide = a => ['Ride','VirtualRide','GravelRide','MountainBikeRide','EBikeRide'].includes(a.sport_type||a.type);
export function normalize(a){
 const legacy = a.strava_id != null;
 const b = legacy?{id:a.strava_id,type:'Run',source:'Strava summary',name:a.name,start_date_local:`${a.date}T${a.start||'12:00'}:00`,distance:a.km*1000,moving_time:a.moving_s,average_heartrate:a.avg_hr,max_heartrate:a.max_hr,total_elevation_gain:a.elev_m,splits_metric:(a.splits||[]).map((s,i)=>({split:i+1,distance:s[0],moving_time:s[1],average_heartrate:s[2]})),laps:(a.laps||[]).map((l,i)=>({name:l.name,lap_index:i,distance:l.km*1000,moving_time:l.s,average_heartrate:l.hr})),strava_url:`https://www.strava.com/activities/${a.strava_id}`}:{...a};
 b.source ||= 'Strava'; b.date=(b.start_date_local||b.start_date||'').slice(0,10);b.km=(b.distance||0)/1000;
 b.pace=b.distance>0&&b.moving_time>0?b.moving_time*1000/b.distance:null;
 b.elapsedPace=b.distance>0&&b.elapsed_time>0?b.elapsed_time*1000/b.distance:null;
 b.stopped=finite(b.elapsed_time)&&finite(b.moving_time)?Math.max(0,b.elapsed_time-b.moving_time):null;
 b.stopPct=b.elapsed_time>0&&finite(b.stopped)?b.stopped/b.elapsed_time*100:null;
 b.efficiency=b.average_heartrate>0&&b.moving_time>0&&b.distance>0?b.distance/(b.moving_time/60)/b.average_heartrate:null;
 return b;
}
function timeMatches(a,b){
 const wall=x=>Date.parse((x.start_date_local||'').slice(0,19)+'Z');
 if(Math.abs(wall(a)-wall(b))<12*60000)return true;
 // Original compact export used UTC clock text; detailed exporter uses local clock.
 return a.source==='Strava summary'&&Math.abs(wall(a)-Date.parse(b.start_date))<12*60000 || b.source==='Strava summary'&&Math.abs(wall(b)-Date.parse(a.start_date))<12*60000;
}
export function mergeActivities(history,legacy,live){
 const out=[];
 for(const raw of [...history,...legacy,...live]){
  const a=normalize(raw);
  const i=out.findIndex(b=>String(b.id)===String(a.id)|| (b.date===a.date && (isRun(a)===isRun(b)) && (a.type===b.type||isRun(a)&&isRun(b)) && Math.abs(a.distance-b.distance)<Math.max(100,a.distance*.02) && timeMatches(a,b)));
  if(i<0)out.push(a);else {const old=out[i];out[i]=normalize({...old,...a,start_date_local:a.source==='Strava summary'&&old.source==='Runalyze CSV'?old.start_date_local:a.start_date_local,runalyze_vo2:old.runalyze_vo2??a.runalyze_vo2,runalyze_vo2_enabled:old.runalyze_vo2_enabled??a.runalyze_vo2_enabled,garmin_vo2:old.garmin_vo2??a.garmin_vo2,race_distance:old.race_distance??a.race_distance,race_time:old.race_time??a.race_time});}
 }
 return out.sort((a,b)=>b.start_date_local.localeCompare(a.start_date_local));
}
export function stepKm(s){return s.unit==='km'?s.value:s.unit==='min'?s.value*60/(s.pace?mean(s.pace):s.kind==='stride'?240:330):0;}
export const sessionKm = s => sum(s.steps||[],stepKm);
export const sessionSeconds = s => sum(s.steps||[],x=>x.unit==='min'?x.value*60:x.unit==='km'?x.value*(x.pace?mean(x.pace):330):0);
export const qualityKm = s => sum((s.steps||[]).filter(x=>['threshold','goal','interval'].includes(x.kind)),stepKm);
export function weekly(sessions,activities,start,today){
 const end=addDays(start,6),ss=sessions.filter(s=>s.date>=start&&s.date<=end&&(!s.optional||s.enabled));
 const aa=activities.filter(a=>a.date>=start&&a.date<=end&&a.date<=today),runs=aa.filter(isRun);
 const plan=sum(ss,s=>s.km),due=sum(ss.filter(s=>s.date<today),s=>s.km),actual=sum(runs,a=>a.km),before=sum(runs.filter(a=>a.date<today),a=>a.km);
 const runTime=sum(runs,a=>a.moving_time);
 return {start,end,sessions:ss,activities:aa,plan,due,actual,before,delta:before-due,runTime,avgPace:actual?runTime/actual:null,rideTime:sum(aa.filter(isRide),a=>a.moving_time),otherTime:sum(aa.filter(a=>!isRun(a)&&!isRide(a)),a=>a.moving_time),quality:sum(ss,qualityKm),longest:Math.max(0,...runs.map(a=>a.km)),days:new Set(runs.map(a=>a.date)).size};
}
export function splitMetrics(a,startKm=0,endKm=a.km){
 let pos=0,dist=0,time=0,hr=0,hrTime=0,elapsed=0,elapsedKnown=true,full=0;
 for(const s of a.splits_metric||[]){const d=s.distance||0;const start=pos;pos+=d;const overlap=Math.max(0,Math.min(pos,endKm*1000)-Math.max(start,startKm*1000));if(!overlap||!d)continue;const f=overlap/d;dist+=overlap;time+=(s.moving_time||0)*f;if(s.average_heartrate>0){hr+=s.average_heartrate*(s.moving_time||0)*f;hrTime+=(s.moving_time||0)*f;}if(finite(s.elapsed_time))elapsed+=s.elapsed_time*f;else elapsedKnown=false;if(f>.999)full++;}
 return {distance:dist,moving:time,pace:dist&&time?time*1000/dist:null,hr:hrTime?hr/hrTime:null,elapsed:elapsedKnown&&dist?elapsed:null,method:'Split overlap estimate',fullSplits:full};
}
export function aerobicEligibility(a,maxHR=198){
 const reasons=[];const splits=(a.splits_metric||[]).filter(s=>s.distance>=800&&s.moving_time>0).map(s=>s.moving_time*1000/s.distance);
 const cv=splits.length>=4?Math.sqrt(mean(splits.map(v=>(v-mean(splits))**2)))/mean(splits):null;
 if(!isRun(a)||a.km<5||a.moving_time<1200)reasons.push('Under 5 km / 20 min');
 if(!finite(a.stopPct))reasons.push('Elapsed time missing');else if(a.stopPct>3)reasons.push('Stops >3%');
 if(!a.average_heartrate)reasons.push('HR missing');else if(a.average_heartrate<maxHR*.65||a.average_heartrate>maxHR*.85)reasons.push('Outside 65–85% HRmax');
 if(!finite(a.total_elevation_gain))reasons.push('Elevation missing');else if(a.total_elevation_gain/Math.max(a.km,.1)>15)reasons.push('Hilly >15 m/km');
 if(cv===null)reasons.push('Steadiness unverified');else if(cv>.08)reasons.push('Variable pace >8%');
 return {eligible:!reasons.length,reasons,cv};
}
export function intervalsFromStream(payload){
 const s=payload.streams||payload;const values=k=>Array.isArray(s[k])?s[k]:s[k]?.data||[];
 const t=values('time'),d=values('distance'),hr=values('heartrate'),moving=values('moving'),alt=values('altitude');let cum=0;const rows=[];
 if(t.length!==d.length)return [];
 for(let i=1;i<t.length;i++){
  const dt=t[i]-t[i-1],dd=d[i]-d[i-1];if(dt<=0||dd<0)continue;
  const on=(moving.length===t.length?moving[i]!==false:dd/dt>.5)&&dd>0;
  const mt=on?dt:0;
  rows.push({t0:t[i-1],t1:t[i],d0:d[i-1],d1:d[i],m0:cum,m1:cum+mt,dt,dd,mt,hr:hr[i]>0?hr[i]:null,alt:alt[i],gap:dt>30,pace:mt&&dd?mt*1000/dd:null});cum+=mt;
 }
 return rows;
}
export function segment(rows,start,end,coordinate='d',target=null){
 let dist=0,mt=0,ht=0,hs=0,inside=0,first=null,last=null,gaps=0;
 for(const r of rows){const a=r[coordinate+'0'],b=r[coordinate+'1'];if(b<=a)continue;const lo=Math.max(a,start),hi=Math.min(b,end);if(hi<=lo)continue;const f=(hi-lo)/(b-a);const st=r.t0+(lo-a)/(b-a)*r.dt,en=r.t0+(hi-a)/(b-a)*r.dt;first??=st;last=en;dist+=r.dd*f;mt+=r.mt*f;if(r.hr&&r.mt){ht+=r.mt*f;hs+=r.hr*r.mt*f;}if(r.gap)gaps+=r.dt*f;if(target&&r.pace>=target[0]&&r.pace<=target[1])inside+=r.mt*f;
 }
 return {distance:dist,moving:mt,elapsed:first===null?null:last-first,pace:dist&&mt?mt*1000/dist:null,hr:ht?hs/ht:null,insidePct:target&&mt?inside/mt*100:null,gaps,method:'Strava streams'};
}
export function workoutExecution(session,streamRows,a){
 let rows=streamRows,method='Strava streams',hasStreams=rows.length>0;
 if(!hasStreams){
  const laps=a.laps||[],useLaps=laps.length&&Math.abs(sum(laps,l=>l.distance)-(a.distance||a.km*1000))<Math.max(100,a.km*30);
  const source=useLaps?laps:(a.splits_metric||[]);method=useLaps?'Recorded-lap overlap estimate':'Split overlap estimate';
  let d=0,t=0,m=0;rows=source.filter(l=>l.distance>0&&l.moving_time>0).map(l=>{const dt=l.elapsed_time||l.moving_time,mt=l.moving_time,dd=l.distance;const r={d0:d,d1:d+dd,t0:t,t1:t+dt,m0:m,m1:m+mt,dd,dt,mt,hr:l.average_heartrate,pace:mt*1000/dd,gap:false};d+=dd;t+=dt;m+=mt;return r;});
 }
 let cursorD=0,cursorM=0,unknownBoundary=false;
 return session.steps.map(s=>{
  if(s.unit==='open'||unknownBoundary){unknownBoundary=true;return {step:s,method:'Open step; manual alignment needed'};}
  const coord=s.unit==='min'?'m':'d',start=coord==='m'?cursorM:cursorD,end=start+(s.unit==='min'?s.value*60:s.value*1000);
  const result=segment(rows,start,end,coord,hasStreams?s.pace:null);
  const boundary=rows.find(r=>r[coord+'1']>=end&&r[coord+'1']>r[coord+'0']);
  if(boundary){const frac=(end-boundary[coord+'0'])/(boundary[coord+'1']-boundary[coord+'0']);cursorD=boundary.d0+frac*boundary.dd;cursorM=boundary.m0+frac*boundary.mt;}else {cursorD=rows.at(-1)?.d1||cursorD;cursorM=rows.at(-1)?.m1||cursorM;}
  result.complete=coord==='d'?result.distance>=(end-start)*.98:result.moving>=(end-start)*.98;
  return {...result,step:s,method};
 });
}

export function streamAerobic(rows){
 let lastStop=-Infinity;
 const kept=rows.filter(r=>{if(!r.mt||r.gap)lastStop=r.t1;return r.t0>=600&&r.t0-lastStop>=90&&r.mt>0&&!r.gap&&r.hr>=90&&r.hr<=205&&r.pace>=240&&r.pace<=420;});
 const total=sum(kept,r=>r.mt);if(total<1200)return {efficiency:null,drift:null,seconds:total,reason:'Needs 20 clean minutes after warm-up / stops'};
 const aggregate=rs=>{const mt=sum(rs,r=>r.mt),dist=sum(rs,r=>r.dd),hr=sum(rs,r=>r.hr*r.mt)/mt;return dist/(mt/60)/hr;};
 let cursor=0;const halves=[[],[]];for(const r of kept){halves[cursor<total/2?0:1].push(r);cursor+=r.mt;}
 const speed=mean(kept.map(r=>r.dd/r.mt)),cv=Math.sqrt(mean(kept.map(r=>(r.dd/r.mt-speed)**2)))/speed;
 const one=aggregate(halves[0]),two=aggregate(halves[1]);return {efficiency:aggregate(kept),drift:cv<.1?(1-two/one)*100:null,seconds:total,cv,reason:cv>=.1?'Variable pace; drift suppressed':null};
}
export function riegel(distanceKm,timeSeconds,exponent=1.06){return distanceKm>0&&timeSeconds>0?timeSeconds*(42.195/distanceKm)**exponent:null;}
export function validateSession(s){
 if(!s||!/^\d{4}-\d{2}-\d{2}$/.test(s.date)||!s.title?.trim())throw Error('Enter a date and workout name.');
 if(!Array.isArray(s.steps)||s.steps.length>50)throw Error('Use at most 50 workout steps.');
 for(const x of s.steps){if(!['km','min','open'].includes(x.unit)||!finite(x.value)||x.unit!=='open'&&(x.value<=0||x.value>1000))throw Error('Each step needs a positive distance or duration.');if(x.pace&&(!Array.isArray(x.pace)||x.pace.length!==2||!x.pace.every(finite)||x.pace[0]<120||x.pace[1]>1200||x.pace[0]>x.pace[1]))throw Error('Pace bounds must be 2:00–20:00/km, fastest first.');}
 return true;
}
