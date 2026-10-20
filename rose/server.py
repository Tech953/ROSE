#!/usr/bin/env python3
"""ROSE server: shared room authority, persistence, timed ecological pulses."""
import argparse
import copy
import json
import logging
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import urllib.error
import webbrowser
import world
import characters
import adventure
import companions
import engine
import scene
import tactical
import navigation
import visual_references
from narrator import Narrator

ROOT=Path(__file__).resolve().parent
LOCK=threading.RLock()
DB=None
NARRATOR=Narrator()
ACTIVE={}
PULSE_SECONDS=30
STOP=threading.Event()

def init_db(path):
    global DB
    DB=sqlite3.connect(path,check_same_thread=False)
    DB.execute('CREATE TABLE IF NOT EXISTS worlds (code TEXT PRIMARY KEY, state TEXT NOT NULL)');DB.commit()
def save(w):
    encoded=json.dumps(w)
    with DB:
        DB.execute('INSERT OR REPLACE INTO worlds VALUES (?,?)',(w['code'],encoded))
def fetch(code):
    row=DB.execute('SELECT state FROM worlds WHERE code=?',(code,)).fetchone()
    world.require(row is not None,'World not found. Check the room code and host address.')
    w=json.loads(row[0]);world.require(w.get('game')=='Rose' and w.get('engine_schema')==1,'This is not a Rose engine save. Use a separate Rose database.');adventure.init(w)
    for c in w['cells'].values():c.setdefault('fauna',3)
    companions.ensure_world(w)
    return w
def identify(w,token):
    world.require(isinstance(token,str),'Invalid session.')
    p=next((p for p in w['players'] if secrets.compare_digest(p['token'],token)),None)
    world.require(p is not None,'Session not recognized. Join this world or restore this browser’s session.')
    return p
def get_state(w,p):
    s=world.snapshot(w,p);s['narrator_enabled']=bool(NARRATOR.url);s['pulse_seconds']=PULSE_SECONDS
    s['clock_error']=ACTIVE.get(w['code'],{}).get('clock_error','')
    return s

def request(d):
    op=d.get('op');code=str(d.get('code','')).upper().strip()
    if op=='create':
        world.require(DB.execute('SELECT COUNT(*) FROM worlds').fetchone()[0]<100,'Host limit reached: 100 saved worlds.')
        seed=d.get('seed','');world.require(isinstance(seed,str) and len(seed)<=80,'Use a seed of up to 80 characters.')
        w=world.new_world(seed or None,d.get('layout','atlas'),d.get('rules'),d.get('profile','balanced'));p=world.add_player(w,d.get('name'),d.get('build'),d.get('character'))
        while True:
            code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            if not DB.execute('SELECT 1 FROM worlds WHERE code=?',(code,)).fetchone():break
        w['code']=code;save(w);ACTIVE[code]=dict(seen=time.monotonic(),next=time.monotonic()+PULSE_SECONDS)
        return dict(code=code,id=p['id'],token=p['token'])
    w=fetch(code)
    if op=='join':
        p=world.add_player(w,d.get('name'),d.get('build'),d.get('character'));w['revision']+=1;world.emit(w,p['name']+' joins the field station.','story');save(w)
        ACTIVE.setdefault(code,dict(seen=time.monotonic(),next=time.monotonic()+PULSE_SECONDS))['seen']=time.monotonic()
        ACTIVE[code]['traveling']=any(a.get('overworld',{}).get('status')=='traveling' for a in w['players'])
        return dict(code=code,id=p['id'],token=p['token'])
    p=identify(w,d.get('token'))
    ACTIVE.setdefault(code,dict(seen=time.monotonic(),next=time.monotonic()+PULSE_SECONDS))['seen']=time.monotonic()
    ACTIVE[code]['traveling']=any(a.get('overworld',{}).get('status')=='traveling' for a in w['players'])
    if op=='state':
        result=get_state(w,p);save(w);return result
    if op=='engine_export':
        return engine.blueprint(w)
    if op=='particle_export':
        target=d.get('target','');world.require(isinstance(target,str) and len(target)<=30,'Choose a bounded particle identity.')
        return world.particles.export(w,p,world,target)
    if op=='vrex_export':
        world.require(not p['percept']['address'],'Return to the baseline field to export its VREX record.')
        f=world.particles.field(w,p,world);v=f.get('vrex')
        world.require(v is not None,'Configure VREX before exporting its measurements.')
        import copy
        return dict(format='Rose-VREX-systems',schema=1,engine_version=world.VERSION,source=world.particles.research.PROTOCOL['source'],field=f['address'],tick=w['tick'],state=copy.deepcopy(v),energy=world.particles.vrex.audit(v))
    if op=='research_export':
        world.particles.ensure(w,p)
        world.require(not p['percept']['address'],'Return to a baseline workshop to export its systems measurement.')
        return world.particles.research.export(world.particles.field(w,p,world))
    if op in {'physics_export','physics_diagnose'}:
        world.require(not p.get('percept',{}).get('address'),'Return to the baseline field for its mechanical development record.')
        f=w.get('substrate',{}).get('fields',{}).get('base:'+world.key(*p['pos']))
        world.require(f is not None,'This field has no retained mechanism.')
        if op=='physics_diagnose':
            world.require(f.get('vrex') is not None,'Fit a mechanism or configure the source model before development tests.')
            return world.machines.diagnostics(f['vrex'])
        return world.machines.export(w,f,world.VERSION)
    if op=='export':
        return dict(title='Rose field journal',seed=w['seed'],tick=w['tick'],character={k:v for k,v in p.items() if k!='token'},journal=w['journal'],reputation=w['reputation'])
    if op=='narrate':return ('narrate',get_state(w,p))
    if op=='interpret':
        text=d.get('text');world.require(isinstance(text,str) and 0<len(text)<=1200,'Use 1–1,200 characters.');return ('interpret',dict(text=text,state=get_state(w,p)))
    world.require(type(d.get('revision'))==int and d['revision']==w['revision'],'The world changed. Review the new state and submit your action again; nothing was spent.')
    if op in ['start','pause']:
        world.require(p['id']==w['host'],'Only the host can change the world clock.')
        if op=='start':world.require(not w['started'],'Already started.');w['started']=True
        else:w['paused']=not w['paused']
        w['revision']+=1;ACTIVE[code]['next']=time.monotonic()+PULSE_SECONDS
        ACTIVE[code].pop('clock_error',None)
        result=None
    elif op=='particle_import':
        world.particles.ensure(w,p)
        result=world.particles.import_objects(w,p,d.get('data'),world);w['revision']+=1
    elif op=='character':
        world.require(not w['started'],'Character editing locks when the expedition begins.')
        p['character']=characters.validate(d.get('character'),d.get('build',p['build']));p['build']=p['character']['role'];w['revision']+=1;result=None
    elif op=='act':
        raw=d.get('text','');world.require(isinstance(raw,str) and len(raw)<=1200,'Action text is too long.')
        intent=d.get('intent')
        if intent is not None:
            world.require(isinstance(intent,dict) and set(intent)=={'action','target'} and isinstance(intent['action'],str) and isinstance(intent['target'],str),'Invalid proposed action.')
            target_limit=80 if intent['action'] in {'particle_tune','particle_excite','particle_quench','particle_survey','particle_audit','vrex_configure','vrex_stimulus','vrex_pump','vrex_stop','vrex_perturb','vrex_expand','vrex_diagnose','machine_fit','machine_operate','machine_stop'} else 30
            world.require(len(intent['target'])<=target_limit,'Invalid proposed action.')
        else:
            intent,error=world.parse(raw)
            if error:return dict(state=get_state(w,p),result=dict(text=error,mechanics='',intent=None,time_spent=False))
        result=world.act(w,p,intent,raw)
    elif op=='chat':
        msg=d.get('text');world.require(isinstance(msg,str) and 0<len(msg.strip())<=500,'Chat uses 1–500 characters.');world.emit(w,p['name']+': '+msg.strip(),'chat');w['revision']+=1;result=None
    elif op=='leave':
        world.require(len(w['players'])>1,'The last player can disconnect; their saved world remains.')
        world.require(not tactical.any_active(w),'Finish active encounters before releasing a seat. Disconnect keeps the seat; the host can advance a waiting turn.')
        companions.release_all(w,p);w['players']=[a for a in w['players'] if a['id']!=p['id']]
        if w['host']==p['id']:w['host']=w['players'][0]['id']
        w['revision']+=1;save(w);return dict(left=True)
    else:raise ValueError('Unknown operation.')
    state=get_state(w,p)
    ACTIVE[code]['traveling']=any(a.get('overworld',{}).get('status')=='traveling' for a in w['players'])
    save(w);return dict(state=state,result=result)

def pulse(now=None):
    now=time.monotonic() if now is None else now
    with LOCK:
        for code,activity in list(ACTIVE.items()):
            if now-activity['seen']>300:ACTIVE.pop(code,None);continue
            if activity.get('clock_error'):continue
            try:
                if activity.get('traveling') and now>=activity.get('travel_next',now):
                    activity['travel_next']=now+1
                    moved=False
                    w=fetch(code)
                    for p in w['players']:
                        moved=navigation.advance(w,p,world) or moved
                    activity['traveling']=any(p.get('overworld',{}).get('status')=='traveling' for p in w['players'])
                    if moved:save(w)
                if now<activity['next']:continue
                activity['next']=now+PULSE_SECONDS
                w=fetch(code)
                if w['started'] and not w['paused'] and not tactical.any_active(w):world.tick(w);save(w)
            except Exception:
                # One room must not kill the shared clock worker or commit partial work.
                activity['clock_error']='Automatic updates stopped for this world. Your latest saved state is retained. The host can pause/resume the clock to retry.'
                logging.exception('Automatic update failed for Rose room %s',code)
def run_clock():
    while not STOP.wait(1):pulse()

class Handler(BaseHTTPRequestHandler):
    def reply(self,status,data,ctype='application/json; charset=utf-8'):
        body=data if isinstance(data,bytes) else json.dumps(data).encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path.startswith('/art/'):
            path=(ROOT/'static'/self.path.lstrip('/')).resolve();art_root=(ROOT/'static'/'art').resolve()
            if not path.is_relative_to(art_root) or path.suffix.lower() not in {'.png','.webp'} or not path.is_file():return self.reply(404,dict(error='Art asset not found.'))
            return self.reply(200,path.read_bytes(),'image/png' if path.suffix.lower()=='.png' else 'image/webp')
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/scene.js':('scene.js','text/javascript; charset=utf-8'),'/prefabs.js':('prefabs.js','text/javascript; charset=utf-8'),'/art-manifest.json':('art-manifest.json','application/json'),'/style.css':('style.css','text/css; charset=utf-8'),'/creator.js':('creator.js','text/javascript; charset=utf-8'),'/atlas.svg':('atlas.svg','image/svg+xml'),'/world-reference.jpg':('../reference/maps/world-reference-1.jpg','image/jpeg'),'/needle-reference.jpg':('../reference/maps/world-reference-2.jpg','image/jpeg')}
        files['/overworld.js']=('overworld.js','text/javascript; charset=utf-8')
        files['/ui.js']=('ui.js','text/javascript; charset=utf-8')
        files['/art-manifest-vector.json']=('art-manifest-vector.json','application/json')
        files['/art-manifest-rendered.json']=('art-manifest-rendered.json','application/json')
        files['/art-manifest-rendered-legacy.json']=('art-manifest-rendered-legacy.json','application/json')
        files['/display.js']=('display.js','text/javascript; charset=utf-8')
        files['/audio.js']=('audio.js','text/javascript; charset=utf-8')
        files['/lighting.js']=('lighting.js','text/javascript; charset=utf-8')
        files['/environment.js']=('environment.js','text/javascript; charset=utf-8')
        files['/weather.js']=('weather.js','text/javascript; charset=utf-8')
        files['/material-visuals.js']=('material-visuals.js','text/javascript; charset=utf-8')
        files['/animations.js']=('animations.js','text/javascript; charset=utf-8')
        files['/motion-visuals.js']=('motion-visuals.js','text/javascript; charset=utf-8')
        files['/terrain.js']=('terrain.js','text/javascript; charset=utf-8')
        files['/particulate.js']=('particulate.js','text/javascript; charset=utf-8')
        files['/lighting-signatures.json']=('lighting-signatures.json','application/json')
        files['/survey.js']=('survey.js','text/javascript; charset=utf-8')
        files['/continental-survey.json']=('continental-survey.json','application/json')
        files['/continental-reference.jpg']=('../reference/maps/continental-reference.jpg','image/jpeg')
        files['/resonance-reference.jpg']=('../reference/science/resonance-light-projection.jpg','image/jpeg')
        files['/vrex-reference.pdf']=('../reference/science/vrex-v3-systems-reference.pdf','application/pdf')
        files['/vrex-proposal.pdf']=files['/vrex-reference.pdf']
        files['/lore-transport.html']=('lore-transport.html','text/html; charset=utf-8')
        files['/lore-transport-catalog.json']=('../reference/lore-transport/catalog.json','application/json')
        files['/lore-transport-guide.txt']=('../docs/LORE-TRANSPORT-INTEGRATION.md','text/plain; charset=utf-8')
        files['/weather-response-guide.txt']=('../docs/WEATHER-RESPONSE-GUIDE.md','text/plain; charset=utf-8')
        files['/visual-references.html']=('visual-references.html','text/html; charset=utf-8')
        files['/visual-references.js']=('visual-references.js','text/javascript; charset=utf-8')
        files['/visual-references.css']=('visual-references.css','text/css; charset=utf-8')
        files['/visual-reference-catalog.json']=('../reference/visual-corpus/catalog.json','application/json')
        files['/visual-reference-review.txt']=('../docs/VISUAL-REFERENCE-REVIEW.md','text/plain; charset=utf-8')
        files.update(visual_references.ASSET_ROUTES)
        files['/art-direction.js']=('art-direction.js','text/javascript; charset=utf-8')
        files['/art-direction-runtime.json']=('art-direction-runtime.json','application/json')
        files['/art-direction-register.json']=('../reference/art-direction/direction-v018.json','application/json')
        files['/art-direction.html']=('art-direction.html','text/html; charset=utf-8')
        files['/art-direction-guide.txt']=('../docs/ART-DIRECTION-AND-TEXT-INTERPRETATION.md','text/plain; charset=utf-8')
        files['/art-direction-preview.png']=('../docs/Rose-art-direction-comparison-v018.png','image/png')
        for index,name in enumerate(['CORP-E PRODUCTS.png','CORP-E PRODUCTS pt. 2.png','CODE.png','CODE FINAL.png']):
            files[f'/lore-transport-image-{index}.png']=('../reference/lore-transport/PROTOTYPE IMAGE v2/'+name,'image/png')
        if self.path=='/health':return self.reply(200,dict(ok=True,game='Rose',version=world.VERSION))
        if self.path=='/catalog':return self.reply(200,dict(builds=characters.ROLES,characters=characters.catalog(),help=world.HELP,engine=engine.catalog()))
        if self.path not in files:return self.reply(404,dict(error='Not found'))
        name,mime=files[self.path];self.reply(200,(ROOT/'static'/name).read_bytes(),mime)
    def do_POST(self):
        try:
            world.require(self.path=='/api','Not found.')
            origin=self.headers.get('Origin')
            if origin:
                from urllib.parse import urlparse
                world.require(urlparse(origin).netloc==self.headers.get('Host'),'Cross-origin actions are not accepted.')
            world.require(self.headers.get('Content-Type','').split(';')[0]=='application/json','JSON required.')
            n=int(self.headers.get('Content-Length','0'));world.require(0<n<=196608,'Request must be at most 192 KiB.');self.connection.settimeout(10)
            d=json.loads(self.rfile.read(n));world.require(isinstance(d,dict),'JSON object required.')
            world.require(d.get('op')=='particle_import' or n<=65536,'Ordinary requests must be at most 64 KiB.')
            with LOCK:result=request(d)
            # Generation is intentionally outside the state lock; it has no write privileges.
            if isinstance(result,tuple):
                kind,payload=result
                result=dict(prose=NARRATOR.describe(payload),tick=payload['tick'],label='Optional model prose — not authoritative') if kind=='narrate' else dict(intent=NARRATOR.interpret(payload['text'],payload['state']))
            self.reply(200,result)
        except (ValueError,TypeError,KeyError,urllib.error.URLError,TimeoutError) as exc:self.reply(400,dict(error=str(exc)))
        except Exception:
            self.reply(500,dict(error='The server could not complete that operation. Your prior saved state is retained.'))
    def log_message(self,*args):pass

def main():
    global NARRATOR,PULSE_SECONDS
    parser=argparse.ArgumentParser(description='Rose text adventure host')
    parser.add_argument('--host',default='0.0.0.0');parser.add_argument('--port',type=int,default=8778);parser.add_argument('--db');parser.add_argument('--rules',default=str(ROOT/'rules.json'));parser.add_argument('--no-browser',action='store_true');parser.add_argument('--pulse-seconds',type=int,default=30);parser.add_argument('--narrator-url',default=os.getenv('ROSE_NARRATOR_URL',''));parser.add_argument('--narrator-model',default=os.getenv('ROSE_NARRATOR_MODEL','local'));args=parser.parse_args()
    try:engine.load(args.rules)
    except (OSError,ValueError) as exc:parser.error(str(exc))
    if args.pulse_seconds<5:parser.error('World pulses must be at least 5 seconds apart.')
    PULSE_SECONDS=args.pulse_seconds;NARRATOR=Narrator(args.narrator_url,args.narrator_model)
    db=Path(args.db) if args.db else Path(os.getenv('LOCALAPPDATA',str(Path.home()/'.local'/'share')))/'Rose'/'worlds.sqlite3';db.parent.mkdir(parents=True,exist_ok=True);init_db(str(db))
    try:http=ThreadingHTTPServer((args.host,args.port),Handler)
    except OSError as exc:raise SystemExit(f'Cannot open port {args.port}: {exc}. Try --port 8777.')
    print(f'ROSE {world.VERSION}\nOpen http://localhost:{args.port}\nWorlds: {db}\nKeep this window open. Ctrl+C stops the host.',flush=True)
    worker=threading.Thread(target=run_clock,daemon=True);worker.start()
    if not args.no_browser:threading.Timer(.5,lambda:webbrowser.open(f'http://localhost:{args.port}')).start()
    try:http.serve_forever()
    except KeyboardInterrupt:pass
    finally:STOP.set();worker.join(3);http.server_close();DB.close()
if __name__=='__main__':main()
