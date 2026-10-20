/* Individual asset resolution uses the same key for draw, masks and bounds. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
module.exports=({context,ids,read,canvasModule,root})=>{
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'static/art-manifest-rendered.json'),'utf8'));
 const initial=JSON.parse(JSON.stringify(read())),host=JSON.stringify(read()),prefabs=context.RosePrefabs;
 const actor=initial.scene.units.find(u=>u.mine);
 assert.ok(actor.visual);assert.equal(actor.visual.model,initial.me.visual.model);
 const key=prefabs.assetFor(actor);assert.ok(manifest.assets[key]);assert.notEqual(key,'player');
 const nodes=initial.scene.infrastructure.nodes;
 for(const node of nodes){assert.ok(manifest.assets[prefabs.assetFor(node)]);assert.equal(node.visual.model,node.kind+'_'+initial.location.region);}
 for(const style of ['rendered-legacy','raster','vector']){prefabs.setStyle(style);assert.equal(prefabs.assetFor(actor),'player');assert.equal(prefabs.assetFor(nodes[0]),nodes[0].kind);}
 prefabs.setStyle('rendered');
 if(canvasModule){
  const images=[];
  const scene=JSON.parse(JSON.stringify(initial));scene.scene.units=scene.scene.units.filter(u=>u.mine);scene.scene.infrastructure.nodes=[];
  for(const profile of Object.keys(manifest.visual_catalog.profiles)){
   const u=scene.scene.units[0];u.visual={...u.visual,model:profile,tone:2};u.pos=[0,0];u.pose='idle';
   context.RoseField.render(scene);context.RoseField.select({type:'unit',id:u.id});context.RoseField.draw(0);
   assert.equal(ids['field-detail'].hidden,false,'Selection opens a view of the actual field appearance');assert.equal(ids['field-detail-canvas'].width,360);assert.equal(ids['field-detail-canvas'].height,360);
   assert.ok(ids['field-detail-canvas'].bitmap.toBuffer('image/png').length>1000,'The enlarged appearance contains actual sprite pixels');
   const chosen=prefabs.assetFor(u),bounds=prefabs.bounds(chosen,'idle',0,u.facing||0);
   assert.ok(bounds[2]>0&&bounds[3]>0);assert.equal(prefabs.hit(chosen,[1000,1000]),false);
   const pt=context.RoseField.project(u.pos,scene.scene.tiles['0,0'].elevation);let picked=false;
   for(let y=-55;y<-12;y+=2)for(let x=-12;x<12;x+=2)if(prefabs.hit(chosen,[x,y],'idle',0,u.facing||0)){
    const hit=context.RoseField.hitAt(pt[0]+x*6/scene.scene.radius,pt[1]+y*6/scene.scene.radius,0);
    if(hit?.type==='unit'&&hit.id===u.id)picked=true;
   }
   assert.ok(picked,'The selected '+profile+' sprite owns its alpha picking');
   images.push(ids['field-canvas'].bitmap.toBuffer('image/png').toString('base64'));
  }
  assert.equal(new Set(images).size,5,'Distinct field bodies produce distinct native images');
  const worn=JSON.parse(JSON.stringify(initial));const node=worn.scene.infrastructure.nodes[0];
  node.condition=90;context.RoseField.render(worn);context.RoseField.draw(0);const before=ids['field-canvas'].bitmap.toBuffer('image/png');
  node.condition=29;context.RoseField.render(worn);context.RoseField.draw(0);const after=ids['field-canvas'].bitmap.toBuffer('image/png');
  assert.equal(prefabs.structurePose(node),'fractured');assert.notDeepEqual(before,after);
  context.RoseField.select({type:'structure',id:node.id});context.RoseField.draw(0);assert.equal(ids['field-detail'].hidden,false);
  fs.writeFileSync(path.join(root,'docs/Rose-detail-preview.png'),ids['field-detail-canvas'].bitmap.toBuffer('image/png'));
  for(const region of manifest.visual_catalog.regions){
   const full=canvasModule.createCanvas(256,160),split=canvasModule.createCanvas(256,160);
   assert.equal(prefabs.path(full.getContext('2d'),region,[0,0,256,160]),true);
   const c=split.getContext('2d');for(const x of [0,128]){c.save();c.beginPath();c.rect(x,0,128,160);c.clip();assert.equal(prefabs.path(c,region,[0,0,256,160]),true);c.restore();}
   assert.deepEqual(full.getContext('2d').getImageData(0,0,256,160).data,c.getImageData(0,0,256,160).data,'Clipped path tiles share one global pattern origin');
  }
  const terrain=JSON.parse(JSON.stringify(initial));context.RoseField.render(terrain);context.RoseField.select(null);context.RoseField.draw(0);const terrainBefore=ids['field-canvas'].bitmap.toBuffer('image/png');
  for(const tile of Object.values(terrain.scene.tiles))if(tile.passable)tile.prefab='path';context.RoseField.render(terrain);context.RoseField.draw(0);
  assert.deepEqual(terrainBefore,ids['field-canvas'].bitmap.toBuffer('image/png'),'Navigation circulation markers cannot paint the hidden movement lattice into the scenery');
 }
 context.RoseField.render(initial);assert.equal(JSON.stringify(read()),host,'Display inspection spends no resources or host revision');
 context.RoseField.select({type:'hex',pos:[0,0]});assert.equal(ids['field-detail'].hidden,true,'Walkable ground has no fabricated body detail');
 console.log('PASS: individualized visuals — stable designations, all five bodies, regional assets, legacy fallback, current-frame alpha picking and condition frames.');
};
