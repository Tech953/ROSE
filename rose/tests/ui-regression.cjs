/* Isolate native image banks between flows to keep the complete audit within memory bounds. */
'use strict';
const assert=require('node:assert/strict'),{spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path');
module.exports=async function(){
 const root=path.resolve(__dirname,'..'),flows=['--core','--direction','--materials','--weather','--animations','--particles'],results=[];
 for(const flow of flows){
  const started=Date.now();console.log('\nRUN: isolated interface flow '+flow);
  const code=await new Promise((resolve,reject)=>{const p=spawn(process.execPath,[path.join(__dirname,'ui-smoke.cjs'),flow],{cwd:root,stdio:'inherit',env:process.env});p.once('error',reject);p.once('exit',(code,signal)=>signal?reject(Error(flow+' terminated by '+signal)):resolve(code));});
  assert.equal(code,0,'Interface flow '+flow);results.push({flow,result:'PASS',seconds:(Date.now()-started)/1000});
 }
 fs.writeFileSync(path.join(root,'docs/ui-regression-audit-v018.json'),JSON.stringify({schema:1,engine_version:'0.18.0',result:'PASS',process_isolation:true,scope:'Real HTTP, modeled semantic DOM and native canvas; full browser layout and audible playback not tested',flows:results},null,2)+'\n');
 console.log('PASS: complete interface regression — all six isolated flows completed.');
};
