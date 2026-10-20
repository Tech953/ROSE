/* Monument scale must share rendered pixels, masks and construction bounds. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
module.exports=async function({context,ids,read,canvasModule,root,baseline}){
 if(!canvasModule)return;
 const initial=JSON.stringify(read()),prefabs=context.RosePrefabs,field=context.RoseField,lighting=context.RoseLighting;
 const display={enabled:context.RoseDisplay.enabled,profile:context.RoseDisplay.profile},metrics=[],navigation=[],oldMode=lighting.mode;
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'static/art-manifest-rendered.json'),'utf8'));
 const fixture=region=>{const s=JSON.parse(initial);s.location.region=region;for(const n of s.scene.infrastructure.nodes){n.visual={...n.visual,model:n.kind+'_'+region};n.condition=90;n.enabled=true;n.connected=true;n.status='working';}for(const t of Object.values(s.scene.tiles))if(t.prefab==='rock')t.visual={...t.visual,model:'rock_'+region};return s;};
 try{
  context.RoseDisplay.configure(false,'sharp');lighting.configure('signature');
  for(const region of manifest.visual_catalog.regions){
   const scene=fixture(region);field.reset();field.render(scene);field.draw(0);const actor=scene.scene.units.find(u=>u.mine),body=prefabs.bounds(prefabs.assetFor(actor),'idle',0,actor.facing||0);
   const dimensions={};
   for(const kind of ['water','power','relay']){
    const n=scene.scene.infrastructure.nodes.find(n=>n.kind===kind);assert.ok(n,'Fixture contains '+kind);const key=prefabs.assetFor(n),frame=prefabs.frameInfo(key,'idle',0),bounds=prefabs.bounds(key,'idle',0);
    assert.equal(frame.association,true,'The actual service frame includes its monument core');assert.equal(frame.scale,manifest.assets[key].scale,'Service hardware retains its authored scale');
    dimensions[kind]={height_px:bounds[3],height_in_bodies:bounds[3]/body[3]};assert.ok(dimensions[kind].height_in_bodies>3,'Key infrastructure reads as a monument beside a person');
    const [x,y]=field.project(n.pos);let owned=false;
    for(let py=bounds[1]+5;py<bounds[1]+bounds[3]-100;py+=5)for(let px=-20;px<20;px+=3)if(prefabs.hit(key,[px,py],'idle',0)){
     const hit=field.hitAt(x+px,y+py,0);if(hit?.type==='structure'&&hit.id===n.id)owned=true;
    }assert.ok(owned,'Pixels high on the monolith select its actual infrastructure node');
    assert.equal(prefabs.hit(key,[bounds[0]-10,bounds[1]+5],'idle',0),false,'Transparent padding cannot select the monolith');
    field.select({type:'structure',id:n.id});assert.equal(ids['field-detail'].hidden,false);assert.match(ids['field-detail-label'].textContent,/current field appearance/);
   }
   assert.ok(dimensions.relay.height_px>dimensions.power.height_px&&dimensions.power.height_px>dimensions.water.height_px,'Function hierarchy is legible in each region');
   metrics.push({region,body_height_px:body[3],structures:dimensions});
  }
  assert.ok(prefabs.associationsAvailable&&prefabs.cachedAssociations<=24,'Monolith composition is active and bounded');
  // A real passable hex two steps behind a foreground core tests fade-through.
  const hidden=fixture('WN_TOWER'),n=hidden.scene.infrastructure.nodes.find(n=>n.kind==='relay'),behind=[n.pos[0]+1,n.pos[1]-2];
  assert.equal(hidden.scene.tiles[behind.join(',')].passable,true,'The occlusion control uses an actual walkable tile');hidden.scene.units=hidden.scene.units.filter(u=>u.mine);hidden.scene.units[0].pos=behind;field.reset();field.render(hidden);field.draw(0);
  assert.ok(field.occlusion(0).includes('structure:'+n.id),'A foreground monolith fades when it hides the player');
  const u=hidden.scene.units[0],point=field.project(u.pos),key=prefabs.assetFor(u);let selectable=false;
  for(let y=-50;y<-10;y+=2)for(let x=-8;x<8;x+=2)if(prefabs.hit(key,[x,y],'idle',0,u.facing||0)){const hit=field.hitAt(point[0]+x,point[1]+y,0);if(hit?.type==='unit'&&hit.id===u.id)selectable=true;}
  assert.ok(selectable,'The player remains selectable through a faded monument');
  for(const kind of ['power','water','relay'])for(const stage of ['foundation','frame','finishing']){
   const prop={type:'project',asset:kind+'_WN_TOWER',pose:'worn',time:0,facing:0,node:{work_done:stage==='foundation'?0:stage==='frame'?4:8,work_required:10}};
   const bounds=context.RoseEnvironment.bounds(prop);assert.equal(context.RoseEnvironment.hit(prop,[0,bounds[1]-4]),false,'Unbuilt upper monument pixels have no physical selection');
  }
  if(baseline){
   const c=canvasModule.createCanvas(2060,1380),p=c.getContext('2d');p.fillStyle='#101812';p.fillRect(0,0,2060,1380);p.fillStyle='#d4c8ac';p.font='20px Courier New';p.fillText('ROSE 0.13.3 / MONOLITH INFRASTRUCTURE SCALE',20,32);p.font='13px Courier New';p.fillText('Same settlement, characters and service frames / fixed camera / original solid 3D cores added',20,55);
   for(const [row,region]of ['WN_TOWER','CITY_CLOUD_S'].entries()){
    const s=fixture(region),destinations=Object.values(s.scene.tiles).filter(t=>t.passable).map(t=>t.pos);let routes;
    for(const [column,current]of [false,true].entries()){
     if(!current){vm.runInContext(fs.readFileSync(path.join(baseline,'prefabs.js'),'utf8'),context);context.RosePrefabs=context.window.RosePrefabs;await context.RosePrefabs.load(manifest);}
     else context.RosePrefabs=context.window.RosePrefabs=prefabs;
     field.reset();field.render(s);field.select(null);field.draw(0);const paths=destinations.map(d=>JSON.stringify(field.path(s.scene.units.find(u=>u.mine).pos,d)));
     if(current){assert.deepEqual(paths,routes,'Monuments cannot block additional walk cells or change route costs');navigation.push({region,paths_compared:paths.length,unchanged:true});}else routes=paths;
     const png=ids['field-canvas'].bitmap.toBuffer('image/png'),x=20+column*1020,y=80+row*650;p.fillStyle='#b5c6a6';p.font='14px Courier New';p.fillText(region+' / '+(current?'0.13.3 / monument cores with human-scale service faces':'0.13.2 / field-sized service modules'),x,y);p.drawImage(await canvasModule.loadImage(png),x,y+16);
    }
   }
   fs.writeFileSync(path.join(root,'docs/Rose-monolith-scale-comparison.png'),c.toBuffer('image/png'));
  }
  fs.writeFileSync(path.join(root,'docs/monolith-scale-audit-v0133.json'),JSON.stringify({schema:1,engine_version:'0.13.3',backend:'native canvas and modeled DOM',metrics,navigation_comparison:navigation.length?{status:'PASS',cases:navigation}:{status:'NOT_RUN',reason:'A prior renderer was not supplied.'},cache_bound:24,occlusion_and_picking:'PASS',construction_selection:'PASS',host_state_unchanged:true,scope:'Relative rendered scale; not planetary measurement, full-browser validation or a new Blender bake.'},null,2)+'\n');
  assert.equal(JSON.stringify(read()),initial,'Art inspection spends no AP, resources or host revision');
 }finally{context.RosePrefabs=context.window.RosePrefabs=prefabs;lighting.configure(oldMode);context.RoseDisplay.configure(display.enabled,display.profile);field.reset();field.render(JSON.parse(initial));}
 console.log('PASS: monolith scale — four regions, body-relative hierarchy, service registration, solid-pixel picking, player fade-through, staged construction, bounded composition and unchanged host state.');
};
