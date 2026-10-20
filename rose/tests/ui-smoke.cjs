/* Real HTTP + DOM logic. Optional native canvas draws the actual field renderer. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),{spawn}=require('node:child_process');
const root=path.resolve(__dirname,'..');
let canvasModule=null;try{canvasModule=require(require.resolve('@napi-rs/canvas',{paths:[process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES||root]}));const font='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf';if(fs.existsSync(font))canvasModule.GlobalFonts.registerFromPath(font,'Courier New');}catch{}
const fakeContext=new Proxy({createRadialGradient:()=>({addColorStop(){}})}, {get:(object,key)=>key in object?object[key]:()=>{},set:(object,key,value)=>(object[key]=value,true)});
let activeDocument=null;
class Element{
 constructor(tag,all){this.ownerDocument=activeDocument;this.tagName=tag.toUpperCase();this.children=[];this.dataset={};this.attrs={};this.hidden=false;this.disabled=false;this.value='';this.textContent='';this.className='';this.style={};this.id='';this.isConnected=false;this.open=false;this.classList={toggle:()=>{},add:()=>{},remove:()=>{}};if(tag==='canvas'&&canvasModule)this.bitmap=canvasModule.createCanvas(1000,620);if(tag!=='canvas')all.push(this);}
 connect(flag){this.isConnected=flag;for(const n of this.children)n.connect(flag);if(!flag&&this.ownerDocument?.activeElement===this)this.ownerDocument.activeElement=this.ownerDocument.body;}
 append(...nodes){this.children.push(...nodes);for(const n of nodes){n.parentElement=this;n.connect(this.isConnected);}}replaceChildren(...nodes){for(const n of this.children)n.connect(false);this.children=[];this.append(...nodes);}
 setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];}
 click(){if(!this.disabled)return this.onclick?.({preventDefault(){}});}requestSubmit(){return this.onsubmit?.({preventDefault(){}});}focus(){if(!this.disabled)this.ownerDocument.activeElement=this;}reportValidity(){return true;}
 querySelectorAll(selector){const result=[];for(const node of this.children){if(node.tagName===selector.toUpperCase())result.push(node);if(node.querySelectorAll)result.push(...node.querySelectorAll(selector));}return result;}
 getContext(){if(!this.bitmap)return fakeContext;if(!this.contextProxy){const native=this.bitmap.getContext('2d');this.contextProxy=new Proxy(native,{get:(o,k)=>k==='drawImage'?(img,...args)=>o.drawImage(img.bitmap||img,...args):typeof o[k]==='function'?o[k].bind(o):o[k],set:(o,k,v)=>(o[k]=v,true)});}return this.contextProxy;}getBoundingClientRect(){return{left:0,top:0,width:1000,height:620};}
 set width(value){this._width=value;if(this.bitmap)this.bitmap.width=value;}get width(){return this.bitmap?.width||this._width||1000;}
 set height(value){this._height=value;if(this.bitmap)this.bitmap.height=value;}get height(){return this.bitmap?.height||this._height||620;}
}
class Storage{constructor(){this.items={};}getItem(k){return this.items[k]??null;}setItem(k,v){this.items[k]=v;}removeItem(k){delete this.items[k];}}
function within(node,predicate){if(predicate(node))return node;for(const child of node.children||[]){const found=within(child,predicate);if(found)return found;}return null;}

function setupInterface(base,tmp,options={}){
 const all=[],ids={};
  const document={hidden:false,getElementById:id=>{const n=ids[id]||all.find(n=>n.id===id&&n.isConnected);assert.ok(n,'Missing DOM ID '+id);return n;},createElement:tag=>{activeDocument=document;return new Element(tag,all);},createElementNS:(ns,tag)=>new Element(tag,all),querySelectorAll:selector=>all.filter(n=>n.isConnected&&(selector==='button'?n.tagName==='BUTTON':selector==='[data-command]'?n.dataset.command:selector==='[data-ui-key]'?n.dataset.uiKey:false))};
  activeDocument=document;document.body=new Element('body',all);document.body.connect(true);document.activeElement=document.body;
  const html=fs.readFileSync(path.join(root,'static/index.html'),'utf8');
  for(const match of html.matchAll(/<(\w+)\b([^>]*)>/g)){const [,tag,attrs]=match,id=attrs.match(/\bid="([^"]+)"/),command=attrs.match(/data-command="([^"]+)"/);if(id||command){const el=new Element(tag,all);el.connect(true);if(id){assert.ok(!ids[id[1]],'Duplicate ID '+id[1]);ids[id[1]]=el;el.id=id[1];}if(command)el.dataset.command=command[1];el.hidden=/\bhidden\b/.test(attrs);if(tag==='canvas')for(const dim of ['width','height']){const value=attrs.match(new RegExp('\\b'+dim+'="(\\d+)"'));if(value)el[dim]=Number(value[1]);}}}
  ids.build.value='Fractech Archivist';
  const Option=function(text,value){const n=new Element('option',all);n.textContent=text;n.value=value;return n;};
  const context={Option,document,Image:canvasModule?.Image||class{},sessionStorage:options.sessionStorage||new Storage(),localStorage:options.localStorage||new Storage(),fetch:(url,options)=>fetch(base+url,options),AbortSignal,Blob,URL,console,performance,setTimeout:(fn,ms)=>setTimeout(fn,Math.min(ms,10)),clearTimeout,setInterval:()=>0,requestAnimationFrame:()=>0,window:{addEventListener(){},matchMedia:()=>({matches:options.reducedMotion??true})}};
  context.window.sessionStorage=context.sessionStorage;context.window.localStorage=context.localStorage;vm.createContext(context);
  if(canvasModule)context.Image=class extends canvasModule.Image{set src(value){fetch(base+value).then(async r=>{if(!r.ok)throw Error('Image load '+value);const target=path.join(tmp,path.basename(value));fs.writeFileSync(target,Buffer.from(await r.arrayBuffer()));super.src=target;}).catch(e=>this.onerror?.(e));}get src(){return super.src;}};
  for(const file of ['ui.js','creator.js','lighting.js','material-visuals.js','art-direction.js','prefabs.js','animations.js','motion-visuals.js','audio.js','display.js','terrain.js','environment.js','weather.js','scene.js','survey.js','overworld.js','particulate.js','app.js']){vm.runInContext(fs.readFileSync(path.join(root,'static',file),'utf8'),context,{filename:file});for(const name of ['RoseUI','RoseCreator','RoseLighting','RoseMaterialVisuals','RoseArtDirection','RosePrefabs','RoseAnimations','RoseMotionVisuals','RoseAudio','RoseDisplay','RoseTerrain','RoseEnvironment','RoseWeather','RoseField','RoseSurvey','RoseWorld','RoseParticulate'])if(context.window[name])context[name]=context.window[name];}
 return {context,all,ids,document};
}

async function main(){
 await require('./ui-prefab-loading.cjs')();
 await require('./ui-audio.cjs')();
 require('./ui-display.cjs')(canvasModule);
 require('./ui-lighting.cjs')(canvasModule);
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'rose-ui-'));
 const bootstrap=`import sys,threading\nsys.path.insert(0,${JSON.stringify(root)})\nimport server as s\ns.world.secrets.randbelow=lambda n:n-1\ns.init_db(${JSON.stringify(path.join(tmp,'world.db'))})\nh=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler)\nthreading.Thread(target=s.run_clock,daemon=True).start()\nprint(h.server_port,flush=True)\nh.serve_forever()\n`;
 const host=spawn(process.env.PYTHON||'python3',['-c',bootstrap],{cwd:root});let errors='';host.stderr.on('data',b=>errors+=b);
 try{
  const port=await new Promise((resolve,reject)=>{host.stdout.once('data',b=>resolve(Number(String(b).trim())));host.once('error',reject);host.once('exit',code=>reject(Error('Host exited: '+code+' '+errors)));});
  const base=`http://127.0.0.1:${port}`;
  if(process.argv.includes('--direction')){await require('./ui-art-direction.cjs')({base,tmp,setupInterface,canvasModule,root});return;}
  if(process.argv.includes('--particles')){await require('./ui-particles.cjs')({base,tmp,setupInterface,canvasModule,root});return;}
  if(process.argv.includes('--materials')){await require('./ui-materials.cjs')({base,tmp,setupInterface,canvasModule,root});return;}
  if(process.argv.includes('--weather')){await require('./ui-weather.cjs')({base,tmp,setupInterface,canvasModule,root});return;}
  if(process.argv.includes('--animations')){await require('./ui-animations.cjs')({base,tmp,setupInterface,canvasModule,root});return;}
  const {context,all,ids,document}=setupInterface(base,tmp);
  for(const m of fs.readFileSync(path.join(root,'static/index.html'),'utf8').matchAll(/<script src="([^"]+)"/g)){const response=await fetch(base+m[1]);assert.ok(response.ok,'Host serves '+m[1]);assert.match(response.headers.get('content-type'),/javascript/);}
  const read=()=>vm.runInContext('state',context),get=id=>document.getElementById(id),command=text=>{const b=all.find(b=>b.dataset.command===text);if(b)return b.click();ids.prompt.value=text;return ids['action-form'].requestSubmit();};
  for(let i=0;i<100&&!context.RoseCreator.ready;i++)await new Promise(resolve=>setTimeout(resolve,10));assert.ok(context.RoseCreator.ready,'Character creator initialized');
  assert.equal(get('engine-fields').querySelectorAll('input').length,19);
  get('char-appearance').value='A repaired coat with rose seams';get('char-voice').value='Quiet, exact sentences';get('char-goal').value='Leave dependable public works';
  get('rule-generation-hostility').value=100;ids.name.value='Rose Explorer';ids.seed.value='ui-rose';await ids['join-form'].requestSubmit();
  assert.equal(ids.game.hidden,false,ids.error.textContent);assert.equal(read().engine_rules.generation.hostility,100);assert.equal(Object.keys(read().scene.tiles).length,127);assert.match(ids['field-mode'].textContent,/EXPLORATION/);
  assert.equal(ids['companion-candidates'].children.length,2);assert.ok(ids['character-sheet'].children.some(n=>n.textContent.includes('rose seams')));
  await ids.start.click();assert.equal(ids.start.hidden,true);
  if(canvasModule){let timer;try{await Promise.race([context.RosePrefabs.ready,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Indexed sprite bank did not finish loading')),15000);})]);}finally{clearTimeout(timer);}}
  if(canvasModule){assert.equal(context.RosePrefabs.style,'rendered','Fresh clients use the baked 3D style');assert.equal(context.RosePrefabs.loaded,144,'All prepared body, environment and monolith entries decoded');}
  require('./ui-visuals.cjs')({context,ids,read,canvasModule,root});
  await require('./ui-lighting.cjs').flow({context,ids,read,canvasModule});
  await require('./ui-monoliths.cjs')({context,ids,read,canvasModule,root,baseline:process.env.ROSE_MONOLITH_BASELINE});
  if(process.argv.includes('--monoliths'))return;
  await vm.runInContext('poll()',context);
  await require('./ui-terrain.cjs')({context,ids,read,canvasModule,root,baseline:process.env.ROSE_TERRAIN_BASELINE});
  if(process.argv.includes('--terrain'))return;
  if(process.env.ROSE_AUDIT_BASELINE)await require('./ui-fidelity-audit.cjs')({context,ids,read,canvasModule,root,baseline:process.env.ROSE_AUDIT_BASELINE});
  await require('./ui-environment.cjs')({context,ids,read,canvasModule,root});
  await ids['open-world'].click();assert.equal(ids['atlas-panel'].hidden,false);assert.equal(ids['rose-field'].hidden,true);
  const discovery=JSON.stringify(read().atlas.navigation.visited);await ids['world-cartography'].click();assert.equal(JSON.stringify(read().atlas.navigation.visited),discovery);
  ids['world-x'].value='-9.8';ids['world-y'].value='3.2';await ids['world-point-go'].click();
  // A short journey may finish during the HTTP response and native repaint.
  assert.ok(['traveling','arrived'].includes(read().atlas.navigation.status),ids.error.textContent||'Point travel must start or complete');
  for(let i=0;i<50&&read().atlas.navigation.status==='traveling';i++){await new Promise(resolve=>setTimeout(resolve,100));await vm.runInContext('poll()',context);}
  assert.equal(read().atlas.navigation.status,'arrived');assert.equal(read().atlas.position.join(','),'-9.8,3.2');assert.equal(ids['atlas-panel'].hidden,false);
  if(canvasModule){context.RoseWorld.draw(performance.now());fs.writeFileSync(path.join(root,'docs','Rose-world-preview.png'),ids['world-canvas'].bitmap.toBuffer('image/png'));}
  await ids['world-enter'].click();assert.equal(ids['rose-field'].hidden,false);assert.equal(ids['atlas-panel'].hidden,true);
  ids['art-style'].value='vector';ids['art-style'].onchange();assert.equal(context.RosePrefabs.style,'vector');ids['art-style'].value='raster';ids['art-style'].onchange();assert.equal(context.RosePrefabs.style,'raster');
  if(canvasModule){for(let i=0;i<200&&context.RosePrefabs.loaded<16;i++)await new Promise(resolve=>setTimeout(resolve,10));assert.equal(context.RosePrefabs.loaded,16,'Preserved material art has its own decoded bank');context.RoseField.draw(0);}
  ids['art-style'].value='rendered';ids['art-style'].onchange();assert.equal(context.RosePrefabs.style,'rendered');assert.equal(context.localStorage.getItem('rose-art-style'),'rendered');
  ids['art-style'].value='rendered-legacy';ids['art-style'].onchange();
  if(canvasModule){for(let i=0;i<200&&context.RosePrefabs.loaded<16;i++)await new Promise(resolve=>setTimeout(resolve,10));assert.equal(context.RosePrefabs.loaded,16,'Original 3D archive decoded independently');}
  assert.equal(context.RosePrefabs.style,'rendered-legacy');ids['art-style'].value='rendered';ids['art-style'].onchange();
  for(let i=0;i<2;i++){const b=within(ids['companion-candidates'],n=>n.tagName==='BUTTON'&&n.textContent.startsWith('RECRUIT'));assert.ok(b);await b.click();}
  assert.equal(ids['companion-count'].textContent,'2/2 ALONGSIDE',ids.error.textContent);
  for(let i=0;i<2;i++){const card=ids['companion-roster'].children[i],task=card.children.find(n=>n.tagName==='SELECT');task.value='guard';await within(card,n=>n.tagName==='BUTTON'&&n.textContent==='PROPOSE TASK').click();}
  await within(ids['companion-roster'].children[0],n=>n.tagName==='BUTTON'&&n.textContent==='LORE').click();assert.match(ids.result.textContent,/learned the everyday practices/);
  await require('./ui-interactions.cjs')({context,ids,read,canvasModule,phase:'exploration',root});
  const water=read().scene.infrastructure.nodes.find(n=>n.kind==='water');context.RoseField.select({type:'structure',id:water.id});await ids['walk-path'].click();
  assert.equal(read().scene.infrastructure.nodes.find(n=>n.id===water.id).adjacent,true,ids.error.textContent);
  const chosenButton=label=>within(ids['field-selection-actions'],n=>n.tagName==='BUTTON'&&n.textContent===label);
  await chosenButton('ACCEPT MAINTENANCE').click();assert.equal(read().me.contract.kind,'infrastructure',ids.error.textContent);
  for(let i=0;i<3&&read().scene.infrastructure.nodes.find(n=>n.id===water.id).condition<85;i++)await chosenButton('REPAIR / 1 SCRAP').click();
  await chosenButton('FULFILL MAINTENANCE').click();assert.equal(read().me.contract,null,ids.error.textContent);assert.match(ids.result.textContent,/maintenance record is accepted/);
  const pack=read().me.inventory.water;await chosenButton('DRAW ONE SUPPLY').click();assert.equal(read().me.inventory.water,pack+1,ids.error.textContent);
  const exchange=read().scene.infrastructure.nodes.find(n=>n.kind==='exchange');context.RoseField.select({type:'structure',id:exchange.id});await ids['walk-path'].click();assert.equal(read().scene.infrastructure.nodes.find(n=>n.id===exchange.id).adjacent,true);
  await within(ids['business-controls'],n=>n.tagName==='BUTTON'&&n.textContent.startsWith('BUY WATER')).click();assert.ok(ids['business-history'].children.some(n=>n.textContent.includes('bought water')),ids.error.textContent);
  await require('./ui-display.cjs').flow({context,ids,read,canvasModule});
  if(canvasModule){const destination=path.join(root,'docs','Rose-field-preview.png');fs.mkdirSync(path.dirname(destination),{recursive:true});context.RoseField.draw(performance.now());const png=ids['field-canvas'].bitmap.toBuffer('image/png');assert.ok(png.length>10000);fs.writeFileSync(destination,png);}
  await ids['export-engine'].click();const session=JSON.parse(context.sessionStorage.getItem('rose-session'));
  const blueprint=await fetch(base+'/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...session,op:'engine_export'})}).then(r=>r.json());assert.equal(blueprint.format,'Rose-infrastructure-blueprint');assert.ok(!JSON.stringify(blueprint).includes(session.token));
  ids.prompt.value='I become omnipotent';await ids['action-form'].requestSubmit();assert.equal(ids.prompt.value,'I become omnipotent');assert.match(ids.result.textContent,/could not map/);
  await command('north');assert.equal(read().me.pos.join(','),'-10,2',ids.error.textContent);assert.equal(ids['field-combat-controls'].hidden,false);
  await ids.engage.click();assert.match(ids['field-mode'].textContent,/COMBAT/);assert.equal(ids['end-turn'].hidden,false);
  await require('./ui-interactions.cjs')({context,ids,read,canvasModule,phase:'combat',root});
  await command('guard');assert.match(ids.result.textContent,/stance/);await ids['end-turn'].click();assert.match(ids['field-ap'].textContent,/YOUR AP/);
  await command('parley');assert.equal(read().scene.combat.active,false,ids.error.textContent);assert.match(ids['field-mode'].textContent,/EXPLORATION/);
  await command('remote survey');ids.prompt.value='hex 1,0';await ids['action-form'].requestSubmit();assert.match(ids.error.textContent,/Lower the remote/);assert.equal(ids.prompt.value,'hex 1,0');await command('return');
  await ids.pause.click();ids.prompt.value='wait';await ids['action-form'].requestSubmit();assert.match(ids.error.textContent,/paused/);await ids.pause.click();
  const position=read().me.pos.join(',');await ids.disconnect.click();assert.equal(ids.entry.hidden,false);await ids.resume.click();assert.equal(read().me.pos.join(','),position);assert.equal(ids['companion-count'].textContent,'2/2 ALONGSIDE');
  await require('./ui-assurance.cjs')({context,all,ids,document,read,get,command,base,tmp,setupInterface});
  if(!process.argv.includes('--core')){
   await require('./ui-art-direction.cjs')({base,tmp,setupInterface,canvasModule,root});
   await require('./ui-materials.cjs')({base,tmp,setupInterface,canvasModule,root});
   await require('./ui-weather.cjs')({base,tmp,setupInterface,canvasModule,root});
   await require('./ui-animations.cjs')({base,tmp,setupInterface,canvasModule,root});
   await require('./ui-particles.cjs')({base,tmp,setupInterface,canvasModule,root});
  }
  console.log('PASS: real HTTP + interface logic — continuous point travel, arrival/entry, cartography and discovery separation, indexed Blender sprite decoding, four isolated art styles, rules, two companions, physical approaches, maintenance, supply conservation, exchange, blueprint, combat/AP/parley, remote boundary, pause and resume.');
  console.log(canvasModule?'PASS: actual canvas renderer exported a 1000×620 PNG. Full browser layout is not tested.':'Native canvas unavailable; canvas drawing and full browser layout were not tested.');
 }finally{host.kill('SIGTERM');await new Promise(resolve=>host.once('exit',resolve));fs.rmSync(tmp,{recursive:true,force:true});}
}
if(process.argv.length===2)require('./ui-regression.cjs')().catch(e=>{console.error(e);process.exitCode=1;});
else main().catch(e=>{console.error(e);process.exitCode=1;});
