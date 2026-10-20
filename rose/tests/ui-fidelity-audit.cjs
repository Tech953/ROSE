/* Compare shipped and audited renderers with identical, frozen scene records. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
module.exports=async function({context,ids,read,canvasModule,root,baseline}){
 assert.ok(canvasModule,'The fidelity audit requires decoded native canvas pixels');
 const initial=JSON.stringify(read()),field=context.RoseField,lighting=context.RoseLighting;
 const profile=context.RoseDisplay.profile,enabled=context.RoseDisplay.enabled,mode=lighting.mode;
 const profiles=JSON.parse(fs.readFileSync(path.join(root,'static/lighting-signatures.json'),'utf8'));
 const canvas=canvasModule.createCanvas(2060,1380),c=canvas.getContext('2d'),metrics=[];
 c.fillStyle='#101812';c.fillRect(0,0,2060,1380);c.fillStyle='#d4c8ac';c.font='20px Courier New';
 c.fillText('ROSE 0.13.1 / PHYSICS AND GRAPHICAL FIDELITY AUDIT',20,32);
 c.font='13px Courier New';c.fillText('Frozen native scene fixture / identical sprites, geometry and camera / sharp display',20,55);
 try{
  context.RoseDisplay.configure(false,'sharp');
  for(const [row,region] of ['WN_TOWER','CITY_CLOUD_S'].entries()){
   const fixture=JSON.parse(initial);fixture.location.region=region;
   for(const node of fixture.scene.infrastructure.nodes){node.visual={...node.visual,model:node.kind+'_'+region};node.condition=90;node.enabled=true;node.connected=true;node.status='working';}
   for(const tile of Object.values(fixture.scene.tiles))if(tile.prefab==='rock')tile.visual={...tile.visual,model:'rock_'+region};
   let hits=null;
   for(const [column,current] of [false,true].entries()){
    if(current){context.RoseField=context.window.RoseField=field;context.RoseLighting=context.window.RoseLighting=lighting;field.reset();}
    else{
     for(const name of ['lighting','scene']){vm.runInContext(fs.readFileSync(path.join(baseline,name+'.js'),'utf8'),context);context[name==='lighting'?'RoseLighting':'RoseField']=context.window[name==='lighting'?'RoseLighting':'RoseField'];}
     context.RoseLighting.load(profiles);
    }
    context.RoseLighting.configure('signature');context.RoseField.render(fixture);context.RoseField.draw(0);
    const points=Object.values(fixture.scene.tiles).map(t=>context.RoseField.project(t.pos));
    const picks=points.map(p=>JSON.stringify(context.RoseField.hitAt(...p,0)));
    if(current)assert.deepEqual(picks,hits,'Surface and light changes retain every sampled scene pick');else hits=picks;
    const png=ids['field-canvas'].bitmap.toBuffer('image/png'),x=20+column*1020,y=80+row*650;
    c.fillStyle='#b5c6a6';c.font='14px Courier New';c.fillText(region+' / '+(current?'0.13.1 / connected paths and blocked light':'0.13.0 / shipped baseline'),x,y);
    c.drawImage(await canvasModule.loadImage(png),x,y+16);
    if(current){const start=performance.now();for(let i=0;i<20;i++)field.draw(0);metrics.push({region,frames:20,mean_draw_ms:(performance.now()-start)/20,hex_picks_checked:picks.length});}
   }
  }
  assert.equal(JSON.stringify(read()),initial,'Audit fixtures cannot mutate the real host world');
  fs.writeFileSync(path.join(root,'docs/Rose-audit-before-after.png'),canvas.toBuffer('image/png'));
  fs.writeFileSync(path.join(root,'docs/renderer-audit-v0131.json'),JSON.stringify({schema:1,engine_version:'0.13.1',backend:'@napi-rs/canvas and modeled DOM',fixture:'Frozen scene with enabled regional presentation copies; host state unchanged.',display:'sharp / CRT off',metrics,scope:'Native draw cost only; not browser layout, device FPS or Windows validation.'},null,2)+'\n');
 }finally{
  context.RoseField=context.window.RoseField=field;context.RoseLighting=context.window.RoseLighting=lighting;
  lighting.configure(mode);context.RoseDisplay.configure(enabled,profile);field.reset();field.render(JSON.parse(initial));
 }
 console.log('PASS: fidelity audit — matched baseline/current fixtures, exact sampled picking, native previews and unchanged host state.');
};
