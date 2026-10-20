/* Native pixels validate the display pass; a real host flow checks state and picking. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
function load(document){const context={window:{},document};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'static/display.js'),'utf8'),context);return context.window.RoseDisplay;}
module.exports=function(canvasModule){
 const unavailable=load({createElement:()=>({getContext:()=>null})});
 unavailable.configure(true,'soft');assert.equal(unavailable.present({},1000,620),false);assert.equal(unavailable.available,false);assert.equal(unavailable.present({},1000,620),false);
 if(!canvasModule){console.log('Display fallback passed; native pixel checks skipped.');return;}
 const {createCanvas}=canvasModule,buffers=[],display=load({createElement:()=>{const c=createCanvas(1,1);buffers.push(c);return c;}}),canvas=createCanvas(1000,620),ctx=canvas.getContext('2d');
 for(let y=0;y<620;y+=2)for(let x=0;x<1000;x+=2){ctx.fillStyle=((x+y)/2)%2?'#b0a98c':'#232920';ctx.fillRect(x,y,2,2);}
 const original=canvas.toBuffer('image/png');
 display.configure(false,'soft');assert.equal(display.present(ctx,1000,620),false);assert.deepEqual(canvas.toBuffer('image/png'),original);assert.equal(buffers.length,0);
 display.configure(true,'sharp');assert.equal(display.present(ctx,1000,620),false);assert.deepEqual(canvas.toBuffer('image/png'),original);assert.equal(buffers.length,0);
 display.configure(true,'soft');ctx.globalAlpha=.61;const priorAlpha=ctx.globalAlpha;ctx.globalCompositeOperation='source-over';ctx.imageSmoothingEnabled=false;
 assert.equal(display.present(ctx,1000,620),true);assert.notDeepEqual(canvas.toBuffer('image/png'),original);assert.equal(buffers[0].width,800);assert.equal(buffers[0].height,496);assert.equal(ctx.globalAlpha,priorAlpha);assert.equal(ctx.globalCompositeOperation,'source-over');assert.equal(ctx.imageSmoothingEnabled,false);
 display.present(ctx,1000,620);assert.equal(buffers.length,2,'Buffers are reused rather than allocated every frame');
 const small=createCanvas(320,200);display.present(small.getContext('2d'),320,200);assert.equal(buffers[0].width,320);assert.equal(buffers[0].height,200);
 console.log('Display checks passed: exact off/sharp, soft pixels, aspect ratio, context restoration, buffer reuse and fallback.');
};
module.exports.flow=async function({context,ids,read,canvasModule}){
 const state=JSON.stringify(read()),revision=read().revision,now=performance.now(),samples=Object.values(read().scene.tiles).map(t=>context.RoseField.project(t.pos));
 const hits=()=>samples.map(p=>JSON.stringify(context.RoseField.hitAt(...p,now)));
 const priorHits=hits();
 let trace=[],nativeText=null,nativePresent=null,c=null;
 if(canvasModule){c=ids['field-canvas'].bitmap.getContext('2d');nativeText=c.fillText;nativePresent=context.RoseDisplay.present;
  c.fillText=function(...args){trace.push({text:args,font:this.font,fill:this.fillStyle,alpha:this.globalAlpha});return nativeText.apply(this,args);};
  context.RoseDisplay.present=function(...args){trace.push('display');return nativePresent(...args);};
 }
 const frame=()=>{trace=[];context.RoseField.draw(now);if(canvasModule){assert.equal(trace[0],'display','Field labels are painted after the display pass');assert.ok(trace.length>4);return JSON.stringify(trace.slice(1));}};
 assert.equal(context.RoseDisplay.profile,'soft');
 ids['display-profile'].value='sharp';ids['display-profile'].onchange();const sharpText=frame();
 assert.equal(context.RoseDisplay.profile,'sharp');assert.equal(context.localStorage.getItem('rose-display-profile'),'sharp');
 let sharp=null,soft=null,sharpCanvas=null;
 if(canvasModule){sharp=ids['field-canvas'].bitmap.toBuffer('image/png');sharpCanvas=await canvasModule.loadImage(sharp);assert.equal(sharpCanvas.width,1000);}
 ids['display-profile'].value='soft';ids['display-profile'].onchange();assert.equal(frame(),sharpText,'Text, font, coordinates, color and alpha retain native settings');
 assert.equal(context.RoseDisplay.profile,'soft');assert.deepEqual(hits(),priorHits);
 if(canvasModule){soft=ids['field-canvas'].bitmap.toBuffer('image/png');assert.notDeepEqual(soft,sharp);
  fs.writeFileSync(path.join(root,'docs/Rose-sharp-field-preview.png'),sharp);fs.writeFileSync(path.join(root,'docs/Rose-soft-field-preview.png'),soft);
  const comparison=canvasModule.createCanvas(2060,720),view=comparison.getContext('2d');view.fillStyle='#101812';view.fillRect(0,0,2060,720);view.font='20px Courier New';view.fillStyle='#d3c7a6';view.fillText('ROSE / INDIVIDUAL FIELD PREFABS',20,34);view.font='14px Courier New';view.fillStyle='#91ab91';view.fillText('SHARP PIXELS / native field',20,60);view.fillText('SOFT PHOSPHOR / field softened, labels native',1040,60);view.imageSmoothingEnabled=false;view.drawImage(sharpCanvas,20,76);view.drawImage(await canvasModule.loadImage(soft),1040,76);fs.writeFileSync(path.join(root,'docs/Rose-display-comparison.png'),comparison.toBuffer('image/png'));
 }
 ids['display-profile'].value='soft';ids['display-profile'].onchange();
 ids.crt.click();assert.equal(context.RoseDisplay.enabled,false);assert.match(ids['display-note'].textContent,/disabled/);context.RoseField.draw(now);
 if(canvasModule)assert.deepEqual(ids['field-canvas'].bitmap.toBuffer('image/png'),sharp,'CRT off fully bypasses the display pass');
 ids.crt.click();assert.equal(context.RoseDisplay.enabled,true);assert.equal(context.localStorage.getItem('rose-crt'),'on');assert.equal(context.localStorage.getItem('rose-display-profile'),'soft');
 assert.equal(read().revision,revision);assert.equal(JSON.stringify(read()),state);assert.deepEqual(hits(),priorHits);
 if(canvasModule){c.fillText=nativeText;context.RoseDisplay.present=nativePresent;}
 console.log('Display host flow passed: profiles, preferences, native label settings/order, picking and unchanged world state.');
};
