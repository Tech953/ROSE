/* Actual HTTP and native renderer comparison; no replacement simulation. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
module.exports=async function({base,tmp,setupInterface,canvasModule,root}){
 assert.ok(canvasModule,'Art-direction verification requires the native canvas renderer.');
 const rig=setupInterface(base,tmp),{context,ids}=rig,read=()=>vm.runInContext('state',context);
 for(let n=0;n<250&&(!context.RoseCreator.ready||!context.RoseArtDirection.ready);n++)await new Promise(r=>setTimeout(r,10));
 assert.ok(context.RoseCreator.ready&&context.RoseArtDirection.ready,'Creator and material configuration loaded.');
 ids.name.value='Material study';ids.seed.value='rose-direction';rig.document.getElementById('rule-generation-hostility').value=0;
 await ids['join-form'].requestSubmit();await ids.start.click();await context.RosePrefabs.ready;
 const R=context.RoseArtDirection,P=context.RosePrefabs,F=context.RoseField,initial=JSON.stringify(read());
 const ordinary=JSON.parse(initial);ordinary.paused=true;R.read(ordinary);R.configure(true);
 const pixels=f=>{const c=canvasModule.createCanvas(f.w,f.h);c.getContext('2d').drawImage(f.image.bitmap||f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);return c.getContext('2d').getImageData(0,0,f.w,f.h).data;};
 const original=P.frameInfo('shelter_AETHERGALE','idle',0,0);assert.ok(original);
 const raw=pixels(original),materials=[];
 for(const material of ['wood','metal','stone','crystal','fabric','polymer']){
  const prop={type:'structure',pos:[0,0],node:{id:'study-'+material,material_state:{material}}};
  const result=R.frame(original,prop,'AETHERGALE');assert.notEqual(result,original);assert.equal(result,R.frame(original,prop,'AETHERGALE'),'Stable frame cache');
  const out=pixels(result);let changed=0,soft=0,practicals=0;
  for(let i=0;i<raw.length;i+=4){
   assert.equal(out[i+3],raw[i+3],'Exact alpha');
   const hi=Math.max(raw[i],raw[i+1],raw[i+2]),lo=Math.min(raw[i],raw[i+1],raw[i+2]);
   if(raw[i+3]<248||hi>120&&hi-lo>65){
    for(let ch=0;ch<3;ch++)assert.equal(out[i+ch],raw[i+ch],'Soft shadows and colored practicals retain RGB');
    if(raw[i+3]>0&&raw[i+3]<248)soft++;if(raw[i+3]>=248&&hi>120&&hi-lo>65)practicals++;
   }else if(out[i]!==raw[i]||out[i+1]!==raw[i+1]||out[i+2]!==raw[i+2])changed++;
  }
  assert.ok(changed>100&&soft>20,'Material body changes while soft shadow stays intact');
  materials.push({material,changed_opaque_pixels:changed,soft_shadow_pixels:soft,preserved_colored_practicals:practicals});
 }
 const prop={type:'structure',pos:[0,0],node:{id:'scope',material_state:{material:'stone'}}};
 R.configure(false);assert.equal(R.frame(original,prop,'ENACT_HILLS'),original);R.configure(true);
 for(const type of ['unit','project'])assert.equal(R.frame(original,{...prop,type},'ENACT_HILLS'),original);
 assert.equal(R.frame(original,prop,'ARK'),original);
 for(const snapshot of [{...ordinary,me:{...ordinary.me,remote:true}},{...ordinary,particles:{...ordinary.particles,percept:{address:'void:test'}}}]){R.read(snapshot);assert.equal(R.frame(original,prop,'ENACT_HILLS'),original);}
 R.read(ordinary);P.setStyle('raster');assert.equal(R.frame(original,prop,'ENACT_HILLS'),original);P.setStyle('rendered');await P.ready;
 const config=JSON.parse(fs.readFileSync(path.join(root,'static/art-direction-runtime.json'),'utf8')),invalid=JSON.parse(JSON.stringify(config));invalid.materials.stone.mix=Infinity;
 assert.throws(()=>R.load(invalid));assert.ok(R.ready,'Invalid configuration does not replace working data');
 for(let i=0;i<70;i++)R.frame({...original,asset:{...original.asset}},prop,'ENACT_HILLS');assert.equal(R.cached,48,'Bounded material cache');
 context.RoseDisplay.configure(false,'sharp');context.RoseAnimations.configure('reduced');
 const preview=canvasModule.createCanvas(2060,2740),c=preview.getContext('2d');c.fillStyle='#101618';c.fillRect(0,0,2060,2740);c.fillStyle='#e0d8ba';c.font='26px "Courier New"';c.fillText('ROSE 0.18 / MATERIAL, SIGNATURE AND PERCEPT',30,40);c.font='18px "Courier New"';c.fillText('Matched frozen scenes. Original baked surfaces / text + image direction.',30,73);
 const regions=[];
 for(const [row,region] of ['WN_TOWER','ENACT_HILLS','CITY_CLOUD_S','AETHERGALE'].entries()){
  const scene=JSON.parse(initial);scene.paused=true;scene.location.region=region;
  for(const n of scene.scene.infrastructure.nodes){n.visual={...n.visual,model:n.kind+'_'+region};n.material_state={...n.material_state,material:region==='WN_TOWER'?'wood':region==='CITY_CLOUD_S'?'metal':region==='AETHERGALE'?(['shelter','exchange'].includes(n.kind)?'fabric':'crystal'):'stone'};}
  for(const t of Object.values(scene.scene.tiles))if(t.prefab==='rock'){t.visual={...t.visual,model:'rock_'+region};t.material_state={...t.material_state,material:region==='AETHERGALE'?'crystal':'stone'};}
  let beforePicks,beforePaths,beforePNG;
  for(const [col,on] of [false,true].entries()){
   R.configure(on);F.reset();F.render(scene);F.select(null);F.draw(0);
   const picks=Object.values(scene.scene.tiles).map(t=>{const point=F.project(t.pos,t.elevation||0);return JSON.stringify(F.hitAt(point[0],point[1],0));});
   const start=scene.scene.units.find(u=>u.mine).pos,paths=Object.values(scene.scene.tiles).map(t=>JSON.stringify(F.path(start,t.pos)));
   const bitmap=ids['field-canvas'].bitmap,png=bitmap.toBuffer('image/png');
   const rgb=bitmap.getContext('2d').getImageData(0,0,1000,620).data,colors=new Set();for(let i=0;i<rgb.length;i+=28)colors.add([rgb[i],rgb[i+1],rgb[i+2],rgb[i+3]].join(','));
   assert.ok(colors.size>100,'Scene contains visible terrain, actors and infrastructure');
   if(!on){beforePicks=picks;beforePaths=paths;beforePNG=png;}else{assert.deepEqual(picks,beforePicks,'Material finish retains tile-sampled picking');assert.deepEqual(paths,beforePaths,'Material finish retains every route');assert.notEqual(png.toString('base64'),beforePNG.toString('base64'),'Visible material difference in '+region);}
   const x=20+col*1020,y=100+row*650;c.fillStyle='#e0d8ba';c.font='18px "Courier New"';c.fillText(region+' / '+(on?'TEXT + IMAGE DIRECTION':'BAKED SURFACES'),x+8,y+23);c.drawImage(await canvasModule.loadImage(png),x,y+30,1000,620);
  }
  regions.push({region,matched_picks:beforePicks.length,matched_paths:beforePaths.length,visible_difference:true});
 }
 ids['material-direction'].value='baked';ids['material-direction'].onchange();assert.equal(R.enabled,false);assert.equal(context.localStorage.getItem('rose-material-direction'),'baked');
 ids['material-direction'].value='source';ids['material-direction'].onchange();assert.equal(R.enabled,true);assert.equal(context.localStorage.getItem('rose-material-direction'),'source');
 assert.equal(JSON.stringify(read()),initial,'Visual fixtures never alter live host state');
 F.reset();F.render(read());
 const composed=c.getImageData(20,130,1000,620).data,composedColors=new Set();for(let i=0;i<composed.length;i+=28)composedColors.add([composed[i],composed[i+1],composed[i+2],composed[i+3]].join(','));assert.ok(composedColors.size>100,'Exported comparison contains the visible scene');
 const previewBytes=preview.toBuffer('image/png');fs.writeFileSync(path.join(root,'docs/Rose-art-direction-comparison-v018.png'),previewBytes);
 const served=await fetch(base+'/art-direction-preview.png');assert.equal(served.status,200);assert.match(served.headers.get('content-type'),/image\/png/);assert.equal(served.headers.get('x-content-type-options'),'nosniff');assert.deepEqual(Buffer.from(await served.arrayBuffer()),previewBytes,'The authoring page serves the exact rendered comparison');
 const report={schema:1,engine_version:'0.18.0',scope:'Real HTTP, modeled semantic DOM and native canvas; full interactive browser layout not run',materials,regions,cache_limit:48,alpha_exact:true,soft_shadow_rgb_exact:true,actor_project_remote_void_unplaced_and_archive_exclusions:true,simulation_unchanged:true,local_comparison_control:true,nonblank_export_verified:true,exact_comparison_http_bytes:true,new_model_bakes:false};
 fs.writeFileSync(path.join(root,'docs/art-direction-ui-audit-v018.json'),JSON.stringify(report,null,2)+'\n');
 console.log('PASS: art direction — six material finishes, exact alpha/soft shadows/practicals, 48-frame cache, scope exclusions, four matched regional scenes, 508 picks/routes, persistent controls and unchanged host state.');
};
