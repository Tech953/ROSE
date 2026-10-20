'use strict';
/* Original, finite vector poses. A sprite manifest can replace any prefab. */
window.RosePrefabs=(()=>{
 const frames={
  idle:[{bob:0,leg:0,arm:0},{bob:-1,leg:0,arm:0},{bob:0,leg:0,arm:0},{bob:1,leg:0,arm:0}],
  walk:[{bob:0,leg:-5,arm:4},{bob:-2,leg:-3,arm:2},{bob:0,leg:0,arm:0},{bob:0,leg:5,arm:-4},{bob:-2,leg:3,arm:-2},{bob:0,leg:0,arm:0}],
  attack:[{bob:0,leg:2,arm:-8},{bob:-2,leg:4,arm:14},{bob:0,leg:1,arm:4}],
  guard:[{bob:1,leg:3,arm:-3}],work:[{bob:2,leg:1,arm:2},{bob:4,leg:1,arm:9},{bob:2,leg:1,arm:5},{bob:0,leg:1,arm:0}],
  talk:[{bob:0,leg:0,arm:4},{bob:0,leg:0,arm:1}],hit:[{bob:3,leg:2,arm:-5},{bob:1,leg:0,arm:0}],down:[{bob:0,leg:0,arm:0}]
 };
 const sprites=new Map();let manifest=null;
 const poly=(c,points,fill,stroke)=>{c.beginPath();points.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.stroke();}};
 function box(c,width,depth,height,color){poly(c,[[-width/2,0],[0,depth/2],[0,depth/2-height],[-width/2,-height]],'#46524e','#718178');poly(c,[[0,depth/2],[width/2,0],[width/2,-height],[0,depth/2-height]],'#263c38','#718178');poly(c,[[-width/2,-height],[0,-depth/2-height],[width/2,-height],[0,depth/2-height]],color,'#96a89b');}
 function shadow(c,w=22){c.fillStyle='#0007';c.beginPath();c.ellipse(0,3,w,w*.34,0,0,Math.PI*2);c.fill();}
 function load(value){manifest=value;for(const[key,asset]of Object.entries(value.assets||{})){if(asset.kind!=='sprite'||!/^\/art\/[\w.-]+\.(png|webp)$/.test(asset.image||''))continue;const img=new Image();img.onload=()=>sprites.set(key,{img,asset});img.src=asset.image;}}
 function sprite(c,key,pose,time,facing=0){const data=sprites.get(key);if(!data)return false;const{img,asset}=data,animation=manifest.animations[pose]||manifest.animations.idle,clip=asset.clips?.[`${pose}_${facing}`]||asset.clips?.[pose]||asset.clips?.idle;
  if(!clip?.length||!asset.frames?.length)return false;const index=animation.loop?Math.floor(time/animation.frame_ms)%clip.length:Math.min(clip.length-1,Math.floor(time/animation.frame_ms));const frame=asset.frames[clip[index]];if(!Array.isArray(frame)||frame.length!==4)return false;
  const[x,y,w,h]=frame,[ax,ay]=asset.anchor||[w/2,h],scale=Number(asset.scale)||1;c.drawImage(img,x,y,w,h,-ax*scale,-ay*scale,w*scale,h*scale);return true;
 }
 function person(c,unit,pose,time,palette){
  const sequence=frames[pose]||frames.idle,loop=['idle','walk','work','talk','guard'].includes(pose),ms=manifest?.animations?.[pose]?.frame_ms||150,index=loop?Math.floor(time/ms)%sequence.length:Math.min(sequence.length-1,Math.floor(time/ms));const f=sequence[index];
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
 function structure(c,node,time,palette){
  shadow(c,33);if(sprite(c,node.kind,'idle',time))return;const off=!node.enabled||node.condition<30,accent=off?'#85736b':palette.accent;
  if(node.kind==='power'){box(c,30,18,17,'#63786b');c.fillStyle='#78857d';c.fillRect(-3,-65,6,49);c.strokeStyle='#b4c4ae';c.lineWidth=3;const blades=[[[0,-84],[0,-50]],[[-17,-67],[17,-67]],[[ -12,-79],[12,-55]],[[ -12,-55],[12,-79]]][Math.floor(time/320)%4];c.beginPath();blades.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.stroke();c.fillStyle=accent;c.beginPath();c.arc(0,-67,4,0,Math.PI*2);c.fill();}
  else if(node.kind==='water'){box(c,44,24,7,'#5a7873');c.fillStyle='#637f7c';c.fillRect(-18,-39,36,31);c.beginPath();c.ellipse(0,-8,18,8,0,0,Math.PI);c.fill();c.fillStyle='#aac1b4';c.beginPath();c.ellipse(0,-39,18,8,0,0,Math.PI*2);c.fill();c.strokeStyle='#213c3b';c.lineWidth=3;c.beginPath();c.moveTo(12,-25);c.lineTo(24,-19);c.lineTo(24,-9);c.stroke();c.fillStyle=accent;c.fillRect(-10,-30,4,15);}
  else if(node.kind==='garden'){box(c,62,35,7,'#52573c');for(let i=0;i<6;i++){const x=(i%3)*16-17,y=Math.floor(i/3)*9-7;poly(c,[[x,y-10],[x-5,y-19],[x+1,y-13],[x+6,y-23],[x+5,y-9]],off?'#79734e':'#94a772','#b1bd85');}}
  else if(node.kind==='shelter'){box(c,57,32,23,'#667868');poly(c,[[-34,-22],[-5,-57],[34,-24],[0,-8]],'#827f68','#c7c3a4');poly(c,[[-5,-57],[34,-24],[12,-14]],'#655b50');c.fillStyle='#182b28';c.fillRect(-11,-24,13,20);c.strokeStyle=accent;c.lineWidth=2;c.beginPath();c.moveTo(-5,-57);c.lineTo(-35,-21);c.stroke();}
  else if(node.kind==='relay'){box(c,32,20,15,'#64786d');c.fillStyle='#a0b3a5';c.fillRect(-2,-72,4,58);c.strokeStyle='#b0c3b3';c.beginPath();c.moveTo(-19,-64);c.lineTo(20,-73);c.moveTo(-15,-58);c.lineTo(15,-65);c.stroke();c.fillStyle=accent;c.fillRect(6,-27,4,5);}
  else{box(c,58,32,30,node.kind==='exchange'?'#9b8d6e':'#758882');c.fillStyle='#192b28';c.fillRect(4,-23,13,20);c.fillStyle=accent;c.fillRect(8,-25,8,3);box(c,23,14,12,'#717267');if(node.kind==='workshop'){c.strokeStyle='#c7b697';c.lineWidth=3;c.beginPath();c.moveTo(-13,-42);c.lineTo(8,-50);c.stroke();}else{poly(c,[[-30,-28],[0,-44],[31,-29],[0,-12]],'#a0936c','#d7c797');}}
  if(node.condition<50){c.strokeStyle='#342526';c.lineWidth=2;c.beginPath();c.moveTo(-8,-20);c.lineTo(1,-13);c.lineTo(-3,-8);c.stroke();}
 }
 function rock(c,palette){shadow(c,26);poly(c,[[-27,-3],[-20,-25],[-3,-38],[24,-19],[29,1],[2,10]],'#657064','#889282');poly(c,[[-3,-38],[24,-19],[2,10],[-1,-9]],'#454f48');poly(c,[[-27,-3],[-20,-25],[-1,-9],[2,10]],'#788075');}
 function unit(c,unit,pose,time,palette){shadow(c,14);if(sprite(c,unit.kind,pose,time,unit.facing||0))return;if(unit.kind==='threat')construct(c,unit,time,palette);else person(c,unit,pose,time,palette);}
 return {load,structure,unit,rock,frames};
})();
