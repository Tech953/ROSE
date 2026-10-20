/* Loading larger art banks must stay bounded, share aliases and drain after errors. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
function setup(){
 const images=[];let active=0,peak=0;
 class Image{set src(url){this.url=url;images.push(this);active++;peak=Math.max(peak,active);}finish(error=false){assert.ok(!this.finished);this.finished=true;active--;if(error)this.onerror();else this.onload();}}
 const context={window:{},Image};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/prefabs.js'),'utf8'),context);
 return {art:context.window.RosePrefabs,images,get peak(){return peak;}};
}
const asset=image=>({kind:'sprite',image}),flush=async()=>{for(let i=0;i<4;i++)await Promise.resolve();};
async function drain(fixture){while(fixture.images.some(image=>!image.finished)){fixture.images.find(image=>!image.finished).finish();await flush();}}
module.exports=async function(){
 const f=setup(),assets=Object.fromEntries(Array.from({length:8},(_,i)=>['unit'+i,asset('/art/unit'+i+'.png')]));assets.alias=asset('/art/unit0.png');assets.secondAlias=asset('/art/unit0.png');
 let ready=false;const current=f.art.load({style:'rendered',assets}).then(()=>{ready=true;});
 const legacy=f.art.load({style:'rendered-legacy',assets:{shared:asset('/art/unit0.png'),old:asset('/art/old.png')}});
 assert.equal(f.images.length,6,'Only a bounded batch begins before any decode finishes');assert.equal(ready,false,'Readiness waits for every required image');
 await drain(f);await Promise.all([current,legacy]);assert.ok(ready);assert.equal(f.images.length,9,'Aliases and banks share one URL decode');assert.ok(f.peak<=6,'All art banks share the concurrency bound');assert.equal(f.art.loaded,10);
 f.art.setStyle('rendered-legacy');await f.art.ready;assert.equal(f.art.loaded,2,'Bank readiness and entries remain isolated');
 const broken=setup(),badAssets=Object.fromEntries(Array.from({length:10},(_,i)=>['unit'+i,asset('/art/failure'+i+'.png')]));
 const failed=broken.art.load({style:'rendered',assets:badAssets}).then(()=>null,error=>error);
 broken.images[0].finish(true);await flush();await drain(broken);const error=await failed;
 assert.match(error.message,/Unable to load \/art\/failure0.png/);assert.equal(broken.images.length,10,'A failed decode releases its slot for queued images');assert.equal(broken.art.loaded,9,'Other images can finish after a decode failure');assert.ok(broken.peak<=6);
 console.log('PASS: sprite loading — bounded requests, shared URL decoding, complete readiness, isolated banks and queue recovery after failure.');
};
