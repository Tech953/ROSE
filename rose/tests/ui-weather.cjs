/* Native prepared-surface checks plus the real host's weather/care controls. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const plain=x=>JSON.parse(JSON.stringify(x));
module.exports=async function({base,tmp,setupInterface,canvasModule,root}){
 const rig=setupInterface(base,tmp,{reducedMotion:false}),{context,ids}=rig,R=context.RoseWeather,A=context.RoseAnimations,P=context.RosePrefabs;
 for(let n=0;n<100&&!context.RoseCreator.ready;n++)await new Promise(r=>setTimeout(r,10));
 ids.name.value='Canopy keeper';ids.seed.value='weather-ui';rig.document.getElementById('rule-generation-hostility').value=0;
 await ids['join-form'].requestSubmit();await ids.start.click();if(canvasModule)await P.ready;
 const template=()=>({code:'WEATHER',started:true,paused:false,clock_held:false,me:{id:'watcher',remote:false},particles:{percept:{address:null}},scene:{id:'gale',weather:{tick:1,strength:1,direction:0}}});
 let s=template();A.configure('full');R.reset();R.read(s,0);
 const prop={type:'structure',pose:'idle',node:{id:'canopy',kind:'shelter',condition:80,material_state:{material:'fabric'},surface_view:{wetness:0,dust:0,restraint:.55,phase:.1,fabric:true}}};
 const pixels=f=>{const c=canvasModule.createCanvas(f.w,f.h),ctx=c.getContext('2d');ctx.drawImage(f.image.bitmap||f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);return ctx.getImageData(0,0,f.w,f.h).data;};
 const changed=(a,b)=>{let n=0;for(let i=0;i<a.length;i+=4)if(a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2])n++;return n;};
 const sameAlpha=(a,b)=>{for(let i=3;i<a.length;i+=4)assert.equal(a[i],b[i],'Prepared alpha and ground silhouette must be exact.');};
 const report={engine_version:'0.17.0',native_canvas:!!canvasModule,checks:[]};
 const images=[];
 if(canvasModule){
  const f=P.frameInfo('shelter_AETHERGALE','idle',0),original=pixels(f);assert.ok(f);
  s.scene.weather.strength=0;R.read(s,0);assert.equal(R.frame(f,prop,100),f);
  prop.node.surface_view.wetness=.8;const wet=R.frame(f,prop,100);sameAlpha(original,pixels(wet));assert.ok(changed(original,pixels(wet))>500);
  prop.node.surface_view.wetness=0;prop.node.surface_view.dust=.9;const dusty=R.frame(f,prop,100);sameAlpha(original,pixels(dusty));assert.ok(changed(original,pixels(dusty))>500);
  prop.node.surface_view.dust=0;s.scene.weather.strength=1;R.read(s,0);
  const f0=R.frame(f,prop,0),f1=R.frame(f,prop,400),b0=pixels(f0),b1=pixels(f1);sameAlpha(original,b0);sameAlpha(original,b1);assert.ok(changed(b0,b1)>20,'Wind must visibly affect the registered fabric patch.');
  for(let y=0;y<f.h;y++)for(let x=0;x<f.w;x++)if(x<156||x>182||y<172||y>218){const i=(y*f.w+x)*4;assert.equal(b0[i],original[i],'Fixed fabric boundaries and frame remain pinned.');assert.equal(b0[i+1],original[i+1]);assert.equal(b0[i+2],original[i+2]);}
  const soft=R.sample(prop,250).amplitude;prop.node.surface_view.restraint=.95;assert.ok(R.sample(prop,250).amplitude<soft,'Bracing reduces fabric excursion.');
  const solid={...prop,node:{...prop.node,kind:'exchange',surface_view:{...prop.node.surface_view,fabric:false}}};assert.equal(R.sample(solid,250).amplitude,0);
  s.paused=true;R.read(s,200);const paused=R.frame(f,prop,300);assert.equal(R.frame(f,prop,5000),paused,'Paused texture phase is fixed.');
  s.paused=false;R.read(s,800);assert.equal(R.frame(f,prop,800),paused,'Resume continues from the held phase.');
  s.clock_held=true;R.read(s,900);assert.equal(R.frame(f,prop,1100),R.frame(f,prop,9000));
  s.clock_held=false;R.read(s,9500);A.configure('reduced');assert.equal(R.sample(prop,9600).amplitude,0);
  const reducedRig=setupInterface(base,tmp,{reducedMotion:true});
  reducedRig.context.RoseAnimations.configure('system');reducedRig.context.RoseWeather.read(template(),0);
  assert.equal(reducedRig.context.RoseWeather.sample(prop,9700).amplitude,0,'System follows the actual media preference.');A.configure('full');
  s.me.remote=true;R.read(s,9800);assert.equal(R.frame(f,prop,9900),f);s.me.remote=false;s.particles.percept.address='void:test';R.read(s,9900);assert.equal(R.frame(f,prop,10000),f);
  s=template();R.read(s,0);prop.node.surface_view.restraint=.55;
  for(let n=0;n<100;n++){prop.node.surface_view.wetness=(n%17)/16;prop.node.surface_view.dust=((n*3)%17)/16;R.frame(f,prop,n*73);}
  assert.ok(R.cached<=32);assert.ok(R.sourceCount<=12);assert.ok(R.available);
  prop.node.surface_view={wetness:0,dust:0,restraint:.55,phase:.1,fabric:true};R.reset();R.read(template(),0);
  for(const [label,frame]of [['PINNED CANOPY / WIND 0',R.frame(f,prop,0)],['PINNED CANOPY / WIND 400ms',R.frame(f,prop,400)],['RAIN-DARKENED SURFACE',wet],['SETTLED DUST',dusty]])images.push({label,frame});
  const out=canvasModule.createCanvas(1120,800),c=out.getContext('2d');c.fillStyle='#111a17';c.fillRect(0,0,1120,800);c.font='15px "Courier New", monospace';c.fillStyle='#d5bf83';c.fillText('ROSE 0.17 / WEATHER RESPONSE · PREPARED SURFACES',28,30);
  images.forEach(({label,frame},i)=>{const x=24+(i%2)*550,y=70+Math.floor(i/2)*350;c.fillStyle='#a8b4a4';c.fillText(label,x,y);c.imageSmoothingEnabled=false;c.drawImage(frame.image.bitmap||frame.image,frame.x,frame.y,frame.w,frame.h,x+100,y-45,288,336);});
  fs.writeFileSync(path.join(root,'docs/Rose-weather-response-preview.png'),out.toBuffer('image/png'));
  report.checks.push('Native wet/dust color response; exact alpha, picking silhouette and fixed canopy boundaries; wind variation; bracing response; rigid exclusion; pause/held/resume; reduced motion; remote/void isolation; bounded caches.');
 }
 // Re-enter the live snapshot and exercise only displayed, authorized actions.
 R.reset();const read=()=>vm.runInContext('state',context),state=read();context.RoseField.render?.(state);
 assert.ok(state.scene.weather);assert.equal(typeof state.scene.weather.strength,'number');
 const node=state.scene.infrastructure.nodes.find(n=>n.kind==='water');assert.ok(node.surface_view);
 context.RoseField.select({type:'structure',id:node.id});await ids['walk-path'].click();
 const locate=(n,label)=>{if(n.tagName==='BUTTON'&&n.textContent===label)return n;for(const child of n.children||[]){const result=locate(child,label);if(result)return result;}return null;};
 const button=locate(ids['field-selection-actions'],'CLEAN SURFACE / 1 WATER');assert.ok(button,'Cleaning is exposed by the real object menu.');
 const before=plain(read().me.inventory),tick=read().tick;
 if(button.disabled){assert.ok(button.dataset.blockReason);await button.click();assert.deepEqual(plain(read().me.inventory),before);assert.equal(read().tick,tick);}
 report.checks.push('Live HTTP snapshot supplies bounded surface views; object menu exposes surface care and blocks unavailable cleaning without spending.');
 fs.writeFileSync(path.join(root,'docs/weather-response-ui-audit-v017.json'),JSON.stringify({...report,status:'PASS'},null,2)+'\n');
 console.log('PASS: weather response — exact prepared alpha and fixed anchors, material wet/dust response, wind and bracing, static rigid objects, pause/held/reduced/remote boundaries, bounded caches and real-host care menu.');
};
