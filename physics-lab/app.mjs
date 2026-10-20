import { Lab, MATERIALS, STRUCTURES, PRESETS, DEFAULTS, worldToAxial } from './engine.mjs';
import { SceneRenderer } from './renderer.mjs';
const $=id=>document.getElementById(id), $$=selector=>[...document.querySelectorAll(selector)];
const STORE='rose.engine.lab.v1';
let stored={};try{stored=JSON.parse(localStorage.getItem(STORE)||'{}');}catch{}
const lab=new Lab(stored.config||DEFAULTS);
let comparison=false,selected=null,clock=0,frameTime=0,lastUi=0,lastDraw=0,dirty=true,trace=[],lastSave=0,review=stored.review||{},toastTimer;
const renderer=new SceneRenderer();
// Restore a stopped, inspectable specimen rather than silently resuming a force.
if(stored.current&&stored.current.config?.material===lab.config.material&&stored.current.config?.structure===lab.config.structure){
  const snap=stored.current;
  for(const key of ['integrity','damage','x','v','rotation','time','energy','peak','force','salvage','salvaged'])if(Number.isFinite(snap[key]))lab[key]=snap[key];
  for(const key of ['collapsed','connected','blocked'])if(typeof snap[key]==='boolean')lab[key]=snap[key];
  if(Array.isArray(snap.rubble))lab.rubble=snap.rubble.filter(r=>Object.values(r).every(v=>typeof v==='number'&&Number.isFinite(v))).slice(0,22);
  if(stored.before)lab.before={...lab.snapshot(),...stored.before};
  lab.v=0;lab.force=0;lab.record('Experiment restored','Saved specimen restored in a paused state.');
}
const prefs={hex:!!stored.hex,motion:stored.motion??matchMedia('(prefers-reduced-motion: reduce)').matches};
$('hex').checked=prefs.hex;$('motion').checked=prefs.motion;
function save(){
  try{localStorage.setItem(STORE,JSON.stringify({config:lab.config,current:lab.snapshot(),before:lab.before,review,hex:prefs.hex,motion:prefs.motion}));}catch{ $('solver-status').textContent='Storage unavailable · export to keep work'; }
}
function notify(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),3300);}
const time=t=>`${String(Math.floor(t/60)).padStart(2,'0')}:${(t%60).toFixed(2).padStart(5,'0')}`;
const number=(n,d=0)=>n.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d});
function selectTab(id){
  $$('.view').forEach(v=>v.classList.toggle('active-view',v.id===id));
  $$('.nav').forEach(n=>{n.classList.toggle('active',n.dataset.tab===id);n.setAttribute('aria-current',n.dataset.tab===id?'page':'false');});
  if(id==='lab'){dirty=true;requestAnimationFrame(()=>render());}
}
$$('[data-tab]').forEach(b=>b.addEventListener('click',()=>selectTab(b.dataset.tab)));
$$('[data-back]').forEach(b=>b.addEventListener('click',()=>selectTab('lab')));
function controlSync(){
  const c=lab.config;
  for(const id of ['structure','magnitude','angle','age','weather','use','friction','damping'])$(id).value=c[id];
  $('scenario').value=PRESETS[c.scenario]?c.scenario:'custom';
  for(const [id,suffix] of [['magnitude',' kN'],['angle','°'],['age',' years'],['weather','%'],['use','%'],['friction',''],['damping','']]){
    $(id+'-out').textContent=(id==='damping'||id==='friction'?c[id].toFixed(2):c[id])+suffix;
    const el=$(id);el.style.setProperty('--pct',`${100*(c[id]-Number(el.min))/(Number(el.max)-Number(el.min))}%`);
  }
  $$('[data-material]').forEach(b=>{const on=b.dataset.material===c.material;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
  $$('[data-force]').forEach(b=>{const on=b.dataset.force===c.force;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
  $$('[data-scale]').forEach(b=>{const on=b.dataset.scale===c.scale;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
  $('material-kind').textContent=MATERIALS[c.material].mode.toUpperCase();
  $('scene-name').textContent=STRUCTURES[c.structure].name.toUpperCase();
  $('scene-description').textContent=c.structure==='canopy'?'Flexible shelter. Continuous ground.':c.structure==='span'?'Continuous span. Continuous ground.':'Solid core. Continuous ground.';
  $('scene').setAttribute('aria-label',`Isometric ${MATERIALS[c.material].name} ${STRUCTURES[c.structure].name} on seamless natural terrain`);
  $('scale-label').textContent=`1.8 m reference · ${lab.props.ratio.toFixed(1)}× ${c.structure==='span'?'deck':c.structure==='canopy'?'canopy':'core'}`;
}
function change(patch){lab.configure({...patch,scenario:patch.scenario||'custom'});trace=[];controlSync();update();dirty=true;save();}
for(const id of ['structure','magnitude','angle','age','weather','use','friction','damping'])$(id).addEventListener(id==='structure'?'change':'input',()=>change({[id]:id==='structure'?$(id).value:Number($(id).value)}));
$$('[data-material]').forEach(b=>b.addEventListener('click',()=>change({material:b.dataset.material,friction:MATERIALS[b.dataset.material].friction})));
$$('[data-force]').forEach(b=>b.addEventListener('click',()=>change({force:b.dataset.force})));
$$('[data-scale]').forEach(b=>b.addEventListener('click',()=>{lab.config.scale=b.dataset.scale;controlSync();dirty=true;save();}));
$('scenario').addEventListener('change',()=>{const id=$('scenario').value;if(PRESETS[id])change({...PRESETS[id],scenario:id,friction:MATERIALS[PRESETS[id].material].friction});else{lab.config.scenario='custom';save();}});
$('age-step').addEventListener('click',()=>{lab.advanceAge();trace=[];controlSync();update();dirty=true;save();notify(`Advanced to ${lab.config.age} equivalent years.`);});
$('run').addEventListener('click',run);
function run(){if(!lab.trigger()){notify('Salvage the rubble and rebuild before applying another force.');return;}trace=[{t:lab.time,v:lab.integrity}];update();dirty=true;save();}
$('reset').addEventListener('click',()=>{lab.reset();trace=[];controlSync();update();dirty=true;save();notify('Specimen restored to its aged baseline.');});
$('pause').addEventListener('click',()=>{lab.running=!lab.running;$('pause').textContent=lab.running?'Ⅱ':'▶';update();dirty=true;save();});
$('step').addEventListener('click',()=>{lab.running=true;lab.integrate(1/60);lab.running=false;trace.push({t:lab.time,v:lab.integrity});update();dirty=true;save();});
$('collapse').addEventListener('click',()=>{lab.before=lab.snapshot();lab.collapse();update();dirty=true;save();notify('Destruction test: service lost; rubble blocks the site.');});
$('repair').addEventListener('click',()=>{if(lab.repair()){update();dirty=true;save();notify('Load damage repaired. Material age retained.');}});
$('salvage-action').addEventListener('click',()=>{const n=lab.salvageRubble();update();dirty=true;save();if(n)notify(`${number(n)} kg recovered. Footprint cleared.`);});
$('rebuild').addEventListener('click',()=>{if(lab.rebuild()){trace=[];update();dirty=true;save();notify('New specimen rebuilt on the cleared footprint.');}});
$('hex').addEventListener('change',()=>{prefs.hex=$('hex').checked;$('render-label').textContent=prefs.hex?'TACTICAL OVERLAY':'SEAMLESS SURFACE';dirty=true;save();});
$('motion').addEventListener('change',()=>{prefs.motion=$('motion').checked;dirty=true;save();});
$('compare').addEventListener('click',()=>{comparison=!comparison;$('compare').setAttribute('aria-pressed',String(comparison));$('compare-labels').hidden=!comparison;dirty=true;});
$('fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.querySelector('.viewport').requestFullscreen();dirty=true;}catch{notify('Fullscreen is unavailable in this browser.');}});
$('scene').addEventListener('click',event=>{
  const rect=$('scene').getBoundingClientRect(),ratio=Math.max(rect.width/1100,rect.height/680),ox=(rect.width-1100*ratio)/2,oy=(rect.height-680*ratio)/2;
  const xx=(event.clientX-rect.left-ox)/ratio,yy=(event.clientY-rect.top-oy)/ratio;
  const z=lab.config.scale==='detail'?1.46:lab.config.scale==='landscape'?.62:1,dy=lab.config.scale==='detail'?42:lab.config.scale==='landscape'?-15:0;
  const a=(xx-560)/(22*z),b=(yy-430-dy)/(10.4*z);selected=worldToAxial((a+b)/2,(b-a)/2);
  $('target-hint').textContent=`GROUND / q ${selected.q} · r ${selected.r} / ${lab.blocked&&Math.abs(selected.q)<2&&Math.abs(selected.r)<2?'BLOCKED BY RUBBLE':'TRAVERSABLE'}`;dirty=true;
});
document.addEventListener('keydown',e=>{if(e.code==='Space'&&!['INPUT','SELECT','BUTTON','TEXTAREA','SUMMARY'].includes(document.activeElement?.tagName)&&!$('validation').open&&$('lab').classList.contains('active-view')){e.preventDefault();run();}});
window.addEventListener('beforeunload',save);
$('export').addEventListener('click',()=>{
  const data={format:'rose.engine.experiment',version:1,exportedAt:new Date().toISOString(),model:'Game-tuned spring/damper structural emulation; not engineering analysis',config:lab.config,properties:lab.props,before:lab.before,after:lab.snapshot(),events:lab.history,visualReview:review};
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='rose-engine-experiment.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('Experiment exported as JSON.');
});
function update(){
  const p=lab.props,c=lab.config,integrity=Math.round(lab.integrity*100),before=Math.round(lab.before.integrity*100),loss=Math.round((1-lab.integrity)*100);
  $('integrity').textContent=integrity;$('integrity-delta').textContent=`−${loss}% from pristine`;$('integrity-bar').style.width=integrity+'%';$('integrity-bar').style.background=integrity<45?'#dca17e':'#c3d99d';
  $('before-integrity').textContent=before+'%';$('after-integrity').textContent=integrity+'%';$('status').textContent=lab.status.split(' · ')[0];$('status').classList.toggle('critical',lab.collapsed||integrity<45);
  const metric=(id,value,unit)=>{const el=$(id);el.textContent=value+' ';const small=document.createElement('small');small.textContent=unit;el.appendChild(small);};
  metric('capacity',number(p.capacity/1000,1),'kN');metric('peak',number(lab.peak/1000),'kN');metric('displacement',number(Math.abs(lab.x)*1000,1),'mm');metric('energy',number(lab.energy/1000,2),'kJ');metric('mass',number(p.mass/1000,1),'t');
  $('failure-mode').textContent=MATERIALS[c.material].mode;
  $('connection').textContent=lab.connected?'● Online':'○ Disconnected';$('connection').style.color=lab.connected?'#b8cba6':'#d4a380';$('footprint').textContent=lab.blocked?'Blocked by rubble':'Traversable';$('salvage').textContent=lab.collapsed?`${number(lab.salvage)} kg`:'—';
  $('run').disabled=lab.collapsed;$('collapse').disabled=lab.collapsed;$('repair').disabled=lab.collapsed;$('salvage-action').disabled=!lab.collapsed||lab.salvage===0;$('rebuild').disabled=!lab.collapsed||lab.blocked;
  $('time').textContent=time(lab.time);$('pause').textContent=lab.running?'Ⅱ':'▶';$('pause').setAttribute('aria-label',lab.running?'Pause simulation':'Resume simulation');$('solver-status').textContent=lab.running?(lab.active?'Force active':'Settling response'):lab.time>0?'Paused / settled':'Ready to simulate';
  const events=$('events');events.replaceChildren();
  const list=lab.history.length?lab.history.slice(0,3):[{time:0,title:'Specimen prepared',detail:'Awaiting force application.'}];
  for(const event of list){const li=document.createElement('li'),at=document.createElement('span'),body=document.createElement('div'),title=document.createElement('b'),detail=document.createElement('p');at.textContent=time(event.time).slice(0,5);title.textContent=event.title;detail.textContent=event.detail;body.append(title,detail);li.append(at,body);events.append(li);}
}
function surface(canvas){const r=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2),width=Math.max(1,Math.round(r.width*dpr)),height=Math.max(1,Math.round(r.height*dpr));if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}return {c:canvas.getContext('2d'),width,height};}
function render(){
  const {c,width,height}=surface($('scene'));if(width<2||height<2)return;
  const snap=lab.snapshot(),opts={hex:prefs.hex,scale:lab.config.scale,clock,motion:!prefs.motion,selected};
  if(comparison){
    c.save();c.beginPath();c.rect(0,0,width/2,height);c.clip();renderer.draw(c,width,height,lab.before,{...opts,motion:false,selected:null});c.restore();
    c.save();c.beginPath();c.rect(width/2,0,width/2,height);c.clip();renderer.draw(c,width,height,snap,opts);c.restore();
    c.strokeStyle='#d2e3b9a0';c.lineWidth=1;c.beginPath();c.moveTo(width/2,0);c.lineTo(width/2,height);c.stroke();
  }else renderer.draw(c,width,height,snap,opts);
  drawTrace();dirty=false;
}
function drawTrace(){
  const {c,width:w,height:h}=surface($('trace'));c.clearRect(0,0,w,h);c.strokeStyle='#b8ce8a';c.lineWidth=1.2;
  c.beginPath();const points=trace.length?trace:[{t:0,v:lab.integrity},{t:1,v:lab.integrity}],maxT=Math.max(1,points.at(-1).t-points[0].t);
  points.forEach((p,i)=>{const x=(p.t-points[0].t)/maxT*w,y=5+(1-p.v)*(h-18);i?c.lineTo(x,y):c.moveTo(x,y);});c.stroke();
  c.strokeStyle='#597a4144';c.setLineDash([3,5]);c.beginPath();c.moveTo(0,h*.5);c.lineTo(w,h*.5);c.stroke();c.setLineDash([]);
}
function visualReview(){
  ['monolith','scale','terrain'].forEach(k=>$('check-'+k).checked=!!review[k]);reviewCount();$('validation').showModal();requestAnimationFrame(drawValidation);
}
function drawValidation(){
  const test=new Lab({material:'stone',structure:'relay',age:12}).snapshot();
  for(const [id,hex] of [['natural-test',false],['hex-test',true]]){const {c,width,height}=surface($(id));renderer.draw(c,width,height,test,{hex,scale:$('test-scale').value,motion:false,labels:true});}
}
function reviewCount(){const n=['monolith','scale','terrain'].filter(k=>$('check-'+k).checked).length;$('review-status').textContent=`${n} / 3 observations confirmed. ${n===3?'All three visual criteria accepted.':'Visual judgment is yours.'}`;}
$('open-validation').addEventListener('click',visualReview);$('close-validation').addEventListener('click',()=>$('validation').close());$('test-scale').addEventListener('change',drawValidation);
['monolith','scale','terrain'].forEach(k=>$('check-'+k).addEventListener('change',reviewCount));
$('save-review').addEventListener('click',()=>{review={date:new Date().toISOString(),scale:$('test-scale').value,...Object.fromEntries(['monolith','scale','terrain'].map(k=>[k,$('check-'+k).checked]))};save();$('validation').close();notify('Visual review saved with your experiment.');});
$('validation').addEventListener('click',e=>{if(e.target===$('validation')){const r=$('validation').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('validation').close();}});
const atlas=$('atlas-grid');
for(const [key,m] of Object.entries(MATERIALS)){
  const card=document.createElement('article');card.className='atlas-card';
  const icon=document.createElement('i');icon.className='swatch '+key;const h=document.createElement('h3');h.textContent=m.name;const desc=document.createElement('p');desc.textContent=m.weather;
  const dl=document.createElement('dl');for(const [k,v] of [['Density',`${number(m.density)} kg/m³`],['Strength coefficient',`${m.strength} MPa`],['Friction',m.friction.toFixed(2)],['Recoverable fraction',`${Math.round(m.salvage*100)}%`],['Response',m.mode]]){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=v;dl.append(dt,dd);}
  const button=document.createElement('button');button.textContent='Use in experiment ↗';button.addEventListener('click',()=>{change({material:key,friction:m.friction});selectTab('lab');});card.append(icon,h,desc,dl,button);atlas.append(card);
}
let resizeTimer;window.addEventListener('resize',()=>{dirty=true;clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{render();if($('validation').open)drawValidation();},100);});
function loop(now){
  const dt=frameTime?Math.min((now-frameTime)/1000,.1):0;frameTime=now;
  const wasRunning=lab.running;if(lab.running){lab.step(dt);if(now-lastUi>80){trace.push({t:lab.time,v:lab.integrity});if(trace.length>600)trace.shift();update();lastUi=now;}dirty=true;}
  if(wasRunning&&!lab.running){update();save();}
  if(!prefs.motion)clock+=dt;
  if($('lab').classList.contains('active-view')&&(dirty||!prefs.motion)&&now-lastDraw>1000/30){render();lastDraw=now;}
  if(lab.running&&now-lastSave>750){save();lastSave=now;}
  requestAnimationFrame(loop);
}
controlSync();update();requestAnimationFrame(loop);
// Accessible debug surface used by local interaction checks; no network or test-only UI.
window.roseLab={lab,getView:()=>({comparison,hex:prefs.hex,reducedMotion:prefs.motion,review,selected}),render};
