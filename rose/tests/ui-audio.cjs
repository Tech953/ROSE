/* Web Audio node contract; this does not test speakers or browser autoplay policy. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
module.exports=async()=>{
 const oscillators=[],panners=[],gains=[];let resumed=0;
 const param=()=>({events:[],setValueAtTime(v,t){this.events.push([v,t]);},exponentialRampToValueAtTime(v,t){this.events.push([v,t]);}});
 const node=()=>({connect(){},disconnect(){this.disconnected=true;}});
 class AudioContext{constructor(){this.state='suspended';this.currentTime=10;this.destination={};}async resume(){resumed++;this.state='running';}createOscillator(){const n={...node(),frequency:param(),start(t){this.startTime=t;},stop(t){this.stopTime=t;}};oscillators.push(n);return n;}createGain(){const n={...node(),gain:param()};gains.push(n);return n;}createStereoPanner(){const n={...node(),pan:{value:0}};panners.push(n);return n;}}
 const context={window:{AudioContext}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/audio.js'),'utf8'),context);const audio=context.window.RoseAudio;
 audio.play('hex_move',1);assert.equal(oscillators.length,0,'Cues stay silent before explicit enable');assert.equal(await audio.toggle(),true);assert.equal(resumed,1);
 audio.play('structure_draw',1);assert.equal(oscillators.length,1);assert.equal(panners[0].pan.value,.8);assert.equal(oscillators[0].type,'sine');assert.ok(oscillators[0].stopTime>oscillators[0].startTime);assert.equal(gains[0].gain.events.at(-1)[0],.0001);
 oscillators[0].onended();assert.equal(oscillators[0].disconnected,true);assert.equal(gains[0].disconnected,true);assert.equal(panners[0].disconnected,true);
 assert.equal(await audio.toggle(),false);audio.play('shoot',-1);assert.equal(oscillators.length,1,'Muting prevents new nodes');
 console.log('PASS: audio node contract — explicit enable, mute, short envelopes, bounded panning and node cleanup. Live browser/audio playback remains untested.');
};
