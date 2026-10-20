'use strict';
/* Prepared surface response. Pixel alpha, edge anchors and world geometry stay fixed. */
window.RoseWeather=(()=>{
 const cache=new Map(),sources=new Map(),ids=new WeakMap();let serial=0,identity=null,snapshot=null,origin=0,freeze=null,disabled=false;
 const clamp=(v,lo=0,hi=1)=>Math.max(lo,Math.min(hi,Number.isFinite(v)?v:lo));
 const id=value=>{if(!ids.has(value))ids.set(value,++serial);return ids.get(value);};
 function retain(map,key,value,limit){map.set(key,value);while(map.size>limit)map.delete(map.keys().next().value);return value;}
 function reset(){cache.clear();sources.clear();identity=null;snapshot=null;origin=0;freeze=null;disabled=false;}
 function hidden(value){return !value||value.me?.remote||!!value.particles?.percept?.address;}
 function read(value,now=performance.now()){
  const next=value?.scene?`${value.code}:${value.me.id}:${value.scene.id}`:null;
  if(next!==identity){reset();identity=next;origin=now;}
  const held=!value?.started||value.paused||value.clock_held||hidden(value);
  if(held&&freeze===null)freeze=now;
  if(!held&&freeze!==null){origin+=now-freeze;freeze=null;}
  snapshot=value;
 }
 function sample(prop,now=performance.now()){
  if(hidden(snapshot)||!snapshot?.scene?.weather||prop.type==='unit')return null;
  const obj=prop.node||prop.tile,s=obj?.surface_view,weather=snapshot.scene.weather;
  if(!s||prop.pose==='ruined'||obj?.material_state?.destroyed)return null;
  const direction=Number.isInteger(weather.direction)&&weather.direction>=0&&weather.direction<6?weather.direction:0;
  const time=Math.max(0,(freeze??now)-origin),phase=clamp(s.phase)*Math.PI*2+time*.0038;
  const strength=clamp(weather.strength),restraint=clamp(s.restraint),wet=clamp(s.wetness),dust=clamp(s.dust);
  // Only the documented fabric refuge has a registered interior cloth patch.
  const cloth=prop.type==='structure'&&obj.kind==='shelter'&&s.fabric&&prop.pose!=='fractured';
  const amplitude=cloth&&!RoseAnimations.reduced?strength*(1.7-restraint*.85)*(1-wet*.25):0;
  return{wet,dust,phase,amplitude,direction,cloth};
 }
 function raw(f){
  const key=id(f.asset)+':'+f.frameIndex;
  if(sources.has(key))return sources.get(key);
  const canvas=document.createElement('canvas');canvas.width=f.w;canvas.height=f.h;
  const c=canvas.getContext('2d');c.drawImage(f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);
  return retain(sources,key,c.getImageData(0,0,f.w,f.h),12);
 }
 function frame(f,prop,now=performance.now()){
  const response=sample(prop,now);if(!f||!response||disabled)return f;
  const wet=Math.round(response.wet*16)/16,dust=Math.round(response.dust*16)/16;
  const patch=response.cloth&&f.w===288&&f.h===336&&/shelter-aethergale(?:-tone[12])?-v6\.png$/.test(f.asset.image||'');
  const amplitude=patch?Math.round(response.amplitude*4)/4:0;
  const phase=amplitude?Math.round((response.phase%(Math.PI*2))/(Math.PI*2)*16)%16:0;
  if(!wet&&!dust&&!amplitude)return f;
  const key=[id(f.asset),f.frameIndex,wet,dust,amplitude,phase,response.direction].join(':');
  if(cache.has(key))return cache.get(key);
  try{
   const source=raw(f),image=document.createElement('canvas');image.width=f.w;image.height=f.h;const c=image.getContext('2d'),output=c.createImageData(f.w,f.h),src=source.data,dst=output.data;
   dst.set(src);const angle=response.direction*Math.PI/3,p=phase/16*Math.PI*2,amp=amplitude/f.scale;
   // The three vertices sit inside the front cloth panel of the existing
   // AETHER refuge sprite. A cubic barycentric weight pins all three edges.
   const A=[156,172],B=[182,210],C=[159,218],den=(B[1]-C[1])*(A[0]-C[0])+(C[0]-B[0])*(A[1]-C[1]);
   for(let y=0;y<f.h;y++)for(let x=0;x<f.w;x++){
    const i=(y*f.w+x)*4;if(src[i+3]<248)continue;
    let from=i,bend=1;
    if(amplitude&&x>=156&&x<=182&&y>=172&&y<=218){
     const a=((B[1]-C[1])*(x-C[0])+(C[0]-B[0])*(y-C[1]))/den,b=((C[1]-A[1])*(x-C[0])+(A[0]-C[0])*(y-C[1]))/den,d=1-a-b;
     if(a>0&&b>0&&d>0){
      const weight=(27*a*b*d)**2,wave=Math.sin(p+(y-172)*.16),dx=amp*weight*wave*Math.cos(angle),dy=amp*weight*wave*Math.sin(angle)*.35;
      const sx=Math.round(clamp(x-dx,156,182)),sy=Math.round(clamp(y-dy,172,218)),j=(sy*f.w+sx)*4;
      if(src[j+3]>=248)from=j;bend=1+weight*Math.cos(p+(y-172)*.16)*amplitude*.035;
     }
    }
    const red=src[from],green=src[from+1],blue=src[from+2],emissive=Math.max(red,green,blue)>120&&Math.max(red,green,blue)-Math.min(red,green,blue)>75;
    if(emissive)continue;
    const shadow=1-wet*.17,grain=.75+((x*13+y*7)%17)/34,deposit=dust*.20*grain;
    for(let n=0;n<3;n++)dst[i+n]=Math.round(clamp(src[from+n]*shadow*bend*(1-deposit)+[156,135,101][n]*deposit,0,255));
    // Alpha is copied from the destination, so drawing, picking, occlusion,
    // contact registration and object bounds use the identical silhouette.
   }
   c.putImageData(output,0,0);
   return retain(cache,key,{...f,asset:{...f.asset,weather_frame:true},image,x:0,y:0},32);
  }catch{disabled=true;return f;}
 }
 return{read,reset,sample,frame,get cached(){return cache.size;},get sourceCount(){return sources.size;},get available(){return !disabled;}};
})();
