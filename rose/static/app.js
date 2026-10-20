'use strict';
const $=id=>document.getElementById(id);
const make=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;};
let session=RoseUI.session('sessionStorage'),state=null,busy=false,suggestion=null,catalog=null,loadedCharacterId=null;
let sessionEpoch=0,readEpoch=0,polling=null,lastResultKey=null,pollError=null;
$('resume').hidden=!RoseUI.session('localStorage');
let crt=RoseUI.read('localStorage','rose-crt')!=='off';
const displayProfile=$('display-profile'),savedDisplay=RoseUI.read('localStorage','rose-display-profile');
displayProfile.value=['soft','sharp'].includes(savedDisplay)?savedDisplay:'soft';
function showCRT(){document.body.classList.toggle('no-crt',!crt);$('crt').textContent=`CRT ${crt?'ON':'OFF'}`;$('crt').setAttribute('aria-pressed',String(crt));RoseDisplay.configure(crt,displayProfile.value);$('display-note').textContent=!crt?'CRT disabled. Native pixels and clear labels.':displayProfile.value==='soft'?'Soft phosphor: softened field art, static scanlines and clear labels.':'Sharp pixels: native field art and clear labels.';RoseField.draw(performance.now());}showCRT();
$('crt').onclick=()=>{crt=!crt;RoseUI.write('localStorage','rose-crt',crt?'on':'off');showCRT();};
displayProfile.onchange=()=>{RoseUI.write('localStorage','rose-display-profile',displayProfile.value);showCRT();};
function error(msg){$('error').textContent=msg||'';}
async function api(op,data={}){
 const timeout=op==='narrate'||op==='interpret'?55000:12000;let timer,signal;
 if(typeof AbortSignal!=='undefined'&&AbortSignal.timeout)signal=AbortSignal.timeout(timeout);
 else{const controller=new AbortController();signal=controller.signal;timer=setTimeout(()=>controller.abort(),timeout);}
 try{const response=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...session,op,...data}),signal});let body;
  try{body=await response.json();}catch{throw Error('The host returned an unreadable response. Reconnect to review the saved state before trying again.');}
  if(!response.ok)throw Error(body?.error||'The host could not complete that request.');return body;
 }catch(e){if(e.name==='TimeoutError'||e.name==='AbortError')throw Error('The host did not respond in time. Reconnect to review the saved state before trying again.');throw e;}finally{if(timer)clearTimeout(timer);}
}
function lock(flag){busy=flag;RoseUI.locks(flag);}
function useSession(value){if(value&&!RoseUI.validSession(value))throw Error('The host returned an invalid session.');session=value;sessionEpoch++;readEpoch++;polling=null;lastResultKey=null;suggestion=null;$('confirm-intent').hidden=true;}
function checkedState(value){if(!value||!Number.isSafeInteger(value.revision)||value.revision<0||value.code!==session?.code||value.me?.id!==session?.id||!value.location||!value.character_sheet||!value.engine_rules||!Array.isArray(value.scene?.units))throw Error('The host returned an invalid world response. Your displayed state and input are retained. Reconnect before trying again.');return value;}
async function poll(){
 if(!session||busy||polling===sessionEpoch)return false;
 const generation=sessionEpoch,requestId=++readEpoch;polling=generation;
 try{const next=await api('state');if(generation!==sessionEpoch||requestId!==readEpoch||busy||!session)return false;checkedState(next);
  if(!state||next.revision>state.revision||next.revision===state.revision&&next.clock_error!==state.clock_error){state=next;render();}
  $('connection').textContent='HOST CONNECTED';if(pollError&&$('error').textContent===pollError)error('');pollError=null;return true;
 }catch(e){if(generation===sessionEpoch&&requestId===readEpoch){$('connection').textContent='RECONNECTING';pollError=e.message;error(e.message);}return false;
 }finally{if(polling===generation)polling=null;}
}
async function action(op,data={}){
 if(busy||!session||!state)return false;
 const generation=sessionEpoch;readEpoch++;RoseField.beforeAction(op,data);lock(true);error('');
 try{const answer=await api(op,{revision:state.revision,...data});if(generation!==sessionEpoch)return false;
  if(answer?.left&&op==='leave'){disconnect();return true;}state=checkedState(answer?.state);render();
  if(answer.result){$('response').hidden=false;$('result').textContent=answer.result.text;$('roll').textContent=answer.result.mechanics||'';}
  return !answer.result||answer.result.intent!==null;
 }catch(e){if(generation===sessionEpoch)error(e.message);return false;}finally{if(generation===sessionEpoch){lock(false);await poll();}}
}
function disconnect(){useSession(null);state=null;loadedCharacterId=null;RoseField.reset();RoseWorld.reset();lock(false);RoseUI.remove('sessionStorage','rose-session');$('game').hidden=true;$('entry').hidden=false;$('character-builder').hidden=false;$('character-apply').hidden=true;$('response').hidden=true;$('model-prose').textContent='';$('connection').textContent='DISCONNECTED';document.body.removeAttribute('data-region');document.body.classList.remove('remote');$('resume').hidden=!RoseUI.session('localStorage');}
function gameReason(command){const s=state;if(!s)return '';if(!s.started)return 'The host must begin the expedition.';if(s.paused)return 'The host has paused this world.';const observed=/^(look|inspect|listen|inventory|map|return|remote survey|inspect environment|inspect particles)$/.test(command)||/^inspect (gear|weapon) [\w_]+$/.test(command)||!s.particles?.percept.address&&/^inspect material (structure|project|hex) [\w,-]+$/.test(command);if(s.particles?.percept.address&&!observed&&!/^(eat|drink|wait|advance void|retreat void|return from void)/.test(command))return 'Return through the recorded void trace before baseline work.';if(s.me.remote&&!observed)return 'Return from remote observation before physical actions.';const availability=s.scene.action_availability?.[command];if(availability)return availability.reason;if(s.scene.combat?.active&&!observed)return 'Resolve the encounter before ordinary field work.';return '';}
function refreshControls(){for(const b of document.querySelectorAll('button'))if(b.dataset.gameAction!==undefined)RoseUI.rule(b,gameReason(b.dataset.gameAction));RoseUI.rule($('submit-action'),!state?.started?'The host must begin the expedition.':state.paused?'The host has paused this world.':'');RoseUI.locks(busy);}
function actionButton(b,command){b.dataset.gameAction=command;return b;}
function render(){if(!state)return;const s=state,p=s.me,c=s.location;
 const saved=RoseUI.remember();
 $('character-builder').hidden=s.started;$('character-apply').hidden=s.started;
 if(loadedCharacterId!==p.id&&catalog){RoseCreator.set(s.character_sheet.role,s.character_sheet);loadedCharacterId=p.id;}
 $('entry').hidden=true;$('game').hidden=false;document.body.dataset.region=c.region;document.body.classList.toggle('remote',p.remote);
 $('world-code').textContent=`WORLD ${s.code} · ${s.players.length}/6 EXPLORERS`;$('clock').textContent=`CYCLE ${s.tick} / ${s.phase.toUpperCase()} / ${s.paused?'PAUSED':s.season.toUpperCase()}`;$('weather').textContent=s.weather.toUpperCase();
 $('clock-fault').hidden=!s.clock_error;$('clock-fault').textContent=s.clock_error||'';
 $('start').hidden=s.started||s.host!==session.id;$('pause').hidden=!s.started||s.host!==session.id;$('pause').textContent=s.paused?'RESUME CLOCK':'PAUSE CLOCK';
 $('region').textContent=s.particles?.percept.address?'void_null / TANGIBLE EXPEDITION':p.remote?'NULL_FIELD.OMNI / REMOTE PERCEPT':c.region;$('location').textContent=s.particles?.percept.address?'The current interact / '+s.particles.percept.path.length:p.remote?'Beyond the received horizon':c.title;
 $('provenance').textContent=s.particles?.percept.address?'TANGIBLE PERCEPT · RECORDED RETURN TRACE / RETAINED WORLD ANCHOR':p.remote?'UNVERIFIED PROJECTION · BODY REMAINS AT CURRENT COORDINATES':(s.atlas?'DRAWING-BASED GEOGRAPHY · DOCUMENTED LANDMARKS / GENERATED LOCAL LIFE':'LEGACY GENERATED SITE · ORIGINAL QUADRANT LAYOUT');$('description').textContent=s.description;
 $('condition-row').replaceChildren(...[`Moisture ${c.moisture}`,`Growth ${c.growth}`,`Stability ${c.stability}`,`AETHER ${c.aether}`,`Shelter ${c.shelter}`,`Fauna index ${c.fauna}`,s.succession].map(x=>make('span',x,'condition')));
 $('opportunities').replaceChildren(...s.opportunities.map(o=>{const n=make('div'),b=RoseUI.key(actionButton(make('button',o.command.toUpperCase(),'quiet'),o.command),'opportunity:'+o.command);b.onclick=()=>action('act',{text:o.command});n.append(make('p',o.text),b);return n;}));
 renderAtlas(s);renderAdventure(s);renderSystems(s);RoseField.render(s);
 $('help').textContent=s.help;$('me').replaceChildren(make('strong',p.name),make('small',`${p.build} · XP ${p.xp} · Karma ${p.karma}`));
 $('vitals').replaceChildren();for(const [key,label]of [['health','HEALTH'],['energy','ENERGY'],['thirst','THIRST'],['food_need','HUNGER'],['sleep','SLEEP DEBT']]){const v=make('div','','vital'),l=make('div','','vital-label'),m=document.createElement('meter'),highGood=['health','energy'].includes(key),danger=highGood?p[key]<=(key==='health'?30:15):p[key]>=80;v.classList.toggle('needs-care',danger);l.append(make('span',label+(danger?' / NEEDS CARE':'')),make('span',`${p[key]}/100`));m.min=0;m.max=100;m.low=highGood?30:60;m.high=80;m.optimum=highGood?100:0;m.value=p[key];m.setAttribute('aria-label',`${label}: ${p[key]} of 100; ${highGood?'higher':'lower'} is better${danger?'; care needed':''}`);v.append(l,m);$('vitals').append(v);}
 $('inventory').textContent=Object.entries(p.inventory).map(([k,v])=>`${k.toUpperCase()} ${v}`).join(' · ');
 renderMaterials(s);
 $('map').replaceChildren();for(const t of s.map){const own=t.x===p.pos[0]&&t.y===p.pos[1],symbol=own?'◎':t.players.length?'●':t.shelter?'⌂':t.known?'·':'?';const cell=make('div',symbol,`map-cell ${t.known?'':'unknown'} ${t.players.length?'occupied':''}`);const label=`${t.x},${t.y}: ${t.title}${t.players.length?' / '+t.players.join(', '):''}`;cell.title=label;cell.setAttribute('aria-label',label);$('map').append(cell);}
 $('position').textContent=`[${p.pos}] · ${s.discovered} recorded sites\n◎ You · ● Party · ⌂ Shelter · ? Unknown\nNearby survey records; world journeys run on the world map.`;
 $('party').replaceChildren(...s.players.map(q=>{const n=make('div',q.name+(q.id===s.host?' / HOST':''),'party-member');n.append(make('small',`${q.build} · [${q.pos}]${q.remote?' · remote observation':''}`));return n;}));
 $('actors').replaceChildren(...(s.actors.length?s.actors.map(a=>make('p',`${a.name} / ${a.role}\n${a.activity} · needs ${a.need}`)):[make('p','No traveler is presently here.')]));
 $('contract').textContent=p.contract?`${(p.contract.kind||'survey').toUpperCase()} · ${p.contract.destination||'field target'} [${p.contract.target}]\nFor ${p.contract.faction}. Reward: ${p.contract.reward}.\n${!p.contract.kind?'At the target, type survey.':p.contract.kind==='restoration'?'Complete a successful repair here, then fulfill.':p.contract.kind==='delivery'?'Carry two food and one water; fulfill at the target.':'At the target, type fulfill.'}`:'No accepted commitment. Review the local board when ready.';
 $('contract-fulfill').onclick=()=>action('act',{text:p.contract&&!p.contract.kind?'survey':'fulfill'});
 $('contract-route').hidden=!s.atlas||!p.contract;
 $('reputation').replaceChildren(...Object.entries(s.reputation).map(([k,v])=>make('div',`${k} · shared ${v>=0?'+':''}${v} · personal ${p.personal_reputation[k]||0}`,'rep')));
 $('journal').replaceChildren(...s.journal.slice(-20).reverse().map(j=>{const n=make('div','',`journal-item ${j.kind}`);n.append(make('small',`CYCLE ${j.tick} / ${j.kind.toUpperCase()}${j.coord?' / ['+j.coord+']':''}`),make('div',j.text));return n;}));
 $('interpret-wrap').hidden=!s.narrator_enabled;$('narrate').hidden=!s.narrator_enabled;$('narrator-note').textContent=s.narrator_enabled?'A local language model is configured on this host.':'No local model configured. The scene above is generated by Rose’s state-driven procedural narrator.';
 $('submit-action').textContent=s.paused?'WORLD PAUSED':s.started?'ACT →':'WAITING FOR HOST';
 const resultKey=JSON.stringify([p.last_action,p.last_result]);if(p.last_result&&lastResultKey!==resultKey){lastResultKey=resultKey;$('response').hidden=false;$('result').textContent=p.last_result;$('roll').textContent=p.last_action?.mechanics||'';}
 refreshControls();RoseUI.restore(saved);
}
$('join-form').onsubmit=async e=>{e.preventDefault();if(busy)return;let generation=sessionEpoch;lock(true);error('');try{const code=$('code').value.trim(),result=await api(code?'join':'create',{name:$('name').value,build:RoseCreator.role(),character:RoseCreator.read(),code,seed:$('seed').value,...(code?{}:RoseField.newWorld())});if(generation!==sessionEpoch)return;useSession(result);generation=sessionEpoch;const saved=RoseUI.write('sessionStorage','rose-session',JSON.stringify(result));const remembered=RoseUI.write('localStorage','rose-session',JSON.stringify(result));const next=await api('state');if(generation!==sessionEpoch)return;state=checkedState(next);render();$('connection').textContent='HOST CONNECTED';if(!saved||!remembered)error('Browser storage is unavailable. This session works while the page stays open, but it cannot be remembered automatically.');}catch(e){if(generation===sessionEpoch)error(e.message);}finally{if(generation===sessionEpoch)lock(false);}};
$('resume').onclick=async()=>{if(busy)return;const saved=RoseUI.session('localStorage');if(!saved){$('resume').hidden=true;error('No valid saved session is available. Create or join a world.');return;}useSession(saved);loadedCharacterId=null;RoseUI.write('sessionStorage','rose-session',JSON.stringify(saved));state=null;await poll();};
$('start').onclick=()=>action('start');$('pause').onclick=()=>action('pause');$('disconnect').onclick=disconnect;
$('leave').onclick=async()=>{if(await action('leave')){RoseUI.remove('localStorage','rose-session');$('resume').hidden=true;}};
$('action-form').onsubmit=async e=>{e.preventDefault();const text=$('prompt').value.trim();if(text&&await action('act',{text})){$('prompt').value='';suggestion=null;$('confirm-intent').hidden=true;}};
$('prompt').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('action-form').requestSubmit();}};
$('prompt').oninput=()=>{suggestion=null;$('confirm-intent').hidden=true;};
for(const command of ['look','inspect the habitat','forage','collect water','repair the habitat','plant a seed','wait']){const b=actionButton(make('button',command.toUpperCase()),command==='inspect the habitat'?'inspect':command);b.type='button';b.onclick=()=>action('act',{text:command});$('quick').append(b);}
document.querySelectorAll('[data-command]').forEach(b=>{actionButton(b,b.dataset.command);b.onclick=()=>action('act',{text:b.dataset.command});});
$('chat-form').onsubmit=async e=>{e.preventDefault();const text=$('chat-text').value;if(await action('chat',{text}))$('chat-text').value='';};
$('export').onclick=async()=>{try{const data=await api('export'),blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Rose-field-journal.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){error(e.message);}};
$('narrate').onclick=async()=>{if(busy||!session)return;const generation=sessionEpoch;readEpoch++;lock(true);error('');$('model-prose').textContent='The local model is composing a scene…';try{const r=await api('narrate');if(generation===sessionEpoch)$('model-prose').textContent=`${r.label} / cycle ${r.tick}\n\n${r.prose}`;}catch(e){if(generation===sessionEpoch){$('model-prose').textContent='';error(e.message);}}finally{if(generation===sessionEpoch){lock(false);await poll();}}};
$('interpret').onclick=async()=>{const text=$('prompt').value.trim();if(busy||!text||!session)return;const generation=sessionEpoch;readEpoch++;lock(true);error('');try{const r=await api('interpret',{text});if(generation!==sessionEpoch||$('prompt').value.trim()!==text)return;suggestion={text,intent:r.intent};$('confirm-intent').textContent=`REVIEWED: TRY ${r.intent.action.toUpperCase()} ${r.intent.target.toUpperCase()} →`;$('confirm-intent').hidden=false;}catch(e){if(generation===sessionEpoch)error(e.message);}finally{if(generation===sessionEpoch){lock(false);await poll();}}};
$('confirm-intent').onclick=async()=>{if(!suggestion)return;if(await action('act',suggestion)){suggestion=null;$('confirm-intent').hidden=true;$('prompt').value='';}};
RoseField.configure({act:action,export:()=>api('engine_export'),busy:()=>busy});
RoseWorld.configure({act:action});
RoseParticulate.configure({act:action,export:target=>api('particle_export',{target:target||''}),busy:()=>busy});
fetch('/catalog').then(r=>{if(!r.ok)throw Error('Cannot load character creation.');return r.json();}).then(c=>{catalog=c;RoseCreator.init(c.characters);RoseField.initRules(c.engine);const update=()=>{$('build-note').textContent=Object.entries(c.characters.presets[RoseCreator.role()].attributes).map(([k,v])=>`${k.toUpperCase()} ${v}`).join(' · ');};const change=$('build').onchange;$('build').onchange=()=>{change();update();};update();if(state)render();}).catch(e=>error(e.message));

poll();setInterval(()=>{if(state?.atlas?.navigation.status==='traveling')poll();},500);setInterval(poll,4000);
window.addEventListener('unhandledrejection',e=>error('The interface could not complete an operation: '+(e.reason?.message||e.reason)));

function renderAtlas(s){RoseWorld.render(s);RoseParticulate.render(s);}
$('character-apply').onclick=async()=>{try{await action('character',{build:RoseCreator.role(),character:RoseCreator.read()});}catch(e){error(e.message);}};
function renderAdventure(s){
 const p=s.me,ch=s.character_sheet,button=(label,command)=>{const b=RoseUI.key(actionButton(make('button',label,'quiet'),command),'adventure:'+command);b.onclick=()=>action('act',{text:command});return b;};
 $('dialogue-options').replaceChildren(...s.dialogue_options.map(o=>button(o.label,o.command)));
 $('dialogue-history').replaceChildren(...p.dialogue_log.slice(-12).reverse().map(d=>make('p',`Cycle ${d.tick} · ${d.location} · ${d.npc} / ${d.topic}\n${d.response}`)));
 $('contract-options').replaceChildren(...(s.atlas?s.contract_options:[{label:'Accept survey commission',command:'accept a survey contract'}]).map(o=>button(o.label,o.command)));
 const serviceCommands={register:'register',mods:'study',lesson:'study',care:'clinic',medical_contract:'clinic',free_provision:'provision'};
 $('services').replaceChildren(button('FIELD TREATMENT / medkit','treat'),...s.local_services.filter(k=>serviceCommands[k]).map(k=>button(k.replaceAll('_',' ').toUpperCase(),serviceCommands[k])));
 $('equipment').replaceChildren();for(const [id,m]of Object.entries(catalog?.characters.equipment||{}))$('equipment').append(button(`${ch.loadout.includes(id)?'REMOVE':'INSTALL / 2 SCRAP'} ${m.label}`,`${ch.loadout.includes(id)?'remove':'install'} ${id}`));
 const lines=[`${ch.role} · ${ch.pronouns||'pronouns unspecified'} · ${ch.age||'age unspecified'}`,`${ch.origin} · ${ch.form} · ${ch.affiliation} · ${ch.affinity}`,Object.entries(ch.attributes).map(([k,v])=>`${k.toUpperCase()} ${v}`).join(' / '),`Appearance: ${ch.appearance||'not yet described'}`,`Voice: ${ch.voice||'not yet described'}`,`Mannerisms: ${ch.mannerisms||'not yet described'}`,`Biography: ${ch.bio||'not yet described'}`,`Goal: ${ch.goal||'not yet stated'}`,`Boundaries: ${ch.boundary||'not yet stated'}`,`Training: ${Object.entries(ch.skills).map(([k,v])=>(catalog?.characters.skills[k]?.label||k)+' '+v).join('; ')||'none'}`,`Verified field credentials: ${ch.credentials.join(', ')||'none'}`,`Loadout: ${ch.loadout.join(', ')||'none'} · care benefit ${ch.care_benefits}/3`,`Injuries: ${ch.injuries.join(', ')||'none'} · ailments: ${ch.ailments.join(', ')||'none'}`];
 $('character-sheet').replaceChildren(...lines.map(l=>make('p',l)));
}

function renderMaterials(s){
 const data=s.materials;if(!data)return;
 $('material-items').replaceChildren(...data.items.map(item=>{
  const detail=RoseUI.key(make('details'),'gear:'+item.key),summary=RoseUI.key(make('summary',`${item.name} · ${item.state.toUpperCase()} · ${item.condition}/100${item.installed?'':' · stored'}`),'gear:'+item.key+':summary');
  detail.append(summary,make('p',`${item.material_label} · ${item.material_state.age} exposure cycles · replacement ${item.generation}`, 'subtle'));
  const controls=make('div','','quick');for(const option of item.actions){const b=RoseUI.key(make('button',option.label,'quiet'),'gear:'+item.key+':'+option.intent.action);b.type='button';b.onclick=()=>action('act',{intent:option.intent});RoseUI.rule(b,option.reason);controls.append(b);}detail.append(controls);return detail;
 }));
 const history=[...data.history,...(data.local_record.history||[])].sort((a,b)=>b.tick-a.tick).slice(0,8);
 $('material-history').textContent=history.map(r=>`Cycle ${r.tick}: ${r.text}`).join('\n')||'Weather, use, repairs and material recovery leave persistent records.';
}

function renderSystems(s){
 const p=s.me,check=p.last_check,command=(label,text)=>{const b=RoseUI.key(actionButton(make('button',label,'quiet'),text),'systems:'+text);b.type='button';b.onclick=()=>action('act',{text});return b;};
 $('check-summary').textContent=check?`${check.grade.toUpperCase()} / ${check.skill} · D20 ${check.die} + ${check.bonus} vs ${check.dc}\n${check.faction}: reputation ${check.reputation>=0?'+':''}${check.reputation} · context ${check.context>=0?'+':''}${check.context} · trust ${check.trust} · attitude ${check.attitude} · companions +${check.support}\n${check.reasons.join(' / ')||'Ordinary local conditions'}`:'Interaction checks appear after your first action.';
 $('check-history').replaceChildren(...p.check_log.slice(-8).reverse().map(c=>make('p',`Cycle ${c.tick} / ${c.action} / ${c.skill}: ${c.grade}. ${c.die} + ${c.bonus} vs ${c.dc}. Faction ${c.faction}. Context ${c.context}, standing ${c.reputation}, support ${c.support}.`)));
 const companions=s.companions;$('companion-count').textContent=`${companions.roster.length}/${companions.limit} ALONGSIDE`;
 function profile(a,own){
  const card=make('section','','companion-card');card.append(make('h3',a.name),make('p',`${a.role} · ${a.faction}\n${a.attitude_label.toUpperCase()} ${a.attitude}/100 · [${a.pos}]`),make('p',`${a.health} health / ${a.energy} energy · ${a.engagement.phase.toUpperCase()} / ${a.engagement.task}`));
  card.append(make('p',a.character.appearance,'subtle'),make('p',Object.entries(a.inventory).map(([k,v])=>`${k} ${v}`).join(' · '),'subtle'));
  const designation=RoseUI.key(make('details'),'npc:'+a.id+':designation');designation.append(RoseUI.key(make('summary','FULL CHARACTER DESIGNATION'),'npc:'+a.id+':designation-summary'));
  for(const text of [`ID: ${a.id}`,`${a.character.pronouns} · ${a.character.form} · ${a.character.origin}`,Object.entries(a.character.attributes).map(([k,v])=>`${k.toUpperCase()} ${v}`).join(' / '),`Training: ${Object.entries(a.character.skills).map(([k,v])=>`${k} ${v}`).join('; ')}`,`Experience: ${a.experience} · verified field credentials: ${a.credentials.join(', ')||'none'} · equipment: ${a.equipment.join(', ')||'none'}`,`Voice: ${a.character.voice}. Mannerisms: ${a.character.mannerisms}.`,`Goal: ${a.character.goal}`,`Boundary: ${a.character.boundary}`,`Items: ${a.items.map(i=>i.name+' / '+i.effect).join('; ')}`,`Faction engagement: ${Object.entries(a.reputation).map(([k,v])=>k+' '+v).join('; ')}`,`Conditions: ${[...a.injuries,...a.ailments].join(', ')||'none'}`])designation.append(make('p',text));
  designation.append(make('p','Material condition: '+(Object.values(a.gear||{}).map(g=>`${g.name} ${g.condition}/100`).join('; ')||'No registered equipment.')));
  designation.append(make('h4','LORE'),...a.character.bio.split('\n\n').map(t=>make('p',t)));
  designation.append(make('h4','CONTRACT VIABILITY'),...Object.entries(a.contract_viability).map(([k,v])=>make('p',`${k.toUpperCase()}: ${v.viable?'READY':'LIMITED'} · training ${v.training}${v.preferred?' · preferred':''} · ${v.reasons.join(', ')}`)));
  card.append(designation);
  const history=RoseUI.key(make('details'),'npc:'+a.id+':history');history.append(RoseUI.key(make('summary','ENGAGEMENT AND CONVERSATION RECORD'),'npc:'+a.id+':history-summary'),...a.engagement.events.slice(-6).reverse().map(e=>make('p',`Cycle ${e.tick}: ${e.text}`)),...a.memory.slice(-3).reverse().map(m=>make('p',`${m.speaker} / ${m.topic}: ${m.response}`)));card.append(history);
  if(own||a.available){const topics=make('div','','quick');for(const topic of companions.topics)topics.append(command(topic.toUpperCase(),`speak with ${a.id} about ${topic}`));card.append(topics);}
  if(own){
   const task=RoseUI.key(make('select'),'npc:'+a.id+':task');task.setAttribute('aria-label','Task for '+a.name);task.append(...companions.tasks.map(t=>new Option(t,t)));task.value=a.engagement.task;
   const taskButton=RoseUI.key(actionButton(make('button','PROPOSE TASK','quiet'),'task'),'npc:'+a.id+':propose');taskButton.onclick=()=>action('act',{text:`task ${a.id} ${task.value}`});card.append(task,taskButton);
   const supply=RoseUI.key(make('select'),'npc:'+a.id+':supply');supply.setAttribute('aria-label','Supply for '+a.name);supply.append(...['water','food','scrap','seed','medkit'].map(t=>new Option(t,t)));supply.value='water';
   const give=RoseUI.key(actionButton(make('button','SHARE ONE','quiet'),'share'),'npc:'+a.id+':share'),ask=RoseUI.key(actionButton(make('button','REQUEST ONE','quiet'),'request'),'npc:'+a.id+':request');give.onclick=()=>action('act',{text:`share ${a.id} ${supply.value}`});ask.onclick=()=>action('act',{text:`request ${a.id} ${supply.value}`});card.append(supply,give,ask,command('FIELD CARE / MEDKIT',`care for ${a.id}`),command('RELEASE AGREEMENT',`dismiss ${a.id}`));
  }else if(a.available)card.append(command('RECRUIT / 1 FOOD + 1 WATER',`recruit ${a.id}`));
  else card.append(make('p','Already engaged with another expedition.','subtle'));
  return card;
 }
 $('companion-roster').replaceChildren(...(companions.roster.length?companions.roster.map(a=>profile(a,true)):[make('p','No active companion agreements. Review nearby NPCs below.','subtle')]));
 $('companion-candidates').replaceChildren(...(companions.candidates.length?companions.candidates.map(a=>profile(a,false)):[make('p','No unengaged traveler is nearby. Your companions keep pace with your physical route.','subtle')]));
 const c=s.location;$('infrastructure-status').textContent=`${c.feature}\nStability ${c.stability} · shelter ${c.shelter} · public relay ${c.relay||0} · water stock ${c.water}`;
 const b=s.business;$('business-panel').hidden=!b;
 if(b){$('business-status').textContent=`${b.name}\n${b.faction} · condition ${b.condition} · demand ${b.demand} · reserve ${b.reserve} scrap`;
  $('business-controls').replaceChildren(command('REVIEW BUSINESS','business'),command('MAINTAIN / 1 SCRAP','work business'),...Object.entries(b.prices).flatMap(([k,v])=>[command(`BUY ${k.toUpperCase()} / ${v} SCRAP / STOCK ${b.stock[k]}`,`buy ${k}`),command(`SELL ${k.toUpperCase()} / 1 SCRAP`,`sell ${k}`)]));
  $('business-history').replaceChildren(...b.ledger.slice(-8).reverse().map(e=>make('p',`Cycle ${e.tick}: ${e.text}`)));
 }
 const t=s.threat;$('combat-panel').hidden=true;if(t)$('threat-status').textContent=`${t.name} / ${t.state.toUpperCase()}\nHealth ${t.health} · defense ${t.defense} · counteraction ${t.attack}\n${t.intent}. ${t.lore}`;
}
