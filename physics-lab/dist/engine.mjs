// Rose.ENGINE lab: deterministic, game-tuned emulation, not engineering analysis.
export const MATERIALS = {
  stone: { name:'Basalt stone', short:'Stone', color:'#708579', light:'#a2aaa0', dark:'#364b46', density:2850, strength:38, friction:.72, restitution:.12, decay:.09, salvage:.50, mode:'Brittle fracture', weather:'Surface erosion → fissures → fragmentation' },
  metal: { name:'Weathering metal', short:'Metal', color:'#798e91', light:'#c0cecb', dark:'#354a51', density:7800, strength:62, friction:.48, restitution:.32, decay:.18, salvage:.60, mode:'Yield & buckle', weather:'Oxidation → section loss → buckling' },
  crystal: { name:'Relay crystal', short:'Crystal', color:'#719e99', light:'#b4e6d0', dark:'#2c5959', density:2600, strength:28, friction:.36, restitution:.40, decay:.07, salvage:.40, mode:'Cleavage fracture', weather:'Surface haze → microcracks → cleavage' },
  wood: { name:'Structural timber', short:'Wood', color:'#947a59', light:'#bfaa7e', dark:'#524534', density:650, strength:15, friction:.60, restitution:.18, decay:.40, salvage:.40, mode:'Split & splinter', weather:'Moisture uptake → rot → splitting' },
  polymer: { name:'Composite polymer', short:'Polymer', color:'#95968a', light:'#d2d0b9', dark:'#50554e', density:1350, strength:23, friction:.44, restitution:.56, decay:.22, salvage:.40, mode:'Flex & tear', weather:'UV embrittlement → crazing → tearing' },
  fabric: { name:'Woven membrane', short:'Fabric', color:'#b19379', light:'#dbc6a2', dark:'#67554e', density:420, strength:6, friction:.55, restitution:.08, decay:.48, salvage:.20, mode:'Tension tear', weather:'Fading → fiber wear → tension failure' }
};
export const STRUCTURES = {
  relay: { name:'Relay monolith', height:9.7, volume:9, area:.014, lever:4.8, stiffness:180000, kind:'Relay', description:'A single cast core on a human-scale service base.' },
  water: { name:'Water core', height:8.4, volume:13, area:.020, lever:4.1, stiffness:220000, kind:'Water', description:'A solid reservoir body with a reciprocating service pump.' },
  power: { name:'Power core', height:10.8, volume:11, area:.0165, lever:5.1, stiffness:200000, kind:'Power', description:'A monolithic housing with a damped rotor at its base.' },
  span: { name:'Raised causeway', height:4.5, volume:12, area:.008, lever:7.8, stiffness:90000, kind:'Transit', description:'One continuous deck supported by two piers.' },
  canopy: { name:'Tension canopy', height:5.4, volume:2, area:.0035, lever:3.5, stiffness:24000, kind:'Shelter', description:'A weather-responsive membrane over a service frame.' }
};
export const DEFAULTS = {material:'stone',structure:'relay',force:'impact',magnitude:480,angle:35,age:12,weather:45,use:30,friction:.72,damping:.65,scale:'site',scenario:'custom'};
export const PRESETS = {
  impact:{label:'Lateral impact',material:'stone',structure:'relay',force:'impact',magnitude:720,age:12,weather:45,use:30},
  weather:{label:'A century of weather',material:'metal',structure:'water',force:'load',magnitude:180,age:100,weather:85,use:60},
  seismic:{label:'Foundation failure',material:'stone',structure:'span',force:'seismic',magnitude:1000,age:45,weather:60,use:70},
  wind:{label:'Storm & membrane',material:'fabric',structure:'canopy',force:'wind',magnitude:360,age:18,weather:75,use:40}
};
export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function normalize(input={}) {
  const s={...DEFAULTS,...input};
  for(const [key,map] of [['material',MATERIALS],['structure',STRUCTURES]]) if(!map[s[key]])s[key]=DEFAULTS[key];
  if(!['impact','load','wind','seismic'].includes(s.force))s.force='impact';
  for(const [key,min,max] of [['magnitude',0,1200],['angle',0,90],['age',0,150],['weather',0,100],['use',0,100],['friction',0,1],['damping',0,1]]) s[key]=clamp(Number.isFinite(+s[key])?+s[key]:DEFAULTS[key],min,max);
  if(!['site','landscape','detail'].includes(s.scale))s.scale='site';
  return s;
}
export function properties(config) {
  const c=normalize(config),m=MATERIALS[c.material],s=STRUCTURES[c.structure];
  const loss=clamp(c.age/150*m.decay*(.3+c.weather/70+c.use/160),0,.88);
  const integrity=clamp(1-loss,0,1),mass=m.density*s.volume;
  const capacity=m.strength*s.area*1e6*integrity**2;
  const fatigue=1-c.use/400;
  return {mass,integrity,loss,capacity:capacity*fatigue,stiffness:s.stiffness*integrity,ratio:s.height/1.8};
}
export class Lab {
  constructor(config) {this.config=normalize(config);this.history=[];this.reset(false);}
  reset(log=true) {
    this.props=properties(this.config);this.integrity=this.props.integrity;this.damage=0;this.x=0;this.v=0;this.rotation=0;
    this.time=0;this.steps=0;this.energy=0;this.peak=0;this.force=0;this.running=false;this.active=false;this.collapsed=false;
    this.salvage=0;this.salvaged=0;this.stock=this.props.mass;this.blocked=false;this.connected=true;this.rubble=[];this.history=[];this.elapsed=0;this.acc=0;
    this.before=this.snapshot();if(log)this.record('Specimen reset','Aged baseline restored.');
  }
  configure(patch) {this.config=normalize({...this.config,...patch});this.reset(false);this.record('Specimen prepared',`${MATERIALS[this.config.material].short} · ${STRUCTURES[this.config.structure].name}`);}
  record(title,detail) {this.history.unshift({time:this.time,title,detail});this.history=this.history.slice(0,12);}
  snapshot() {return {config:{...this.config},integrity:this.integrity,damage:this.damage,x:this.x,v:this.v,rotation:this.rotation,time:this.time,energy:this.energy,peak:this.peak,force:this.force,collapsed:this.collapsed,salvage:this.salvage,salvaged:this.salvaged,stock:this.stock,blocked:this.blocked,connected:this.connected,rubble:this.rubble?.map(r=>({...r}))||[]};}
  trigger() {
    if(this.collapsed)return false;
    this.before=this.snapshot();this.active=true;this.running=true;this.elapsed=0;
    const f=this.config.magnitude*1000;this.peak=Math.max(this.peak,f);this.force=f;
    if(this.config.force==='impact') {const j=f*.12;this.v+=j*Math.cos(this.config.angle*Math.PI/180)/this.props.mass;this.energy+=j*j/(2*this.props.mass);}
    this.record('Force applied',`${this.config.magnitude} kN · ${this.config.force}`);return true;
  }
  step(dt=1/60) {
    if(!this.running)return;
    this.acc+=clamp(dt,0,.1);
    while(this.acc>=1/60){this.integrate(1/60);this.acc-=1/60;}
  }
  integrate(dt) {
    this.time+=dt;this.steps++;this.elapsed+=dt;
    const c=this.config,p=this.props,s=STRUCTURES[c.structure];
    const duration=c.force==='impact'?.12:c.force==='seismic'?3:4;
    let f=0;
    if(this.active&&this.elapsed<duration) {
      const base=c.magnitude*1000;
      f=c.force==='impact'?base:c.force==='seismic'?base*Math.sin(this.elapsed*17):c.force==='wind'?base*(.7+.3*Math.sin(this.elapsed*6)):base;
      if(c.force!=='impact')this.energy+=Math.abs(f*this.v*dt);
    }else this.active=false;
    this.force=f;this.peak=Math.max(this.peak,Math.abs(f));
    const lateral=Math.cos(c.angle*Math.PI/180);
    const stress=Math.abs(f)*(.25+.75*lateral)*(s.lever/4.8);
    const ratio=stress/Math.max(1,p.capacity);
    if(!this.collapsed) {
      const dd=Math.max(0,ratio-.30)*dt*(c.force==='impact'?1.9:.15);
      this.damage=clamp(this.damage+dd,0,1);this.integrity=clamp(p.integrity-this.damage,0,1);
      const forceX=c.force==='impact'?0:f*lateral;
      const spring=-p.stiffness*this.x;
      const damp=-2*Math.sqrt(p.stiffness*p.mass)*c.damping*this.v;
      const friction=-Math.sign(this.v)*c.friction*p.mass*9.81*.05;
      this.v+=(forceX+spring+damp+friction)/p.mass*dt;
      this.x=clamp(this.x+this.v*dt,-12,12);this.rotation=clamp(this.x/s.height,-.8,.8);
      if(this.integrity<.17||Math.abs(this.rotation)>.65)this.collapse();
    }else {
      this.rubble.forEach(r=>{r.vz-=9.81*dt;r.x+=r.vx*dt;r.z+=r.vz*dt;r.rotation+=r.spin*dt;
        if(r.z<0){r.z=0;r.vz=Math.abs(r.vz)*MATERIALS[c.material].restitution;r.vx*=1-c.friction*.18;r.spin*=.8;
          if(Math.abs(r.vz)<.3)r.vz=0;} });
    }
    if(!this.active&&this.elapsed>7){this.running=false;this.v=0;this.record('Run complete',this.collapsed?'Rubble footprint persists.':'The damped response has settled.');}
  }
  collapse() {
    if(this.collapsed)return false;
    this.collapsed=true;this.integrity=0;this.connected=false;this.blocked=true;this.running=true;this.active=false;this.elapsed=0;
    this.salvage=Math.floor(this.props.mass*MATERIALS[this.config.material].salvage);this.salvaged=0;
    this.rubble=Array.from({length:22},(_,i)=>({x:0,y:0,z:1+(i%6)*.65,vx:Math.sin(i*2.4)*(1.3+i%3),vy:Math.cos(i*3)*1.4,vz:2+(i%5)*.7,rotation:i*.5,spin:Math.sin(i)*1.6,size:.4+(i%4)*.22}));
    this.record('Structural collapse','Connections lost · cover lost · footprint blocked.');return true;
  }
  salvageRubble() {
    if(!this.collapsed||this.salvage===0)return 0;
    const n=this.salvage;this.salvaged+=n;this.stock+=n;this.salvage=0;this.blocked=false;this.rubble=[];this.running=false;
    this.record('Salvage recovered',`${n.toLocaleString()} kg recovered. Footprint cleared.`);return n;
  }
  repair() {
    const cost=Math.ceil(this.props.mass*.02);
    if(this.collapsed||this.damage<=0||this.stock<cost)return false;
    this.stock-=cost;this.damage=Math.max(0,this.damage-.25);this.integrity=this.props.integrity-this.damage;this.x=0;this.v=0;this.rotation=0;this.running=false;this.active=false;this.force=0;
    this.record('Structure repaired',`${cost.toLocaleString()} kg spent; up to 25% load damage removed. Age retained.`);return true;
  }
  rebuild() {
    if(!this.collapsed||this.blocked||this.stock<this.props.mass)return false;
    const remaining=this.stock-this.props.mass;this.reset(false);this.stock=remaining;this.record('Structure rebuilt',`${this.props.mass.toLocaleString()} kg spent; ${remaining.toLocaleString()} kg remains.`);return true;
  }
  advanceAge(years=10) {this.configure({age:clamp(this.config.age+years,0,150)});this.record('Weather exposure advanced',`${this.config.age} equivalent years · ${this.config.weather}% exposure.`);}
  get status(){return this.collapsed?(this.blocked?'Collapsed · blocked':'Cleared · ready to rebuild'):this.integrity<.45?'Critical':this.damage>.02?'Damaged':'Stable';}
}
export function axialRound(q,r) {
  let x=Math.round(q),z=Math.round(r),y=Math.round(-q-r);const dx=Math.abs(x-q),dz=Math.abs(z-r),dy=Math.abs(y+q+r);
  if(dx>dy&&dx>dz)x=-y-z;else if(dz>dy)z=-x-y;return {q:x||0,r:z||0};
}
export const HEX_SIZE=1.2;
export function axialToWorld(q,r){return {x:Math.sqrt(3)*(q+r/2)*HEX_SIZE,y:1.5*r*HEX_SIZE};}
export function worldToAxial(x,y){return axialRound((Math.sqrt(3)/3*x-y/3)/HEX_SIZE,(2*y/3)/HEX_SIZE);}
