'use strict';
/* Prepared PBR scenery, with bounded RGB bounce/radiance for the 2D field.
   Original alpha masks remain authoritative for picking and occlusion. */
window.RoseLighting=(()=>{
 const modes=['signature','subdued','baked'],cache=new Map(),poolCache=new Map(),identities=new WeakMap();
 let profiles=null,mode='signature',serial=0,failed=false,poolFailed=false;
 const strength=()=>mode==='signature'?1:mode==='subdued'?.38:0;
 const linear=Array.from({length:256},(_,i)=>{const v=i/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
 const encode=v=>Math.round(255*(v<=.0031308?12.92*v:1.055*Math.max(0,v)**(1/2.4)-.055));
 function load(value){
  if(value?.schema!==1||!value.profiles)throw Error('Regional lighting data is unavailable.');
  for(const p of Object.values(value.profiles)){
   if(typeof p.name!=='string'||!Number.isFinite(p.radiance)||p.radiance<0||p.radiance>1)throw Error('Invalid regional lighting profile.');
   for(const k of ['primary','secondary','atmosphere','body_gain'])if(!Array.isArray(p[k])||p[k].length!==3||!p[k].every(n=>Number.isFinite(n)&&n>=0&&n<=(k==='body_gain'?2:1)))throw Error('Invalid regional lighting color.');
  }
  profiles=value.profiles;cache.clear();poolCache.clear();failed=false;poolFailed=false;
 }
 function configure(value){mode=modes.includes(value)?value:'signature';}
 function profile(region){return profiles?.[region]||null;}
 function powered(node,fixture){
  if(!node.enabled||node.condition<30)return false;
  if(fixture.portable)return true;
  return node.connected!==false&&!['offline','disconnected','power deficit'].includes(node.status);
 }
 function prepare(field,region,props,scale=1,optical=null,project=null){
  const p=profile(region),enabled=p&&strength()>0&&RosePrefabs.style==='rendered',emitters=[];
  if(enabled)for(const prop of props){
   if(prop.type!=='structure')continue;
   for(const fixture of RosePrefabs.practicals(prop.asset).slice(0,3)){
    if(!powered(prop.node,fixture)||!Array.isArray(fixture.offset)||fixture.offset.length!==2||!fixture.offset.every(Number.isFinite)||!Array.isArray(fixture.color)||fixture.color.length!==3||!fixture.color.every(v=>Number.isFinite(v)&&v>=0&&v<=1)||!Number.isFinite(fixture.radius)||fixture.radius<=0)continue;
    const intensity=Math.max(0,Math.min(1,fixture.intensity||0))*(prop.node.condition<50?.35:1)*p.radiance*strength();
    emitters.push({id:prop.node.id,pos:prop.pos,offset:fixture.offset,color:fixture.color,
     ground:[prop.screen[0]+fixture.offset[0]*scale,prop.screen[1]+3*scale],
     screen:[prop.screen[0]+fixture.offset[0]*scale,prop.screen[1]+fixture.offset[1]*scale],radius:Math.min(100,fixture.radius)*scale,intensity});
   }
  }
  if(enabled&&optical?.source_online&&Number.isFinite(optical.exposure)&&optical.exposure>0&&Array.isArray(optical.color)&&optical.color.length===3&&optical.color.every(v=>Number.isFinite(v)&&v>=0&&v<=1)){
   const prop=props.find(n=>n.type==='structure'&&n.node.id===optical.source_node);
   if(prop&&powered(prop.node,{portable:false}))emitters.push({id:prop.node.id,pos:prop.pos,offset:[0,-27],color:optical.color.map(v=>Math.round(v*16)/16),ground:[prop.screen[0],prop.screen[1]+3*scale],screen:[prop.screen[0],prop.screen[1]-27*scale],radius:80*scale,intensity:Math.min(1,optical.exposure*6)*strength()});
  }
  const blockers=project?Object.values(field.tiles).filter(t=>!t.passable&&Array.isArray(t.pos)).map(t=>({pos:t.pos,screen:project(t.pos,t.elevation||0),radius:34*scale*.60})):[];
  return{profile:p,region,field,emitters,scale,project,blockers,enabled:!!enabled};
 }
 function roundHex(q,r){let x=Math.round(q),z=Math.round(r),y=Math.round(-q-r);const dx=Math.abs(x-q),dy=Math.abs(y+q+r),dz=Math.abs(z-r);if(dx>dy&&dx>dz)x=-y-z;else if(dz>dy)z=-x-y;return[x,z];}
 function clearRay(field,start,end){
  const count=Math.ceil(Math.max(Math.abs(start[0]-end[0]),Math.abs(start[1]-end[1]),Math.abs(start[0]+start[1]-end[0]-end[1])));
  for(let i=1;i<count;i++){const t=i/count,pos=roundHex(start[0]+(end[0]-start[0])*t,start[1]+(end[1]-start[1])*t),tile=field.tiles[pos.join(',')];if(!tile||!tile.passable)return false;}
  return true;
 }
 function sample(prepared,pos,screen){
  if(!prepared.enabled)return null;
  let light=null,strongest=0,energy=0;const sum=[0,0,0];
  for(const emitter of prepared.emitters){
   const d=Math.hypot(screen[0]-emitter.ground[0],(screen[1]-emitter.ground[1])/.52),e=Math.max(0,1-d/emitter.radius)**2*emitter.intensity;
   if(e>0&&clearRay(prepared.field,emitter.pos,pos)){
    energy+=e;for(let channel=0;channel<3;channel++)sum[channel]+=emitter.color[channel]*e;
    if(e>strongest){strongest=e;light=emitter;}
   }
  }
  const level=Math.round(Math.min(1,energy)*4)/4,color=light&&level?sum.map(v=>Math.round(Math.min(1,v/energy)*16)/16):[0,0,0],direction=light&&level?Math.sign(light.screen[0]-screen[0]):0;
  return{region:prepared.region,gain:prepared.profile.body_gain,color,level,direction,amount:strength()};
 }
 function frame(f,light){
  if(!light||failed||strength()===0)return null;
  if(!identities.has(f.asset))identities.set(f.asset,++serial);
  const key=[identities.get(f.asset),f.frameIndex,light.region,light.amount,light.level,light.direction,...light.color].join(':');
  if(cache.has(key)){const result=cache.get(key);cache.delete(key);cache.set(key,result);return result;}
  try{
   const canvas=document.createElement('canvas');canvas.width=f.w;canvas.height=f.h;const c=canvas.getContext('2d',{willReadFrequently:true});
   if(!c)throw Error('Canvas lighting unavailable');
   c.drawImage(f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);const image=c.getImageData(0,0,f.w,f.h),data=image.data;
   for(let i=0;i<data.length;i+=4){
    // Preserve shadow-opacity slots and every alpha byte, including edge holes.
    if(data[i+3]<248||Math.max(data[i],data[i+1],data[i+2])<=8)continue;
    const luminance=.2126*linear[data[i]]+.7152*linear[data[i+1]]+.0722*linear[data[i+2]],x=(i/4)%f.w;
    const side=light.direction===0?1:.45+.55*(light.direction<0?1-x/f.w:x/f.w);
    for(let channel=0;channel<3;channel++){
     const gain=1+(light.gain[channel]-1)*light.amount;
     const bounce=light.color[channel]*light.level*.13*side*(.20+.80*luminance);
     data[i+channel]=Math.min(255,Math.max(0,encode(linear[data[i+channel]]*gain+bounce)));
    }
   }
   c.putImageData(image,0,0);cache.set(key,canvas);
   while(cache.size>64)cache.delete(cache.keys().next().value);
   return canvas;
  }catch{failed=true;cache.clear();return null;}
 }
 const rgba=(color,alpha)=>'rgba('+color.map(v=>Math.round(v*255)).join(',')+','+alpha+')';
 function poolImage(e,prepared){
  if(poolFailed)return null;
  const blockers=prepared.blockers.filter(b=>b.pos[0]!==e.pos[0]||b.pos[1]!==e.pos[1]),signature=JSON.stringify([e.ground,e.radius,e.color,e.intensity,blockers]);
  if(poolCache.has(signature)){const image=poolCache.get(signature);poolCache.delete(signature);poolCache.set(signature,image);return image;}
  try{
   const r=Math.ceil(e.radius),image=document.createElement('canvas');image.width=r*2+4;image.height=Math.ceil(r*2*.52)+4;const c=image.getContext('2d');if(!c)throw Error('Ground light canvas unavailable');
   c.save();c.translate(image.width/2,image.height/2);c.scale(1,.52);
   const g=c.createRadialGradient(0,0,1,0,0,e.radius);g.addColorStop(0,rgba(e.color,.28*e.intensity));g.addColorStop(.3,rgba(e.color,.13*e.intensity));g.addColorStop(1,rgba(e.color,0));c.fillStyle=g;c.fillRect(-r,-r,r*2,r*2);c.restore();c.save();
   // Circular ground footprints cast continuous tangent shadows. Neither the
   // pool nor its shadow is clipped to the host's movement-cell silhouettes.
   c.globalCompositeOperation='destination-out';c.fillStyle='#fff';
   for(const b of blockers){
    const x=b.screen[0]-e.ground[0],y=(b.screen[1]-e.ground[1])/.52,d=Math.hypot(x,y),br=b.radius;if(d-br>=r)continue;
    if(d<=br){c.fillRect(0,0,image.width,image.height);break;}
    const a=Math.atan2(y,x),offset=Math.asin(br/d),near=Math.sqrt(d*d-br*br),far=(r+br+2)/Math.cos(offset);
    c.beginPath();c.ellipse(image.width/2+x,image.height/2+y*.52,br,br*.52,0,0,Math.PI*2);c.fill();c.beginPath();
    const points=[[a-offset,near],[a-offset,far],[a+offset,far],[a+offset,near]];
    points.forEach(([angle,distance],i)=>{const px=image.width/2+Math.cos(angle)*distance,py=image.height/2+Math.sin(angle)*distance*.52;i?c.lineTo(px,py):c.moveTo(px,py);});c.closePath();c.fill();
   }
   c.restore();poolCache.set(signature,image);while(poolCache.size>32)poolCache.delete(poolCache.keys().next().value);return image;
  }catch{poolFailed=true;poolCache.clear();return null;}
 }
 function pools(c,prepared){
  if(!prepared.enabled)return;
  c.save();c.globalCompositeOperation='screen';
  for(const e of prepared.emitters){
   const image=poolImage(e,prepared);if(image)c.drawImage(image,e.ground[0]-image.width/2,e.ground[1]-image.height/2);
  }
  c.restore();
 }
 function glow(c,prop,prepared){
  if(!prepared.enabled)return;
  c.save();c.globalCompositeOperation='screen';
  for(const e of prepared.emitters.filter(e=>e.id===prop.node?.id)){
   const[x,y]=e.offset,r=13;const g=c.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,rgba(e.color,.38*e.intensity));g.addColorStop(.28,rgba(e.color,.12*e.intensity));g.addColorStop(1,rgba(e.color,0));
   c.fillStyle=g;c.fillRect(x-r,y-r,r*2,r*2);
  }
  c.restore();
 }
 return{load,configure,profile,prepare,sample,frame,pools,glow,clearRay,powered,
  get mode(){return mode;},get ready(){return !!profiles;},get available(){return !failed;},get cachedFrames(){return cache.size;},get cachedPools(){return poolCache.size;}};
})();
