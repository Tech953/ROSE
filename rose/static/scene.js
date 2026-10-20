'use strict';
window.RoseField=(()=>{
 const get=id=>document.getElementById(id),dirs=[[1,0],[1,-1],[0,-1],[-1,0],[-1,1],[0,1]],key=p=>p.join(','),distance=(a,b=[0,0])=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]),Math.abs(a[0]+a[1]-b[0]-b[1]));
 let hooks=null,snapshot=null,selected=null,walking=false,walkToken=0,grid=false,showLinks=false,rulesReady=false,lastScene=null,lastFrame=0;
 let cursorMode='move',hover=null,reveal=false,shiftReveal=false,fadeProps=true,menuOpen=false,menuGroup='look',holdTimer=null,press=null,suppressClick=false;
 const canvas=get('field-canvas'),ctx=canvas.getContext('2d'),width=1000,height=620;
 const opticalDrafts=new Map();
 const reduced=()=>RoseAnimations.reduced;
 const groups={look:'LOOK / EXAMINE',use:'USE / TALK',item:'USE ITEM ON',skill:'USE SKILL ON'};
 let size=34;
 const project=(p,elevation=0)=>[width/2+Math.sqrt(3)*size*(p[0]+p[1]/2),height*.55+size*1.5*p[1]*.52-elevation*2];
 const me=()=>snapshot?.scene.units.find(u=>u.mine),field=()=>snapshot?.scene;
 const notice=text=>{get('field-notice').textContent=text;};
 const selectionKey=value=>!value?'':value.type==='hex'?'hex:'+key(value.pos):value.type+':'+value.id;
 function optionsFor(value=selected){const id=selectionKey(value),f=field();if(!f||!id)return[];if(value.type==='project')return f.lifecycle?.projects.find(p=>p.id===value.id)?.actions||[];if(value.type==='hex')return f.interaction_options?.[id]?.actions||(f.interaction_options?.hex?.actions||[]).map(a=>({...a,intent:{...a.intent,target:id}}));return f.interaction_options?.[id]?.actions||[];}
 function nameFor(value){if(value?.type==='hex')return 'HEX ['+value.pos+']';if(value?.type==='project'){const p=field()?.lifecycle?.projects.find(p=>p.id===value.id);return p?p.kind.toUpperCase()+' / '+p.id:'COMPLETED OR REMOVED PROJECT';}return field()?.interaction_options?.[selectionKey(value)]?.name||'REGISTERED OBJECT';}
 function neighbors(pos){return dirs.map(d=>[pos[0]+d[0],pos[1]+d[1]]);}
 function path(start,goal){const f=field();if(!f?.tiles[key(goal)]?.passable)return null;const blocked=new Set(f.units.filter(u=>u.id!==snapshot.me.id&&u.health>0&&!(u.kind==='threat'&&u.resolved)).map(u=>key(u.pos))),end=key(goal),from=key(start),parents=new Map([[from,null]]),queue=[start];if(blocked.has(end))return null;
  for(let head=0;head<queue.length;head++){const current=queue[head],id=key(current);if(id===end){const result=[];let n=id;while(n!==null){result.push(n.split(',').map(Number));n=parents.get(n);}return result.reverse();}for(const p of neighbors(current)){const next=key(p);if(f.tiles[next]?.passable&&!blocked.has(next)&&!parents.has(next)){parents.set(next,id);queue.push(p);}}}return null;
 }
 function goal(){if(!selected||!field())return null;if(selected.type==='hex'&&field().tiles[key(selected.pos)]?.passable)return selected.pos;
  const item=selected.type==='hex'?field().tiles[key(selected.pos)]:selected.type==='project'?RoseEnvironment.projects().find(n=>n.id===selected.id):selected.type==='structure'?field().infrastructure.nodes.find(n=>n.id===selected.id):field().units.find(u=>u.id===selected.id);if(!item)return null;if(item.mine)return item.pos;
  const routes=neighbors(item.pos).map(p=>path(me().pos,p)).filter(Boolean).sort((a,b)=>a.length-b.length);return routes[0]?.at(-1)||null;
 }

 function button(label,handler,reason=''){const b=RoseUI.key(document.createElement('button'),'field:'+(selected?.id||key(selected?.pos||[]))+':'+label);b.type='button';b.className='quiet';b.textContent=label;b.onclick=handler;RoseUI.rule(b,reason);return b;}
 async function commit(action,target='',pos=null){if(hooks?.busy?.()){notice('Wait for the current host action to finish.');return false;}const ok=await hooks.act('act',{intent:{action,target}});if(ok){const point=pos||me()?.pos;RoseAudio.play(action,point?(project(point)[0]-width/2)/(width/2):0);}return ok;}
 function cancelPress(){if(holdTimer!==null)clearTimeout(holdTimer);holdTimer=null;press=null;}
 function closeMenu(focus=true){const wasOpen=menuOpen;menuOpen=false;get('field-menu').hidden=true;get('field-context').setAttribute('aria-expanded','false');if(wasOpen&&focus)canvas.focus({preventScroll:true});}
 function stop(){walkToken++;walking=false;get('stop-route').hidden=true;notice('Local route stopped.');}
 function reset(){stop();closeMenu(false);cancelPress();snapshot=null;selected=null;hover=null;lastScene=null;cursorMode='move';shiftReveal=false;suppressClick=false;opticalDrafts.clear();RoseAnimations.reset();get('field-detail').hidden=true;}
 async function perform(option,identity=lastScene,targetKey=selectionKey(selected)){
  if(identity!==lastScene||!snapshot){notice('This selection belongs to a previous field.');return false;}
  const value=selectionFromKey(targetKey),fresh=optionsFor(value).find(a=>a.intent.action===option.intent.action&&(option.settings?a.settings?.workshop===option.settings.workshop:a.intent.target===option.intent.target));
  if(!fresh){notice('That action is no longer available for this subject.');return false;}
  if(fresh.reason){notice(fresh.reason);return false;}
  const settings=fresh.settings,choice=settings?(opticalDrafts.get(targetKey)||{band:settings.band,mode:settings.mode}):null;
  const target=settings?settings.workshop+'|'+choice.band+':'+choice.mode:fresh.intent.target;
  closeMenu();const ok=await commit(fresh.intent.action,target,field().interaction_options?.[targetKey]?.pos||value?.pos);
  if(ok&&settings&&identity===lastScene){const current=opticalDrafts.get(targetKey);if(current&&current.band===choice.band&&current.mode===choice.mode)opticalDrafts.delete(targetKey);renderSelection();}
  return ok;
 }
 function selectionFromKey(id){const colon=id.indexOf(':'),type=id.slice(0,colon),identity=id.slice(colon+1);return type==='hex'?{type,pos:identity.split(',').map(Number)}:['unit','structure','project'].includes(type)?{type,id:identity}:null;}
 function actionRow(option,prefix){const identity=lastScene,targetKey=selectionKey(selected),row=document.createElement('div'),b=button(option.label,()=>perform(option,identity,targetKey),option.reason),meta=document.createElement('small');row.className='field-action-option';RoseUI.key(b,prefix+':'+targetKey+':'+option.intent.action+':'+option.intent.target);
  if(option.settings){const settings=option.settings,choice=opticalDrafts.get(targetKey)||settings,controls=document.createElement('div');controls.className='field-optical-settings';
   for(const [name,values]of [['band',settings.bands],['mode',settings.modes]]){const label=document.createElement('label'),select=RoseUI.key(document.createElement('select'),prefix+':'+targetKey+':optical-'+name+':'+settings.band+':'+settings.mode);label.textContent=name==='band'?'Spectrum':'Response';select.dataset.opticalSetting=name;select.dataset.restoreValue='false';RoseUI.options(select,values.map(value=>[value==='alternating'?'PROGRAMMED ALTERNATING':value==='boundary'?'BOUNDARY MODULATION':value.toUpperCase(),value]));select.value=choice[name];select.setAttribute('aria-label',label.textContent+' for '+nameFor(selected));select.onchange=()=>{const focus=RoseUI.remember();opticalDrafts.set(targetKey,{...(opticalDrafts.get(targetKey)||{band:settings.band,mode:settings.mode}),[name]:select.value});renderSelection();RoseUI.restore(focus);};label.append(select);controls.append(label);}row.append(controls);
  }
  const detail=option.skill+' · training '+option.training+' · '+option.stat.toUpperCase()+' vs '+option.dc+'\n'+option.cost+(option.reason?'\n'+option.reason:'');meta.textContent=detail;b.title=detail;row.append(b,meta);return row;
 }
 function renderMenu(){if(!menuOpen)return;const actions=optionsFor();if(!actions.length){closeMenu();return;}get('field-menu-title').textContent=nameFor(selected);get('field-menu').hidden=false;
  for(const group of Object.keys(groups))get('field-menu-'+group).setAttribute('aria-pressed',String(menuGroup===group));
  const entries=actions.filter(a=>a.group===menuGroup),list=get('field-menu-actions');list.replaceChildren(...entries.map(a=>actionRow(a,'menu')));
  if(!entries.length){const p=document.createElement('p');p.className='subtle';p.textContent='No applicable '+groups[menuGroup].toLowerCase()+' action is registered for this subject.';list.append(p);}RoseUI.locks(hooks?.busy?.()||false);
 }
 function openMenu(){if(!selected||!optionsFor().length){notice('Select a registered scene object or hex first.');return;}if(walking)stop();menuOpen=true;menuGroup='look';get('field-context').setAttribute('aria-expanded','true');renderMenu();get('field-menu-look').focus({preventScroll:true});}
 function select(value){if(walking)stop();closeMenu(false);selected=value;const id=selectionKey(value);get('field-object').value=Array.from(get('field-object').children).some(o=>o.value===id)?id:'';if(value?.type==='hex'&&field()?.tiles[key(value.pos)]?.passable)get('field-destination').value=key(value.pos);renderSelection();draw(performance.now());}
 function renderSelection(){
  const f=field(),p=me();if(!f||!p)return;const controls=get('field-selection-actions'),destination=goal(),route=destination?path(p.pos,destination):null;
  let line='Choose a destination, structure or person.';
  if(selected?.type==='structure'){const n=f.infrastructure.nodes.find(n=>n.id===selected.id);if(n){line=n.name.toUpperCase()+' / '+n.id+'\nHex ['+n.pos+'] · '+n.material+'\nCondition '+n.condition+'/100 · '+(n.enabled?'ENABLED':'ISOLATED')+' · '+(n.connected?'CONNECTED':'DISCONNECTED')+' · '+n.status;const ph=snapshot.particles?.photonics;if(n.kind==='workshop'&&ph)line+='\nSHARED RESONANCE / '+ph.band.toUpperCase()+' / '+ph.mode.toUpperCase()+' · STORED '+ph.energy.toFixed(3)+'\nASSIGNED WORKSHOP / '+(ph.source_node||'NONE');}}
  else if(selected?.type==='project'){const n=RoseEnvironment.projects().find(p=>p.id===selected.id);line=n?n.kind.toUpperCase()+' / '+n.id+' / '+n.stage.toUpperCase()+'\nHex ['+n.pos+'] · '+n.material+'\nWork '+n.work_done+'/'+n.work_required+' · reserved '+n.escrow+' · spent '+n.spent:'This project is complete or dismantled. Select its structure or another site.';}
  else if(selected?.type==='unit'){const u=f.units.find(u=>u.id===selected.id);if(u)line=u.name+' / '+u.kind.toUpperCase()+'\nHex ['+u.pos+'] · health '+u.health+' · '+(u.task||u.pose);}
  else if(selected?.type==='hex'){const tile=f.tiles[key(selected.pos)];if(tile)line='AXIAL HEX ['+tile.pos+']\n'+tile.prefab.toUpperCase()+' · '+(tile.passable?'WALKABLE':'SOLID')+' · cover +'+tile.cover;}
  const actions=optionsFor(),sections=[];for(const[group,label]of Object.entries(groups)){const entries=actions.filter(a=>a.group===group);if(!entries.length)continue;const section=document.createElement('div'),title=document.createElement('p');section.className='field-action-group';title.textContent=label;title.className='field-action-heading';section.append(title,...entries.map(a=>actionRow(a,'selection')));sections.push(section);}controls.replaceChildren(...sections);
  get('field-selection').textContent=line;get('field-route').textContent=!selected?'Choose a destination to preview movement.':route?(route.length-1)+' hexes · '+(f.combat?.active?(route.length-1)*f.ap_rules.move_ap+' AP':'six local steps per survival cycle'):'No unoccupied approach is currently available. An adjacent willing companion can be asked to make room.';
  get('walk-path').textContent=walking?'WALKING…':selected?.type==='hex'&&f.tiles[key(selected.pos)]?.passable?'WALK SELECTED PATH':'APPROACH SELECTION';
  const move=f.action_availability?.hex_move?.reason||'',cost=(route?.length-1)*f.ap_rules.move_ap;
  RoseUI.rule(get('walk-path'),move||(!route?'Choose a reachable approach.':route.length<2?'Already at this approach.':f.combat?.active&&cost>(f.combat.ap[snapshot.me.id]||0)?'Choose a path within your AP budget.':''));
  RoseUI.rule(get('field-context'),!actions.length?'Select a scene object or hex.':'');renderMenu();RoseUI.locks(hooks?.busy?.()||false);
 }
 function renderObjects(){const f=field(),options=[['Choose a scene object','']];for(const n of f.infrastructure.nodes)options.push([n.name+' · ['+n.pos+']','structure:'+n.id]);for(const n of RoseEnvironment.projects())options.push([n.kind+' / '+n.stage+' · ['+n.pos+']','project:'+n.id]);for(const u of f.units)options.push([u.name+' · '+u.kind+' · ['+u.pos+']','unit:'+u.id]);for(const t of Object.values(f.tiles))if(t.prefab==='rock')options.push(['Rock · ['+t.pos+']','hex:'+key(t.pos)]);RoseUI.options(get('field-object'),options);const id=selectionKey(selected);get('field-object').value=options.some(o=>o[1]===id)?id:'';}
 function setMode(value){if(value==='target'&&!field()?.combat?.active){notice('Target mode is available during a local encounter.');return;}if(walking)stop();cancelPress();closeMenu(false);cursorMode=value;hover=null;updateMode();draw(performance.now());}
 function updateMode(){for(const mode of ['move','interact','target'])get('cursor-'+mode).setAttribute('aria-pressed',String(cursorMode===mode));RoseUI.rule(get('cursor-target'),field()?.combat?.active?'':'Begin a local encounter to target the construct.');canvas.dataset.cursorMode=cursorMode;get('target-action').disabled=!field()?.combat?.active;get('field-cursor-hint').textContent=cursorMode==='move'?'MOVE / Click to walk or approach. Right-click cycles modes.':cursorMode==='interact'?'INTERACT / Click to Look or Talk. Hold to open actions.':'TARGET / Click the hostile construct for the selected attack. Range, AP and equipment are checked.';RoseUI.locks(hooks?.busy?.()||false);}
 async function walk(){
  if(walking||!snapshot||!snapshot.started||snapshot.paused||snapshot.me.remote){notice('Begin the world, resume its clock and return from remote observation before walking.');return;}
  const destination=goal();if(!destination){notice('Choose a reachable hex or an accessible structure apron.');return;}
  const route=path(me().pos,destination);if(!route||route.length<2){notice('You are already at the selected approach.');return;}
  const encounter=field().combat,cost=(route.length-1)*field().ap_rules.move_ap;
  if(encounter?.active&&(encounter.current!==snapshot.me.id||cost>(encounter.ap[snapshot.me.id]||0))){notice('Choose a path within your current turn and AP budget.');return;}
  walking=true;get('stop-route').hidden=false;const token=++walkToken,sector=field().id;
  try{for(const position of route.slice(1)){if(token!==walkToken||field()?.id!==sector)break;const enteredCombat=field().combat?.active;if(!await commit('hex_move',key(position)))break;if(token!==walkToken)break;if(field()?.combat?.active&&!enteredCombat){notice('A hostile encounter interrupted the route. Review the turn sequence.');break;}await new Promise(resolve=>setTimeout(resolve,reduced()?0:RoseAnimations.stepMs));}
  }finally{if(token===walkToken){walking=false;get('stop-route').hidden=true;renderSelection();}}
 }
 function render(value){
  snapshot=value;const f=field();if(!f)return;size=34*6/f.radius;RoseEnvironment.render(value);
  const identity=`${value.code}:${value.me.id}:${f.id}`;if(lastScene!==identity){lastScene=identity;closeMenu(false);cancelPress();cursorMode='move';hover=null;opticalDrafts.clear();selected=null;walking=false;walkToken++;get('stop-route').hidden=true;}
  get('field-title').textContent=`${value.me.remote?'REMOTE VIEW / BODY AT ':'LOCAL FIELD / '}${value.location.title}`;
  get('field-canvas').setAttribute('aria-label',`Isometric hex field at ${value.location.title}. ${f.units.length} registered units and ${f.infrastructure.nodes.length} structures. Use the scene object and destination selectors for keyboard access. Keys 1, 2 and 3 choose cursor modes; Shift reveals objects; F opens selected actions.`);
  get('field-coordinates').textContent=`SECTOR [${value.me.pos}] · HEX [${me().pos}] · ${f.tiles?Object.keys(f.tiles).length:0} HEXES`;
  const enc=f.combat,names=new Map(f.units.map(u=>[u.id,u.name]));
  get('field-mode').textContent=enc?.active?`COMBAT / ROUND ${enc.round} / ${names.get(enc.current)||enc.current}`:'EXPLORATION / PUBLIC WORKS';
  get('field-ap').textContent=enc?.active?`YOUR AP ${enc.ap[value.me.id]||0} · MOVE ${f.ap_rules.move_ap} · STRIKE ${f.ap_rules.melee_ap} · SHOT ${f.ap_rules.ranged_ap}`:'REAL-TIME DISPLAY / SHARED ECOLOGICAL CLOCK';
  get('field-turn-order').textContent=enc?.active?enc.order.map(id=>`${id===enc.current?'▶ ':''}${names.get(id)||id} (${enc.ap[id]||0} AP)`).join(' → '):'Exploration and combat share this location. Prepared poses keep each actor visually consistent.';
  get('field-combat-controls').hidden=!(value.threat&&!value.threat.resolved)&&!enc?.active;
  get('end-turn').hidden=!enc?.active;get('engage').hidden=!!enc?.active;
  for(const[id,action]of [['engage','engage'],['end-turn','end_turn'],['combat-care','combat_care']])RoseUI.rule(get(id),f.action_availability[action].reason);
  get('field-combat-hint').textContent=enc?.active?['attack','shoot','parley','flee','combat_care'].filter(a=>f.action_availability[a].reason).map(a=>`${{attack:'Strike',shoot:'Shot',parley:'Parley',flee:'Disengage',combat_care:'Care'}[a]}: ${f.action_availability[a].reason}`).join('\n'):f.action_availability.engage.reason;
  get('field-events').textContent=(enc?.log||f.events.map(e=>e.text)).slice(-4).join('\n');
  RoseUI.options(get('field-destination'),Object.values(f.tiles).filter(t=>t.passable).sort((a,b)=>distance(a.pos)-distance(b.pos)).map(t=>[`[${t.pos}] · ${t.prefab} · cover ${t.cover}`,key(t.pos)]));
  const infrastructure=f.infrastructure;
  get('network-summary').textContent=`${infrastructure.nodes.length} STRUCTURES · ${infrastructure.population} RESIDENT DEMAND\nPOWER ${infrastructure.stores.power}/${infrastructure.cap} · WATER ${infrastructure.stores.water} · FOOD ${infrastructure.stores.food} · SCRAP ${infrastructure.stores.scrap}\nLast cycle ${infrastructure.last_cycle<0?'pending':infrastructure.last_cycle} · unmet water ${infrastructure.metrics.unmet_water}, food ${infrastructure.metrics.unmet_food}`;
  get('network-nodes').replaceChildren(...infrastructure.nodes.map(n=>{const card=document.createElement('div');card.className='network-node';const text=document.createElement('span');text.textContent=`${n.name}\n${n.condition}/100 · ${n.connected?'connected':'disconnected'} · ${n.status}`;const choose=button('SELECT / APPROACH',()=>select({type:'structure',id:n.id}));RoseUI.key(choose,'network:'+n.id);card.append(text,choose);return card;}));
  get('network-ledger').textContent=infrastructure.ledger.slice(-6).map(e=>`Cycle ${e.tick}: ${e.text}`).join('\n')||'The first operating cycle is pending. Public stores and every later transfer persist.';
  const now=performance.now();RoseAnimations.read(value,now);RoseWeather.read(value,now);RoseArtDirection.read(value);
  get('rose-rules-summary').textContent=`${value.generation_profile.toUpperCase()} · radius ${value.engine_rules.generation.scene_radius} · infrastructure ${value.engine_rules.generation.infrastructure_density}% · initial condition ${value.engine_rules.generation.starting_condition} · hostile sites ${value.engine_rules.generation.hostility}%\nRules are saved with this world. New host defaults affect new worlds.`;
  if(cursorMode==='target'&&!f.combat?.active)cursorMode='move';renderObjects();updateMode();renderSelection();draw(now);
 }
 function position(u,now){return RoseAnimations.unit(u,now).pos;}
 function polygon(points,fill,stroke){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.stroke();}}
 function hex(pos,elevation=0,fill=null,stroke=null){const[x,y]=project(pos,elevation);polygon(Array.from({length:6},(_,i)=>{const a=(i*60-30)*Math.PI/180;return[x+size*Math.cos(a),y+size*.52*Math.sin(a)];}),fill,stroke);}
 function drawLabels(labels){const placed=[];for(const label of labels){ctx.font=label.font;const w=(ctx.measureText(label.text)?.width||label.text.length*6)+10,h=16,preferred=label.above?-64*size/34:16;let rect=null;
   for(const dy of [0,-18,-36,-54,18,36,54]){for(const dx of [0,-w*.6,w*.6,-w,w]){const candidate={x:Math.max(12,Math.min(width-w-12,label.x+dx-w/2)),y:Math.max(76,Math.min(height-h-55,label.y+preferred+dy-10)),w,h};if(!placed.some(p=>candidate.x<p.x+p.w+5&&candidate.x+candidate.w+5>p.x&&candidate.y<p.y+p.h+3&&candidate.y+candidate.h+3>p.y)){rect=candidate;break;}}if(rect)break;}
   if(!rect)continue;placed.push(rect);if(Math.abs(rect.x+rect.w/2-label.x)>20||Math.abs(rect.y-(label.y+preferred-10))>14){ctx.strokeStyle='#a4b59b66';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(label.x,label.y+(label.above?-44*size/34:8));ctx.lineTo(rect.x+rect.w/2,rect.y+(label.above?rect.h:0));ctx.stroke();}
   ctx.fillStyle='#09130fea';ctx.fillRect(rect.x,rect.y,rect.w,rect.h);ctx.fillStyle=label.color;ctx.textAlign='center';ctx.fillText(label.text,rect.x+rect.w/2,rect.y+11);
  }}

 function propsAt(now){const f=field();if(!f)return[];const props=[];
  for(const tile of Object.values(f.tiles))if(tile.prefab==='rock')props.push({type:'rock',pos:tile.pos,tile,asset:RosePrefabs.assetFor(tile,'rock'),pose:RosePrefabs.materialPose(tile),time:0,facing:0,selection:{type:'hex',pos:tile.pos}});
  for(const node of f.infrastructure.nodes)props.push({type:'structure',pos:node.pos,node,asset:RosePrefabs.assetFor(node),pose:RosePrefabs.structurePose(node),time:reduced()?0:RoseAnimations.clock(now),facing:0,selection:{type:'structure',id:node.id}});
  for(const node of RoseEnvironment.projects()){const preview={...node,condition:Math.min(40,node.condition??40),enabled:false};props.push({type:'project',pos:node.pos,node:preview,asset:RosePrefabs.assetFor(node,node.kind),pose:RosePrefabs.structurePose(preview),time:0,facing:0,selection:{type:'project',id:node.id}});}
  for(const u of f.units){const motion=RoseAnimations.unit(u,now);props.push({type:'unit',pos:motion.pos,elevation:motion.elevation,u:{...u,health:motion.health,facing:motion.facing},asset:RosePrefabs.assetFor(u),pose:motion.pose,time:reduced()?0:motion.time,facing:motion.facing,offset:motion.offset,selection:{type:'unit',id:u.id}});}
  for(const prop of props){
   prop.frame=RosePrefabs.frameInfo(prop.asset,prop.pose,prop.time,prop.facing);
   prop.frame=RoseArtDirection.frame(prop.frame,prop,snapshot.location.region);
   if(prop.type==='structure'&&prop.pose!=='ruined')prop.frame=RoseMotionVisuals.hardware(prop.frame,RoseAnimations.hardware(prop.node,now));
   const cue=RoseAnimations.object(selectionKey(prop.selection),now);
   if(cue?.kind==='impact'){
    const response={stone:.4,metal:.8,wood:1.8,crystal:1.2,polymer:1.5,fabric:2}[cue.material]??.5;
    prop.offset=[response*Math.sin(cue.progress*Math.PI*4)*(1-cue.progress),0];
   }
   const failure=cue?.pending_collapse||(['collapse','collapse_wait'].includes(cue?.kind)?cue:null);
   if(failure&&prop.pose==='ruined'){
    const sourceBefore=RosePrefabs.frameInfo(prop.asset,failure.before_condition<30?'fractured':failure.before_condition<60?'worn':'idle',0,0);
    const before=RoseArtDirection.frame(sourceBefore,prop,snapshot.location.region);
    prop.frame=cue.kind==='collapse'?RoseMotionVisuals.collapse(before,prop.frame,cue):before;
   }
   if(!cue&&prop.pose!=='ruined')prop.frame=RoseWeather.frame(prop.frame,prop,now);
  }
  props.sort((a,b)=>project(a.pos)[1]-project(b.pos)[1]||project(a.pos)[0]-project(b.pos)[0]);for(const prop of props){const tile=f.tiles[key(prop.pos)];prop.screen=project(prop.pos,prop.elevation??tile?.elevation??0).map((v,i)=>v+(prop.offset?.[i]||0)*size/34);}
  const focus=props.filter(p=>p.type==='unit'&&(p.u.mine||selected?.type==='unit'&&selected.id===p.u.id));
  for(const prop of props){prop.faded=fadeProps&&prop.type!=='unit'&&focus.some(u=>props.indexOf(prop)>props.indexOf(u)&&coversBody(prop,u));}
  return props;
 }
 function coversBody(prop,unit){const scale=size/34,pb=RoseEnvironment.bounds(prop),ub=RoseEnvironment.bounds(unit),left=Math.max(prop.screen[0]+pb[0]*scale,unit.screen[0]+ub[0]*scale),right=Math.min(prop.screen[0]+(pb[0]+pb[2])*scale,unit.screen[0]+(ub[0]+ub[2])*scale),top=Math.max(prop.screen[1]+pb[1]*scale,unit.screen[1]+ub[1]*scale),bottom=Math.min(prop.screen[1]+(pb[1]+pb[3])*scale,unit.screen[1]+(ub[1]+ub[3])*scale,unit.screen[1]-4*scale);
  if(right<=left||bottom<=top)return false;const overlap=(x,y)=>RoseEnvironment.hit(prop,[(x-prop.screen[0])/scale,(y-prop.screen[1])/scale])&&RoseEnvironment.hit(unit,[(x-unit.screen[0])/scale,(y-unit.screen[1])/scale]);
  if(overlap((left+right)/2,(top+bottom)/2))return true;for(let y=top;y<bottom;y+=3*scale)for(let x=left;x<right;x+=3*scale)if(overlap(x,y))return true;return false;
 }
 function hitAt(x,y,now=performance.now()){const props=propsAt(now),scale=size/34,behind=[];
  for(const prop of props.slice().reverse()){if(!RoseEnvironment.hit(prop,[(x-prop.screen[0])/scale,(y-prop.screen[1])/scale]))continue;if(prop.faded){behind.push(prop);continue;}return prop.selection;}
  if(behind.length)return behind[0].selection;
  const tile=Object.values(field()?.tiles||{}).reduce((best,t)=>{const[tx,ty]=project(t.pos,t.elevation),d=(x-tx)**2+((y-ty)/.52)**2;return d<best.d?{d,t}:best;},{d:Infinity,t:null});return tile.d<size*size?{type:'hex',pos:tile.t.pos}:null;
 }
 function coordinates(event){const rect=canvas.getBoundingClientRect();return[(event.clientX-rect.left)*width/rect.width,(event.clientY-rect.top)*height/rect.height];}
 function hoverAt(event){if(!field())return;const[x,y]=coordinates(event);if(press&&Math.hypot(x-press.x,y-press.y)>12)cancelPress();hover=hitAt(x,y);let hint='';
  if(hover){if(cursorMode==='target'){const action=get('target-action').value,availability=field().action_availability[action];hint=hover.type==='unit'&&hover.id==='threat'?(availability?.reason||action.toUpperCase()+' · '+(action==='shoot'?field().ap_rules.ranged_ap+' AP + 1 scrap':field().ap_rules.melee_ap+' AP')):'Targeting applies to the hostile construct.';}
   else if(cursorMode==='interact'){const primary=optionsFor(hover).find(a=>a.default)||optionsFor(hover)[0];hint=nameFor(hover)+' · '+(primary?.reason||'CLICK '+(primary?.label||'LOOK'));}
   else hint=nameFor(hover)+' · CLICK TO WALK / APPROACH';}
  get('field-hover').textContent=hint;draw(performance.now());
 }
 function drawDetail(props,palette,lighting){
  const prop=props.find(p=>selectionKey(p.selection)===selectionKey(selected)),container=get('field-detail');container.hidden=!prop;if(!prop)return;
  const detail=get('field-detail-canvas');if(detail.width!==360)detail.width=360;if(detail.height!==360)detail.height=360;const c=detail.getContext('2d');if(!c){container.hidden=true;return;}
  c.clearRect(0,0,360,360);c.fillStyle='#202923';c.fillRect(0,0,360,360);const[x,y,w,h]=RoseEnvironment.bounds(prop),scale=Math.min(4.5,312/Math.max(w,1),312/Math.max(h,1));
  c.save();c.translate(180-(x+w/2)*scale,180-(y+h/2)*scale);c.scale(scale,scale);
  if(prop.type==='rock')RosePrefabs.rock(c,palette,prop.tile,prop.frame);else if(prop.type==='project')RoseEnvironment.drawProject(c,prop,palette);else if(prop.type==='structure'){RosePrefabs.structure(c,prop.node,prop.time,palette,prop.frame);RoseLighting.glow(c,prop,lighting);}else RosePrefabs.unit(c,prop.u,prop.pose,prop.time,palette,RoseLighting.sample(lighting,prop.pos,prop.screen),prop.frame);c.restore();
  const name=nameFor(prop.selection);get('field-detail-label').textContent=name+' / current field appearance';detail.setAttribute('aria-label',name+' field appearance');
 }
 function draw(now){
  ctx.clearRect(0,0,width,height);ctx.fillStyle='#101916';ctx.fillRect(0,0,width,height);const f=field();if(!f){ctx.fillStyle='#9bb69d';ctx.font='18px "Courier New", monospace';ctx.fillText('ROSE / FIELD INITIALIZATION',45,60);return;}
  const palette=f.palette,gradient=ctx.createRadialGradient(500,320,60,500,320,540);gradient.addColorStop(0,palette.ground);gradient.addColorStop(1,'#0c1513');ctx.fillStyle=gradient;ctx.fillRect(0,0,width,height);
  RoseTerrain.draw(ctx,f,snapshot.location.region,project,size,width,height);RoseEnvironment.ground(ctx,f,project,size);
  const reachable=new Set(f.reachable.map(key)),route=goal()?path(me().pos,goal()):null,routeKeys=new Set((route||[]).map(key));
  for(const tile of Object.values(f.tiles).sort((a,b)=>a.pos[1]-b.pos[1]||a.pos[0]-b.pos[0])){
   if(grid)hex(tile.pos,tile.elevation,null,palette.edge);
   if(f.combat?.active&&reachable.has(key(tile.pos)))hex(tile.pos,tile.elevation,'#94c9a017');
   if(routeKeys.has(key(tile.pos)))hex(tile.pos,tile.elevation,'#e8c99b35','#ccb991');
  }
  if(showLinks){for(const link of f.infrastructure.links){ctx.strokeStyle=link.condition>=30?'#b0a77a77':'#c5876b88';ctx.lineWidth=2;ctx.setLineDash([4,5]);ctx.beginPath();link.path.forEach((p,i)=>{const point=project(p);i?ctx.lineTo(...point):ctx.moveTo(...point);});ctx.stroke();ctx.setLineDash([]);}}

  RoseEnvironment.plants(ctx,f,snapshot.location.region,project,size,palette);
  const props=propsAt(now),lighting=RoseLighting.prepare(f,snapshot.location.region,props,size/34,snapshot.particles?.photonics,project);
  RoseLighting.pools(ctx,lighting);
  for(const prop of props){const[x,y]=prop.screen;ctx.save();ctx.translate(x,y);ctx.scale(size/34,size/34);if(prop.faded)ctx.globalAlpha=.24;
   if(prop.type==='rock')RosePrefabs.rock(ctx,palette,prop.tile,prop.frame);else if(prop.type==='project')RoseEnvironment.drawProject(ctx,prop,palette);else if(prop.type==='structure'){RosePrefabs.structure(ctx,prop.node,prop.time,palette,prop.frame);RoseLighting.glow(ctx,prop,lighting);}else RosePrefabs.unit(ctx,prop.u,prop.pose,prop.time,palette,RoseLighting.sample(lighting,prop.pos,prop.screen),prop.frame);ctx.restore();
  }
  drawDetail(props,palette,lighting);
  RoseMotionVisuals.effects(ctx,RoseAnimations.effects(now),pos=>project(pos,f.tiles[key(pos)]?.elevation||0),size/34,palette);
  RoseDisplay.present(ctx,width,height);
  const revealed=reveal||shiftReveal;
  const labels=[];for(const u of f.units.slice().sort((a,b)=>Number(b.mine)-Number(a.mine))){const[x,y]=props.find(p=>p.type==='unit'&&p.u.id===u.id)?.screen||project(position(u,now));if(u.mine||u.kind==='threat'||selected?.id===u.id||revealed||hover?.type==='unit'&&hover.id===u.id)labels.push({text:u.mine?snapshot.me.name:u.name,x,y,above:true,color:u.mine?'#e7bbc8':u.kind==='threat'&&!u.resolved?'#e2a181':palette.accent,font:'10px "Courier New", monospace'});}
  for(const node of f.infrastructure.nodes)if(revealed||selected?.type==='structure'&&selected.id===node.id||hover?.type==='structure'&&hover.id===node.id){const[x,y]=project(node.pos);labels.push({text:node.kind.toUpperCase()+' '+node.condition,x,y,above:false,color:node.condition<30?'#dc9a85':palette.accent,font:'9px "Courier New", monospace'});}
  for(const node of RoseEnvironment.projects())if(revealed||selected?.type==='project'&&selected.id===node.id||hover?.type==='project'&&hover.id===node.id){const[x,y]=project(node.pos);labels.push({text:node.kind.toUpperCase()+' / '+node.stage+' '+node.work_done+'/'+node.work_required,x,y,above:false,color:'#d8bf96',font:'9px "Courier New", monospace'});}
  for(const prop of props){const id=selectionKey(prop.selection),chosen=id===selectionKey(selected),pointed=id===selectionKey(hover);if(!chosen&&!pointed&&!revealed)continue;const[x,y]=prop.screen,scale=size/34;ctx.strokeStyle=prop.type==='unit'&&prop.u.kind==='threat'&&!prop.u.resolved?'#f0a48e':chosen?'#f3dfae':'#b1d8c0';ctx.lineWidth=chosen?2:1;
   const[bX,bY,bW,bH]=RoseEnvironment.bounds(prop);ctx.strokeRect(x+bX*scale-3,y+bY*scale-3,bW*scale+6,bH*scale+6);
   if(revealed&&prop.type==='rock')labels.push({text:'ROCK ['+prop.pos+']',x,y,above:false,color:'#c0c6ae',font:'9px "Courier New", monospace'});
  }
  drawLabels(labels);
  if(selected?.type==='structure'||selected?.type==='project'){const n=selected.type==='project'?RoseEnvironment.projects().find(n=>n.id===selected.id):f.infrastructure.nodes.find(n=>n.id===selected.id);if(n)hex(n.pos,0,null,'#eadcc0');}else if(selected?.type==='hex')hex(selected.pos,0,null,'#eadcc0');
  if(hover?.type==='hex')hex(hover.pos,0,null,cursorMode==='target'?'#ce8e7d':'#c8e7c6');
  ctx.textAlign='left';ctx.fillStyle=palette.accent;ctx.font='12px "Courier New", monospace';ctx.fillText('ROSE / '+snapshot.location.region.replaceAll('_','.'),32,34);ctx.fillStyle='#b3b6a6';ctx.font='10px "Courier New", monospace';ctx.fillText('LOCAL TERRAIN'+(f.lifecycle?.season?' · '+f.lifecycle.season.toUpperCase():''),32,53);ctx.fillText(cursorMode.toUpperCase()+' / '+(revealed?'OBJECTS REVEALED':f.combat?.active?'TACTICAL / ACTION POINTS':'EXPLORATION'),32,height-26);
 }
 async function click(event){if(!field())return;if(suppressClick){suppressClick=false;return;}cancelPress();const[x,y]=coordinates(event),value=hitAt(x,y);if(!value){notice('Beyond this local field. Open World Map to travel onward.');return;}select(value);
  if(cursorMode==='move')return walk();
  if(cursorMode==='target'){if(value.type!=='unit'||value.id!=='threat'){notice('Choose the hostile construct for targeting.');return;}const action=get('target-action').value,reason=field().action_availability[action]?.reason;if(reason){notice(reason);return;}return commit(action,'threat',field().units.find(u=>u.id==='threat').pos);}
  const actions=optionsFor(),primary=actions.find(a=>a.default)||actions[0];if(primary)return perform(primary);
 }
 function pointerDown(event){suppressClick=false;cancelPress();if(event.button!==0||cursorMode!=='interact'||!field())return;const[x,y]=coordinates(event),value=hitAt(x,y);if(!value)return;press={x,y,value};const identity=lastScene;
  holdTimer=setTimeout(()=>{holdTimer=null;if(identity!==lastScene||!press)return;const target=press.value;press=null;suppressClick=true;select(target);openMenu();},450);
 }
 function menuKey(event){if(event.key==='Escape'){event.preventDefault();closeMenu();return;}if(document.activeElement?.tagName==='SELECT'||!['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;const buttons=Array.from(get('field-menu').querySelectorAll('button')).filter(b=>!b.disabled);if(!buttons.length)return;event.preventDefault();const index=buttons.indexOf(document.activeElement),next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus({preventScroll:true});}
 function initRules(catalog){
  for(const[group,fields]of Object.entries(catalog.limits)){const fieldset=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent=group.toUpperCase();fieldset.append(legend);for(const[name,[min,max]]of Object.entries(fields)){const label=document.createElement('label');label.textContent=name.replaceAll('_',' ');const input=document.createElement('input');input.type='number';input.min=min;input.max=max;input.step='1';input.value=catalog.rules[group][name];input.id=`rule-${group}-${name}`;input.dataset.group=group;input.dataset.variable=name;label.append(input);fieldset.append(label);}get('engine-fields').append(fieldset);}
  get('engine-profile').replaceChildren(...catalog.profiles.map(p=>new Option(p.toUpperCase(),p)));get('engine-profile').value='balanced';get('engine-profile').onchange=()=>{const preset=catalog.profile_rules[get('engine-profile').value];for(const[group,fields]of Object.entries(catalog.limits))for(const name of Object.keys(fields))get(`rule-${group}-${name}`).value=preset[group][name];};rulesReady=true;
 }
 function newWorld(){if(!rulesReady)throw Error('Engine configuration is still loading.');const rules={schema:1};get('engine-fields').querySelectorAll('input').forEach(input=>{const group=input.dataset.group;(rules[group]??={})[input.dataset.variable]=Number(input.value);});return{profile:get('engine-profile').value,rules};}

 function configure(callbacks){hooks=callbacks;RoseEnvironment.configure({act:hooks.act,select,busy:hooks.busy});get('walk-path').onclick=walk;get('stop-route').onclick=stop;get('field-destination').onchange=()=>select({type:'hex',pos:get('field-destination').value.split(',').map(Number)});get('field-object').onchange=()=>{if(get('field-object').value)select(selectionFromKey(get('field-object').value));};get('field-context').onclick=openMenu;get('field-menu-close').onclick=()=>closeMenu();get('field-menu').onkeydown=menuKey;
  for(const mode of ['move','interact','target'])get('cursor-'+mode).onclick=()=>setMode(mode);
  for(const group of Object.keys(groups))get('field-menu-'+group).onclick=()=>{menuGroup=group;renderMenu();};
  get('target-action').value='attack';get('target-action').onchange=()=>{updateMode();get('field-hover').textContent='';};
  reveal=RoseUI.read('localStorage','rose-reveal')==='on';fadeProps=RoseUI.read('localStorage','rose-prop-fade')!=='off';
  const settings=()=>{get('toggle-reveal').textContent='REVEAL '+(reveal?'ON':'OFF');get('toggle-reveal').setAttribute('aria-pressed',String(reveal));get('toggle-occlusion').textContent='PROP FADE '+(fadeProps?'ON':'OFF');get('toggle-occlusion').setAttribute('aria-pressed',String(fadeProps));};settings();
  get('toggle-reveal').onclick=()=>{reveal=!reveal;RoseUI.write('localStorage','rose-reveal',reveal?'on':'off');settings();draw(performance.now());};get('toggle-occlusion').onclick=()=>{fadeProps=!fadeProps;RoseUI.write('localStorage','rose-prop-fade',fadeProps?'on':'off');settings();draw(performance.now());};
  get('field-audio').onclick=async()=>{try{await RoseAudio.toggle();get('field-audio').textContent='AUDIO '+(RoseAudio.enabled?'ON':'OFF');get('field-audio').setAttribute('aria-pressed',String(RoseAudio.enabled));}catch(error){notice(error.message);}};
  get('toggle-grid').onclick=()=>{grid=!grid;get('toggle-grid').textContent='HEX GRID '+(grid?'ON':'OFF');draw(performance.now());};get('toggle-links').onclick=()=>{showLinks=!showLinks;get('toggle-links').textContent='NETWORK '+(showLinks?'ON':'OFF');draw(performance.now());};get('engage').onclick=()=>commit('engage');get('end-turn').onclick=()=>commit('end_turn');get('combat-care').onclick=()=>commit('combat_care');
  get('export-engine').onclick=async()=>{try{const data=await hooks.export(),blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Rose-infrastructure-blueprint.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){notice(error.message);}};
  canvas.onclick=click;canvas.onpointerdown=pointerDown;canvas.onpointerup=cancelPress;canvas.onpointercancel=()=>{cancelPress();suppressClick=false;};canvas.onpointermove=hoverAt;canvas.onpointerleave=()=>{cancelPress();hover=null;get('field-hover').textContent='';draw(performance.now());};canvas.oncontextmenu=e=>{e.preventDefault();suppressClick=false;cancelPress();if(e.pointerType==='touch'){const[x,y]=coordinates(e),value=hitAt(x,y);if(value)select(value);openMenu();return;}const modes=field()?.combat?.active?['move','interact','target']:['move','interact'];setMode(modes[(modes.indexOf(cursorMode)+1)%modes.length]);};
  canvas.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();cancelPress();closeMenu();if(walking)stop();return;}if(e.key==='Shift'){shiftReveal=true;draw(performance.now());return;}if(['1','2','3'].includes(e.key)){e.preventDefault();setMode({'1':'move','2':'interact','3':'target'}[e.key]);return;}if(e.key.toLowerCase()==='f'||e.key==='ContextMenu'||e.shiftKey&&e.key==='F10'){e.preventDefault();openMenu();return;}
   const index={d:0,e:1,w:2,a:3,z:4,x:5,ArrowRight:0,ArrowUp:2,ArrowLeft:3,ArrowDown:5}[e.key];if(index!==undefined&&me()){e.preventDefault();const p=me().pos.map((v,i)=>v+dirs[index][i]);select({type:'hex',pos:p});walk();}else if(e.key==='Enter'){e.preventDefault();if(cursorMode==='interact'){const primary=optionsFor().find(a=>a.default)||optionsFor()[0];if(primary)perform(primary);}else if(cursorMode==='target'){if(selected?.id==='threat'){const option=optionsFor().find(a=>a.intent.action===get('target-action').value);if(option)perform(option);}else notice('Select the construct before a targeted attack.');}else walk();}};
  canvas.onkeyup=e=>{if(e.key==='Shift'){shiftReveal=false;draw(performance.now());}};canvas.onblur=()=>{shiftReveal=false;cancelPress();draw(performance.now());};
  const style=get('art-style'),savedStyle=RoseUI.read('localStorage','rose-art-style');style.value=['rendered','rendered-legacy','raster','vector'].includes(savedStyle)?savedStyle:'rendered';RosePrefabs.setStyle(style.value);style.onchange=()=>{RosePrefabs.setStyle(style.value);RoseUI.write('localStorage','rose-art-style',style.value);draw(performance.now());};
  const light=get('lighting-mode'),savedLight=RoseUI.read('localStorage','rose-lighting-mode');light.value=['signature','subdued','baked'].includes(savedLight)?savedLight:'signature';RoseLighting.configure(light.value);light.onchange=()=>{RoseLighting.configure(light.value);RoseUI.write('localStorage','rose-lighting-mode',RoseLighting.mode);draw(performance.now());};
  const motion=get('animation-mode'),savedMotion=RoseUI.read('localStorage','rose-motion-profile');motion.value=['system','full','reduced'].includes(savedMotion)?savedMotion:'system';RoseAnimations.configure(motion.value);motion.onchange=()=>{RoseAnimations.configure(motion.value);RoseUI.write('localStorage','rose-motion-profile',RoseAnimations.mode);draw(performance.now());};
  const direction=get('material-direction');direction.value=RoseUI.read('localStorage','rose-material-direction')==='baked'?'baked':'source';RoseArtDirection.configure(direction.value==='source');direction.onchange=()=>{RoseArtDirection.configure(direction.value==='source');RoseUI.write('localStorage','rose-material-direction',direction.value);draw(performance.now());};
  fetch('/art-direction-runtime.json').then(r=>{if(!r.ok)throw Error('Material direction is unavailable; using baked surfaces.');return r.json();}).then(value=>{RoseArtDirection.load(value);draw(performance.now());}).catch(e=>notice(e.message));
  fetch('/lighting-signatures.json').then(r=>{if(!r.ok)throw Error('Regional lighting data is unavailable.');return r.json();}).then(value=>{RoseLighting.load(value);draw(performance.now());}).catch(e=>notice(e.message));
  for(const url of ['/art-manifest-rendered.json','/art-manifest-rendered-legacy.json','/art-manifest.json'])fetch(url).then(r=>{if(!r.ok)throw Error('Art manifest unavailable: '+url);return r.json();}).then(RosePrefabs.load).then(()=>draw(performance.now())).catch(e=>notice(e.message));
  function frame(now){if(!reduced()&&now-lastFrame>33){lastFrame=now;if(snapshot&&!document.hidden&&!get('rose-field').hidden)draw(now);}requestAnimationFrame(frame);}requestAnimationFrame(frame);
 }
 return{configure,initRules,newWorld,render,path,stop,reset,select,draw,project,hitAt,appearance:now=>propsAt(now),occlusion:now=>propsAt(now).filter(p=>p.faded).map(p=>selectionKey(p.selection)),get mode(){return cursorMode;},get menuOpen(){return menuOpen;},beforeAction:(op,data)=>{cancelPress();closeMenu();if(walking&&(op!=='act'||data.intent?.action!=='hex_move'))stop();}};
})();
