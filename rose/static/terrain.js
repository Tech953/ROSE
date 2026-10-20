'use strict';
/* Continuous scenery. Circulation cells remain host navigation data. */
window.RoseTerrain=(()=>{
 const cache=new Map(),dirs=[[1,0],[1,-1],[0,-1],[-1,0],[-1,1],[0,1]],key=p=>p.join(',');let failed=false;
 const palettes={WN_TOWER:['#1c2218','#526043','#aea17a'],ENACT_HILLS:['#4c3525','#8a7958','#c7ad7b'],CITY_CLOUD_S:['#222a33','#505758','#9a9483'],AETHERGALE:['#39303e','#5c665c','#b9ac9c']};
 function random(text){let state=2166136261;for(const ch of text)state=Math.imul(state^ch.charCodeAt(0),16777619);return()=>{state+=0x6d2b79f5;let n=state;n=Math.imul(n^n>>>15,n|1);n^=n+Math.imul(n^n>>>7,n|61);return((n^n>>>14)>>>0)/4294967296;};}
 function canvas(w,h){const value=document.createElement('canvas');value.width=w;value.height=h;if(!value.getContext('2d'))throw Error('Terrain canvas unavailable');return value;}
 function routes(field){
  const tiles=field.tiles,parents=new Map(),queue=[];if(tiles['0,0']?.passable){parents.set('0,0',null);queue.push([0,0]);}
  for(let i=0;i<queue.length;i++)for(const d of dirs){const p=[queue[i][0]+d[0],queue[i][1]+d[1]],id=key(p);if(tiles[id]?.passable&&!parents.has(id)){parents.set(id,key(queue[i]));queue.push(p);}}
  const targets=[...field.infrastructure.nodes,...(field.lifecycle?.projects||[]).filter(p=>['foundation','frame','finishing'].includes(p.stage))],result=[];
  for(const node of targets){const candidates=dirs.map(d=>[node.pos[0]+d[0],node.pos[1]+d[1]]).filter(p=>parents.has(key(p))),paths=[];
   for(const p of candidates){const points=[];let id=key(p);while(id!==null){points.push(tiles[id].pos);id=parents.get(id);}paths.push(points.reverse());}
   paths.sort((a,b)=>a.length-b.length||key(a.at(-1)).localeCompare(key(b.at(-1))));if(paths[0]?.length>1)result.push(paths[0]);
  }return result;
 }
 function curve(c,points,jitter){
  if(points.length<2)return;c.beginPath();c.moveTo(...points[0]);for(let i=1;i<points.length-1;i++){const a=points[i],b=points[i+1],offset=jitter[i]||[0,0];c.quadraticCurveTo(a[0]+offset[0],a[1]+offset[1],(a[0]+b[0])/2,(a[1]+b[1])/2);}c.lineTo(...points.at(-1));c.stroke();
 }
 function build(field,region,project,size,w,h){
  const image=canvas(w,h),c=image.getContext('2d'),life=field.lifecycle||{},colors=palettes[region]||palettes.WN_TOWER;
  const seed=field.id+':'+region+':'+Object.values(field.tiles).map(t=>t.variant).join(''),rng=random(seed),scale=size/34;
  c.fillStyle=field.palette.ground;c.fillRect(0,0,w,h);
  if(RosePrefabs.style!=='vector'){c.save();c.scale(scale,scale);c.globalAlpha=.92;RosePrefabs.ground(c,region,[0,0,w/scale,h/scale]);c.restore();}
  // Broad irregular material patches and fine ground detail have no cell edges.
  for(let i=0;i<42;i++){
   const x=rng()*w,y=rng()*h,r=(24+rng()*105)*scale,points=[];for(let j=0;j<16;j++){const a=j*Math.PI/8,rr=r*(.74+rng()*.33);points.push([Math.cos(a)*rr,Math.sin(a)*rr]);}
   c.save();c.translate(x,y);c.scale(1,.52);c.globalAlpha=.035+rng()*.07;c.fillStyle=colors[i%2];c.beginPath();c.moveTo((points[15][0]+points[0][0])/2,(points[15][1]+points[0][1])/2);
   for(let j=0;j<16;j++){const a=points[j],b=points[(j+1)%16];c.quadraticCurveTo(...a,(a[0]+b[0])/2,(a[1]+b[1])/2);}c.closePath();c.fill();c.restore();
  }
  for(let i=0;i<1800;i++){const x=rng()*w,y=rng()*h;c.globalAlpha=.055+rng()*.10;c.fillStyle=colors[i%3];c.fillRect(x,y,(.6+rng()*1.6)*scale,.65*scale);}c.globalAlpha=1;
  const count=Math.round((region==='CITY_CLOUD_S'?32:region==='WN_TOWER'?150:85)+(life.growth||0)*(region==='CITY_CLOUD_S'?.12:.75));
  for(let i=0;i<count;i++){
   const x=rng()*w,y=rng()*h;c.strokeStyle=i%3?colors[1]:colors[2];c.globalAlpha=.18+rng()*.22;c.lineWidth=.7*scale;c.beginPath();
   for(let j=0;j<3+(i%3);j++){const dx=(rng()-.5)*7*scale;c.moveTo(x+dx,y);c.lineTo(x+dx+(rng()-.5)*3*scale,y-(1.4+rng()*4)*scale);}c.stroke();
  }c.globalAlpha=1;
  // Foot-worn approaches follow reachable building aprons. Navigation reserves
  // and utility branches do not become an exposed painted movement lattice.
  const paths=routes(field),mask=canvas(w,h),m=mask.getContext('2d'),pathRandom=random(seed+':approaches');m.save();m.scale(1,.52);m.lineCap='round';m.lineJoin='round';m.strokeStyle='#fff';
  for(const route of paths){const points=route.map(p=>{const[x,y]=project(p);return[x,y/.52];}),jitter=points.map(()=>[(pathRandom()-.5)*size*.16,(pathRandom()-.5)*size*.14]);
   for(const [width,alpha] of [[.84,.10],[.62,.16],[.43,.27],[.28,.32]]){m.lineWidth=size*width;m.globalAlpha=alpha;curve(m,points,jitter);}
  }m.restore();const texture=canvas(w,h),paint=texture.getContext('2d');paint.save();paint.scale(scale,scale);
  if(RosePrefabs.style==='vector'||!RosePrefabs.path(paint,region,[0,0,w/scale,h/scale])){paint.fillStyle=colors[2];paint.fillRect(0,0,w/scale,h/scale);}paint.restore();
  m.globalCompositeOperation='source-in';m.drawImage(texture,0,0);
  c.globalAlpha=.62;c.drawImage(mask,0,0);c.globalAlpha=1;
  c.save();c.translate(w/2,h*.55);c.scale(1,.52);const shade=c.createRadialGradient(0,0,190,0,0,790);shade.addColorStop(0,'#07100a00');shade.addColorStop(1,'#07100aac');c.fillStyle=shade;c.fillRect(-w,-h/.52,w*2,h*2/.52);c.restore();return{image,paths:paths.length};
 }
 function draw(c,field,region,project,size,w=1000,h=620){
  if(failed)return false;const life=field.lifecycle||{},signature=JSON.stringify([field.id,region,RosePrefabs.style,RosePrefabs.loaded,size,w,h,field.palette.ground,
   Object.values(field.tiles).map(t=>[t.pos,t.passable,t.elevation,t.variant]),field.infrastructure.nodes.map(n=>[n.id,n.pos]),(life.projects||[]).map(p=>[p.id,p.pos,p.stage]),life.growth]);
  try{let value=cache.get(signature);if(!value){value=build(field,region,project,size,w,h);cache.set(signature,value);while(cache.size>2)cache.delete(cache.keys().next().value);}else{cache.delete(signature);cache.set(signature,value);}c.drawImage(value.image,0,0);return true;}
  catch{failed=true;cache.clear();return false;}
 }
 return{draw,routes,get cachedViews(){return cache.size;},get available(){return !failed;}};
})();
