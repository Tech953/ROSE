'use strict';
/* Original, short procedural cues. The player must enable audio with a gesture. */
window.RoseAudio=(()=>{
 let context=null,enabled=false;
 async function toggle(){
  if(enabled){enabled=false;return false;}
  const Audio=window.AudioContext||window.webkitAudioContext;
  if(!Audio)throw Error('Audio is unavailable in this browser.');
  context??=new Audio();await context.resume();enabled=context.state==='running';return enabled;
 }
 function play(action,pan=0){
  if(!enabled||!context||context.state!=='running')return;
  const sounds={hex_move:[95,55,.055,'triangle'],field_look:[540,360,.07,'sine'],structure_inspect:[540,360,.07,'sine'],structure_toggle:[160,70,.13,'square'],structure_draw:[740,380,.18,'sine'],structure_repair:[130,45,.16,'triangle'],structure_contract:[390,620,.12,'sine'],structure_fulfill:[390,780,.2,'sine'],attack:[100,35,.16,'triangle'],shoot:[430,50,.12,'sawtooth'],npc_talk:[280,370,.09,'sine'],field_dialogue:[280,370,.09,'sine'],companion_yield:[160,110,.06,'triangle']};
  const spec=sounds[action];if(!spec)return;
  try{const [start,end,duration,type]=spec,osc=context.createOscillator(),gain=context.createGain(),panner=context.createStereoPanner?.(),at=context.currentTime;
   osc.type=type;osc.frequency.setValueAtTime(start,at);osc.frequency.exponentialRampToValueAtTime(end,at+duration);gain.gain.setValueAtTime(.0001,at);gain.gain.exponentialRampToValueAtTime(.065,at+.008);gain.gain.exponentialRampToValueAtTime(.0001,at+duration);
   osc.connect(gain);if(panner){panner.pan.value=Math.max(-.8,Math.min(.8,pan));gain.connect(panner);panner.connect(context.destination);}else gain.connect(context.destination);
   osc.onended=()=>{osc.disconnect();gain.disconnect();panner?.disconnect();};osc.start(at);osc.stop(at+duration+.02);
  }catch{enabled=false;}
 }
 return{toggle,play,get enabled(){return enabled;}};
})();
