"""Bounded turn-based encounters with generated hostile maintenance constructs."""
import copy
import survival
import materials

ACTS={'attack','shoot','guard','flee','parley'}

def ensure(c,w,engine):
    if 'threat' in c:return c['threat']
    g=engine.rng(w['seed'],'threat',c['x'],c['y'])
    c['threat']=None
    if not c.get('landmark') and not c['shelter'] and g.randrange(100)<w['rules']['generation']['hostility']:
        c['threat']=dict(id='threat',name=g.choice(['misaligned salvage drone','rogue route warden','fractured reclamation construct']),
            health=g.randint(24,34),defense=12,attack=11,damage=7,state='watchful',intent='guarding an abandoned material cache',
            lore='A generated Rose maintenance construct whose local routine no longer recognizes ordinary route traffic.',resolved=False)
    return c['threat']

def public(c):
    return copy.deepcopy(c.get('threat'))

def retaliation(w,p,c,engine,guard=False):
    t=c['threat'];ok,roll=engine.check(w,p,'body',t['attack'],'fieldcraft',dict(modifier=2 if guard else 0,reason='guarded stance +2' if guard else 'hostile counteraction'))
    damage=0 if ok else max(1,t['damage']-(3 if guard else 0))
    defenders=[a for a in w['actors'] if a.get('owner')==p['id'] and [a['x'],a['y']]==p['pos'] and a['health']>=35 and a['energy']>=15 and a['engagement']['task']=='guard' and a['attitude']>=30]
    if damage and defenders:
        a=defenders[0];share=min(3,damage);damage-=share;a['health']=max(0,a['health']-share);a['energy']=max(0,a['energy']-2)
        import companions
        companions.event(w,a,'Shared '+str(share)+' health of an active defensive encounter.')
    p['health']=max(0,p['health']-damage)
    if damage>=6:survival.harm(p,'impact strain')
    return f" The construct’s counteraction costs {damage} player health.",roll

def handle(w,p,intent,raw,engine):
    op=intent['action'];c=engine.local(w,p);t=ensure(c,w,engine);target=intent.get('target','')
    engine.require(t is not None and not t['resolved'] and t['health']>0,'No unresolved hostile construct is present. Inspect the sector first.')
    engine.require(target in {'','threat',t['name']},'This encounter targets the displayed hostile construct.')
    out='';roll='';t['state']='engaged'
    if op in {'attack','shoot'}:
        materials.ensure_gear(p,w['tick'])
        engine.require(materials.operable(p,'crystallin' if op=='shoot' else 'field_staff'),'Repair or replace the weapon before attacking.')
        if op=='shoot':
            engine.require('black.dot' in p['credentials'] and 'crystallin' in p['loadout'],'Ranged crystallin work requires an active registered retrofit.')
            engine.require(p['inventory']['scrap']>=1,'A crystallin shot uses one scrap charge.');p['inventory']['scrap']-=1
        skill='ballistics' if op=='shoot' else 'transversal'
        ok,roll=engine.check(w,p,'body',t['defense'],skill)
        factor=materials.weapon_use(w,p,op=='shoot')
        damage=max(1,int(((9 if op=='shoot' else 6)+p['character']['attributes']['body'])*factor))
        if ok:t['health']=max(0,t['health']-damage);out=f"Your {'shot' if op=='shoot' else 'field-staff strike'} deals {damage} construct damage."
        else:out='The attempt fails to find a reliable opening.'
        if t['health']==0:
            t['resolved']=True;t['state']='disabled';amount=min(2,99-p['inventory']['scrap']);p['inventory']['scrap']+=amount;p['xp']+=1
            engine.standing(w,p,engine.REGIONS[c['region']]['faction'],1);out+=f' The construct is disabled; its cache yields {amount} scrap. The encounter cannot pay twice.'
        else:extra,counter=retaliation(w,p,c,engine);out+=extra;roll+='\n'+counter
    elif op=='guard':
        ok,roll=engine.check(w,p,'body',10,'fieldcraft');extra,counter=retaliation(w,p,c,engine,guard=ok);out='You hold a defensive stance.'+extra;roll+='\n'+counter
    elif op=='parley':
        ok,roll=engine.check(w,p,'rapport',13,'memetic')
        if ok:
            t['resolved']=True;t['state']='truce';p['xp']+=1;engine.standing(w,p,engine.REGIONS[c['region']]['faction'],1)
            out='A bounded transit protocol is accepted. The construct stands down without yielding its cache.'
        else:extra,counter=retaliation(w,p,c,engine);out='The proposed transit protocol is refused.'+extra;roll+='\n'+counter
    else:
        candidates=[]
        for direction,(dx,dy) in engine.DIRS.items():
            x,y=p['pos'][0]+dx,p['pos'][1]+dy
            if w.get('layout')=='atlas':
                import geography
                if not geography.info(x,y)['passable']:continue
            if abs(x)>engine.MAX_COORD or abs(y)>engine.MAX_COORD:continue
            known=w['cells'].get(engine.key(x,y))
            if known and known.get('threat') and not known['threat']['resolved']:continue
            candidates.append((0 if known and known['shelter'] else 1,direction,x,y))
        engine.require(candidates,'No accessible neighboring escape sector is available.')
        ok,roll=engine.check(w,p,'body',11,'transversal')
        if ok:
            _,direction,x,y=min(candidates);engine.visit(w,x,y);p['pos']=[x,y];p['route']=[];p['destination']=None;t['state']='watchful'
            out='You disengage into the next physical sector '+direction+'. The unresolved construct remains behind.'
        else:extra,counter=retaliation(w,p,c,engine);out='The disengagement route does not open.'+extra;roll+='\n'+counter
    return dict(text=out,mechanics=roll,intent=intent,time_spent=True)
