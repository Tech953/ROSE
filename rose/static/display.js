'use strict';
/* A restrained CRT-inspired presentation pass. Simulation and picking stay native. */
window.RoseDisplay=(()=>{
 let enabled=true,profile='soft',sample=null,glow=null,failed=false;
 const profiles=['soft','sharp'];
 function configure(on,value){enabled=!!on;profile=profiles.includes(value)?value:'soft';}
 function buffer(current,width,height){
  current??=document.createElement('canvas');
  if(current.width!==width)current.width=width;
  if(current.height!==height)current.height=height;
  return current;
 }
 function present(ctx,width,height){
  if(!enabled||profile==='sharp'||failed)return false;
  try{
   // Preserve finer material detail while retaining the restrained phosphor pass.
   const w=Math.min(800,width),h=Math.max(1,Math.round(height*w/width));
   sample=buffer(sample,w,h);const s=sample.getContext('2d');
   if(!s)throw Error('Canvas sampling unavailable');
   s.imageSmoothingEnabled=true;s.clearRect(0,0,w,h);s.drawImage(ctx.canvas,0,0,width,height,0,0,w,h);
   glow=buffer(glow,Math.max(1,Math.round(w/4)),Math.max(1,Math.round(h/4)));const g=glow.getContext('2d');
   if(!g)throw Error('Canvas glow unavailable');
   g.imageSmoothingEnabled=true;g.clearRect(0,0,glow.width,glow.height);g.drawImage(s.canvas,0,0,glow.width,glow.height);
   ctx.save();
   try{
    ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.imageSmoothingEnabled=true;
    ctx.drawImage(s.canvas,0,0,width,height);
    ctx.globalCompositeOperation='screen';ctx.globalAlpha=.045;ctx.drawImage(g.canvas,0,0,width,height);
    ctx.globalCompositeOperation='source-over';ctx.globalAlpha=.032;ctx.fillStyle='#070803';
    for(let y=1;y<height;y+=3)ctx.fillRect(0,y,width,1);
    ctx.globalAlpha=1;const edge=ctx.createRadialGradient(width/2,height/2,height*.30,width/2,height/2,Math.max(width,height)*.64);
    edge.addColorStop(0,'#00000000');edge.addColorStop(1,'#00000035');ctx.fillStyle=edge;ctx.fillRect(0,0,width,height);
   }finally{ctx.restore();}
   return true;
  }catch{failed=true;return false;}
 }
 return{configure,present,get enabled(){return enabled;},get profile(){return profile;},get available(){return !failed;}};
})();
