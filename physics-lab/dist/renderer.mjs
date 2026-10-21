import { MATERIALS,STRUCTURES,clamp,axialToWorld,HEX_SIZE } from './engine.mjs';
const noise=(a,b=0)=>{const n=Math.sin(a*127.1+b*311.7)*43758.5453;return n-Math.floor(n);};
function poly(c,pts,fill,stroke=null,width=1){c.beginPath();pts.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.closePath();if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.strokeStyle=stroke;c.lineWidth=width;c.stroke();}}
function line(c,pts,color,width=1){c.beginPath();pts.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.strokeStyle=color;c.lineWidth=width;c.lineJoin='round';c.stroke();}
function ellipse(c,x,y,rx,ry,color){c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fillStyle=color;c.fill();}
const box=(c,p,x,y,z,w,d,h,colors)=>{
  const A=p(x,y,z),B=p(x+w,y,z),C=p(x+w,y+d,z),D=p(x,y+d,z),a=p(x,y,z+h),b=p(x+w,y,z+h),cc=p(x+w,y+d,z+h),dd=p(x,y+d,z+h);
  poly(c,[A,B,b,a],colors[2]);poly(c,[B,C,cc,b],colors[0]);poly(c,[C,D,dd,cc],colors[1]);poly(c,[a,b,cc,dd],colors[3]||colors[0]);return {A,B,C,D,a,b,c:cc,d:dd};
};
function tree(c,x,y,s,variant=0){
  ellipse(c,x+3*s,y+3*s,12*s,4*s,'#0c211970');
  line(c,[[x,y],[x,y-25*s]],'#394534',2*s);
  for(let i=0;i<3;i++)poly(c,[[x,y-(55-i*12)*s],[x-(15-i*1.5)*s,y-(20-i*9)*s],[x+2*s,y-(24-i*7)*s]],variant?'#3c4a32':'#2e4835');
  for(let i=0;i<3;i++)poly(c,[[x,y-(55-i*12)*s],[x+(13-i)*s,y-(20-i*9)*s],[x-2*s,y-(24-i*7)*s]],variant?'#526043':'#3e5940');
}
function human(c,p,x,y,scale=1){const b=p(x,y,0),h=1.8*scale;const head=p(x,y,h-.12),hip=p(x,y,.8*scale),shoulder=p(x,y,1.4*scale);
  ellipse(c,b[0]+3,b[1]+2,11*scale,3*scale,'#071c1390');
  line(c,[[b[0]-3*scale,b[1]],[hip[0],hip[1]],[b[0]+4*scale,b[1]-1]],'#a9b5a0',2.3*scale);
  line(c,[[hip[0],hip[1]],[shoulder[0],shoulder[1]]],'#c5b697',5*scale);
  line(c,[[shoulder[0]-2,shoulder[1]+2],[shoulder[0]-5*scale,shoulder[1]+10*scale]],'#b6a38b',2*scale);
  ellipse(c,head[0],head[1],3.2*scale,3.7*scale,'#c4baa2');
}
export class SceneRenderer {
  constructor(){this.backgrounds=new Map();}
  draw(c,width,height,snapshot,options={}) {
    const {hex=false,scale='site',motion=false,clock=0,selected=null,labels=true}=options;
    const W=1100,H=680,ratio=Math.max(width/W,height/H);const offX=(width-W*ratio)/2,offY=(height-H*ratio)/2;
    c.save();c.clearRect(0,0,width,height);c.translate(offX,offY);c.scale(ratio,ratio);
    const zoom=scale==='detail'?1.46:scale==='landscape'?.62:1;
    const cx=560,cy=430;const p=(x,y,z=0)=>[cx+(x-y)*22*zoom,cy+(x+y)*11.44*zoom-z*24*zoom];
    // Cache the continuous terrain so live animation only repaints the dynamic objects.
    if(typeof OffscreenCanvas!=='undefined'){
      if(!this.backgrounds.has(scale)){
        const surface=new OffscreenCanvas(W,H),context=surface.getContext('2d');this.world(context,W,H);context.save();if(scale==='detail')context.translate(0,42);if(scale==='landscape')context.translate(0,-15);this.terrain(context,p,zoom,0,false);context.restore();this.backgrounds.set(scale,surface);
      }
      c.drawImage(this.backgrounds.get(scale),0,0);
    }else this.world(c,W,H);
    c.save();if(scale==='detail')c.translate(0,42);if(scale==='landscape')c.translate(0,-15);
    if(typeof OffscreenCanvas==='undefined')this.terrain(c,p,zoom,clock,motion);
    // Lattice is a diagnostic layer only. Natural terrain is independent of it.
    if(hex)this.lattice(c,p,zoom);
    this.props(c,p,zoom,clock,motion);
    const m=MATERIALS[snapshot.config.material],s=STRUCTURES[snapshot.config.structure];
    this.specimen(c,p,snapshot,zoom,clock,motion);
    human(c,p,3.7,1.8,zoom);human(c,p,-5,-.9,.83*zoom);
    if(labels){this.annotation(c,p,3.7,1.8,'1.8 m / REFERENCE',zoom,48);this.annotation(c,p,-1,-.4,s.name.toUpperCase(),zoom,-85,s.height);}
    if(snapshot.force&&motion){const a=p(-7,-2,3),b=p(-2,0,3);line(c,[a,b],'#d5ad7c',2);poly(c,[b,[b[0]-12,b[1]-6],[b[0]-12,b[1]+6]],'#d5ad7c');ellipse(c,...p(-1,0,.05),Math.abs(Math.sin(clock*4))*65+30,18,'#cc9a6720');}
    if(snapshot.blocked){const q=p(0,0);c.setLineDash([5,6]);ellipse(c,q[0],q[1],105*zoom,44*zoom,'#df9a6820');c.strokeStyle='#cb987990';c.stroke();c.setLineDash([]);}
    if(selected){const pos=axialToWorld(selected.q,selected.r),q=p(pos.x,pos.y,.05);c.strokeStyle='#c9dea4';c.lineWidth=1;ellipse(c,q[0],q[1],16*zoom,7*zoom,'#bed49c20');c.stroke();line(c,[[q[0]-8,q[1]],[q[0]+8,q[1]]],'#d2e4b6');line(c,[[q[0],q[1]-8],[q[0],q[1]+8]],'#d2e4b6');}
    c.restore();
    // Subtle film grain and vignette retain the prepared CRT palette without obscuring edges.
    const vignette=c.createRadialGradient(550,320,100,550,320,660);vignette.addColorStop(0,'#08171000');vignette.addColorStop(1,'#07160e80');c.fillStyle=vignette;c.fillRect(0,0,W,H);
    c.restore();
  }
  world(c,w,h){
    const sky=c.createLinearGradient(0,0,0,h);sky.addColorStop(0,'#263a2e');sky.addColorStop(.5,'#283d2e');sky.addColorStop(1,'#12291f');c.fillStyle=sky;c.fillRect(0,0,w,h);
    const glow=c.createRadialGradient(560,220,0,560,220,480);glow.addColorStop(0,'#9ba77718');glow.addColorStop(1,'#9ba77700');c.fillStyle=glow;c.fillRect(0,0,w,h);
    for(let layer=0;layer<4;layer++){
      const y=105+layer*39;const pts=[[0,h],[0,y+100]];for(let x=0;x<=w+30;x+=30)pts.push([x,y+Math.sin(x/153+layer*3)*32+Math.sin(x/61+layer)*13+noise(x,layer)*17]);pts.push([w,h]);poly(c,pts,['#354c38','#304833','#2b442f','#243e2b'][layer]);
      for(let i=0;i<32;i++){const x=i*38+noise(i,layer)*30,yy=y+65+Math.sin(x/153+layer*3)*26;tree(c,x,yy,.45+layer*.15);}
    }
    // Distant monumental silhouettes establish an environmental rather than board-game scale.
    poly(c,[[156,224],[156,129],[172,109],[188,119],[188,226]],'#62755a30');poly(c,[[188,119],[199,114],[199,219],[188,226]],'#243f2c70');
    poly(c,[[919,228],[919,136],[932,117],[943,125],[943,228]],'#74846625');
    for(let i=0;i<65;i++){const x=noise(i,42)*1100,y=140+noise(i,91)*220;ellipse(c,x,y,noise(i,3)*3+.4,.5,'#afbe8c13');}
    // Broad winding channel; its banks have no cell-aligned boundaries.
    c.beginPath();c.moveTo(1130,340);c.bezierCurveTo(850,254,885,378,682,325);c.bezierCurveTo(495,282,464,348,315,325);c.bezierCurveTo(150,300,38,381,-30,425);c.strokeStyle='#6b806438';c.lineWidth=34;c.stroke();c.strokeStyle='#8e9b6a22';c.lineWidth=3;c.stroke();
  }
  terrain(c,p,z,clock,motion){
    // An irregular continuous island, constructed from smooth contours, never from visible hex cells.
    const X=560,Y=443;const outline=[[X-390*z,Y-80*z],[X-284*z,Y-182*z],[X-65*z,Y-197*z],[X+109*z,Y-163*z],[X+330*z,Y-91*z],[X+415*z,Y+5*z],[X+323*z,Y+101*z],[X+113*z,Y+170*z],[X-131*z,Y+168*z],[X-330*z,Y+86*z]];
    const path=(dy=0)=>{c.beginPath();const last=outline.at(-1),first=outline[0];c.moveTo((last[0]+first[0])/2,(last[1]+first[1])/2+dy);for(let i=0;i<outline.length;i++){const a=outline[i],b=outline[(i+1)%outline.length];c.quadraticCurveTo(a[0],a[1]+dy,(a[0]+b[0])/2,(a[1]+b[1])/2+dy);}c.closePath();};
    ellipse(c,X+15*z,Y+80*z,430*z,155*z,'#071c1580');path(35*z);const side=c.createLinearGradient(0,Y,0,Y+200*z);side.addColorStop(0,'#394436');side.addColorStop(1,'#243a29');c.fillStyle=side;c.fill();path(20*z);c.strokeStyle='#63715130';c.lineWidth=1;c.stroke();path();const land=c.createLinearGradient(X-250*z,Y-100*z,X+200*z,Y+200*z);land.addColorStop(0,'#526143');land.addColorStop(.5,'#4a593b');land.addColorStop(1,'#374e32');c.fillStyle=land;c.fill();
    c.save();path();c.clip();
    for(let i=0;i<2300;i++){
      const x=X+(noise(i,7)-.5)*820*z,y=Y+(noise(i,13)-.5)*410*z;
      const sz=(noise(i,87)*5+.6)*z;const col=noise(i,3)>.6?'#a3ad6a13':'#152e181b';ellipse(c,x,y,sz,sz*.4,col);
    }
    // Two natural paths with soft shoulders.
    for(let k=0;k<2;k++){c.beginPath();c.moveTo(X-400*z,Y+42*z);c.bezierCurveTo(X-250*z,Y+110*z,X-190*z,Y-15*z,X-40*z,Y+10*z);c.bezierCurveTo(X+100*z,Y+25*z,X+170*z,Y+130*z,X+440*z,Y+90*z);c.strokeStyle=k?'#8b8d6370':'#283e2990';c.lineWidth=(k?25:33)*z;c.stroke();}
    for(let i=0;i<80;i++){const x=X+(noise(i,88)-.5)*820*z,y=Y+(noise(i,95)-.5)*360*z;ellipse(c,x,y,(noise(i,6)*7+3)*z,noise(i,4)*2*z,'#9c9d682b');}
    // Organic moss/grass accents; no edge outlines or tessellated patches.
    for(let i=0;i<250;i++){const x=X+(noise(i,9)-.5)*780*z,y=Y+(noise(i,29)-.5)*340*z;const sway=motion?Math.sin(clock*2+i)*1.5*z:0;
      line(c,[[x-2*z,y],[x+sway,y-5*z],[x+1*z+sway,y-7*z]],i%3?'#a5ac622e':'#b2ae6c45',.8*z);
    }
    c.restore();
    // Trees stay on the far banks, preserving the specimen's readable silhouette.
    for(let i=0;i<30;i++){const x=X-390*z+noise(i,55)*800*z;const y=Y-136*z+Math.sin(i*4)*21*z;if(x>X-130*z&&x<X+150*z)continue;tree(c,x,y,(.45+noise(i,12)*.6)*z,i%3===0);}
    for(let i=0;i<6;i++)tree(c,X+(-385+i*12)*z,Y+(30+i*10)*z,(.6+i*.04)*z);
    for(let i=0;i<6;i++)tree(c,X+(322+i*9)*z,Y+(-12+i*16)*z,(.5+i*.04)*z);
  }
  props(c,p,z,clock,motion){
    // Continuous service lines and smaller, human-scale machine housings.
    const a=p(-9,-2,.08),b=p(-4,0,.08),d=p(-1,1,.08);line(c,[a,b,d],'#24362a',7*z);line(c,[a,b,d],'#9a9e75',2*z);
    box(c,p,-8.8,-2.4,.05,1.5,1.5,1.3,['#75806a','#4e6150','#394d40','#97a082']);
    box(c,p,-8.4,-2.2,1.35,.7,.8,.25,['#a8ac83','#7e8d6e','#50674f','#bec098']);
    for(let i=0;i<3;i++)box(c,p,-8.6+i*.35,-2.5,.4,.08,.1,.45,['#d8bd8d','#b29268','#7e7758']);
    const ring=p(-7.9,-2.6,.9);ellipse(c,ring[0],ring[1],7*z,3*z,'#b6cb9940');
    // Rocky outcrops are irregular and separate from built volumes.
    for(let i=0;i<19;i++){const x=-12+noise(i,3)*24,y=5+noise(i,6)*2.5;const a=p(x,y);if(i>7&&i<13)continue;poly(c,[[a[0]-8*z,a[1]],[a[0]-4*z,a[1]-8*z],[a[0]+6*z,a[1]-6*z],[a[0]+10*z,a[1]+2*z],[a[0],a[1]+5*z]],i%2?'#6c7555':'#57674b');}
    // Wind-responsive marker cloth.
    const a1=p(5,-4,0),b1=p(5,-4,2.8);line(c,[a1,b1],'#b5b58b',1*z);const wave=motion?Math.sin(clock*3)*5:0;poly(c,[b1,[b1[0]+22*z,b1[1]+5*z+wave],[b1[0]+18*z,b1[1]+16*z+wave],[b1[0],b1[1]+11*z]],'#b2946f');
  }
  specimen(c,p,snap,z,clock,motion){
    const {config,integrity,collapsed}=snap,m=MATERIALS[config.material],s=STRUCTURES[config.structure];
    const pal=[m.color,m.dark,m.dark,m.light];
    // A cast foundation with a continuous footprint, never an assemblage of stacked bricks.
    box(c,p,-2.1,-1.7,0,4.2,3.4,.48,['#6b7660','#475744','#364a3b','#849076']);
    if(collapsed){
      snap.rubble.forEach((r,i)=>{const q=motion?p(r.x,(r.vy||0)*(Math.min(snap.time,4))+.3,r.z):p(Math.sin(i*2.4)*(1.3+i%3)*1.4,Math.cos(i*3)*2.8,0);c.save();c.translate(...q);c.rotate(motion?r.rotation:i*.5);const v=r.size*18*z;poly(c,[[-v/2,-v*.7],[v*.4,-v*.5],[v*.65,v*.3],[-v*.4,v*.4]],i%3?m.color:m.light,m.dark,.8);c.restore();});
      if(!snap.rubble.length){const q=p(0,0,.5);ellipse(c,q[0],q[1],39*z,17*z,'#273c2890');}return;
    }
    const x=motion?clamp(snap.x,-4,4):0,tilt=motion?snap.rotation:0;
    // Transform only the specimen; ground and service base remain stable.
    const pp=(a,b,h=0)=>p(a+x+h*tilt*.25,b,h);
    ellipse(c,...p(1.7,2.2,.1),100*z,24*z,'#13291e60');
    if(config.structure==='span'){
      box(c,pp,-5.8,-.7,.48,1.8,1.8,3.25,pal);box(c,pp,4,-.7,.48,1.8,1.8,3.25,pal);
      box(c,pp,-6.7,-1.4,3.7,13.3,3.2,.8,pal);for(let i=0;i<2;i++)line(c,[pp(-6,-1.1+i*2.6,4.5),pp(6,-1.1+i*2.6,4.5)],'#bec6a57a',1*z);
    }else if(config.structure==='canopy'){
      [[-3,-2],[3,-2],[-3,2],[3,2]].forEach(([a,b])=>box(c,pp,a,b,.48,.2,.2,4.5,['#8c9a7c','#52664f','#374e3e','#b6bf99']));
      const wave=motion?Math.sin(clock*3)*(.12+config.magnitude/1700):0;
      const a=pp(-3,-2,5.1+wave),b=pp(3,-2,4.8-wave),cc=pp(3,2,5.1+wave),d=pp(-3,2,4.8-wave),mid=pp(0,0,3.9);
      poly(c,[a,b,mid],m.light);poly(c,[b,cc,mid],m.color);poly(c,[cc,d,mid],m.dark);poly(c,[d,a,mid],m.color);line(c,[a,b,cc,d,a],'#d4d6ad77',1*z);
    }else{
      const hh=s.height-.48,w=config.structure==='water'?3.4:2.6,d=config.structure==='water'?2.6:1.85;
      // Large uninterrupted planar faces make the core read as a singular solid.
      const A=pp(-w/2,-d/2,.48),B=pp(w/2,-d/2,.48),C=pp(w/2,d/2,.48),D=pp(-w/2,d/2,.48);
      const a=pp(-w/2+.25,-d/2+.25,hh),b=pp(w/2-.25,-d/2+.25,hh+.45),cc=pp(w/2-.25,d/2-.25,hh+.45),dd=pp(-w/2+.25,d/2-.25,hh);
      const face=c.createLinearGradient(A[0],a[1],C[0],C[1]);face.addColorStop(0,m.color);face.addColorStop(1,m.dark);
      poly(c,[A,B,b,a],m.dark);poly(c,[B,C,cc,b],face);poly(c,[C,D,dd,cc],m.color);poly(c,[a,b,cc,dd],m.light);
      line(c,[dd,cc,C],m.light+'80',.8*z);
      // A narrow inlaid signal channel, not a modular seam.
      const glow=config.structure==='power'?'#d6b47e':config.structure==='water'?'#91c8bd':'#b6dfb3';
      const stripe1=pp(-.24,d/2+.015,2),stripe2=pp(-.24,d/2-.11,hh-1.5);
      c.save();c.shadowBlur=12*z;c.shadowColor=glow;line(c,[stripe1,stripe2],glow,2*z);c.restore();
      for(let i=0;i<3;i++)line(c,[pp(.35+i*.13,d/2,2.1),pp(.35+i*.13,d/2-.02,2.5)],'#c4d0a76b',.7*z);
      // Upper inset is a cut in one solid mass.
      poly(c,[pp(-.6,d/2-.1,hh-1),pp(.4,d/2-.1,hh-.9),pp(.4,d/2-.07,hh-1.2),pp(-.6,d/2-.07,hh-1.3)],'#1d392c');
    }
    // Human-scale service hatch anchors core scale; the pump and rotor are animated machinery.
    box(c,p,-1.3,1,.48,1.1,.8,1.35,['#8d8b6d','#666e52','#41563f','#a4a182']);
    const hatch=p(-.68,1.81,1.2);poly(c,[[hatch[0]-7*z,hatch[1]-9*z],[hatch[0]+7*z,hatch[1]-4*z],[hatch[0]+7*z,hatch[1]+10*z],[hatch[0]-7*z,hatch[1]+5*z]],'#233e2e','#869975',.8*z);
    const lamp=p(-.68,1.82,1.75);ellipse(c,lamp[0],lamp[1],2*z,2*z,'#dcbb87');
    if(config.structure==='water'){
      const h=motion?Math.sin(clock*4)*.25:0;box(c,p,2,.4,.5,.6,.6,.8+h,['#a0aa8a','#677e60','#415d45','#bed0a2']);line(c,[p(2.3,.7,1.3+h),p(2.3,.7,2)],'#c0d2b3',3*z);
    }
    if(config.structure==='power'){
      const q=p(1.9,.8,1.3);ellipse(c,q[0],q[1],14*z,14*z,'#283d2d');c.save();c.translate(...q);if(motion)c.rotate(clock*3);for(let i=0;i<4;i++){c.rotate(Math.PI/2);line(c,[[0,0],[10*z,0]],'#b3ba8b',2*z);}c.restore();
    }
    // Weathering stays material-dependent and appears without horizontal block seams.
    const aging=1-integrity;
    if(aging>.03){for(let i=0;i<Math.round(aging*65);i++){
      const h=.9+noise(i,34)*(s.height-2),a=-.9+noise(i,87)*1.8;const q=pp(a,1,h);const l=(4+noise(i,8)*10)*z;
      const col=config.material==='metal'?'#bc805169':config.material==='wood'?'#303d206b':config.material==='fabric'?'#6a654477':'#142f2180';
      line(c,[[q[0],q[1]],[q[0]-2*z,q[1]+l*.6],[q[0]+2*z,q[1]+l]],col,.6*z+aging);
    }}
    if(snap.damage>.04){for(let i=0;i<Math.ceil(snap.damage*9);i++){const a=pp(-.7+noise(i,4),1,.9+noise(i,5)*(s.height-2));line(c,[[a[0],a[1]],[a[0]+8*z,a[1]+14*z],[a[0]+3*z,a[1]+26*z]],'#152e23',1.4*z);}}
  }
  lattice(c,p,z){
    c.save();c.globalAlpha=.44;for(let q=-6;q<=6;q++)for(let r=-6;r<=6;r++){
      if(Math.abs(q+r)>8)continue;const {x,y}=axialToWorld(q,r),pts=[];
      for(let i=0;i<6;i++){const a=(i*60+30)*Math.PI/180;pts.push(p(x+Math.cos(a)*HEX_SIZE,y+Math.sin(a)*HEX_SIZE,.08));}
      poly(c,pts,null,'#b6d496',.7*z);
    }c.restore();
  }
  annotation(c,p,x,y,label,z,offset,height=0){
    const q=p(x,y,height);const end=[q[0]+offset*z,q[1]-20*z];line(c,[q,[q[0]+offset*z*.25,q[1]-20*z],end],'#a5bb8a75',.7*z);
    ellipse(c,q[0],q[1],2*z,2*z,'#cfdfaf');c.font=`${Math.max(7,8*z)}px monospace`;c.fillStyle='#c4d6ac';c.textAlign=offset<0?'right':'left';c.fillText(label,end[0]+(offset<0?-5:5),end[1]+3*z);
  }
}
