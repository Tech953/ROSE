'use strict';
/* Small prepared-surface composites; draw, detail, bounds and picking share them. */
window.RoseMotionVisuals=(()=>{
 const cache=new Map(),ids=new WeakMap();let serial=0,failed=false;
 const id=a=>{if(!ids.has(a))ids.set(a,++serial);return ids.get(a);};
 function remember(key,value){cache.set(key,value);while(cache.size>24)cache.delete(cache.keys().next().value);return value;}
 function wrapper(f,image,anchor){return{...f,asset:{...f.asset,pick_alpha_min:248,motion_frame:true},image,x:0,y:0,w:image.width,h:image.height,anchor};}
 function source(f){const c=document.createElement('canvas');c.width=f.w;c.height=f.h;c.getContext('2d').drawImage(f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);return c;}
 function hardware(f,m){
  if(!f||!m||failed)return f;const shift=m.offset.map(v=>Math.round(v*4)/4),angle=Math.round(Math.atan2(Math.sin(m.angle||0),Math.cos(m.angle||0))*180/Math.PI)*Math.PI/180,key='hardware:'+id(f.asset)+':'+f.frameIndex+':'+m.kind+':'+shift+':'+angle+':'+m.contact;
  if(cache.has(key))return cache.get(key);
  try{
   const pad=32,image=document.createElement('canvas');image.width=f.w+pad*2;image.height=f.h+pad;const c=image.getContext('2d');c.imageSmoothingEnabled=false;
   c.drawImage(f.image,f.x,f.y,f.w,f.h,pad,0,f.w,f.h);const a=[f.anchor[0]+pad,f.anchor[1]],x=a[0]+13/f.scale,y=a[1]-12/f.scale,z=1/f.scale;
   c.save();c.translate(x,y);c.scale(z,z);c.fillStyle='#3c4842';c.strokeStyle='#929988';c.lineWidth=1;
   c.beginPath();c.moveTo(-13,2);c.lineTo(-10,-3);c.lineTo(15,-1);c.lineTo(12,5);c.closePath();c.fill();c.stroke();
   c.strokeStyle='#818d82';c.beginPath();c.moveTo(-11,-2);c.lineTo(14,0);c.moveTo(-11,3);c.lineTo(14,5);c.stroke();
   const dx=shift[0],dy=shift[1];
   if(m.kind==='damper'){c.strokeStyle='#afb2a0';c.beginPath();for(let n=0;n<9;n++){const t=n/8,px=-11+(dx+7)*t,py=-4+dy*t+(n&&n<8?(n%2?2:-2):0);n?c.lineTo(px,py):c.moveTo(px,py);}c.stroke();}
   if(m.kind==='press'){c.fillStyle='#596858';c.fillRect(11,-10,4,13);c.fillStyle='#b3b49a';c.fillRect(10,-10,6,2);}
   c.translate(dx,dy);c.rotate(angle);
   c.fillStyle=m.contact?'#c9b38b':'#879486';c.fillRect(-4,-8,8,9);c.fillStyle='#33463e';c.fillRect(1,-6,3,8);
   const sx=Math.max(0,Math.min(f.w-18,f.anchor[0]-9)),sy=Math.max(0,Math.min(f.h-15,f.anchor[1]-28));
   c.drawImage(f.image,f.x+sx,f.y+sy,18,15,-4,-8,8,7);c.strokeStyle='#c4c2a9';c.beginPath();c.moveTo(-4,-8);c.lineTo(4,-8);c.lineTo(4,0);c.stroke();
   c.restore();return remember(key,wrapper(f,image,a));
  }catch{failed=true;return f;}
 }
 function collapse(f,ruined,cue){
  if(!f||!ruined||!cue||failed)return ruined||f;const frame=Math.min(15,Math.floor(cue.progress*16)),key='collapse:'+id(f.asset)+':'+f.frameIndex+':'+cue.material+':'+frame;
  if(cache.has(key))return cache.get(key);if(frame===15)return ruined;
  try{
   const old=source(f),ctx=old.getContext('2d'),rgba=ctx.getImageData(0,0,f.w,f.h).data;let l=f.w,t=f.h,r=-1,b=-1;
   for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]>=248){const x=i/4%f.w,y=Math.floor(i/4/f.w);l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);}
   if(r<l)return ruined;const image=document.createElement('canvas');image.width=f.w+64;image.height=f.h+48;const c=image.getContext('2d');c.imageSmoothingEnabled=false;const anchor=[f.anchor[0]+32,f.anchor[1]];
   const p=frame/15;if(p<.13)c.drawImage(old,32,0);else{
    c.fillStyle='#0005';c.beginPath();c.ellipse(anchor[0],anchor[1]+2,36/f.scale,12/f.scale,0,0,Math.PI*2);c.fill();
    const restitution={wood:.08,metal:.2,stone:.1,crystal:.12,fabric:.01,polymer:.18}[cue.material]??.1;
    const elapsed=(p-.13)/.8,g=2*(anchor[1]-t+20)/.55**2;
    for(let n=0;n<24;n++){
     const col=n%3,row=Math.floor(n/3),sw=(r-l+1)/3,sh=(b-t+1)/8,sx=l+col*sw,sy=t+row*sh;
     const initial=sy+sh/2,landing=anchor[1]-4-(n%4)*2,fallTime=Math.sqrt(Math.max(0,2*(landing-initial)/g)),after=Math.max(0,elapsed-fallTime);
     let y=elapsed<fallTime?initial+.5*g*elapsed**2:landing;
     if(after<2*restitution*fallTime)y=landing-restitution*g*fallTime*after+.5*g*after**2;
     const q=Math.min(1,elapsed/.65),start=sx+sw/2+32,finish=anchor[0]+((n*17)%47-23)/f.scale,x=start+(finish-start)*q;
     const shrink=1-q*.72;c.save();c.translate(x,y);c.rotate((n%2?-1:1)*q*.5);c.drawImage(old,sx,sy,sw,sh,-sw*shrink/2,-sh*shrink/2,sw*shrink,sh*shrink);c.restore();
    }
    if(p>.72)c.drawImage(ruined.image,ruined.x,ruined.y,ruined.w,ruined.h,anchor[0]-ruined.anchor[0],anchor[1]-ruined.anchor[1],ruined.w,ruined.h);
   }
   return remember(key,wrapper(f,image,anchor));
  }catch{failed=true;return ruined;}
 }
 function effects(c,rows,project,scale,palette){
  for(const e of rows){
   if(e.kind==='clear'){const[x,y]=project(e.pos),p=e.progress;c.save();c.globalAlpha=(1-p)*.22;c.fillStyle=palette.accent;for(let n=0;n<6;n++){c.beginPath();c.ellipse(x+Math.cos(n*2.4)*p*22*scale,y+Math.sin(n*2.4)*p*7*scale,2+p*5,1+p*2,0,0,Math.PI*2);c.fill();}c.restore();continue;}
   const contact=e.contact_ms/e.duration_ms,[sx,sy]=project(e.source),[tx,ty]=project(e.destination);
   if(e.ranged&&e.progress>=.32&&e.progress<contact){const p=(e.progress-.32)/(contact-.32),x=sx+(tx-sx)*p,y=sy+(ty-sy)*p-30*scale;c.save();c.strokeStyle=palette.accent;c.lineWidth=2;c.beginPath();c.moveTo(x-(tx-sx)*.055,y-(ty-sy)*.055);c.lineTo(x,y);c.stroke();c.restore();}
   if(!e.hit||e.progress<contact)continue;const p=(e.progress-contact)/(1-contact);c.save();c.globalAlpha=Math.max(0,1-p);c.strokeStyle=palette.accent;c.lineWidth=1;
   for(let n=0;n<6;n++){const dx=Math.cos(n*1.047)*p*14*scale,dy=Math.sin(n*1.047)*p*9*scale;c.beginPath();c.moveTo(tx+dx,ty-22*scale+dy+18*p*p*scale);c.lineTo(tx+dx*1.1,ty-22*scale+dy+18*p*p*scale+2);c.stroke();}c.restore();
  }
 }
 return{hardware,collapse,effects,get cached(){return cache.size;},get available(){return !failed;}};
})();
