'use strict';
/* Condition frames derived from actual prepared surfaces; one shared hit image. */
window.RoseMaterialVisuals=(()=>{
 const cache=new Map(),identities=new WeakMap();let serial=0,failed=false;
 function frame(f,pose){
  const weathered=pose==='worn'&&f&&!f.asset.clips?.worn;
  if(!f||!weathered&&!['fractured','ruined'].includes(pose)||failed)return f;
  if(!identities.has(f.asset))identities.set(f.asset,++serial);
  const key=identities.get(f.asset)+':'+f.frameIndex+':'+pose;
  if(cache.has(key)){const v=cache.get(key);cache.delete(key);cache.set(key,v);return v;}
  try{
   const source=document.createElement('canvas');source.width=f.w;source.height=f.h;const s=source.getContext('2d',{willReadFrequently:true});s.imageSmoothingEnabled=false;s.drawImage(f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);
   const rgba=s.getImageData(0,0,f.w,f.h).data;let l=f.w,t=f.h,r=0,b=0;
   for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]>=248){const x=i/4%f.w,y=Math.floor(i/4/f.w);l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);}
   let seed=2166136261;for(const ch of (f.asset.image||'prepared')+pose)seed=Math.imul(seed^ch.charCodeAt(0),16777619)>>>0;
   const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
   let image=source,anchor=f.anchor,w=f.w,h=f.h;
   if(weathered){
    s.save();s.globalCompositeOperation='source-atop';s.fillStyle='#887f4c30';s.fillRect(l,t,r-l+1,b-t+1);s.strokeStyle='#49443950';s.lineWidth=1;
    for(let n=0;n<14;n++){const x=l+(r-l)*random(),y=t+(b-t)*random();s.beginPath();s.moveTo(x,y);s.lineTo(x+2,y+5+random()*8);s.stroke();}s.restore();
   }else if(pose==='fractured'){
    s.save();s.globalCompositeOperation='destination-out';s.strokeStyle='#fff';
    for(let n=0;n<10;n++){const x=l+(r-l)*random(),y=t+(b-t)*random(),length=8+(b-t)*.14*random();s.lineWidth=1+random()*2;s.beginPath();s.moveTo(x,y);s.lineTo(x+3,y+length*.45);s.lineTo(x-4,y+length*.7);s.lineTo(x+1,y+length);s.stroke();}s.restore();
   }else{
    w=144;h=100;anchor=[72,78];image=document.createElement('canvas');image.width=w;image.height=h;const c=image.getContext('2d');c.imageSmoothingEnabled=false;
    c.fillStyle='#0005';c.beginPath();c.ellipse(72,80,36,12,0,0,Math.PI*2);c.fill();
    const pieces=[];for(let n=0;n<36;n++){
     let x,y,valid=false;for(let attempt=0;attempt<60;attempt++){x=Math.floor(l+(r-l)*random());y=Math.floor(t+(b-t)*random());if(rgba[(y*f.w+x)*4+3]>=248){valid=true;break;}}if(!valid)continue;
     const angle=random()*Math.PI*2,rad=Math.sqrt(random()),dx=Math.cos(angle)*rad*30,dy=Math.sin(angle)*rad*10;
     pieces.push({x,y,dx,dy,width:8+random()*14,height:6+random()*10,angle:(random()-.5)*1.2});
    }
    for(const p of pieces.sort((a,b)=>a.dy-b.dy)){
     c.save();c.translate(72+p.dx,75+p.dy-Math.max(0,1-Math.hypot(p.dx/30,p.dy/10))*10);c.rotate(p.angle);
     c.beginPath();c.moveTo(-p.width/2,-p.height/2);c.lineTo(p.width*.4,-p.height*.4);c.lineTo(p.width/2,p.height*.2);c.lineTo(-p.width*.35,p.height/2);c.closePath();c.clip();c.drawImage(source,p.x-8,p.y-6,16,12,-p.width/2,-p.height/2,p.width,p.height);c.restore();
    }
   }
   const asset={...f.asset,pick_alpha_min:248,material_pose:pose},value={...f,asset,image,x:0,y:0,w,h,anchor};
   cache.set(key,value);while(cache.size>32)cache.delete(cache.keys().next().value);return value;
  }catch{failed=true;cache.clear();return f;}
 }
 return{frame,get cached(){return cache.size;},get available(){return !failed;}};
})();
