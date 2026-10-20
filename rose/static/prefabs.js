'use strict';
/* Original Blender renders, preserved material prefabs, and original vectors. */
window.RosePrefabs=(()=>{
 const frames={
  idle:[{bob:0,leg:0,arm:0},{bob:-1,leg:0,arm:0},{bob:0,leg:0,arm:0},{bob:1,leg:0,arm:0}],
  walk:[{bob:0,leg:-5,arm:4},{bob:-2,leg:-3,arm:2},{bob:0,leg:0,arm:0},{bob:0,leg:5,arm:-4},{bob:-2,leg:3,arm:-2},{bob:0,leg:0,arm:0}],
  attack:[{bob:0,leg:2,arm:-8},{bob:-2,leg:4,arm:14},{bob:0,leg:1,arm:4}],
  guard:[{bob:1,leg:3,arm:-3}],work:[{bob:2,leg:1,arm:2},{bob:4,leg:1,arm:9},{bob:2,leg:1,arm:5},{bob:0,leg:1,arm:0}],
  talk:[{bob:0,leg:0,arm:4},{bob:0,leg:0,arm:1}],hit:[{bob:3,leg:2,arm:-5},{bob:1,leg:0,arm:0}],down:[{bob:0,leg:0,arm:0}]
 };
 const banks=new Map();
 const poly=(c,points,fill,stroke)=>{c.beginPath();points.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.stroke();}};
 function box(c,width,depth,height,color){poly(c,[[-width/2,0],[0,depth/2],[0,depth/2-height],[-width/2,-height]],'#46524e','#718178');poly(c,[[0,depth/2],[width/2,0],[width/2,-height],[0,depth/2-height]],'#263c38','#718178');poly(c,[[-width/2,-height],[0,-depth/2-height],[width/2,-height],[0,depth/2-height]],color,'#96a89b');}
 function shadow(c,w=22){c.fillStyle='#0007';c.beginPath();c.ellipse(0,3,w,w*.34,0,0,Math.PI*2);c.fill();}
 let style='rendered';const cache=new Map(),imageQueue=[],bank=()=>banks.get(style==='vector'?'raster':style);let activeImages=0;
 function startImages(){while(activeImages<6&&imageQueue.length){activeImages++;imageQueue.shift()();}}
 function imageFor(url){if(!cache.has(url))cache.set(url,new Promise((resolve,reject)=>{
  imageQueue.push(()=>{const img=new Image();let finished=false;const finish=error=>{if(finished)return;finished=true;activeImages--;if(error)reject(Error('Unable to load '+url));else resolve(img);startImages();};img.onload=()=>finish();img.onerror=()=>finish(true);try{img.src=url;}catch{finish(true);}});
 }));startImages();return cache.get(url);}
 function load(value){const target=['rendered','rendered-legacy'].includes(value.style)?value.style:'raster',data={manifest:value,sprites:new Map(),ready:null},pending=[];banks.set(target,data);for(const[key,asset]of Object.entries(value.assets||{})){if(!['sprite','texture'].includes(asset.kind))continue;const urls=asset.images||[asset.image];if(!urls.every(url=>/^\/art\/[\w.-]+\.(png|webp)$/.test(url||'')))continue;
   pending.push(Promise.all(urls.map(imageFor)).then(imgs=>data.sprites.set(key,{imgs,asset})));}data.ready=Promise.all(pending);return data.ready;}
 function rawFrameInfo(key,pose,time,facing=0){const active=bank(),data=active?.sprites.get(key);if(style==='vector'||!data)return null;const manifest=active.manifest,{imgs,asset}=data,animation=manifest.animations[pose]||manifest.animations.idle,clip=asset.clips?.[`${pose}_${facing}`]||asset.clips?.[pose]||asset.clips?.[`idle_${facing}`]||asset.clips?.idle;
  if(!clip?.length||!asset.frames?.length)return null;const index=animation.loop?Math.floor(time/animation.frame_ms)%clip.length:Math.min(clip.length-1,Math.floor(time/animation.frame_ms)),frameIndex=clip[index],frame=asset.frames[frameIndex];if(!Array.isArray(frame)||![4,5].includes(frame.length))return null;
  const[x,y,w,h,sheet=0]=frame,anchor=asset.anchors?.[frameIndex]||asset.anchor||[w/2,h],scale=asset.scales?.[frameIndex]||Number(asset.scale)||1;return{asset,image:imgs[sheet],x,y,w,h,anchor,scale,frameIndex};
 }
 const associations=new Map(),assetIds=new WeakMap();let assetSerial=0,associationFailed=false;
 function assetId(asset){if(!assetIds.has(asset))assetIds.set(asset,++assetSerial);return assetIds.get(asset);}
 function composedFrameInfo(key,pose,time,facing=0){
  const registeredPose=['fractured','ruined'].includes(pose)?'worn':pose;
  const base=rawFrameInfo(key,registeredPose,time,facing);if(!base||style!=='rendered'||!base.asset.monolith_core||associationFailed)return base;
  const core=rawFrameInfo(base.asset.monolith_core,registeredPose,time);if(!core)return base;
  const signature=[assetId(base.asset),base.frameIndex,assetId(core.asset),core.frameIndex].join(':');
  if(associations.has(signature)){const value=associations.get(signature);associations.delete(signature);associations.set(signature,value);return value;}
  try{
   const ratio=core.scale/base.scale,left=Math.floor(Math.min(-base.anchor[0],-core.anchor[0]*ratio)),top=Math.floor(Math.min(-base.anchor[1],-core.anchor[1]*ratio));
   const w=Math.ceil(Math.max(base.w-base.anchor[0],(core.w-core.anchor[0])*ratio))-left,h=Math.ceil(Math.max(base.h-base.anchor[1],(core.h-core.anchor[1])*ratio))-top;
   const image=document.createElement('canvas');image.width=w;image.height=h;const c=image.getContext('2d');if(!c)throw Error('Monolith composition unavailable');c.imageSmoothingEnabled=false;
   c.drawImage(core.image,core.x,core.y,core.w,core.h,-core.anchor[0]*ratio-left,-core.anchor[1]*ratio-top,core.w*ratio,core.h*ratio);
   c.drawImage(base.image,base.x,base.y,base.w,base.h,-base.anchor[0]-left,-base.anchor[1]-top,base.w,base.h);
   const asset={...base.asset,pick_alpha_min:248,source_asset:base.asset,core_asset:core.asset},value={...base,asset,image,x:0,y:0,w,h,anchor:[-left,-top],association:true};
   associations.set(signature,value);while(associations.size>24)associations.delete(associations.keys().next().value);return value;
  }catch{associationFailed=true;associations.clear();return base;}
 }
 function frameInfo(key,pose,time,facing=0){const f=composedFrameInfo(key,pose,time,facing);return typeof RoseMaterialVisuals!=='undefined'?RoseMaterialVisuals.frame(f,pose):f;}
 function drawFrame(c,f,light=null){if(!f)return false;c.imageSmoothingEnabled=false;const lit=style==='rendered'&&typeof RoseLighting!=='undefined'?RoseLighting.frame(f,light):null;c.drawImage(lit||f.image,lit?0:f.x,lit?0:f.y,f.w,f.h,-f.anchor[0]*f.scale,-f.anchor[1]*f.scale,f.w*f.scale,f.h*f.scale);return true;}
 function sprite(c,key,pose,time,facing=0,light=null,prepared=null){return drawFrame(c,prepared||frameInfo(key,pose,time,facing),light);}
 function assetFor(subject,fallback=subject.kind){const key=subject.visual?.model,tone=subject.visual?.tone||0,active=bank();if(style==='rendered'&&key){const toned=key+'_tone'+tone;if(active?.sprites.has(toned))return toned;if(active?.sprites.has(key))return key;}return fallback;}
 const materialPose=obj=>obj.material_state?.destroyed||obj.condition===0?'ruined':obj.condition<30?'fractured':obj.condition<60?'worn':'idle';
 const structurePose=node=>materialPose(node)==='ruined'?'ruined':node.condition<30?'fractured':node.condition<60||!node.enabled||node.connected===false||(node.kind==='garden'&&(node.growth<20||node.moisture<20))||['offline','disconnected','power deficit','cultivation input deficit'].includes(node.status)?'worn':'idle';
 const masks=new WeakMap();let maskCanvas=null;
 function mask(f){let frames=masks.get(f.asset);if(!frames){frames=new Map();masks.set(f.asset,frames);}if(frames.has(f.frameIndex))return frames.get(f.frameIndex);let result=null;
  try{maskCanvas??=document.createElement('canvas');maskCanvas.width=f.w;maskCanvas.height=f.h;const c=maskCanvas.getContext('2d',{willReadFrequently:true});c.clearRect(0,0,f.w,f.h);c.drawImage(f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);const rgba=c.getImageData(0,0,f.w,f.h).data,alpha=new Uint8Array(f.w*f.h),threshold=f.asset.pick_alpha_min||48;let left=f.w,top=f.h,right=-1,bottom=-1;for(let i=0;i<alpha.length;i++){alpha[i]=rgba[i*4+3];if(alpha[i]>=threshold){const x=i%f.w,y=Math.floor(i/f.w);left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}}result={alpha,box:[left,top,right-left+1,bottom-top+1]};}catch{}frames.set(f.frameIndex,result);return result;
 }
 function fallbackBounds(key){return key==='power'?[-24,-85,48,94]:key==='relay'?[-24,-76,48,92]:key==='water'?[-30,-52,65,67]:key==='garden'?[-34,-30,68,49]:key==='shelter'?[-36,-59,72,82]:['exchange','workshop'].includes(key)?[-37,-53,76,74]:key==='rock'?[-31,-39,64,54]:key==='threat'?[-29,-48,58,64]:[-29,-59,58,69];}
 function boundsFrame(f){const b=mask(f)?.box||[0,0,f.w,f.h];return[(b[0]-f.anchor[0])*f.scale,(b[1]-f.anchor[1])*f.scale,b[2]*f.scale,b[3]*f.scale];}
 function bounds(key,pose='idle',time=0,facing=0){const f=frameInfo(key,pose,time,facing);return f?boundsFrame(f):pose==='ruined'?[-29,-15,58,27]:fallbackBounds(key);}
 function hitFrame(f,point){
  const x=Math.floor(point[0]/f.scale+f.anchor[0]),y=Math.floor(point[1]/f.scale+f.anchor[1]);if(x<0||y<0||x>=f.w||y>=f.h)return false;const m=mask(f);return m?m.alpha[y*f.w+x]>=(f.asset.pick_alpha_min||48):true;
 }
 function hit(key,point,pose='idle',time=0,facing=0){const f=frameInfo(key,pose,time,facing);if(f)return hitFrame(f,point);const[x,y,w,h]=bounds(key,pose,time,facing);return point[0]>=x&&point[0]<x+w&&point[1]>=y&&point[1]<y+h;}
 function person(c,unit,pose,time,palette){
  const sequence=frames[pose]||frames.idle,loop=['idle','walk','work','talk','guard'].includes(pose),ms=bank()?.manifest?.animations?.[pose]?.frame_ms||150,index=loop?Math.floor(time/ms)%sequence.length:Math.min(sequence.length-1,Math.floor(time/ms));const f=sequence[index];
  shadow(c,14);c.save();if(unit.facing===3||unit.facing===4)c.scale(-1,1);
  if(pose==='down'||unit.health<=0){poly(c,[[-21,-6],[16,-8],[24,0],[-17,5]],'#655857','#9e9388');c.restore();return;}
  c.translate(0,f.bob);const coat=unit.mine?'#cb9aa7':unit.kind==='companion'?'#8aac8e':unit.kind==='npc'?'#9c9e85':'#809390';
  c.lineWidth=5;c.strokeStyle='#1a2323';c.beginPath();c.moveTo(-5,-17);c.lineTo(-6+f.leg,-2);c.moveTo(5,-17);c.lineTo(6-f.leg,-2);c.stroke();
  poly(c,[[-10,-35],[8,-36],[12,-16],[-13,-17]],coat,'#d0cec1');poly(c,[[-9,-31],[1,-32],[1,-15],[-12,-17]],'#0003');
  c.fillStyle='#c5ae95';c.beginPath();c.ellipse(0,-45,7,9,0,0,Math.PI*2);c.fill();poly(c,[[-8,-49],[-4,-55],[7,-53],[9,-45],[4,-46],[-6,-45]],'#343b3b','#6c7d73');
  c.strokeStyle='#d2b89a';c.lineWidth=3;c.beginPath();c.moveTo(-8,-32);c.lineTo(-14-f.arm*.2,-21);c.moveTo(8,-32);c.lineTo(13+f.arm,-24-f.arm*.4);c.stroke();
  c.strokeStyle=palette.accent;c.lineWidth=2;c.beginPath();c.moveTo(14+f.arm,-27-f.arm*.4);c.lineTo(18+f.arm,-4-f.arm*.4);c.stroke();
  c.fillStyle='#263732';c.fillRect(-10,-28,5,8);c.fillStyle='#d1be83';c.fillRect(-9,-23,3,2);c.restore();
 }
 function construct(c,unit,time,palette){shadow(c,22);if(unit.health<=0){poly(c,[[-25,-10],[13,-17],[28,-5],[4,3]],'#403e3e','#7d8275');return;}c.strokeStyle='#738080';c.lineWidth=4;for(const[x,y]of [[-22,0],[19,1],[4,9]]){c.beginPath();c.moveTo(x*.5,-24);c.lineTo(x,y-4);c.stroke();}box(c,32,20,30,'#71827b');c.fillStyle=unit.resolved?palette.accent:'#dc9978';c.fillRect(3,-25,7,4);c.strokeStyle='#b6b8a0';c.lineWidth=2;c.beginPath();c.moveTo(-6,-30);c.lineTo(-6,-43);c.lineTo(9,-44);c.stroke();}
 function structure(c,node,time,palette,prepared=null){
  const key=assetFor(node),pose=structurePose(node);if(style!=='rendered'||!frameInfo(key,pose,time))shadow(c,33);if(sprite(c,key,pose,time,0,null,prepared))return;const off=!node.enabled||node.condition<30,accent=off?'#85736b':palette.accent;
  if(pose==='ruined'){rubble(c,palette);return;}
  if(node.kind==='power'){box(c,30,18,17,'#63786b');c.fillStyle='#78857d';c.fillRect(-3,-65,6,49);c.strokeStyle='#b4c4ae';c.lineWidth=3;const blades=[[[0,-84],[0,-50]],[[-17,-67],[17,-67]],[[ -12,-79],[12,-55]],[[ -12,-55],[12,-79]]][Math.floor(time/320)%4];c.beginPath();blades.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.stroke();c.fillStyle=accent;c.beginPath();c.arc(0,-67,4,0,Math.PI*2);c.fill();}
  else if(node.kind==='water'){box(c,44,24,7,'#5a7873');c.fillStyle='#637f7c';c.fillRect(-18,-39,36,31);c.beginPath();c.ellipse(0,-8,18,8,0,0,Math.PI);c.fill();c.fillStyle='#aac1b4';c.beginPath();c.ellipse(0,-39,18,8,0,0,Math.PI*2);c.fill();c.strokeStyle='#213c3b';c.lineWidth=3;c.beginPath();c.moveTo(12,-25);c.lineTo(24,-19);c.lineTo(24,-9);c.stroke();c.fillStyle=accent;c.fillRect(-10,-30,4,15);}
  else if(node.kind==='garden'){box(c,62,35,7,'#52573c');for(let i=0;i<6;i++){const x=(i%3)*16-17,y=Math.floor(i/3)*9-7;poly(c,[[x,y-10],[x-5,y-19],[x+1,y-13],[x+6,y-23],[x+5,y-9]],off?'#79734e':'#94a772','#b1bd85');}}
  else if(node.kind==='shelter'){box(c,57,32,23,'#667868');poly(c,[[-34,-22],[-5,-57],[34,-24],[0,-8]],'#827f68','#c7c3a4');poly(c,[[-5,-57],[34,-24],[12,-14]],'#655b50');c.fillStyle='#182b28';c.fillRect(-11,-24,13,20);c.strokeStyle=accent;c.lineWidth=2;c.beginPath();c.moveTo(-5,-57);c.lineTo(-35,-21);c.stroke();}
  else if(node.kind==='relay'){box(c,32,20,15,'#64786d');c.fillStyle='#a0b3a5';c.fillRect(-2,-72,4,58);c.strokeStyle='#b0c3b3';c.beginPath();c.moveTo(-19,-64);c.lineTo(20,-73);c.moveTo(-15,-58);c.lineTo(15,-65);c.stroke();c.fillStyle=accent;c.fillRect(6,-27,4,5);}
  else{box(c,58,32,30,node.kind==='exchange'?'#9b8d6e':'#758882');c.fillStyle='#192b28';c.fillRect(4,-23,13,20);c.fillStyle=accent;c.fillRect(8,-25,8,3);box(c,23,14,12,'#717267');if(node.kind==='workshop'){c.strokeStyle='#c7b697';c.lineWidth=3;c.beginPath();c.moveTo(-13,-42);c.lineTo(8,-50);c.stroke();}else{poly(c,[[-30,-28],[0,-44],[31,-29],[0,-12]],'#a0936c','#d7c797');}}
  if(node.condition<50){c.strokeStyle='#342526';c.lineWidth=2;c.beginPath();c.moveTo(-8,-20);c.lineTo(1,-13);c.lineTo(-3,-8);c.stroke();}
 }
 function rubble(c,palette){for(let i=0;i<12;i++){const x=((i*17)%49)-24,y=((i*7)%13)-5;poly(c,[[x-4,y+3],[x-5,y-4],[x+1,y-10],[x+5,y-3],[x+3,y+4]],i%2?'#505d56':'#778074',palette.accent+'66');}}
 function rock(c,palette,tile={},prepared=null){const key=assetFor(tile,'rock'),pose=materialPose(tile);if(style!=='rendered'||!frameInfo(key,pose,0))shadow(c,26);if(sprite(c,key,pose,0,0,null,prepared))return;if(pose==='ruined'){rubble(c,palette);return;}poly(c,[[-27,-3],[-20,-25],[-3,-38],[24,-19],[29,1],[2,10]],'#657064','#889282');poly(c,[[-3,-38],[24,-19],[2,10],[-1,-9]],'#454f48');poly(c,[[-27,-3],[-20,-25],[-1,-9],[2,10]],'#788075');if(pose==='fractured'){c.strokeStyle='#26312b';c.lineWidth=2;c.beginPath();c.moveTo(0,-32);c.lineTo(4,-19);c.lineTo(-4,-10);c.lineTo(2,3);c.stroke();}}
 function unit(c,unit,pose,time,palette,light=null,prepared=null){const key=assetFor(unit),bodyPose=unit.health<=0&&!prepared?'down':pose,facing=unit.facing||0;if(style!=='rendered'||!frameInfo(key,bodyPose,time,facing))shadow(c,14);c.strokeStyle=unit.mine?'#e3aabd':unit.kind==='companion'?'#a5cda4':unit.kind==='threat'&&!unit.resolved?'#e78c78':'#8eaa9f';c.lineWidth=1.4;c.beginPath();c.ellipse(0,3,17,6,0,0,Math.PI*2);c.stroke();if(sprite(c,key,bodyPose,time,facing,light,prepared))return;if(unit.kind==='threat')construct(c,unit,time,palette);else person(c,unit,pose,time,palette);}
 const patterns=new WeakMap();
 function surface(c,key,bounds){const data=bank()?.sprites.get(key);if(style==='vector'||!data)return false;const[x,y,w,h]=data.asset.frames[0];c.imageSmoothingEnabled=false;if(style.startsWith('rendered')&&c.createPattern){let cached=patterns.get(c);if(!cached){cached=new WeakMap();patterns.set(c,cached);}let pattern=cached.get(data);if(!pattern){pattern=c.createPattern(data.imgs[0],'repeat');if(pattern){const s=data.asset.scale||1;pattern.setTransform?.({a:s,b:0,c:0,d:s,e:0,f:0});cached.set(data,pattern);}}if(pattern){c.save();c.translate(bounds[0],bounds[1]);c.fillStyle=pattern;c.fillRect(0,0,bounds[2],bounds[3]);c.restore();return true;}}c.drawImage(data.imgs[0],x,y,w,h,...bounds);return true;}
 const ground=(c,region,bounds)=>surface(c,'ground_'+region,bounds),path=(c,region,bounds)=>surface(c,'ground_path_'+region,bounds);
 return {load,structure,unit,rock,ground,path,frames,hit,bounds,hitFrame,boundsFrame,drawFrame,assetFor,structurePose,materialPose,frameInfo,clipDuration:pose=>{const a=bank()?.manifest?.animations?.[pose];return a?a.frames*a.frame_ms:(frames[pose]?.length||1)*150;},practicals:key=>bank()?.sprites.get(key)?.asset.practicals||[],setStyle:value=>{style=['rendered','rendered-legacy','raster','vector'].includes(value)?value:'rendered';},get style(){return style;},get ready(){return bank()?.ready||Promise.resolve();},get loaded(){return bank()?.sprites.size||0;},get cachedAssociations(){return associations.size;},get associationsAvailable(){return !associationFailed;}};
})();
