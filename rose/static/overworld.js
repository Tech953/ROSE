'use strict';
window.RoseWorld=(()=>{
 const get=id=>document.getElementById(id),canvas=get('world-canvas'),ctx=canvas.getContext('2d'),width=1000,height=620;
 const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||false;
 const project=p=>[56+(p[0]+18)*24,66+(p[1]+12)*21],key=p=>p.join(',');
 const colors={WN_TOWER:'#3b4b3d',ENACT_HILLS:'#61553d',CITY_CLOUD_S:'#445563',AETHERGALE:'#584859'};
 let snapshot=null,hooks=null,motion=null,hover=null,lastFrame=0,cartography=false,identity=null,visitedKey=null,announcement=null;
 function reset(){snapshot=null;motion=null;hover=null;identity=null;visitedKey=null;announcement=null;}
 const current=now=>{if(!motion)return snapshot?.atlas.position||[0,0];const t=reduced||motion.duration<=0?1:Math.min(1,Math.max(0,(now-motion.start)/motion.duration));return motion.from.map((v,i)=>v+(motion.to[i]-v)*t);};
 const commit=(action,target='')=>hooks.act('act',{intent:{action,target}});
 function description(){if(!snapshot?.atlas)return;const l=snapshot.atlas.landmarks.find(l=>l.id===get('atlas-destination').value);get('atlas-location-description').textContent=l?`${l.name} [${l.pos}] · ${l.visited?'VISITED':'DRAWING REFERENCE'}\n${l.description}\nSource: ${l.source}. Confidence: ${l.confidence}.`:'';}
 function render(value){const nextIdentity=`${value.code}:${value.me.id}`;if(identity!==nextIdentity){reset();identity=nextIdentity;}snapshot=value;const a=value.atlas,nav=a?.navigation,combat=value.scene.combat?.active;
  const voided=!!value.particles?.percept.address,world=!!a&&nav.mode==='world'&&!combat&&!voided;get('atlas-panel').hidden=!world;get('rose-field').hidden=world||voided;
  get('world-enter').textContent=world?'ENTER LOCATION':'LOCAL FIELD';get('open-world').setAttribute('aria-pressed',String(world));get('world-enter').setAttribute('aria-pressed',String(!world));
  get('open-world').hidden=!a;if(!a)return;
  get('atlas-note').textContent=a.note;
  RoseUI.options(get('atlas-destination'),a.landmarks.map(l=>[`${l.visited?'● ':''}${l.name}`,l.id]));
  get('route-status').textContent=`${nav.status.toUpperCase()} · ${a.destination||'Choose a destination'}\n${nav.reason||'Click any land point to travel continuously. Click again to redirect.'}\nWORLD [${a.position.map(v=>Number(v).toFixed(2))}] · ${a.route.length} route waypoints remaining`;
  get('world-travel-status').textContent=value.paused?'CLOCK PAUSED':value.clock_held?'ENCOUNTER / CLOCK HELD':nav.status.toUpperCase();
  const nextAnnouncement=`${get('world-travel-status').textContent}. ${a.destination||'Choose a destination'}. ${nav.reason||''}`;if(announcement!==nextAnnouncement){announcement=nextAnnouncement;get('world-announcement').textContent=announcement;}
  const reason=!value.started?'The host must begin the expedition.':value.paused?'The host has paused this world.':value.me.remote?'Return from remote observation first.':voided?'Return through the recorded void trace first.':combat?'Resolve the local encounter first.':'';for(const id of ['open-world','world-enter','world-stop','world-resume','route-plan','world-point-go'])RoseUI.rule(get(id),reason);
  get('world-stop').hidden=nav.status!=='traveling';get('world-resume').hidden=nav.status==='traveling'||!nav.target||(!a.route.length&&key(a.position)===key(nav.target));
  const visited=a.landmarks.filter(l=>l.visited),nextVisited=JSON.stringify(visited.map(l=>[l.id,l.name]));if(visitedKey!==nextVisited){visitedKey=nextVisited;get('world-visited').replaceChildren(...visited.map(l=>{const b=RoseUI.key(document.createElement('button'),'visited:'+l.id);b.type='button';b.textContent=l.name;b.onclick=()=>commit('goto',l.id);return b;}));}for(const b of get('world-visited').children)RoseUI.rule(b,reason);
  get('world-visited-count').textContent=`${a.landmarks.filter(l=>l.visited).length} VISITED`;
  const now=performance.now();if(!motion||motion.serial!==nav.serial){const from=motion?current(now):a.position;motion={serial:nav.serial,from:from.slice(),to:a.position.slice(),start:now,duration:nav.status==='traveling'?850:0};}
  description();draw(now);
 }
 function draw(now){const a=snapshot?.atlas;if(!a)return;ctx.clearRect(0,0,width,height);ctx.fillStyle='#111a16';ctx.fillRect(0,0,width,height);
  const seen=new Set(a.navigation.seen.map(key)),visited=new Set(a.navigation.visited.map(key));
  for(const t of a.terrain){const[x,y]=project(t.pos);ctx.fillStyle=t.passable?colors[t.region]:'#193039';ctx.fillRect(x-12,y-11,24,21);
   if(t.terrain==='woodland'){ctx.strokeStyle='#78987766';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x-8,y+5);ctx.quadraticCurveTo(x-9,y-4,x,y-8);ctx.quadraticCurveTo(x+9,y-4,x+7,y+6);ctx.moveTo(x,y-7);ctx.lineTo(x-1,y+8);ctx.stroke();}
   else if(t.terrain==='mountain path'){ctx.strokeStyle='#a6b6ac88';ctx.beginPath();ctx.moveTo(x-11,y+7);ctx.lineTo(x,y-9);ctx.lineTo(x+11,y+7);ctx.moveTo(x,y-9);ctx.lineTo(x+2,y+6);ctx.stroke();}
   else if(t.terrain==='interpreted bridge'){ctx.strokeStyle='#bbbd9977';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x-9,y+3);ctx.lineTo(x+9,y-3);ctx.stroke();}
   if(!cartography&&!visited.has(key(t.pos))){ctx.fillStyle=seen.has(key(t.pos))?'#07110b66':'#07110be8';ctx.fillRect(x-12,y-11,24,21);}
  }
  ctx.strokeStyle='#9aab8255';ctx.lineWidth=1;ctx.strokeRect(43,54,890,527);
  ctx.textAlign='left';ctx.fillStyle='#adc1a1';ctx.font='12px "Courier New", monospace';ctx.fillText('ROSE / WORLD SURVEY',32,30);ctx.font='10px "Courier New", monospace';ctx.fillText(`CYCLE ${snapshot.tick} / ${snapshot.phase.toUpperCase()} / ${snapshot.weather.toUpperCase()}`,550,30);
  const points=[a.position,...a.route,...(a.navigation.target?[a.navigation.target]:[])];if(points.length>1){ctx.strokeStyle='#d5c294aa';ctx.lineWidth=2;ctx.setLineDash([4,5]);ctx.beginPath();points.forEach((p,i)=>{const[x,y]=project(p);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();ctx.setLineDash([]);}
  for(const l of a.landmarks){if(!cartography&&!l.revealed&&!l.visited)continue;const[x,y]=project(l.pos);ctx.beginPath();ctx.arc(x,y,l.visited?8:5,0,Math.PI*2);ctx.fillStyle=l.visited?'#8bbd8880':'#81a97a55';ctx.fill();ctx.strokeStyle='#b1d09e';ctx.lineWidth=1.5;ctx.stroke();if(l.visited){ctx.fillStyle='#dbe4c8';ctx.font='9px "Courier New", monospace';ctx.fillText(l.name,x+12,y-7);}}
  if(cartography){ctx.fillStyle='#c4c8a6';ctx.font='11px "Courier New", monospace';for(const[label,p]of [['WN_TOWER',[-17,-7]],['ENACT_HILLS',[-2,-9]],['CITY_CLOUD_S',[5,-4]],['AETHERGALE',[-2,11]]]){const[x,y]=project(p);ctx.fillText(label,x,y);}ctx.font='9px "Courier New", monospace';ctx.fillText('DRAWING CARTOGRAPHY / UNVISITED LIFE REMAINS UNKNOWN',32,height-34);}
  if(snapshot.me.contract){const[x,y]=project(snapshot.me.contract.target);ctx.strokeStyle='#dbaa83';ctx.lineWidth=2;ctx.strokeRect(x-10,y-10,20,20);}
  const[x,y]=project(current(now)),arrived=a.navigation.status==='arrived';ctx.strokeStyle='#add6a4';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,12,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#e0efd4';ctx.beginPath();if(arrived){ctx.moveTo(x-7,y-8);ctx.lineTo(x+7,y-8);ctx.lineTo(x,y+5);ctx.closePath();}else ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();
  if(a.navigation.status==='encounter'){ctx.strokeStyle='#eeb09e';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x+18,y-14);ctx.lineTo(x+10,y);ctx.lineTo(x+20,y);ctx.lineTo(x+12,y+14);ctx.stroke();}
  if(hover){const[hx,hy]=project(hover);ctx.strokeStyle='#d3d9af77';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(hx-8,hy);ctx.lineTo(hx+8,hy);ctx.moveTo(hx,hy-8);ctx.lineTo(hx,hy+8);ctx.stroke();}
  ctx.fillStyle='#b7c3a8';ctx.font='10px "Courier New", monospace';ctx.fillText(arrived?'DESTINATION REACHED / CLICK YOUR MARKER OR ENTER LOCATION':'CLICK ANY LAND POINT / CLICK AGAIN TO REDIRECT / STOP TO HALT',32,height-17);
 }
 function location(event){const box=canvas.getBoundingClientRect(),x=(event.clientX-box.left)*width/box.width,y=(event.clientY-box.top)*height/box.height;return [Number(((x-56)/24-18).toFixed(3)),Number(((y-66)/21-12).toFixed(3))];}
 async function click(event){if(!snapshot?.atlas)return;const p=location(event),nav=snapshot.atlas.navigation;
  if(nav.status==='arrived'&&Math.hypot((p[0]-nav.point[0])*24,(p[1]-nav.point[1])*21)<14)return commit('enter_location');
  if(p[0]<-18.49||p[0]>18.49||p[1]<-12.49||p[1]>12.49)return;
  const lm=snapshot.atlas.landmarks.find(l=>(cartography||l.revealed||l.visited)&&Math.hypot((p[0]-l.pos[0])*24,(p[1]-l.pos[1])*21)<9);
  if(lm){get('atlas-destination').value=lm.id;description();return commit('goto',lm.id);}
  return commit('goto',key(p));
 }
 function configure(callbacks){hooks=callbacks;get('open-world').onclick=()=>{if(snapshot?.atlas.navigation.mode!=='world')return commit('world_map');};get('world-enter').onclick=()=>{if(snapshot?.atlas.navigation.mode!=='local')return commit('enter_location');};get('world-stop').onclick=()=>commit('stop_travel');get('world-resume').onclick=()=>commit('resume_travel');
  RoseSurvey.configure({selectApproach:id=>{get('atlas-destination').value=id;description();get('route-plan').focus();}});
  get('route-plan').onclick=()=>commit('goto',get('atlas-destination').value);get('atlas-destination').onchange=description;
  get('world-point-go').onclick=()=>{if(get('world-x').reportValidity()&&get('world-y').reportValidity())return commit('goto',`${get('world-x').value},${get('world-y').value}`);};
  get('world-cartography').onclick=()=>{cartography=!cartography;get('world-cartography').textContent=cartography?'RETURN TO FIELD DISCOVERY':'SHOW DRAWING CARTOGRAPHY';draw(performance.now());};
  canvas.onclick=click;canvas.onmousemove=e=>{hover=location(e);get('world-pointer').textContent=`WORLD [${hover}]`;if(reduced)draw(performance.now());};canvas.onmouseleave=()=>{hover=null;if(reduced)draw(performance.now());};
  canvas.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();if(snapshot?.atlas.navigation.status==='arrived')commit('enter_location');else get('world-x').focus();}};
  function frame(now){if(!reduced&&now-lastFrame>33){lastFrame=now;if(snapshot&&!document.hidden&&!get('atlas-panel').hidden)draw(now);}requestAnimationFrame(frame);}if(!reduced)requestAnimationFrame(frame);
 }
 return {configure,render,draw,click,project,reset};
})();
