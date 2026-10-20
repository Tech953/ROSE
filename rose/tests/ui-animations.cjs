/* Ordered playback invariants and real HTTP/native-canvas animation captures. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const plain=value=>JSON.parse(JSON.stringify(value));
const equal=(a,b,message)=>assert.deepEqual(plain(a),plain(b),message);
function find(node,predicate){if(predicate(node))return node;for(const child of node.children||[]){const hit=find(child,predicate);if(hit)return hit;}return null;}
module.exports=async function({base,tmp,setupInterface,canvasModule,root}){
 const mark=value=>{if(process.env.ROSE_ANIMATION_DEBUG)console.log('ANIMATION DEBUG: '+value);};mark('setup');
 const rig=setupInterface(base,tmp,{reducedMotion:false}),{context,ids}=rig,read=()=>vm.runInContext('state',context),A=context.RoseAnimations;
 for(let n=0;n<100&&!context.RoseCreator.ready;n++)await new Promise(r=>setTimeout(r,10));
 ids.name.value='Motion keeper';ids.seed.value='motion-ui';rig.document.getElementById('rule-generation-hostility').value=0;
 mark('joining');await ids['join-form'].requestSubmit();mark('starting');await ids.start.click();mark('loading');if(canvasModule)await context.RosePrefabs.ready;mark('timeline controls');
 const template=()=>({code:'MOTION',started:true,paused:false,me:{id:'actor',remote:false},particles:{percept:{address:null}},scene:{id:'0,0',tiles:{'0,0':{elevation:0},'1,0':{elevation:8}},infrastructure:{nodes:[]},animation:{schema:1,serial:0,events:[]}}});
 let state=template(),serial=0;const u={id:'actor',pos:[1,0],health:100,pose:'walk',facing:0},target={id:'target',pos:[2,0],health:90,pose:'hit',facing:3};
 const emit=(cue,now=0)=>{state.scene.animation.serial=++serial;state.scene.animation.events.push({id:serial,...cue});state.scene.animation.events=state.scene.animation.events.slice(-96);A.read(state,now);};
 const reset=()=>{A.reset();A.configure('full');state=template();serial=0;A.read(state,0);};
 reset();emit({kind:'move',subject:'actor',duration_ms:360,pose:'walk',path:[[0,0],[1,0]],facing:0});
 equal(A.unit(u,180).pos,[.5,0]);assert.equal(A.unit(u,180).elevation,4);assert.equal(A.unit(u,180).time,180);
 emit({kind:'strike',subject:'actor',duration_ms:870,pose:'attack',source:[1,0],destination:[2,0],target:'unit:target',contact_ms:435,damage:10,hit:true,facing:0,ranged:false},0);
 assert.equal(A.unit(u,200).pose,'walk','A queued attack waits for the committed movement');assert.equal(A.unit(u,500).pose,'attack');assert.equal(A.unit(target,794).pose,'idle');assert.equal(A.unit(target,795).pose,'hit');
 assert.ok(A.unit(target,960).offset[0]>0,'Confirmed damage recoils away from its source');assert.equal(A.unit(target,1400).pose,'idle');
 const fatal={...target,health:0};assert.equal(A.unit(fatal,794).pose,'idle','A fatal result does not fall before its attack contact');assert.equal(A.unit(fatal,795).pose,'hit');assert.equal(A.unit(fatal,1300).pose,'down');
 emit({kind:'collapse',subject:'unit:target',duration_ms:1200,pos:[2,0],before_condition:20,material:'stone'},0);assert.equal(A.object('unit:target',700).kind,'collapse_wait');assert.ok(A.object('unit:target',800).pending_collapse,'The intact surface is retained through the impact before collapse');
 const beforePoll=plain(A.unit(u,500));A.read(state,100);equal(A.unit(u,500),beforePoll,'Repeated snapshots do not restart a clip');
 reset();emit({kind:'strike',subject:'actor',duration_ms:870,source:[1,0],destination:[2,0],target:'unit:target',contact_ms:435,damage:0,hit:false,ranged:true,facing:0});
 assert.equal(A.unit(target,500).pose,'idle');assert.ok(A.effects(500).every(e=>!e.hit),'A miss cannot advertise a hit flash');
 reset();emit({kind:'strike',subject:'actor',duration_ms:870,source:[1,0],destination:[2,0],target:'unit:target',contact_ms:435,damage:4,hit:true,facing:0,reactions:[{target:'unit:guard',destination:[2,-1],damage:3}]});
 assert.equal(A.unit(target,500).pose,'hit');assert.equal(A.unit({...target,id:'guard'},500).pose,'hit');assert.equal(A.effects(500).length,1,'Shared guards react to one attack');
 reset();emit({kind:'move',subject:'actor',duration_ms:360,path:[[0,0],[1,0]],facing:0});state.paused=true;A.read(state,100);equal(A.unit(u,900).pos,[100/360,0]);state.paused=false;A.read(state,1000);equal(A.unit(u,1080).pos,[.5,0],'Resume continues from the frozen foot position');
 state.me.remote=true;A.read(state,1100);assert.equal(A.pending,0);state.me.remote=false;A.read(state,1200);assert.equal(A.pending,0,'Returning does not replay hidden field actions');
 reset();emit({kind:'pose',subject:'actor',duration_ms:720,path:[[1,0]],pose:'work'});state.particles.percept.address='void';A.read(state,100);assert.equal(A.pending,0);
 reset();state.scene.animation={schema:1,serial:110,events:[{id:100,kind:'pose',subject:'actor',duration_ms:720,path:[[1,0]],pose:'work'}]};A.read(state,0);assert.equal(A.pending,0,'Missing old event history is consumed without a catch-up replay');
 A.reset();A.read(state,0);assert.equal(A.pending,0,'First connection restores the settled pose');
 reset();emit({kind:'move',subject:'actor',duration_ms:360,path:[[0,0],[2,0]],facing:0});assert.equal(A.pending,0,'Impossible movement segments are discarded');
 emit({kind:'strike',subject:'actor',duration_ms:870,source:[0,0],destination:[1,0],target:'unit:target',contact_ms:999,damage:1,hit:true});assert.equal(A.pending,0,'An invalid contact time cannot create a reaction');
 reset();for(let n=0;n<200;n++)emit({kind:'pose',subject:'actor'+n,duration_ms:720,path:[[1,0]],pose:'work'});assert.ok(A.pending<=96,'Action tracks are bounded');
 reset();for(let n=0;n<100;n++)emit({kind:'pose',subject:'actor',duration_ms:720,path:[[1,0]],pose:'work'});assert.ok(A.pending<=12,'A busy actor cannot accumulate an unbounded playback queue');
 A.configure('reduced');assert.equal(A.pending,0);equal(A.unit(u,100).pos,u.pos);A.configure('full');A.read(state,100);assert.equal(A.pending,0,'Profile changes do not replay consumed cues');
 reset();const node={id:'device',enabled:true,condition:90,machine:{kind:'pump',motion:{schema:1,serial:1,duration_ms:500,active:true,frames:[{at:0,offset:[0,0],angle:0},{at:1,offset:[10,0],angle:0}]}}};state.scene.infrastructure.nodes=[node];A.read(state,0);equal(A.hardware(node,0).offset,[10,0],'A first snapshot displays the current solver pose');
 node.machine.motion.serial++;A.read(state,100);equal(A.hardware(node,350).offset,[5,0]);A.read(state,300);equal(A.hardware(node,350).offset,[5,0]);equal(A.hardware(node,100000).offset,[10,0],'Hardware holds its endpoint without extrapolation');
 state.clock_held=true;A.read(state,400);equal(A.hardware(node,400).offset,[10,0]);state.clock_held=false;
 node.machine.motion={schema:1,serial:3,duration_ms:0,active:false,frames:[{at:0,offset:[0,0],angle:0}]};A.read(state,500);equal(A.hardware(node,100000).offset,[0,0]);
 state.scene.infrastructure.nodes=[];A.read(state,501);assert.equal(A.devices,0,'Cleared hardware releases its playback state');
 mark('host render');const authoritative=JSON.stringify(read());A.reset();context.RoseField.render(read());context.RoseField.draw(performance.now());assert.equal(JSON.stringify(read()),authoritative,'Reading and rendering cues cannot mutate the host snapshot');
 // Actual host actions use a controlled presentation clock for frame capture.
 mark('live movement');let time=1000;context.performance={now:()=>time};A.reset();context.RoseField.render(read());
 const act=async(action,target='')=>{time+=2500;const ok=await vm.runInContext('action',context)('act',{intent:{action,target}});assert.equal(ok,true,ids.error.textContent);return time;};
 const chosen=label=>find(ids['field-selection-actions'],n=>n.tagName==='BUTTON'&&n.textContent===label);
 const motionSetting=mode=>{ids['animation-mode'].value=mode;ids['animation-mode'].onchange();};
 motionSetting('full');assert.equal(context.localStorage.getItem('rose-motion-profile'),'full');
 const before=read().scene.units.find(n=>n.mine).pos.slice(),next=read().scene.reachable.find(p=>Math.max(Math.abs(p[0]-before[0]),Math.abs(p[1]-before[1]),Math.abs(p[0]+p[1]-before[0]-before[1]))===1);
 assert.ok(next);const movementTime=await act('hex_move',next.join(','));const moving=context.RoseField.appearance(movementTime+180).find(p=>p.u?.mine);
 equal(moving.pos,before.map((v,n)=>(v+next[n])/2),'Live-host footsteps interpolate the committed adjacent route');
 const mine=read().scene.units.find(n=>n.mine);assert.equal(A.unit(mine,movementTime+180).pose,'walk');
 if(canvasModule){const f=moving.frame,c=canvasModule.createCanvas(f.w,f.h),draw=c.getContext('2d');draw.drawImage(f.image.bitmap||f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);const rgba=draw.getImageData(0,0,f.w,f.h).data;let picks=0;for(let i=0;i<rgba.length;i+=16)if(rgba[i+3]>=248){const pixel=i/4,x=pixel%f.w,y=Math.floor(pixel/f.w),hit=context.RoseField.hitAt(moving.screen[0]+(x-f.anchor[0]+.25)*f.scale,moving.screen[1]+(y-f.anchor[1]+.25)*f.scale,movementTime+180);if(hit?.type==='unit'&&hit.id===mine.id)picks++;}assert.ok(picks>0,'The moving sprite remains selectable at its current drawn position');}
 const images=[];const capture=(label,now)=>{if(!canvasModule)return;time=now;context.RoseField.draw(now);images.push({label,png:ids['field-canvas'].bitmap.toBuffer('image/png')});};
 if(canvasModule){context.RoseDisplay.configure(false,'sharp');context.RoseLighting.configure('baked');capture('FOOT PLANT / START',movementTime);capture('FOOT PLANT / MIDPOINT',movementTime+180);capture('FOOT PLANT / ARRIVAL',movementTime+361);}
 mark('live hardware');time+=2500;motionSetting('reduced');const workshop=read().scene.infrastructure.nodes.find(n=>n.kind==='workshop');context.RoseField.select({type:'structure',id:workshop.id});await ids['walk-path'].click();
 assert.ok(chosen('FIT PUMP / 2 SCRAP')&&!chosen('FIT PUMP / 2 SCRAP').disabled,chosen('FIT PUMP / 2 SCRAP')?.dataset.blockReason);assert.equal(await chosen('FIT PUMP / 2 SCRAP').click(),true,ids.error.textContent);motionSetting('full');
 for(let n=0;n<12&&chosen('OPERATE MACHINE / 1 PUBLIC POWER').disabled;n++)await act('wait');
 time+=2500;const machineTime=time;assert.equal(await chosen('OPERATE MACHINE / 1 PUBLIC POWER').click(),true,ids.error.textContent);
 const machine=read().scene.infrastructure.nodes.find(n=>n.id===workshop.id);assert.equal(machine.machine.motion.duration_ms,500);assert.ok(machine.machine.motion.active);
 equal(A.hardware(machine,machineTime+500).offset,machine.machine.motion.frames.at(-1).offset,'Live hardware finishes at the host solver pose');
 for(const [label,delay]of [['START',0],['TRAVEL',250],['ENDPOINT',500]])capture('FITTED PUMP / '+label,machineTime+delay);
 const diagnostic=await vm.runInContext('api',context)('physics_export');assert.equal(diagnostic.energy.status,'PASS');
 assert.equal(await chosen('DISENGAGE MACHINE').click(),true,ids.error.textContent);const parked=read().scene.infrastructure.nodes.find(n=>n.id===workshop.id);assert.equal(parked.machine.motion.active,false);equal(A.hardware(parked,time+100000).offset,[0,0]);
 mark('live demolition');time+=2500;const water=read().scene.infrastructure.nodes.find(n=>n.kind==='water');context.RoseField.select({type:'structure',id:water.id});motionSetting('reduced');await ids['walk-path'].click();motionSetting('full');
 assert.equal(read().scene.infrastructure.nodes.find(n=>n.id===water.id).adjacent,true);
 let last=0;for(let n=0;n<8&&read().scene.infrastructure.nodes.find(n=>n.id===water.id).condition>0;n++){time+=2500;last=time;assert.equal(await chosen('STRIKE PUBLIC WORKS').click(),true,ids.error.textContent);}
 assert.equal(read().scene.infrastructure.nodes.find(n=>n.id===water.id).condition,0);
 const collapse=read().scene.animation.events.findLast(e=>e.kind==='collapse'&&e.subject==='structure:'+water.id);assert.ok(collapse);
 if(canvasModule){ids['toggle-occlusion'].click();context.RoseField.select(null);}
 if(canvasModule){const waiting=context.RoseField.appearance(last).find(p=>p.node?.id===water.id),settled=context.RoseField.appearance(last+3000).find(p=>p.node?.id===water.id);assert.ok(context.RosePrefabs.boundsFrame(waiting.frame)[3]>context.RosePrefabs.boundsFrame(settled.frame)[3]*1.5,'The earlier standing mass remains visible during demolition wind-up');}
 const frames=[];
 if(canvasModule){
  for(const [label,delay]of [['CONTACT',500],['SETTLING',975],['FALLING',1400],['DEBRIS',2200]])capture('DEMOLITION / '+label,last+delay);
  const frameDir=process.env.ROSE_ANIMATION_FRAMES||path.join(path.dirname(root),'rose-v015-animation-frames');fs.mkdirSync(frameDir,{recursive:true});
  for(let n=0;n<28;n++){const now=last+n*90;time=now;context.RoseField.draw(now);const name='frame-'+String(n).padStart(3,'0')+'.png';fs.writeFileSync(path.join(frameDir,name),ids['field-canvas'].bitmap.toBuffer('image/png'));frames.push({file:name,at_ms:n*90});}
  fs.writeFileSync(path.join(frameDir,'frames.json'),JSON.stringify({source:'Rose native canvas / real-host demolition',frame_duration_ms:90,frames},null,2));
  assert.ok(context.RoseMotionVisuals.available,'Prepared-surface composites rendered successfully');
  const catalog=JSON.parse(fs.readFileSync(path.join(root,'static/art-manifest-rendered.json'),'utf8')).visual_catalog;
  for(const region of catalog.regions){
   const f=context.RosePrefabs.frameInfo('water_'+region,'fractured',0),ruin=context.RosePrefabs.frameInfo('water_'+region,'ruined',0);assert.ok(f&&ruin);
   for(let n=0;n<16;n++){
    const rendered=context.RoseMotionVisuals.collapse(f,ruin,{material:'stone',progress:n/16}),c=rendered.image.bitmap||rendered.image,rgba=c.getContext('2d').getImageData(rendered.x,rendered.y,rendered.w,rendered.h).data;let solid=0,shadow=0;
    for(let i=0;i<rgba.length;i+=16){const pixel=i/4,x=pixel%rendered.w,y=Math.floor(pixel/rendered.w),point=[(x-rendered.anchor[0]+.25)*rendered.scale,(y-rendered.anchor[1]+.25)*rendered.scale],alpha=rgba[i+3];
     assert.equal(context.RosePrefabs.hitFrame(rendered,point),alpha>=248,'Collapse drawing and picking share every sampled alpha pixel');if(alpha>=248)solid++;else if(alpha)shadow++;
    }assert.ok(solid>0);if(n>2&&n<15)assert.ok(shadow>0,'Falling debris shadows remain click-through');
   }
   const workshopFrame=context.RosePrefabs.frameInfo('workshop_'+region,'idle',0);
   for(const kind of ['pump','press','damper'])for(const shift of [0,5,10]){
    const rendered=context.RoseMotionVisuals.hardware(workshopFrame,{offset:[shift,0],kind,contact:shift===10}),copy=canvasModule.createCanvas(rendered.w,rendered.h),c=copy.getContext('2d');c.drawImage(rendered.image.bitmap||rendered.image,rendered.x,rendered.y,rendered.w,rendered.h,0,0,rendered.w,rendered.h);const rgba=c.getImageData(0,0,rendered.w,rendered.h).data;
    for(let i=0;i<rgba.length;i+=28){const pixel=i/4,x=pixel%rendered.w,y=Math.floor(pixel/rendered.w),point=[(x-rendered.anchor[0]+.25)*rendered.scale,(y-rendered.anchor[1]+.25)*rendered.scale];assert.equal(context.RosePrefabs.hitFrame(rendered,point),rgba[i+3]>=248,'Mechanical surfaces share their current solid-pixel masks');}
   }
  }
  assert.ok(context.RoseMotionVisuals.cached<=24,'Composed motion surfaces stay bounded');
 }
 if(canvasModule){
  const sheet=canvasModule.createCanvas(1200,Math.ceil(images.length/3)*280),c=sheet.getContext('2d');c.fillStyle='#081511';c.fillRect(0,0,sheet.width,sheet.height);c.font='13px Courier New';
  for(let n=0;n<images.length;n++){const image=await canvasModule.loadImage(images[n].png);const x=(n%3)*400,y=Math.floor(n/3)*280;c.drawImage(image,x+8,y+28,384,238);c.fillStyle='#b6c5ac';c.fillText(images[n].label,x+10,y+18);}
  fs.writeFileSync(path.join(root,'docs','Rose-physics-animation-preview.png'),sheet.toBuffer('image/png'));
 }
 assert.equal(context.localStorage.getItem('rose-motion-profile'),'full');await ids.disconnect.click();
 console.log('PASS: physics animation — committed paths, terrain registration, contact-time recoil, misses, shared guards, serial deduplication, bounded queues, pause/resume, remote/void boundaries, reduced motion, solver-only hardware endpoints, parked shutdown, native collapse alpha picking, prepared-surface limits and real-host rendering.');
};
