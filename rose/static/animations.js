'use strict';
/* Ordered, read-only playback of committed actions and hardware poses. */
window.RoseAnimations=(()=>{
 const tracks=new Map(),devices=new Map();let identity=null,serial=0,snapshot=null,freeze=null,mode='system';
 const maxTracks=96,maxQueue=12,maxLatency=2400,stepMs=360;
 const media=window.matchMedia?.('(prefers-reduced-motion: reduce)');
 const reduced=()=>mode==='reduced'||mode==='system'&&!!media?.matches;
 const nowTime=now=>freeze??now;
 const point=p=>Array.isArray(p)&&p.length===2&&p.every(n=>Number.isFinite(n)&&Math.abs(n)<=100);
 const selector=(type,id)=>type+':'+id;
 function reset(){tracks.clear();devices.clear();identity=null;serial=0;snapshot=null;freeze=null;}
 function configure(value){const next=['system','full','reduced'].includes(value)?value:'system';if(next!==mode){tracks.clear();for(const d of devices.values())d.start=-Infinity;}mode=next;}
 function trim(now){for(const[k,q]of tracks){while(q.length&&q[0].end<now)q.shift();if(!q.length)tracks.delete(k);}while(tracks.size>maxTracks)tracks.delete(tracks.keys().next().value);}
 function endOf(key,now){return tracks.get(key)?.at(-1)?.end??now;}
 function add(key,cue,start,now){let q=tracks.get(key)||[];if(start-now>maxLatency){q=[];start=now;}const item={...cue,start,end:start+cue.duration_ms};q.push(item);tracks.set(key,q.slice(-maxQueue));return item;}
 function valid(e){return e&&Number.isInteger(e.id)&&e.id>0&&typeof e.subject==='string'&&e.subject.length<=180&&Number.isInteger(e.duration_ms)&&e.duration_ms>=0&&e.duration_ms<=36000&&['move','pose','strike','collapse','clear'].includes(e.kind);}
 function accept(e,now){
  const key=e.kind==='collapse'||e.kind==='clear'?e.subject:selector('unit',e.subject);
  if(e.kind==='move'||e.kind==='pose'){
   if(!Array.isArray(e.path)||e.path.length>101||!e.path.length||!e.path.every(point))return;
   if(e.kind==='move'&&e.path.some((p,i)=>i&&Math.max(Math.abs(p[0]-e.path[i-1][0]),Math.abs(p[1]-e.path[i-1][1]),Math.abs(p[0]+p[1]-e.path[i-1][0]-e.path[i-1][1]))!==1))return;
  }else if(e.kind==='strike'){
   if(!point(e.source)||!point(e.destination)||typeof e.target!=='string'||e.target.length>180||!Number.isFinite(e.contact_ms)||e.contact_ms<0||e.contact_ms>e.duration_ms||!Number.isFinite(e.damage)||e.damage<0)return;
   const reactions=e.reactions||[];if(!Array.isArray(reactions)||reactions.length>2||!reactions.every(r=>typeof r.target==='string'&&r.target.length<=180&&point(r.destination)&&Number.isFinite(r.damage)&&r.damage>=0))return;
   const start=Math.max(now,endOf(key,now),endOf(e.target,now)-e.contact_ms),attack=add(key,e,start,now);
   if(e.hit&&e.damage>0)add(e.target,{...e,kind:'impact',duration_ms:540},attack.start+e.contact_ms,now);
   for(const r of reactions)if(r.damage>0)add(r.target,{...e,...r,kind:'impact',duration_ms:540},attack.start+e.contact_ms,now);
   return;
  }else if(!point(e.pos))return;
  add(key,e,Math.max(now,endOf(key,now)),now);
 }
 function deviceKey(n){return n.id+':'+(n.machine?.kind||'');}
 function read(value,now=performance.now()){
  const id=value?.scene&&`${value.code}:${value.me.id}:${value.scene.id}`,fresh=id!==identity;
  if(fresh){reset();identity=id;}
  const paused=!!value.paused||!value.started;
  if(paused&&freeze===null)freeze=now;
  if(!paused&&freeze!==null){const elapsed=now-freeze;for(const q of tracks.values())for(const e of q){e.start+=elapsed;e.end+=elapsed;}for(const d of devices.values())d.start+=elapsed;freeze=null;}
  snapshot=value;const time=nowTime(now),data=value.scene?.animation;trim(time);
  const hidden=value.me.remote||value.particles?.percept.address;if(hidden)tracks.clear();
  if(data&&Number.isInteger(data.serial)&&Array.isArray(data.events)){
   if(fresh)serial=data.serial;
   else if(data.serial>=serial){
    const rows=data.events.filter(valid).sort((a,b)=>a.id-b.id);if(rows.length&&serial<rows[0].id-1){tracks.clear();serial=data.serial;}
    else{if(!reduced()&&!hidden)for(const e of rows)if(e.id>serial&&e.id<=data.serial)accept(e,time);serial=data.serial;}
   }
   else{tracks.clear();serial=data.serial;}
  }
  const present=new Set();for(const n of value.scene?.infrastructure?.nodes||[]){
   const m=n.machine?.motion,key=deviceKey(n);if(!m||!Array.isArray(m.frames)||m.frames.length>33||!Number.isInteger(m.serial)||!Number.isFinite(m.duration_ms)||m.duration_ms<0||m.duration_ms>4000)continue;
   if(!m.frames.length||!m.frames.every(f=>Number.isFinite(f.at)&&f.at>=0&&f.at<=1&&point(f.offset)&&Number.isFinite(f.angle)))continue;
   if(m.frames.some((f,i)=>i&&f.at<m.frames[i-1].at))continue;
   present.add(key);const old=devices.get(key);if(!old||old.serial!==m.serial)devices.set(key,{...m,start:fresh||!old||reduced()?-Infinity:time});
  }for(const k of devices.keys())if(!present.has(k))devices.delete(k);
  if(reduced())tracks.clear();trim(time);
 }
 function current(key,now){const time=nowTime(now);return tracks.get(key)?.find(e=>time>=e.start&&time<=e.end);}
 function progress(e,now){return e.duration_ms?Math.max(0,Math.min(1,(nowTime(now)-e.start)/e.duration_ms)):1;}
 function direction(a,b){const d=[b[0]-a[0],b[1]-a[1]],xy=[Math.sqrt(3)*(d[0]+d[1]/2),1.5*d[1]],dirs=[[1,0],[1,-1],[0,-1],[-1,0],[-1,1],[0,1]];let best=0,score=-Infinity;for(let n=0;n<6;n++){const[q,r]=dirs[n],s=xy[0]*Math.sqrt(3)*(q+r/2)+xy[1]*1.5*r;if(s>score){best=n;score=s;}}return best;}
 function unit(u,now){
  const elevation=pos=>snapshot?.scene?.tiles?.[pos.join(',')]?.elevation||0;
  const lane=reduced()?[]:tracks.get('unit:'+u.id)||[],e=reduced()?null:current('unit:'+u.id,now),pending=lane.find(c=>c.start>nowTime(now)),waitingHit=u.health<=0&&lane.some(c=>c.kind==='impact'&&(c.start>nowTime(now)||c===e&&progress(c,now)<=.65));
  const base={pos:u.pos,health:waitingHit?1:u.health,elevation:elevation(u.pos),pose:u.health<=0&&!waitingHit?'down':u.pose==='guard'?'guard':'idle',time:nowTime(now),facing:u.facing||0,offset:[0,0],cue:null};
  if(!e&&pending)base.pos=pending.kind==='move'?pending.path[0]:pending.kind==='strike'?pending.source:pending.kind==='impact'?pending.destination:pending.path?.at(-1)||base.pos;
  base.elevation=elevation(base.pos);
  if(!e)return base;const p=progress(e,now);base.cue=e;
  if(e.kind==='move'){
   const d=p*(e.path.length-1),i=Math.min(e.path.length-2,Math.floor(d)),fraction=d-i;
   if(i<0)return base;base.pos=e.path[i].map((v,a)=>v+(e.path[i+1][a]-v)*fraction);base.elevation=elevation(e.path[i])+(elevation(e.path[i+1])-elevation(e.path[i]))*fraction;base.pose='walk';base.facing=direction(e.path[i],e.path[i+1]);base.time=d*(RosePrefabs.clipDuration('walk')/2);
  }else if(e.kind==='impact'){
   base.pos=e.destination;base.elevation=elevation(base.pos);
   const dx=Math.sqrt(3)*(e.destination[0]-e.source[0]+(e.destination[1]-e.source[1])/2),dy=(e.destination[1]-e.source[1])*.78,norm=Math.hypot(dx,dy)||1;
   const displacement=Math.min(7,1+e.damage*.25)*Math.sin(Math.PI*p)*Math.exp(-2*p);base.offset=[dx/norm*displacement,dy/norm*displacement];base.pose=u.health<=0&&p>.65?'down':'hit';base.time=p*RosePrefabs.clipDuration(base.pose);
  }else{base.pos=e.kind==='strike'?e.source:e.path?.at(-1)||base.pos;base.elevation=elevation(base.pos);base.pose=e.pose||'attack';base.time=p*RosePrefabs.clipDuration(base.pose);base.facing=e.facing??base.facing;}
  return base;
 }
 function object(id,now){if(reduced())return null;const e=current(id,now),pending=(tracks.get(id)||[]).find(c=>c.kind==='collapse'&&c.start>nowTime(now));return e?{...e,progress:progress(e,now),pending_collapse:pending}:pending?{...pending,kind:'collapse_wait',progress:0}:null;}
 function hardware(node,now){
  const d=devices.get(deviceKey(node)),m=node.machine?.motion;if(!d||!m?.frames?.length)return null;
  const p=reduced()||!d.active||!node.enabled||node.condition<30||snapshot?.clock_held?1:d.duration_ms?Math.min(1,Math.max(0,(nowTime(now)-d.start)/d.duration_ms)):1;
  let i=0;while(i<d.frames.length-2&&d.frames[i+1].at<p)i++;const a=d.frames[i],b=d.frames[Math.min(i+1,d.frames.length-1)],t=b.at>a.at?Math.max(0,Math.min(1,(p-a.at)/(b.at-a.at))):1;
  return{offset:a.offset.map((v,n)=>v+(b.offset[n]-v)*t),angle:a.angle+(b.angle-a.angle)*t,contact:!!(t<.5?a.contact:b.contact),active:d.active&&node.enabled&&node.condition>=30,kind:node.machine.kind};
 }
 function effects(now){const rows=[];if(reduced())return rows;for(const[key,q]of tracks)for(const e of q)if(['strike','clear'].includes(e.kind)&&nowTime(now)>=e.start&&nowTime(now)<=e.end)rows.push({...e,key,progress:progress(e,now)});return rows.slice(-24);}
 return{read,reset,configure,unit,object,hardware,effects,clock:nowTime,progress,stepMs,get reduced(){return reduced();},get mode(){return mode;},get pending(){return [...tracks.values()].reduce((n,q)=>n+q.length,0);},get devices(){return devices.size;}};
})();
