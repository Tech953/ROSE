/* Real host + shipped HTML/JS, with a parsed semantic DOM (not browser layout). */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {spawn,spawnSync}=require('node:child_process');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const parser=String.raw`import json,sys
from html.parser import HTMLParser
class Parser(HTMLParser):
 def __init__(self):
  super().__init__();self.root={'tag':'document','attrs':{},'children':[]};self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  node={'tag':tag,'attrs':dict((k,v or '') for k,v in attrs),'children':[]};self.stack[-1]['children'].append(node)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(node)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i]['tag']==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1]['children'].append(data)
p=Parser();p.feed(sys.stdin.read());print(json.dumps(p.root))`;
class Element{
 constructor(tag,attrs={}){this.tagName=tag.toUpperCase();this.attrs={...attrs};this.children=[];this.events={};this.dataset={};this.hidden='hidden'in attrs;this.value='';
  for(const [k,v]of Object.entries(attrs))if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,s)=>s.toUpperCase())]=v;
 }
 get textContent(){return this.children.map(x=>typeof x==='string'?x:x.textContent).join('');}
 set textContent(value){this.children=[String(value)];}
 getAttribute(name){return this.attrs[name]??null;}
 setAttribute(name,value){this.attrs[name]=String(value);}
 append(...nodes){for(const n of nodes){if(typeof n!=='string')n.parentElement=this;this.children.push(n);}}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 addEventListener(name,fn){(this.events[name]??=[]).push(fn);}
 fire(type){for(const fn of this.events[type]||[])fn({type,target:this});}
 querySelectorAll(selector){const found=[];const match=n=>selector.startsWith('[')?selector.slice(1,-1)in n.attrs:selector.startsWith('.')?(n.attrs.class||'').split(/\s+/).includes(selector.slice(1)):n.tagName===selector.toUpperCase();
  for(const n of this.children)if(typeof n!=='string'){if(match(n))found.push(n);found.push(...n.querySelectorAll(selector));}return found;}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
}
function hydrate(n){if(typeof n==='string')return n;const e=new Element(n.tag,n.attrs);e.append(...n.children.map(hydrate));return e;}
async function main(){
 const host=spawn(process.env.PYTHON||'python3',['-u','-c',"import server; from http.server import ThreadingHTTPServer; server.init_db(':memory:'); h=ThreadingHTTPServer(('127.0.0.1',0),server.Handler); print(h.server_port,flush=True); h.serve_forever()"],{cwd:root,stdio:['ignore','pipe','pipe']});
 let stderr='';host.stderr.on('data',d=>stderr+=d);
 try{
  const port=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(Error('Host startup timed out: '+stderr)),10000);host.stdout.on('data',d=>{output+=d;const m=output.match(/^(\d+)\n/);if(m){clearTimeout(timer);resolve(Number(m[1]));}});host.on('error',reject);});
  const base='http://127.0.0.1:'+port;
  const get=async p=>{const r=await fetch(base+p);assert.equal(r.status,200,p);return r;};
  const request=async d=>{const r=await fetch(base+'/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});assert.equal(r.status,200);return r.json();};
  const health=await(await get('/health')).json();assert.equal(health.version,'0.18.0');
  const session=await request({op:'create',name:'Archive reader',build:'NanoClad Scout',seed:'reference-ui'});
  const before=await request({...session,op:'export'});
  const html=await(await get('/visual-references.html')).text();
  const parsed=spawnSync(process.env.PYTHON||'python3',['-c',parser],{input:html,encoding:'utf8',maxBuffer:4*1024*1024});assert.equal(parsed.status,0,parsed.stderr);
  const doc=hydrate(JSON.parse(parsed.stdout));
  const walk=(n,p)=>{if(p(n))return n;for(const c of n.children)if(typeof c!=='string'){const f=walk(c,p);if(f)return f;}return null;};
  doc.getElementById=id=>{const n=walk(doc,n=>n.attrs.id===id);assert.ok(n,id);return n;};
  const created=[];doc.createElement=tag=>{const e=new Element(tag);created.push(e);return e;};
  const cards=doc.querySelectorAll('[data-reference]');assert.equal(cards.length,80);
  assert.equal(doc.querySelectorAll('img').length,0,'No automatic original image loads.');
  assert.equal(cards.filter(c=>!c.hidden).length,80,'All original links work without scripting.');
  for(const c of cards){assert.ok(c.querySelector('[data-original]').getAttribute('href').startsWith('/visual-reference/'));assert.equal(c.querySelector('[data-preview]').hidden,true);}
  const ids={};for(const id of ['reference-search','reference-category','reference-count','reference-controls','preview-status'])ids[id]=doc.getElementById(id);
  const script=await(await get('/visual-references.js')).text();await get('/visual-references.css');
  vm.runInNewContext(script,{document:doc,console},{filename:'visual-references.js'});
  assert.equal(ids['reference-controls'].hidden,false);assert.equal(ids['reference-count'].textContent,'80 of 80 unique references shown.');
  assert.equal(created.filter(e=>e.tagName==='IMG').length,0);
  const search=text=>{ids['reference-search'].value=text;ids['reference-search'].fire('input');};
  const category=value=>{ids['reference-category'].value=value;ids['reference-category'].fire('change');};
  const visible=()=>cards.filter(c=>!c.hidden);
  search('test image 28(1).png');assert.equal(visible().length,1);assert.ok(visible()[0].textContent.includes('TEST IMAGE 27(1).png'));
  category('framework');assert.equal(visible().length,0);search('');assert.equal(visible().length,6);
  category('unassigned');assert.equal(visible().length,11);category('architecture');assert.equal(visible().length,13);category('');
  const first=cards[0],second=cards[1],b1=first.querySelector('[data-preview]'),b2=second.querySelector('[data-preview]');
  b1.fire('click');let img=first.querySelector('img');assert.ok(img);assert.equal(b1.getAttribute('aria-expanded'),'true');
  assert.equal(img.width,Number(first.dataset.width));assert.equal(img.height,Number(first.dataset.height));
  const catalog=await(await get('/visual-reference-catalog.json')).json();const record=catalog.references.find(r=>r.id===first.dataset.reference);
  const raw=Buffer.from(await(await get(img.src)).arrayBuffer());assert.equal(crypto.createHash('sha256').update(raw).digest('hex'),record.sha256);
  img.fire('load');assert.ok(ids['preview-status'].textContent.includes('ready'));
  b2.fire('click');assert.equal(first.querySelectorAll('img').length,0);assert.equal(doc.querySelectorAll('img').length,1);
  const newerStatus=ids['preview-status'].textContent;img.fire('error');assert.equal(ids['preview-status'].textContent,newerStatus,'Late events cannot overwrite the current preview.');
  const stale=second.querySelector('img');b2.fire('click');b2.fire('click');const sameCardStatus=ids['preview-status'].textContent;stale.fire('load');assert.equal(ids['preview-status'].textContent,sameCardStatus,'Same-card reopened preview rejects stale events.');
  second.querySelector('img').fire('error');assert.equal(ids['preview-status'].textContent,'Image preview could not load.');
  search('no matching source xyz');assert.equal(visible().length,0);assert.equal(doc.querySelectorAll('img').length,0);assert.equal(b2.getAttribute('aria-expanded'),'false');
  search('');assert.equal(visible().length,80);await get('/visual-reference-review.txt');
  const after=await request({...session,op:'export'});assert.deepEqual(after,before,'Reference browsing cannot change the saved character or world export.');
  const report={engine_version:health.version,scope:'Real HTTP + parsed semantic DOM; full browser layout not tested',references:cards.length,
   checks:['No image preloads; original links and notes without JavaScript','Alias search, combined filtering, empty result and subject counts','Exactly one preview; original dimensions and SHA256','Close/reopen, stale different/same-card load events, error feedback and filter cleanup','No saved-world or character export mutation']};
  fs.writeFileSync(path.join(root,'docs/visual-reference-ui-audit-v0171.json'),JSON.stringify(report,null,2)+'\n');
  console.log('PASS: real HTTP + archive interface logic — 80 original links, alias search, combined filters, one-image preview, exact bytes, stale-event rejection, error recovery and unchanged saved state.');
  console.log('Full browser layout is not tested.');
 }finally{host.kill('SIGTERM');await new Promise(resolve=>host.once('exit',resolve));}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
