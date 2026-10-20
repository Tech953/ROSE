/* Real-host material work plus native-frame draw/pick and condition comparisons. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
function find(node,predicate){if(predicate(node))return node;for(const child of node.children||[]){const hit=find(child,predicate);if(hit)return hit;}return null;}
module.exports=async function({base,tmp,setupInterface,canvasModule,root}){
 const rig=setupInterface(base,tmp),{context,ids}=rig,read=()=>vm.runInContext('state',context);
 for(let n=0;n<100&&!context.RoseCreator.ready;n++)await new Promise(r=>setTimeout(r,10));
 ids.name.value='Material keeper';ids.seed.value='material-ui';rig.document.getElementById('rule-generation-hostility').value=0;
 await ids['join-form'].requestSubmit();await ids.start.click();
 if(canvasModule)await context.RosePrefabs.ready;
 const chosen=label=>find(ids['field-selection-actions'],b=>b.tagName==='BUTTON'&&b.textContent===label);
 const gearButton=(key,op)=>find(ids['material-items'],b=>b.dataset.uiKey==='gear:'+key+':'+op);
 assert.ok(gearButton('field_staff','gear_inspect'),'Registered staff has a real inspection control');
 const initialGear=JSON.stringify(read().me.gear),tick=read().tick;
 await gearButton('field_staff','gear_inspect').click();assert.equal(read().tick,tick);assert.equal(JSON.stringify(read().me.gear),initialGear);
 assert.equal(gearButton('field_staff','gear_repair').disabled,true,'Maintained tools cannot consume repair materials');
 const node=read().scene.infrastructure.nodes.find(n=>n.kind==='water'),selector={type:'structure',id:node.id};
 context.RoseField.select(selector);await ids['walk-path'].click();assert.equal(read().scene.infrastructure.nodes.find(n=>n.id===node.id).adjacent,true,ids.error.textContent);
 let strikes=0;
 for(let n=0;n<8&&read().scene.infrastructure.nodes.find(n=>n.id===node.id).condition>0;n++){
  const b=chosen('STRIKE PUBLIC WORKS');assert.ok(b&&!b.disabled,b?.dataset.blockReason);await b.click();strikes++;
 }
 const ruined=read().scene.infrastructure.nodes.find(n=>n.id===node.id);assert.equal(ruined.condition,0,ids.error.textContent);
 assert.equal(ruined.status,'ruined');assert.equal(ruined.enabled,false);assert.equal(read().scene.tiles[ruined.pos.join(',')].opaque,false);
 assert.equal(chosen('REPAIR / 1 SCRAP'),null,'Ordinary repairs are absent for a collapsed structure');
 const staff=read().me.gear.field_staff;assert.ok(staff.condition<=100-strikes*2,'Actual demolition wears the staff');
 assert.equal(gearButton('field_staff','gear_repair').disabled,false);
 const scrap=read().me.inventory.scrap,condition=staff.condition;await gearButton('field_staff','gear_repair').click();
 assert.equal(read().me.inventory.scrap,scrap-1);assert.ok(read().me.gear.field_staff.condition>condition);
 const pending=read().scene.infrastructure.nodes.find(n=>n.id===node.id).material_state.salvage_remaining,pack=read().me.inventory.scrap;
 const clear=chosen('CLEAR RUBBLE / RECOVER '+pending+' SCRAP');assert.ok(clear&&!clear.disabled,clear?.dataset.blockReason);await clear.click();
 assert.equal(read().me.inventory.scrap,pack+pending);assert.equal(read().scene.infrastructure.nodes.some(n=>n.id===node.id),false);
 assert.equal(read().scene.tiles[node.pos.join(',')].passable,true);assert.ok(ids['material-history'].textContent.includes('Cleared'));
 const rock=Object.values(read().scene.tiles).find(t=>t.prefab==='rock');context.RoseField.select({type:'hex',pos:rock.pos});assert.ok(chosen('STRIKE MATERIAL'),'Individual rock selection exposes its material controls');
 const session=JSON.parse(context.sessionStorage.getItem('rose-session'));
 const rejected=await fetch(base+'/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...session,op:'act',revision:read().revision,intent:{action:'material_clear',target:'structure:'+node.id}})}).then(r=>r.json());
 assert.match(rejected.error,/existing structure/);await vm.runInContext('poll()',context);assert.equal(read().me.inventory.scrap,pack+pending,'Repeated recovery cannot mint another output');
 const records=[],host=JSON.stringify(read()),prefabs=context.RosePrefabs,oldMode=context.RoseLighting.mode;
 if(canvasModule){
  context.RoseDisplay.configure(false,'sharp');context.RoseLighting.configure('baked');
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'static/art-manifest-rendered.json'),'utf8'));
  for(const region of manifest.visual_catalog.regions)for(const kind of ['water','power','relay','shelter','rock']){
   const subject=kind==='rock'?{...rock,visual:{model:'rock_'+region}}:{...node,kind,condition:90,enabled:true,connected:true,status:'working',visual:{model:kind+'_'+region}};
   const key=prefabs.assetFor(subject,kind),poses=['idle','worn','fractured','ruined'],frames=poses.map(p=>prefabs.frameInfo(key,p,0));assert.ok(frames.every(Boolean));
   const images=frames.map(f=>{const c=canvasModule.createCanvas(f.w,f.h);c.getContext('2d').drawImage(f.image.bitmap||f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);return c.toBuffer('image/png').toString('base64');});
   assert.equal(new Set(images).size,4,region+'/'+kind+' has distinct intact, worn, fractured and debris frames');
   const intact=prefabs.bounds(key,'idle',0),debris=prefabs.bounds(key,'ruined',0);assert.ok(debris[3]<intact[3]*.8,'Collapsed object has a low physical silhouette');
   const f=frames[3],c=canvasModule.createCanvas(f.w,f.h);c.getContext('2d').drawImage(f.image.bitmap||f.image,0,0);const rgba=c.getContext('2d').getImageData(0,0,f.w,f.h).data;let solid=0,shadow=0;
   for(let i=0;i<rgba.length;i+=4){const x=i/4%f.w,y=Math.floor(i/4/f.w),point=[(x+.5-f.anchor[0])*f.scale,(y+.5-f.anchor[1])*f.scale];if(rgba[i+3]>=248){solid++;assert.equal(prefabs.hit(key,point,'ruined',0),true);}else if(rgba[i+3]>0&&rgba[i+3]<248){shadow++;assert.equal(prefabs.hit(key,point,'ruined',0),false,'Graded debris shadow cannot own a cursor hit');}}
   assert.ok(solid>50&&shadow>20);assert.equal(prefabs.hit(key,[-200,-200],'ruined',0),false);
   records.push({region,kind,intact_height_px:intact[3],debris_height_px:debris[3],solid_pixels:solid,shadow_pixels:shadow});
  }
  assert.ok(context.RoseMaterialVisuals.available&&context.RoseMaterialVisuals.cached<=32,'Actual-surface damage composition is active and bounded');
  for(const style of ['rendered-legacy','raster','vector']){
   prefabs.setStyle(style);await prefabs.ready;const subject={...node,condition:0,material_state:{destroyed:true}};assert.equal(prefabs.structurePose(subject),'ruined');
   const c=rig.document.createElement('canvas');c.width=160;c.height=160;c.getContext('2d').translate(80,100);prefabs.structure(c.getContext('2d'),subject,0,{accent:'#a4bd88'});
   assert.ok(c.bitmap.toBuffer('image/png').length>400,'Collapsed state draws in '+style);assert.equal(prefabs.hit('water',[0,-100],'ruined',0),false);
  }
  prefabs.setStyle('rendered');
  const preview=canvasModule.createCanvas(1500,1020),p=preview.getContext('2d');p.fillStyle='#101719';p.fillRect(0,0,1500,1020);p.fillStyle='#d9d1b3';p.font='21px "Courier New"';p.fillText('ROSE.ENGINE 0.14.0 / MATERIAL CONDITION',26,30);
  const names=['SOUND / 90','WORN / 50','FRACTURED / 20','COLLAPSED / 0'],values=[90,50,20,0];
  for(let i=0;i<4;i++){
   const s=JSON.parse(host);s.scene.units=s.scene.units.filter(u=>u.mine);s.scene.infrastructure.nodes=s.scene.infrastructure.nodes.filter(n=>n.kind==='power');s.scene.infrastructure.links=[];
   const n=s.scene.infrastructure.nodes[0];n.condition=values[i];n.enabled=values[i]>=30;n.connected=values[i]>=30;n.status=values[i]===0?'ruined':'working';n.material_state.destroyed=values[i]===0;
   const tile=s.scene.tiles[n.pos.join(',')];tile.opaque=values[i]>0;tile.passable=false;
   context.RoseField.reset();context.RoseField.render(s);context.RoseField.select(null);context.RoseField.draw(0);
   const x=i%2*750,y=50+Math.floor(i/2)*475;p.fillStyle='#d9d1b3';p.font='17px "Courier New"';p.fillText(names[i],x+22,y+20);p.drawImage(ids['field-canvas'].bitmap,x,y+30,750,435);
  }
  fs.writeFileSync(path.join(root,'docs/Rose-material-aging-and-destruction.png'),preview.toBuffer('image/png'));
 }
 context.RosePrefabs.setStyle('rendered');context.RoseLighting.configure(oldMode);context.RoseDisplay.configure(true,'soft');context.RoseField.render(read());
 assert.equal(JSON.stringify(read()),host,'Visual condition fixtures never mutate the live host state');
 fs.writeFileSync(path.join(root,'docs/material-aging-audit-v014.json'),JSON.stringify({schema:1,engine_version:'0.14.0',live_host:{strikes,collapse:true,paid_gear_repair:true,finite_clear:true,rock_controls:true,duplicate_rejected:true},native_canvas:!!canvasModule,regions:records,cache_limit:32,prototype:'Deterministic fragments and cracks derived from prepared sprite pixels; not new Blender fracture meshes.'},null,2)+'\n');
 console.log('PASS: materials — live HTTP demolition, staff wear, paid repairs, finite clearing, persistent receipts and rock menus; four regional condition states, lower debris silhouettes, exact solid/shadow picking, legacy/vector fallbacks and bounded caches.');
};
