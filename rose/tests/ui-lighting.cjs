/* Light spill is a display preference; original alpha and host state persist. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),profiles=JSON.parse(fs.readFileSync(path.join(root,'static/lighting-signatures.json'),'utf8'));
module.exports=function(canvasModule){
 const api={style:'rendered',practicals:()=>[{offset:[0,-20],color:[.1,.8,1],radius:74,intensity:1,portable:false}]};
 const context={window:{},RosePrefabs:api,document:{createElement:()=>canvasModule?.createCanvas(1,1)}};
 vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'static/lighting.js'),'utf8'),context);
 const light=context.window.RoseLighting;assert.equal(light.ready,false);light.load(profiles);assert.equal(light.ready,true);
 assert.throws(()=>light.load({schema:1,profiles:{bad:{name:'bad',radiance:Infinity}}}),/Invalid/);
 const node={id:'one',enabled:true,condition:90,connected:true,status:'working'},field={tiles:{'0,0':{passable:false},'1,0':{passable:true},'2,0':{passable:true}}};
 const props=[{type:'structure',node,asset:'workshop',pos:[0,0],screen:[0,0]}];
 let prepared=light.prepare(field,'CITY_CLOUD_S',props);
 assert.equal(prepared.emitters.length,1);assert.ok(light.sample(prepared,[1,0],[12,3]).level>0);
 const optical={source_online:true,source_node:'one',exposure:.08,color:[.22,.73,.96]};
 assert.equal(light.prepare(field,'CITY_CLOUD_S',props,1,optical).emitters.length,2,'A paid optical response adds a workshop emitter');
 assert.equal(light.prepare(field,'CITY_CLOUD_S',props,1,{...optical,exposure:0}).emitters.length,1,'An empty reservoir cannot add light');
 assert.equal(light.prepare(field,'CITY_CLOUD_S',props,1,{...optical,source_online:false}).emitters.length,1,'An offline optical source cannot add light');
 assert.equal(light.prepare(field,'CITY_CLOUD_S',props,1,{...optical,color:[Infinity,0,0]}).emitters.length,1,'Malformed optical colors are refused');
 field.tiles['1,0'].passable=false;assert.equal(light.sample(prepared,[2,0],[20,3]).level,0,'A solid intermediate hex blocks actor light spill');field.tiles['1,0'].passable=true;
 for(const change of [{enabled:false},{condition:29},{connected:false},{status:'power deficit'}]){
  const modified={...node,...change};assert.equal(light.prepare(field,'CITY_CLOUD_S',[{...props[0],node:modified}]).emitters.length,0);
  assert.equal(light.prepare(field,'CITY_CLOUD_S',[{...props[0],node:modified}],1,optical).emitters.length,0,'Workshop state also gates optical spill');
 }
 assert.equal(light.powered({...node,connected:false},{portable:true}),true,'A portable hearth remains distinct from grid-fed lights');
 assert.equal(light.powered({...node,enabled:false},{portable:true}),false);
 light.configure('subdued');const subdued=light.prepare(field,'CITY_CLOUD_S',props);assert.ok(subdued.emitters[0].intensity<prepared.emitters[0].intensity);
 light.configure('baked');assert.equal(light.prepare(field,'CITY_CLOUD_S',props).emitters.length,0);assert.equal(light.frame({},null),null);
 light.configure('invalid');assert.equal(light.mode,'signature');api.style='vector';assert.equal(light.prepare(field,'CITY_CLOUD_S',props).enabled,false);api.style='rendered';
 if(canvasModule){
  const source=canvasModule.createCanvas(2,2),c=source.getContext('2d'),pixels=c.createImageData(2,2);
  pixels.data.set([120,90,60,255,0,0,0,240,50,60,70,0,180,150,120,255]);c.putImageData(pixels,0,0);
  const asset={},frame={asset,image:source,x:0,y:0,w:2,h:2,frameIndex:0};
  prepared=light.prepare(field,'CITY_CLOUD_S',props);const sample=light.sample(prepared,[1,0],[12,3]);
  const result=light.frame(frame,sample),data=result.getContext('2d').getImageData(0,0,2,2).data,original=c.getImageData(0,0,2,2).data;
  assert.notDeepEqual(data,original);for(let i=3;i<data.length;i+=4)assert.equal(data[i],original[i],'Lighting preserves every alpha byte');
  assert.deepEqual([...data.slice(4,8)],[...original.slice(4,8)],'A graded black shadow remains unchanged');
  assert.equal(light.frame(frame,sample),result,'Identical current-frame lighting reuses its canvas');
  const oldPracticals=api.practicals;api.practicals=()=>[
   {offset:[27,-20],color:[1,0,0],radius:100,intensity:1,portable:false},
   {offset:[27,-20],color:[0,0,1],radius:100,intensity:1,portable:false}];
  const mixed=light.sample(light.prepare(field,'CITY_CLOUD_S',props),[1,0],[27,3]);
  assert.ok(mixed.color[0]>0&&mixed.color[2]>0,'Overlapping practicals contribute both spectra');
  const wallField={tiles:{'0,0':{pos:[0,0],passable:false},'1,0':{pos:[1,0],passable:false},'2,0':{pos:[2,0],passable:true}}};
  const project=p=>[40+Math.sqrt(3)*34*(p[0]+p[1]/2),60+34*1.5*.52*p[1]];
  const wallProps=[{...props[0],screen:project([0,0])}],pool=canvasModule.createCanvas(230,120),poolContext=pool.getContext('2d');
  light.pools(poolContext,light.prepare(wallField,'CITY_CLOUD_S',wallProps,1,null,project));
  const receiver=project([2,0]);let pixel=poolContext.getImageData(Math.round(receiver[0]),Math.round(receiver[1]),1,1).data;
  assert.equal(pixel[3],0,'Solid intermediate scenery blocks ground light beyond it');
  wallField.tiles['1,0'].passable=true;poolContext.clearRect(0,0,230,120);
  light.pools(poolContext,light.prepare(wallField,'CITY_CLOUD_S',wallProps,1,null,project));
  pixel=poolContext.getImageData(Math.round(receiver[0]),Math.round(receiver[1]),1,1).data;
  assert.ok(pixel[3]>0,'Removing the blocker restores the same ground receiver');api.practicals=oldPracticals;
  for(let i=0;i<40;i++)light.pools(poolContext,light.prepare(wallField,'CITY_CLOUD_S',[{...wallProps[0],screen:[40+i,60]}],1,null,project));
  assert.ok(light.cachedPools>0&&light.cachedPools<=32,'Continuous shadow masks are bounded as scene and emitter positions change');
  for(let i=0;i<100;i++)light.frame({...frame,frameIndex:i},sample);assert.ok(light.cachedFrames<=64,'The decoded light response cache is bounded');
  c.globalAlpha=.43;const priorAlpha=c.globalAlpha;c.globalCompositeOperation='source-over';light.pools(c,prepared);light.glow(c,props[0],prepared);assert.equal(c.globalAlpha,priorAlpha);assert.equal(c.globalCompositeOperation,'source-over');
  light.configure('baked');assert.equal(light.frame(frame,sample),null,'Baked only returns the exact original frame');
 }
 console.log('PASS: spectrum lighting — regional data, offline/portable lamps, additive spectra, blocker-aware actor/ground spill, unchanged alpha/shadows, bounded cache and exact baked fallback.');
};
module.exports.flow=async function({context,ids,read,canvasModule}){
 const host=JSON.stringify(read()),initial=JSON.parse(host),light=context.RoseLighting,oldMode=light.mode,oldProfile=context.RoseDisplay.profile;
 assert.equal(light.ready,true,'Regional light definitions have loaded');context.RoseDisplay.configure(true,'sharp');
 const native=canvasModule?canvasModule.createCanvas(2060,1380):null,view=native?.getContext('2d');
 if(view){view.fillStyle='#101812';view.fillRect(0,0,2060,1380);view.fillStyle='#d3c7a6';view.font='20px Courier New';view.fillText('ROSE / REGIONAL SPECTRUM LIGHT',20,32);}
 let index=0;
 for(const region of Object.keys(profiles.profiles)){
  const scene=JSON.parse(host);scene.location.region=region;
  for(const node of scene.scene.infrastructure.nodes){node.visual={...node.visual,model:node.kind+'_'+region,tone:0};node.enabled=true;node.connected=true;node.status='working';node.condition=90;}
  for(const tile of Object.values(scene.scene.tiles))if(tile.prefab==='rock')tile.visual={...tile.visual,model:'rock_'+region,tone:0};
  context.RoseField.render(scene);context.RoseField.select(null);ids['lighting-mode'].value='baked';ids['lighting-mode'].onchange();context.RoseField.draw(0);
  const points=scene.scene.units.map(u=>context.RoseField.project(u.pos)),hits=points.map(p=>JSON.stringify(context.RoseField.hitAt(...p,0)));
  const baked=canvasModule?ids['field-canvas'].bitmap.toBuffer('image/png'):null;
  ids['lighting-mode'].value='signature';ids['lighting-mode'].onchange();context.RoseField.draw(0);
  assert.deepEqual(points.map(p=>JSON.stringify(context.RoseField.hitAt(...p,0))),hits,'Radiance cannot change scene picking');
  if(view){const png=ids['field-canvas'].bitmap.toBuffer('image/png');assert.notDeepEqual(png,baked);const x=20+(index%2)*1020,y=62+Math.floor(index/2)*650;view.font='14px Courier New';view.fillText(region+' / '+profiles.profiles[region].name,x,y);const shot=await canvasModule.loadImage(png);assert.equal(shot.width,1000);view.drawImage(shot,x,y+14);}
  index++;
 }
 if(view)fs.writeFileSync(path.join(root,'docs/Rose-spectrum-preview.png'),native.toBuffer('image/png'));
 assert.equal(context.localStorage.getItem('rose-lighting-mode'),'signature');assert.equal(JSON.stringify(read()),host,'Lighting controls spend no AP, resources or host revision');
 context.RoseField.render(initial);light.configure(oldMode);ids['lighting-mode'].value=oldMode;context.RoseDisplay.configure(true,oldProfile);context.RoseField.draw(0);
 console.log('PASS: spectrum host flow — four regions, exact picking, saved browser preference and unchanged game state.');
};
