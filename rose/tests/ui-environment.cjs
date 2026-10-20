/* Native pixels and accessible controls share authoritative ecology/project state. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
module.exports=async({context,ids,read,canvasModule,root})=>{
 const original=JSON.parse(JSON.stringify(read())),host=JSON.stringify(read());
 assert.ok(ids['environment-summary'].textContent.includes('SOIL'));assert.equal(ids['construction-kind'].children.length,6);
 assert.ok(ids['construction-cost'].textContent.includes('RESERVED'));assert.ok(ids['particle-summary'].textContent.includes('12 INDIVIDUAL PARTICLES'));
 for(let i=0;i<100&&!context.RoseSurvey.data;i++)await new Promise(r=>setTimeout(r,10));assert.ok(context.RoseSurvey.data,'Converted survey loads from the real host');
 const survey=context.RoseSurvey.data;assert.equal(survey.features.filter(f=>f.kind==='anchor').length,3);assert.equal(survey.scale.metric_transform,null);
 context.RoseSurvey.choose('red-gate');ids['survey-approach'].click();assert.equal(ids['atlas-destination'].value,'red_gate');assert.equal(JSON.stringify(read()),host,'Selecting a survey approach does not move or discover');
 context.RoseSurvey.choose('scarlet-plateau');assert.equal(ids['survey-approach'].hidden,true,'No invented route for an unregistered continental feature');
 const response=await context.fetch('/continental-reference.jpg');assert.ok(response.ok);assert.match(response.headers.get('content-type'),/image\/jpeg/);
 assert.throws(()=>context.RoseSurvey.load({schema:1,features:[{id:'bad',geometry:'point',points:[[Infinity,0]]}]}),/Invalid/);
 context.RoseSurvey.load(survey);
 if(canvasModule){
  context.RoseSurvey.draw();fs.writeFileSync(path.join(root,'docs/Rose-continental-survey.png'),ids['survey-canvas'].bitmap.toBuffer('image/png'));
  context.RoseParticulate.draw();const plot=ids['particle-canvas'].bitmap.toBuffer('image/png');assert.ok(plot.length>10000);fs.writeFileSync(path.join(root,'docs/Rose-particle-preview.png'),plot);
  const collage=canvasModule.createCanvas(1000,1980),out=collage.getContext('2d');out.fillStyle='#111a16';out.fillRect(0,0,1000,1980);out.font='16px "Courier New", monospace';
  const value=JSON.parse(JSON.stringify(original));value.scene.units=value.scene.units.filter(n=>n.mine);value.scene.infrastructure.nodes=[];
  const pos=Object.values(value.scene.tiles).find(n=>n.passable&&Math.max(Math.abs(n.pos[0]),Math.abs(n.pos[1]))===2).pos;
  const project={id:'project-visual',kind:'shelter',pos,stage:'foundation',work_done:0,work_required:5,escrow:5,spent:0,material:'registered regional material',visual:{model:'shelter_'+value.location.region,tone:0},actions:[]};
  value.scene.lifecycle.projects=[project];value.scene.tiles[pos.join(',')].passable=false;
  const tops=[];for(const[i,work]of [0,2,4].entries()){
   project.work_done=work;project.stage=['foundation','frame','finishing'][i];value.scene.lifecycle.moisture=[70,40,10][i];value.scene.lifecycle.litter=[8,20,50][i];value.scene.lifecycle.erosion=[3,12,35][i];value.scene.lifecycle.plantings=[{id:'plant-proof',species:'registered patch',stage:['seedling','established','wilted'][i],age:4+i*6,stress:i*3,pos:[-2,0]}];
   context.RoseField.render(value);context.RoseField.select({type:'project',id:project.id});context.RoseField.draw(0);
   const prop={type:'project',node:project,asset:context.RosePrefabs.assetFor(project,project.kind),pose:'worn',time:0,facing:0},b=context.RoseEnvironment.bounds(prop),full=context.RosePrefabs.bounds(prop.asset,'worn',0,0);tops.push(b[1]);
   assert.ok(b[3]<full[3]);assert.equal(context.RoseEnvironment.hit(prop,[0,b[1]-1]),false,'Undrawn upper building cannot own a click');
   assert.equal(ids['field-detail'].hidden,false);assert.match(ids['field-selection'].textContent,/reserved 5/);
   out.fillStyle='#c8d3b7';out.fillText(['FOUNDATION / DAMP SEEDLING','FRAME / ESTABLISHED PATCH','FINISHING / DRY, WILTED PATCH'][i],24,i*660+26);const shot=await canvasModule.loadImage(ids['field-canvas'].bitmap.toBuffer('image/png'));assert.equal(shot.width,1000);out.drawImage(shot,0,i*660+40);
  }
  assert.ok(tops[0]>tops[1]&&tops[1]>tops[2],'Physical work reveals progressively more of the same prefab');fs.writeFileSync(path.join(root,'docs/Rose-environment-preview.png'),collage.toBuffer('image/png'));
 }
 context.RoseField.render(original);context.RoseParticulate.render(original);assert.equal(JSON.stringify(read()),host,'Every survey, particle and environment preview leaves host state untouched');
 console.log('PASS: environment interface — measured ecology, six blueprints, clipped construction draw/hit bounds, particle readout, converted survey, guarded approach selection and unchanged host state.');
};
