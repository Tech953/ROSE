/* Failure paths in the real interface logic. DOM behavior is modeled, not browser-certified. */
const assert=require('node:assert/strict'),vm=require('node:vm');
const clone=value=>JSON.parse(JSON.stringify(value));
const waitFor=async predicate=>{const deadline=Date.now()+10000;while(!predicate()&&Date.now()<deadline)await new Promise(r=>setTimeout(r,10));assert.ok(predicate(),'Deferred operation became available');};
module.exports=async({context,ids,document,read,get,command,base,tmp,setupInterface})=>{
 const keyed=key=>document.querySelectorAll('[data-ui-key]').find(n=>n.dataset.uiKey===key),originalFetch=context.fetch;
 const npc=read().companions.roster[0].id;
 keyed('npc:'+npc+':designation').open=true;
 keyed('npc:'+npc+':supply').value='food';
 const chosenTask=read().companions.tasks.find(t=>t!==read().companions.roster[0].engagement.task);
 keyed('npc:'+npc+':task').value=chosenTask;keyed('npc:'+npc+':task').focus();
 const option=ids['field-destination'].children[0],atlasOption=ids['atlas-destination'].children[0];
 await command('look');
 assert.equal(keyed('npc:'+npc+':designation').open,true);
 assert.equal(keyed('npc:'+npc+':supply').value,'food');
 assert.equal(keyed('npc:'+npc+':task').value,chosenTask);
 assert.equal(document.activeElement,keyed('npc:'+npc+':task'));
 assert.equal(ids['field-destination'].children[0],option);
 assert.equal(ids['atlas-destination'].children[0],atlasOption);
 await ids.pause.click();vm.runInContext('lock(true);lock(false);',context);
 assert.equal(ids['walk-path'].disabled,true);assert.equal(ids['world-point-go'].disabled,true);
 assert.equal(ids.disconnect.disabled,false);assert.equal(ids.crt.disabled,false);
 await ids.pause.click();
 const beforeCharacter=JSON.stringify(context.RoseCreator.read()),bad=clone(context.RoseCreator.read());
 bad.voice='An invalid replacement';bad.attributes.body=9;
 const payload=JSON.stringify({format:'Rose-character',version:2,role:context.RoseCreator.role(),character:bad});
 await ids['character-import'].onchange({target:{files:[{size:Buffer.byteLength(payload),text:async()=>payload}],value:'template.json'}});
 assert.equal(JSON.stringify(context.RoseCreator.read()),beforeCharacter);assert.match(ids['character-message'].textContent,/previous draft is retained/);

 const saved=clone(read()),frame=clone(read());frame.atlas.navigation.status='traveling';frame.atlas.navigation.mode='world';
 context.RoseWorld.render(frame);const spoken=ids['world-announcement'].textContent;
 frame.atlas.position[0]+=.1;frame.atlas.navigation.serial++;context.RoseWorld.render(frame);
 assert.equal(ids['world-announcement'].textContent,spoken,'Coordinates do not repeatedly announce');
 const other=clone(frame);other.code='OTHER123';other.me.id='other-seat';other.atlas.position=[-12,4];other.atlas.navigation.point=[-12,4];
 const ctx=ids['world-canvas'].getContext('2d'),arc=ctx.arc,circles=[];ctx.arc=function(...args){if(args[2]===12)circles.push(args.slice(0,2));return arc.apply(this,args);};
 context.RoseWorld.render(other);ctx.arc=arc;assert.deepEqual(circles.at(-1),Array.from(context.RoseWorld.project([-12,4])),'New room resets the marker even when serials match');
 context.RoseField.select({type:'hex',pos:[0,0]});context.RoseField.render(other);
 assert.match(ids['field-selection'].textContent,/Choose a destination/,'New room clears the previous selection');
 assert.equal(ids['field-object'].value,'','Room entry does not automatically select scenery');
 assert.equal(ids['field-detail'].hidden,true,'Room entry has no automatic inspection or route overlay');
 vm.runInContext('render()',context);

 for(const response of [()=>({ok:true,json:async()=>{throw new SyntaxError('Not JSON');}}),()=>({ok:true,json:async()=>({})})]){
  const before=JSON.stringify(read().me);
  context.fetch=(url,options)=>JSON.parse(options?.body||'{}').op==='act'?Promise.resolve(response()):originalFetch(url,options);
  ids.prompt.value='wait';await ids['action-form'].requestSubmit();assert.equal(ids.prompt.value,'wait');assert.equal(JSON.stringify(read().me),before);assert.match(ids.error.textContent,/unreadable|invalid world response/);
 }
 context.fetch=originalFetch;
 let release=null,stateCalls=0;const stale=clone(read());
 context.fetch=(url,options)=>{if(JSON.parse(options?.body||'{}').op==='state'&&!release){stateCalls++;return new Promise(resolve=>release=()=>resolve({ok:true,json:async()=>stale}));}return originalFetch(url,options);};
 const pending=vm.runInContext('poll()',context);await vm.runInContext('poll()',context);assert.equal(stateCalls,1,'Polling cannot overlap');
 await command('look');const latestRevision=read().revision;assert.ok(latestRevision>stale.revision);release();await pending;assert.equal(read().revision,latestRevision,'A delayed poll cannot overwrite the action');
 context.fetch=originalFetch;
 release=null;const leaving=clone(read());
 context.fetch=(url,options)=>JSON.parse(options?.body||'{}').op==='state'?new Promise(resolve=>release=()=>resolve({ok:true,json:async()=>leaving})):originalFetch(url,options);
 const abandoned=vm.runInContext('poll()',context);await ids.disconnect.click();release();await abandoned;
 assert.equal(read(),null);assert.equal(ids.game.hidden,true);assert.equal(ids.entry.hidden,false);
 context.fetch=originalFetch;await ids.resume.click();assert.equal(read().me.id,saved.me.id);

 const scene=read().scene,body=scene.units.find(u=>u.mine),destination=scene.reachable.find(p=>context.RoseField.path(body.pos,p)?.length>=3);
 assert.ok(destination);context.RoseField.select({type:'hex',pos:destination});let steps=0;release=null;
 context.fetch=async(url,options)=>{if(JSON.parse(options?.body||'{}').intent?.action==='hex_move'){steps++;const response=await originalFetch(url,options);return new Promise(resolve=>release=()=>resolve(response));}return originalFetch(url,options);};
 const walking=ids['walk-path'].click();await waitFor(()=>!!release);assert.equal(ids.disconnect.disabled,false);
 await ids.disconnect.click();release();await walking;assert.equal(steps,1,'Disconnect cancels the remaining route');assert.equal(read(),null);assert.equal(ids.game.hidden,true);
 context.fetch=originalFetch;await ids.resume.click();

 const originalAbort=context.AbortSignal;context.AbortSignal={};context.AbortController=AbortController;
 context.fetch=(url,options)=>{assert.ok(options.signal instanceof AbortSignal);return Promise.resolve({ok:true,json:async()=>({})});};
 await vm.runInContext("api('export')",context);context.fetch=originalFetch;context.AbortSignal=originalAbort;
 const unchanged=JSON.stringify(read().me);context.fetch=(url,options)=>JSON.parse(options?.body||'{}').op==='act'?Promise.reject(Object.assign(Error('Timed out'),{name:'TimeoutError'})):originalFetch(url,options);
 ids.prompt.value='wait';await ids['action-form'].requestSubmit();assert.equal(ids.prompt.value,'wait');assert.equal(JSON.stringify(read().me),unchanged);assert.match(ids.error.textContent,/did not respond in time/);context.fetch=originalFetch;
 console.log('PASS: assurance flows — stable NPC details/drafts/focus, unchanged menus, contextual locks, rejected import rollback, quieter announcements, room identity, malformed responses, serialized polls, stale-response rejection, disconnect during poll/walk, and timeout fallback.');

 const blocked={getItem(){throw Error('Storage blocked');},setItem(){throw Error('Storage blocked');},removeItem(){throw Error('Storage blocked');}};
 const restricted=setupInterface(base,tmp,{localStorage:blocked,sessionStorage:blocked});
 await waitFor(()=>restricted.context.RoseCreator.ready);
 await restricted.ids.crt.click();restricted.ids['display-profile'].value='sharp';restricted.ids['display-profile'].onchange();assert.equal(restricted.context.RoseDisplay.profile,'sharp');restricted.ids['art-style'].value='vector';restricted.ids['art-style'].onchange();
 await restricted.ids['character-draft'].click();assert.match(restricted.ids['character-message'].textContent,/storage is unavailable/);
 restricted.ids.name.value='Restricted storage';restricted.ids.seed.value='restricted-storage';await restricted.ids['join-form'].requestSubmit();
 assert.equal(restricted.ids.game.hidden,false,restricted.ids.error.textContent);assert.match(restricted.ids.error.textContent,/cannot be remembered/);
 await restricted.ids.disconnect.click();assert.equal(restricted.ids.entry.hidden,false);
 const invalid={getItem(){return '{corrupt json';},setItem(){},removeItem(){}};
 const corrupt=setupInterface(base,tmp,{localStorage:invalid,sessionStorage:invalid});await waitFor(()=>corrupt.context.RoseCreator.ready);
 assert.equal(vm.runInContext('session',corrupt.context),null);assert.equal(corrupt.ids.resume.hidden,true);
 console.log('PASS: restricted-storage and corrupt-session startup; creation, graphics preferences and disconnect continue safely.');
};
