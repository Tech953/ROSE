/* Local controls against the real HTTP host and actual decoded sprite pixels. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const clone=value=>JSON.parse(JSON.stringify(value));
const within=(node,predicate)=>{if(predicate(node))return node;for(const child of node.children||[]){const found=within(child,predicate);if(found)return found;}return null;};
const pause=()=>new Promise(resolve=>setTimeout(resolve,25));
module.exports=async({context,ids,read,canvasModule,phase,root})=>{
 const field=context.RoseField,canvas=ids['field-canvas'],originalFetch=context.fetch;let acts=0;
 context.fetch=(url,options)=>{if(JSON.parse(options?.body||'{}').op==='act')acts++;return originalFetch(url,options);};
 const pointFor=(type,id)=>{const f=read().scene,object=type==='unit'?f.units.find(u=>u.id===id):f.infrastructure.nodes.find(n=>n.id===id),tile=f.tiles[object.pos.join(',')],base=field.project(object.pos,tile?.elevation||0),scale=6/f.radius;
  for(const dy of [-24,-40,-12,-55,0,-65])for(const dx of [0,-8,8,-16,16,-24,24]){const x=base[0]+dx*scale,y=base[1]+dy*scale,hit=field.hitAt(x,y,0);if(hit?.type===type&&hit.id===id)return{clientX:x,clientY:y,button:0,preventDefault(){}};}throw Error('No visible pick point for '+id);
 };
 try{
  if(phase==='exploration'){
   assert.equal(field.mode,'move');canvas.oncontextmenu({preventDefault(){}});assert.equal(field.mode,'interact');assert.equal(ids['cursor-interact'].attrs['aria-pressed'],'true');assert.equal(ids['cursor-target'].disabled,true);
   const water=read().scene.infrastructure.nodes.find(n=>n.kind==='water'),point=pointFor('structure',water.id),pack=clone(read().me.inventory),before=acts;
   canvas.onpointermove(point);assert.equal(acts,before,'Hover never rolls or commits');
   canvas.onpointerdown(point);await pause();assert.equal(field.menuOpen,true);assert.equal(acts,before,'Hold opens a menu without the default action');assert.equal(ids['field-menu'].hidden,false);assert.ok(ids['field-menu-actions'].children.length);
   canvas.onpointerup(point);await canvas.onclick(point);assert.equal(acts,before,'The click following a long press is suppressed');
   ids['field-menu-item'].click();const repair=within(ids['field-menu-actions'],n=>n.tagName==='BUTTON'&&n.textContent==='REPAIR / 1 SCRAP');assert.ok(repair);assert.equal(repair.disabled,true);assert.match(repair.title,/adjacent|scrap/);await repair.click();assert.equal(acts,before);assert.deepEqual(clone(read().me.inventory),pack);
   ids['field-menu-look'].click();await within(ids['field-menu-actions'],n=>n.tagName==='BUTTON'&&n.textContent==='LOOK').click();assert.equal(acts,before+1);assert.equal(field.menuOpen,false);assert.equal(read().me.last_check.action,'field_look');assert.deepEqual(clone(read().me.inventory),pack);
   ids['field-object'].value='unit:'+read().me.id;ids['field-object'].onchange();canvas.onkeydown({key:'f',preventDefault(){}});assert.equal(field.menuOpen,true);ids['field-menu'].onkeydown({key:'Escape',preventDefault(){}});assert.equal(field.menuOpen,false);
   ids['field-object'].value='structure:'+water.id;ids['field-object'].onchange();await canvas.onclick(point);assert.equal(read().me.last_action.action,'field_look','Interact single click performs the registered default');
   ids['toggle-reveal'].click();assert.equal(context.localStorage.getItem('rose-reveal'),'on');assert.equal(ids['toggle-reveal'].attrs['aria-pressed'],'true');ids['toggle-reveal'].click();
   await ids['field-audio'].click();assert.match(ids['field-notice'].textContent,/Audio is unavailable/);assert.equal(context.RoseAudio.enabled,false);
   if(canvasModule){
    const actual=clone(read()),fixture=clone(actual),body=fixture.scene.units.find(u=>u.mine),shelter=fixture.scene.infrastructure.nodes.find(n=>n.kind==='shelter');fixture.code='PICKTEST';body.pos=[0,0];body.pose='idle';body.pose_serial=0;body.trail=[];fixture.scene.units=[body];shelter.pos=[-1,1];fixture.scene.infrastructure.nodes=[shelter];fixture.scene.infrastructure.links=[];for(const t of Object.values(fixture.scene.tiles))t.prefab='ground';
    field.render(fixture);assert.ok(field.occlusion(0).includes('structure:'+shelter.id),'Foreground shelter actually covers the player');
    const unitPoint=field.project(body.pos),scale=6/fixture.scene.radius;let covered=null;
    for(let dy=-48;dy<-9&&!covered;dy+=2)for(let dx=-16;dx<=16;dx+=2){const x=unitPoint[0]+dx*scale,y=unitPoint[1]+dy*scale;if(field.hitAt(x,y,0)?.id!==body.id)continue;ids['toggle-occlusion'].click();const hidden=field.hitAt(x,y,0);ids['toggle-occlusion'].click();if(hidden?.type==='structure'){covered=[x,y];break;}}
    assert.ok(covered,'Click-through reaches an opaque character pixel behind the faded prefab');
    field.draw(0);const faded=canvas.getContext('2d').getImageData(covered[0]|0,covered[1]|0,1,1).data;ids['toggle-occlusion'].click();assert.equal(field.occlusion(0).length,0);field.draw(0);const solid=canvas.getContext('2d').getImageData(covered[0]|0,covered[1]|0,1,1).data;assert.notDeepEqual(Array.from(faded),Array.from(solid),'Fading changes the rendered overlap pixel');ids['toggle-occlusion'].click();
    assert.equal(context.RosePrefabs.hit('player',[1000,-1000]),false);assert.equal(context.RosePrefabs.hit('player',[-40,-65]),false,'Transparent sprite padding never grabs a click');
    field.render(actual);field.select({type:'structure',id:water.id});ids['field-context'].click();ids['field-menu-item'].click();ids['toggle-reveal'].click();field.draw(0);fs.writeFileSync(path.join(root,'docs','Rose-interaction-preview.png'),canvas.bitmap.toBuffer('image/png'));ids['toggle-reveal'].click();ids['field-menu-close'].click();
    const switched=clone(actual);switched.code='NEXTROOM';ids['field-context'].click();field.render(switched);assert.equal(field.menuOpen,false,'A new room closes the old target menu');vm.runInContext('render()',context);
   }
   const beforeMove=clone(read().scene.units.find(u=>u.mine).pos),destination=read().scene.reachable.find(p=>field.path(beforeMove,p)?.length===2);assert.ok(destination);ids['cursor-move'].click();const position=field.project(destination,read().scene.tiles[destination.join(',')].elevation);await canvas.onclick({clientX:position[0],clientY:position[1],preventDefault(){}});assert.notDeepEqual(clone(read().scene.units.find(u=>u.mine).pos),beforeMove,'Move click follows a real HTTP hex path');
   console.log('PASS: local interaction — cursor cycle, no-roll hover, hold suppression, keyboard/touch fallback, explicit item costs, blocked action conservation, Look/default actions, discovery, room identity and one-click movement.');
   if(canvasModule)console.log('PASS: sprite pixels — transparent padding, real foreground occlusion, fade rendering and picking through to the covered character.');
  }else{
   ids['cursor-target'].click();assert.equal(field.mode,'target');const npc=read().scene.units.find(u=>u.kind==='companion'),before=acts,encounter=clone(read().scene.combat);
   if(npc){await canvas.onclick(pointFor('unit',npc.id));assert.equal(acts,before,'Target mode cannot attack an ordinary NPC');assert.deepEqual(clone(read().scene.combat),encounter);}
   ids['target-action'].value='shoot';ids['target-action'].onchange();const reason=read().scene.action_availability.shoot.reason;assert.ok(reason,'Fixture has a blocked crystallin shot');await canvas.onclick(pointFor('unit','threat'));assert.equal(acts,before,'Blocked target click does not consume AP or ammo');assert.match(ids['field-notice'].textContent,/visible|blocks|Equip|scrap|turn|AP/);assert.deepEqual(clone(read().scene.combat),encounter);
   ids['field-context'].click();await within(ids['field-menu-actions'],n=>n.tagName==='BUTTON'&&n.textContent==='LOOK').click();assert.equal(read().me.last_check.action,'field_look');assert.deepEqual(clone(read().scene.combat),encounter,'Look in combat does not advance the turn');ids['cursor-move'].click();
   console.log('PASS: target mode — ordinary NPCs rejected, equipment/range/AP prerequisites retained, and combat Look has no AP or turn cost.');
  }
 }finally{context.fetch=originalFetch;}
};
