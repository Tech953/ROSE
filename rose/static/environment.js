'use strict';
window.RoseEnvironment=(()=>{
 const get=id=>document.getElementById(id),live=p=>['foundation','frame','finishing','ruined'].includes(p.stage);
 let hooks=null,snapshot=null;
 const projects=()=>snapshot?.scene.lifecycle?.projects.filter(live)||[];
 function configure(callbacks){hooks=callbacks;get('construction-kind').onchange=updatePlan;get('construction-site').onchange=updatePlan;
  get('construction-plan').onclick=()=>hooks.act('act',{intent:{action:'construction_plan',target:get('construction-kind').value+'|'+get('construction-site').value}});
 }
 function updatePlan(){const life=snapshot?.scene.lifecycle;if(!life)return;const kind=get('construction-kind').value,bp=life.blueprints[kind],site=life.candidates.find(n=>n.pos.join(',')===get('construction-site').value);if(!bp)return;
  get('construction-cost').textContent=`${bp.scrap} SCRAP RESERVED · ${bp.work} SUCCESSFUL WORK STEPS\n${bp.skill.toUpperCase()} vs ${bp.dc} · local conditions, standing and trained companions apply.`;
  RoseUI.rule(get('construction-plan'),life.work_reason||site?.reason||(!site?'Choose an adjacent construction site.':snapshot.me.inventory.scrap<bp.scrap?'Gather enough scrap to reserve this project.':''));
  RoseUI.locks(hooks?.busy?.()||false);
 }
 function render(value){snapshot=value;const life=value.scene.lifecycle;if(!life)return;
  get('environment-summary').textContent=(value.particles?.percept.address?`RETAINED BASELINE ANCHOR [${value.particles.percept.anchor}]\n`:'')+`MOISTURE ${life.moisture} · GROWTH ${life.growth} · SOIL ${life.soil_health}\nDETRITUS ${life.litter} · EROSION ${life.erosion} · ${life.season.toUpperCase()}`;
  get('environment-plants').textContent=life.plantings.map(n=>`${n.species} / ${n.stage.toUpperCase()} · age ${n.age} · stress ${n.stress} · hex [${n.pos||[0,0]}]`).join('\n')||'No planted patches yet. Planting needs suitable moisture and soil to establish.';
  RoseUI.options(get('construction-kind'),Object.keys(life.blueprints).map(k=>[k.toUpperCase(),k]));
  if(!life.blueprints[get('construction-kind').value])get('construction-kind').value=Object.keys(life.blueprints)[0];
  RoseUI.options(get('construction-site'),life.candidates.map(n=>[`[${n.pos}] · ${n.reason||'OPEN SITE'}`,n.pos.join(',')]));if(!life.candidates.some(n=>n.pos.join(',')===get('construction-site').value))get('construction-site').value=(life.candidates.find(n=>!n.reason)||life.candidates[0])?.pos.join(',')||'';updatePlan();
  get('construction-projects').replaceChildren(...life.projects.filter(live).map(n=>{const card=document.createElement('div');card.className='network-node';const text=document.createElement('span');text.textContent=`${n.id} / ${n.kind.toUpperCase()} / ${n.stage.toUpperCase()}\nWork ${n.work_done}/${n.work_required} · ${n.escrow-n.spent} unspent scrap · hex [${n.pos}]`;const b=RoseUI.key(document.createElement('button'),'project:'+n.id);b.textContent='SELECT / APPROACH';b.onclick=()=>hooks.select({type:'project',id:n.id});card.append(text,b);return card;}));
  get('environment-ledger').textContent=life.ledger.slice(-8).map(n=>`Cycle ${n.tick}: ${n.text}`).join('\n')||'The field record will register establishment, care, decay and building work.';
 }
 function rawBounds(prop){return prop.frame?RosePrefabs.boundsFrame(prop.frame):RosePrefabs.bounds(prop.asset,prop.pose,prop.time,prop.facing);}
 function cut(prop){const b=rawBounds(prop);return prop.node.stage==='ruined'?b[1]:b[1]+b[3]*(1-Math.max(.22,Math.min(.94,.22+.72*prop.node.work_done/prop.node.work_required)));}
 function bounds(prop){const b=rawBounds(prop);if(prop.type!=='project')return b;const top=cut(prop);return[b[0],top,b[2],Math.max(0,b[1]+b[3]-top)];}
 function hit(prop,point){if(prop.type==='project'&&point[1]<cut(prop))return false;return prop.frame?RosePrefabs.hitFrame(prop.frame,point):RosePrefabs.hit(prop.asset,point,prop.pose,prop.time,prop.facing);}
 function drawProject(c,prop,palette){const[x,y,w,h]=bounds(prop);c.save();c.beginPath();c.rect(x,y,w,h);c.clip();RosePrefabs.structure(c,{...prop.node,condition:Math.min(40,prop.node.condition??40),enabled:false},prop.time,palette,prop.frame);c.restore();}
 function ground(c,field,project,size){const life=field.lifecycle;if(!life)return;c.save();c.globalAlpha=.04+Math.abs(life.moisture-50)/900;c.fillStyle=life.moisture>=50?'#173b33':'#b48c5e';c.fillRect(0,0,1000,620);c.globalAlpha=1;
  const tiles=Object.values(field.tiles).filter(t=>t.passable);for(let i=0;i<Math.min(tiles.length,Math.floor(life.litter/3));i++){const t=tiles[(i*17)%tiles.length],[x,y]=project(t.pos);c.fillStyle='#ad916343';c.fillRect(x+(((i*31)%101)/100-.5)*size*1.25,y+(((i*47)%101)/100-.5)*size*.65,3,1);}
  if(life.erosion>=20){c.strokeStyle='#bd956c44';c.lineWidth=1;for(let i=0;i<Math.min(12,Math.floor(life.erosion/6));i++){const t=tiles[(i*13)%tiles.length];if(!t)break;const[x,y]=project(t.pos);c.beginPath();c.moveTo(x-size*.38,y);c.lineTo(x,y+size*.09);c.lineTo(x+size*.34,y-size*.08);c.stroke();}}
  c.restore();
 }
 function plants(c,field,region,project,size,palette){for(const plant of field.lifecycle?.plantings||[]){const pos=plant.pos||[0,0],tile=field.tiles[pos.join(',')];if(!tile)continue;const[x,y]=project(pos,tile.elevation);const scale=(plant.stage==='germinating'?.10:plant.stage==='seedling'?.20:plant.stage==='decayed'?.13:.30)*size/34;c.save();c.translate(x+7,y+3);c.scale(scale,scale);if(plant.stage==='decayed')c.globalAlpha=.48;RosePrefabs.structure(c,{kind:'garden',condition:['wilted','decayed'].includes(plant.stage)?25:90,enabled:true,connected:true,visual:{model:'garden_'+region,tone:0}},0,palette);c.restore();}}
 return{configure,render,projects,bounds,hit,drawProject,ground,plants};
})();
