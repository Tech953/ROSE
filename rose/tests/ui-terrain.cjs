/* Natural scenery controls and matched native scene comparisons. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
module.exports=async function({context,ids,read,canvasModule,root,baseline}){
 const initial=JSON.stringify(read()),field=context.RoseField,lighting=context.RoseLighting,terrain=context.RoseTerrain;
 const display={enabled:context.RoseDisplay.enabled,profile:context.RoseDisplay.profile},mode=lighting.mode,metrics=[];
 const profiles=JSON.parse(fs.readFileSync(path.join(root,'static/lighting-signatures.json'),'utf8'));
 const fixture=region=>{const f=JSON.parse(initial);f.location.region=region;
  for(const n of f.scene.infrastructure.nodes){n.visual={...n.visual,model:n.kind+'_'+region};n.condition=90;n.enabled=true;n.connected=true;n.status='working';}
  for(const t of Object.values(f.scene.tiles))if(t.prefab==='rock')t.visual={...t.visual,model:'rock_'+region};return f;};
 try{
  context.RoseDisplay.configure(false,'sharp');field.reset();field.render(JSON.parse(initial));field.draw(0);
  assert.equal(ids['field-object'].value,'','A new field has no automatically selected scenery');
  assert.match(ids['field-route'].textContent,/Choose a destination/,'A new field has no automatically drawn tactical route');
  assert.equal(ids['field-detail'].hidden,true);
  const f=JSON.parse(initial).scene,paths=JSON.stringify(terrain.routes(f));assert.ok(JSON.parse(paths).length>0,'The fixture has reachable building approaches');
  for(const route of terrain.routes(f))for(let i=0;i<route.length;i++){
   assert.equal(f.tiles[route[i].join(',')].passable,true,'Every worn approach follows passable ground');
   if(i){const a=route[i-1],b=route[i];assert.equal(Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]),Math.abs(a[0]+a[1]-b[0]-b[1])),1,'Approaches do not jump across solid scenery');}
  }
  const moving=JSON.parse(initial).scene;for(const u of moving.units)u.pos=[1,0];
  assert.equal(JSON.stringify(terrain.routes(moving)),paths,'Worn approaches do not move when characters do');
  const grown=JSON.parse(initial).scene;grown.lifecycle.growth=100;
  assert.equal(JSON.stringify(terrain.routes(grown)),paths,'Ecological growth leaves the established approach geometry stable');
  const pixels=canvasModule?context.document.createElement('canvas'):null;
  if(pixels){
   assert.equal(terrain.available,true,'The field renderer has not fallen back from continuous terrain');pixels.width=1000;pixels.height=620;
   const c=pixels.getContext('2d'),size=34*6/f.radius;
   assert.equal(terrain.draw(c,f,'WN_TOWER',field.project,size),true);
   const before=c.getImageData(0,0,1000,620).data;
   for(const [x,y]of[[20,90],[980,90],[20,560],[980,560]])assert.equal(before[(y*1000+x)*4+3],255,'Ground continues beyond the finite navigation domain');
   terrain.draw(c,grown,'WN_TOWER',field.project,size);assert.notDeepEqual(c.getImageData(0,0,1000,620).data,before,'Registered growth changes ground cover');
   for(const region of Object.keys(profiles.profiles))assert.equal(terrain.draw(c,f,region,field.project,size),true);
   assert.ok(terrain.available&&terrain.cachedViews<=2,'Continuous terrain uses a bounded cache');
   for(const radius of [5,6,9]){
    const framed=JSON.parse(initial);framed.scene.radius=radius;field.render(framed);const scale=34*6/radius;
    terrain.draw(c,framed.scene,'WN_TOWER',field.project,scale);const approached=c.getImageData(0,0,1000,620).data;
    const empty=JSON.parse(JSON.stringify(framed.scene));empty.infrastructure.nodes=[];empty.lifecycle.projects=[];
    terrain.draw(c,empty,'WN_TOWER',field.project,scale);assert.notDeepEqual(c.getImageData(0,0,1000,620).data,approached,'Worn approaches render at every supported local field scale');
   }field.render(JSON.parse(initial));
   const picks=Object.values(f.tiles).map(t=>field.project(t.pos,t.elevation)).map(p=>JSON.stringify(field.hitAt(...p,0)));
   field.draw(0);const plain=ids['field-canvas'].bitmap.toBuffer('image/png');
   ids['toggle-grid'].click();field.draw(0);assert.notDeepEqual(ids['field-canvas'].bitmap.toBuffer('image/png'),plain,'The tactical grid is available explicitly');
   assert.deepEqual(Object.values(f.tiles).map(t=>field.project(t.pos,t.elevation)).map(p=>JSON.stringify(field.hitAt(...p,0))),picks,'The grid toggle retains picking');ids['toggle-grid'].click();
  }
  await ids['field-canvas'].onclick({clientX:10,clientY:610});assert.match(ids['field-notice'].textContent,/World Map/,'Continuous scenery outside the local domain gives an onward-travel hint');
  if(canvasModule&&baseline){
   const panel=canvasModule.createCanvas(2060,1380),c=panel.getContext('2d');c.fillStyle='#101812';c.fillRect(0,0,2060,1380);c.fillStyle='#d4c8ac';c.font='20px Courier New';c.fillText('ROSE 0.13.2 / CONTINUOUS LOCAL SCENERY',20,32);
   c.font='13px Courier New';c.fillText('Same original sprites, frozen geometry and camera / ordinary exploration / CRT off',20,55);
   for(const [row,region]of ['WN_TOWER','CITY_CLOUD_S'].entries()){
    const frozen=fixture(region),destinations=Object.values(frozen.scene.tiles).filter(t=>t.passable).map(t=>t.pos);let oldPicks,oldPaths;
    for(const [column,current]of [false,true].entries()){
     if(current){context.RoseField=context.window.RoseField=field;context.RoseLighting=context.window.RoseLighting=lighting;field.reset();}
     else{for(const name of ['lighting','scene']){vm.runInContext(fs.readFileSync(path.join(baseline,name+'.js'),'utf8'),context);const api=name==='lighting'?'RoseLighting':'RoseField';context[api]=context.window[api];}context.RoseLighting.load(profiles);}
     const active=context.RoseField;context.RoseLighting.configure('signature');active.render(frozen);active.select(null);active.draw(0);
     const picks=Object.values(frozen.scene.tiles).map(t=>active.project(t.pos,t.elevation)).map(p=>JSON.stringify(active.hitAt(...p,0)));
     const routes=destinations.map(p=>JSON.stringify(active.path(frozen.scene.units.find(u=>u.mine).pos,p)));
     assert.ok(routes.some(r=>r!=='null'),'The fixture checks real reachable navigation paths');
     if(current){assert.deepEqual(picks,oldPicks,'Continuous scenery preserves every sampled sprite/ground pick');assert.deepEqual(routes,oldPaths,'Continuous scenery preserves every sampled navigation path');}
     else{oldPicks=picks;oldPaths=routes;}
     const png=ids['field-canvas'].bitmap.toBuffer('image/png'),x=20+column*1020,y=80+row*650;c.fillStyle='#b5c6a6';c.font='14px Courier New';c.fillText(region+' / '+(current?'0.13.2 / continuous ground and worn approaches':'0.13.1 / hex field boundary and circulation surfaces'),x,y);c.drawImage(await canvasModule.loadImage(png),x,y+16);
     if(current){const start=performance.now();for(let i=0;i<20;i++)field.draw(0);metrics.push({region,frames:20,mean_draw_ms:(performance.now()-start)/20,hex_picks_checked:picks.length,navigation_paths_checked:routes.length});}
    }
   }
   fs.writeFileSync(path.join(root,'docs/Rose-continuous-terrain-comparison.png'),panel.toBuffer('image/png'));
   fs.writeFileSync(path.join(root,'docs/renderer-audit-v0132.json'),JSON.stringify({schema:1,engine_version:'0.13.2',baseline_version:'0.13.1',backend:'@napi-rs/canvas and modeled DOM',fixture:'Frozen enabled regional presentation copies; no host mutation or asset rebake.',display:'sharp / CRT off',metrics,scope:'Native draw cost only; excludes browser layout, device FPS and Windows validation.'},null,2)+'\n');
  }
  assert.equal(JSON.stringify(read()),initial,'Scenery, labels, grids and comparison fixtures spend no AP, resources or host revision');
 }finally{context.RoseField=context.window.RoseField=field;context.RoseLighting=context.window.RoseLighting=lighting;lighting.configure(mode);context.RoseDisplay.configure(display.enabled,display.profile);field.reset();field.render(JSON.parse(initial));}
 console.log('PASS: continuous scenery — opaque viewport, stable passable approaches and growth, no automatic selection, optional tactical grid, onward-travel hint, bounded buffers and unchanged host state.');
 if(metrics.length)console.log('PASS: matched 0.13.1/0.13.2 native scenes — exact picking and paths in both regions.');
};
