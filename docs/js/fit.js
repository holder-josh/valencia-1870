import {Encoder,Decoder,Stream,Profile} from '../vendor/fit/src/index.js';
import {validateSession} from './metrics.js';
export function encodeWorkout(session,tolerance=0){
 validateSession(session);if(!session.steps.length)throw Error('This day has no workout steps.');
 const e=new Encoder();
 let serial=2166136261;for(const ch of JSON.stringify([session.date,session.title,session.steps,tolerance]))serial=Math.imul(serial^ch.charCodeAt(0),16777619)>>>0;
 serial=serial||1;
 e.onMesg(Profile.MesgNum.FILE_ID,{type:'workout',manufacturer:'development',product:1,serialNumber:serial,timeCreated:new Date()});
 e.onMesg(Profile.MesgNum.WORKOUT,{wktName:(session.date.slice(5)+' '+session.title).replace(/[^\x20-\x7E]/g,' ').slice(0,40),sport:'running',numValidSteps:session.steps.length});
 session.steps.forEach((s,i)=>{
  // SDK accepts the raw parent fields; subfield values are ignored by the encoder.
  // FIT distance in centimetres; duration in milliseconds; speed in mm/s.
  const p=s.pace;const msg={messageIndex:i,wktStepName:s.label.replace(/[^\x20-\x7E]/g,' ').slice(0,30),durationType:s.unit==='km'?'distance':s.unit==='min'?'time':'open',durationValue:s.unit==='km'?Math.round(s.value*100000):s.unit==='min'?Math.round(s.value*60000):0,targetType:p?'speed':'open',targetValue:0,intensity:s.label.toLowerCase().includes('warm')?'warmup':s.label.toLowerCase().includes('cool')?'cooldown':s.kind==='recovery'?'recovery':'active'};
  if(p){msg.customTargetValueLow=Math.round(1000000/(p[1]+tolerance));msg.customTargetValueHigh=Math.round(1000000/Math.max(120,p[0]-tolerance));}
  e.onMesg(Profile.MesgNum.WORKOUT_STEP,msg);
 });
 const bytes=e.close();const decoder=new Decoder(Stream.fromByteArray(bytes));if(!decoder.checkIntegrity())throw Error('FIT integrity check failed.');const result=decoder.read();if(result.errors.length||result.messages.workoutStepMesgs?.length!==session.steps.length)throw Error('FIT validation failed.');return bytes;
}
