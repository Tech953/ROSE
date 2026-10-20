'use strict';
/* A bounded surface finish. Existing geometry, alpha and live simulation remain authoritative. */
window.RoseArtDirection=(()=>{
 const cache=new Map(),ids=new WeakMap();let serial=0,data=null,enabled=true,failed=false,ordinary=false;
 const id=x=>{if(!ids.has(x))ids.set(x,++serial);return ids.get(x);};
 const clamp=x=>Math.max(0,Math.min(255,Math.round(x)));
 function load(value){
  if(value?.schema!==1||!value.materials||!value.regions)throw Error('Invalid art-direction configuration.');
  for(const p of Object.values(value.materials)){
   if(typeof p.label!=='string'||!['shadow','light'].every(k=>Array.isArray(p[k])&&p[k].length===3&&p[k].every(n=>Number.isFinite(n)&&n>=0&&n<=255))||
    !Number.isFinite(p.mix)||p.mix<0||p.mix>.5||!Number.isFinite(p.contrast)||p.contrast<0||p.contrast>.2||!Number.isFinite(p.grain)||p.grain<0||p.grain>4)throw Error('Invalid art-direction material.');
  }
  data=JSON.parse(JSON.stringify(value));cache.clear();failed=false;
 }
 function read(value){ordinary=!!value?.scene&&!value.me?.remote&&!value.particles?.percept?.address;}
 function configure(value){enabled=!!value;}
 function variant(prop){const obj=prop.node||prop.tile;let h=2166136261;for(const c of String(obj?.visual?.signature||obj?.id||prop.pos)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return(h>>>0)%4;}
 function frame(f,prop,region){
  if(!f||!data||!enabled||failed||!ordinary||RosePrefabs.style!=='rendered'||!Object.hasOwn(data.regions,region)||!['structure','rock'].includes(prop.type))return f;
  const material=(prop.node||prop.tile)?.material_state?.material,p=data.materials[material];if(!p)return f;
  const v=variant(prop),key=[id(f.asset),f.frameIndex,region,material,v].join(':');
  if(cache.has(key)){const result=cache.get(key);cache.delete(key);cache.set(key,result);return result;}
  try{
   const image=document.createElement('canvas');image.width=f.w;image.height=f.h;const c=image.getContext('2d');c.imageSmoothingEnabled=false;
   c.drawImage(f.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);const pixels=c.getImageData(0,0,f.w,f.h),a=pixels.data;
   for(let i=0;i<a.length;i+=4){
    if(a[i+3]<248)continue;
    const hi=Math.max(a[i],a[i+1],a[i+2]),lo=Math.min(a[i],a[i+1],a[i+2]);if(hi<=10||hi>120&&hi-lo>65)continue;
    const lum=.2126*a[i]+.7152*a[i+1]+.0722*a[i+2],t=Math.max(0,Math.min(1,(lum-16)/180)),pixel=i/4,x=pixel%f.w,y=Math.floor(pixel/f.w),
      grain=(((Math.imul(x+v*11,13)+Math.imul(y,7))%17)/8-1)*p.grain;
    for(let ch=0;ch<3;ch++){const target=p.shadow[ch]+(p.light[ch]-p.shadow[ch])*t,mixed=a[i+ch]*(1-p.mix)+target*p.mix;a[i+ch]=clamp((mixed-78)*(1+p.contrast)+78+grain);}
   }
   c.putImageData(pixels,0,0);const result={...f,asset:{...f.asset,art_direction_frame:true},image,x:0,y:0};
   cache.set(key,result);while(cache.size>48)cache.delete(cache.keys().next().value);return result;
  }catch{failed=true;cache.clear();return f;}
 }
 return{load,read,configure,frame,get ready(){return !!data;},get enabled(){return enabled;},get available(){return !failed;},get cached(){return cache.size;}};
})();
