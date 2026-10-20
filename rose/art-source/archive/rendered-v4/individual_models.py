"""Original detailed Rose bodies and regional scenery; Blender authoring only."""
import math
import random


def body(s, name):
    s.collection(name)
    broad = name in ('artisan', 'metal_kin')
    width = .29 if broad else .235
    metal = name == 'metal_kin'
    coat = {'traveler':'olive_coat','archivist':'slate_coat','artisan':'ochre_coat','mediator':'burgundy_coat','metal_kin':'metal'}[name]
    skin = 'skin_light' if name in ('traveler', 'artisan') else 'skin_deep'
    if metal: skin = 'canvas'
    root = s.empty(name + ' / stable foot origin')
    proportions={'traveler':(1,1,1.02),'archivist':(.92,.95,1.06),'artisan':(1.07,1.06,.98),'mediator':(.96,1.03,.95),'metal_kin':(1.03,1,1.04)}
    root.scale=proportions[name]
    torso = s.empty('Breath and lean', (0,0,.99), root)
    # Ring mesh gives the cloth a waist, chest, shoulder slope and open collar.
    verts=[]
    for z,w,d in [(-.14,width+.025,.155),(.02,width,.145),(.20,width-.015,.15),(.43,width,.155),(.50,width*.78,.125)]:
        for i in range(12):
            a=i*math.tau/12;verts.append((math.cos(a)*w,math.sin(a)*d,z))
    faces=[tuple(range(11,-1,-1))]
    for j in range(4):
        for i in range(12):faces.append((j*12+i,j*12+(i+1)%12,(j+1)*12+(i+1)%12,(j+1)*12+i))
    faces.append(tuple(range(48,60)))
    s.mesh('Tailored torso / five anatomical sections',verts,faces,coat,torso)
    s.cylinder('Open collar',(0,0,.50),.12,.06,'leather',torso)
    s.cube('Worn belt',(0,-.01,-.035),(width*2.12,.335,.055),'leather',torso,.012)
    s.cube('Belt buckle',(.02,-.183,-.032),(.075,.025,.065),'brass',torso,.006)
    # Seams and pleats are geometry, independent of color reduction.
    for x in [-.11,0,.12]:
        s.beam('Coat seam',(x,-.153,.04),(x*.8,-.161,.41),.006,'canvas',torso)
    for x in [-.15,.16]:
        s.cube('Buttoned utility pocket',(x,-.16,.21),(.135,.035,.15),coat,torso,.018)
        s.sphere('Pocket button',(x,-.182,.24),(.013,.008,.013),'brass',torso)
    s.cube('Asymmetric repaired cloth patch',(-.14,-.18,.02),(.11,.02,.105),'canvas',torso,.003)
    for i in range(4):s.beam('Hand stitched patch',(-.185+i*.025,-.193,-.015),(-.179+i*.025,-.193,.0),.004,'dark',torso)
    for side in [-1,1]:
        for i in range(3):
            s.beam('Tailored waist fold',(side*.12,-.15,.055+i*.035),(side*width,-.12,.10+i*.04),.005,'leather',torso)
    if name in ('archivist','mediator'):
        for x in [-1,1]:
            s.mesh('Split coat tail',[(x*.03,-.145,.05),(x*width,-.14,.05),(x*(width+.045),-.10,-.40),(x*.05,-.12,-.36)],[(0,1,2,3)],coat,torso)
    if name in ('artisan','metal_kin'):
        s.mesh('Scored work apron',[(-.19,-.18,.36),(.19,-.18,.36),(.23,-.20,-.30),(-.23,-.20,-.30)],[(0,1,2,3)],'leather',torso)
        for x in [-.105,.03,.13]:
            s.beam('Apron tool',(x,-.224,-.12),(x,-.225,.04),.019,'metal',torso)
    if name=='mediator':
        s.mesh('Shoulder mantle',[(-.32,-.19,.43),(.32,-.19,.43),(.31,.18,.42),(0,.22,.06),(-.31,.18,.42)],[(0,1,2,3,4)],'burgundy_coat',torso)
        s.beam('Mantle clasp',(-.08,-.202,.41),(.08,-.202,.41),.022,'brass',torso)
    if name=='archivist':
        s.cube('Document case',(-.27,.09,.03),(.14,.31,.38),'leather',torso,.035)
        s.beam('Case shoulder strap',(-.25,-.15,.46),(.23,-.17,-.03),.014,'canvas',torso)
    else:
        s.cube('Stitched field pack',(0,.21,.24),(.35,.20,.40),'leather',torso,.045)
        for x in [-.10,.10]:s.cube('Pack straps',(x,.325,.24),(.025,.015,.39),'canvas',torso,.003)
    if name=='traveler':
        s.cylinder('Bedroll',(0,.24,.49),.075,.46,'canvas',torso,rotation=(0,math.pi/2,0))
        s.cylinder('Water flask',(.255,.04,.05),.06,.23,'metal',torso)
    head=s.empty('Facial turn',(0,-.012,.65),torso)
    s.cylinder('Neck',(0,0,-.13),.069,.14,skin,head)
    # Skull, jaw, cheekbones and projecting brow/nose read as a sculpted face.
    s.sphere('Cranium',(0,0,.055),(.153 if broad else .139,.124,.172),skin,head)
    s.sphere('Jaw',(0,-.052,-.064),(.113 if broad else .098,.09,.09),skin,head)
    for x in [-.074,.074]:
        s.sphere('Cheekbone',(x,-.093,.004),(.052,.045,.055),skin,head)
        s.sphere('Eye socket',(x*.80,-.120,.059),(.036,.016,.019),'leather',head)
        s.sphere('Eye',(x*.80,-.136,.061),(.013,.009,.009),'dark',head)
        s.beam('Brow',(x*.80-.025,-.129,.093),(x*.80+.026,-.123,.086),.009,'hair',head)
        s.sphere('Ear',(math.copysign(.144,x),-.003,.012),(.021,.027,.044),skin,head)
    s.mesh('Bridge and tip of nose',[(-.022,-.13,.095),(.022,-.13,.095),(-.03,-.14,-.013),(.03,-.14,-.013),(0,-.178,.004)],[(0,1,4),(0,4,2),(1,3,4),(2,4,3)],skin,head)
    s.beam('Mouth',(-.035,-.133,-.060),(.035,-.133,-.060),.006,'leather',head)
    if name=='traveler':s.beam('Healed cheek scar',(.083,-.129,.009),(.101,-.119,-.024),.004,'canvas',head)
    if name not in ('mediator','metal_kin'):
        hair='hair_gray' if name=='traveler' else 'hair'
        s.sphere('Sculpted hair',(0,.018,.138),(.148,.127,.096),hair,head)
        if name=='traveler':s.sphere('Tied hair',(0,.13,.018),(.043,.06,.10),hair,head)
        if name=='artisan':s.sphere('Short beard',(0,-.091,-.083),(.102,.046,.078),hair,head)
    if name=='archivist':
        s.cube('Single brow lens',(-.065,-.148,.068),(.076,.028,.046),'metal',head,.008)
        s.cube('Lens glass',(-.065,-.166,.07),(.047,.008,.022),'cyan',head,.004)
    if metal:
        s.cube('Ceramic forehead',(0,-.10,.134),(.24,.10,.08),'canvas',head,.02)
        s.cube('Jaw plate',(0,-.115,-.07),(.18,.075,.075),'metal',head,.02)
        s.beam('Face seam',(0,-.138,.16),(0,-.176,.035),.008,'cyan',head)
    joints=dict(root=root,body=torso,head=head)
    for side,sign in [('L',-1),('R',1)]:
        shoulder=s.empty('Shoulder '+side,(sign*(width+.026),0,.395),torso)
        s.sphere('Upper arm',(0,0,-.105),(.084,.092,.165),coat,shoulder)
        elbow=s.empty('Elbow '+side,(0,0,-.30),shoulder)
        s.sphere('Elbow fold',(0,0,0),(.071,.074,.069),'metal' if metal else coat,elbow)
        s.sphere('Forearm',(0,0,-.11),(.063,.070,.126),'metal' if metal else coat,elbow)
        s.cylinder('Cuff',(0,0,-.216),.071,.055,'leather',elbow)
        s.sphere('Hand',(0,-.016,-.264),(.062,.048,.073),skin,elbow)
        for i in range(3):s.beam('Finger crease',(-.038+i*.027,-.06,-.25),(-.038+i*.027,-.058,-.29),.004,'leather',elbow)
        if side=='R':
            s.beam('Field staff',(.03,-.085,-.51),(.03,-.085,.16),.018,'wood' if not metal else 'metal',elbow)
            s.cube('Registered tool head',(.03,-.085,.15),(.13,.055,.07),'metal',elbow,.008)
        hip=s.empty('Hip '+side,(sign*.126,0,-.055),torso)
        s.sphere('Thigh',(0,0,-.19),(.10 if broad else .085,.097,.205),'metal' if metal else 'trousers',hip)
        knee=s.empty('Knee '+side,(0,0,-.395),hip)
        s.sphere('Kneecap',(0,-.024,0),(.083,.078,.078),'metal' if broad else 'leather',knee)
        s.sphere('Shin',(0,0,-.17),(.072,.077,.175),'metal' if metal else 'trousers',knee)
        s.cylinder('Boot upper',(0,-.002,-.294),.087,.12,'leather',knee)
        s.cube('Anatomical boot',(0,-.058,-.45),(.19,.29,.10),'leather',knee,.033)
        s.cube('Boot sole',(0,-.059,-.498),(.193,.296,.025),'dark',knee,.006)
        for z in [-.335,-.37,-.405]:s.beam('Boot laces',(-.05,-.107,z),(.05,-.107,z-.008),.004,'canvas',knee)
        for key,obj in [('arm',shoulder),('elbow',elbow),('leg',hip),('knee',knee)]:joints[key+side]=obj
    root['designation']=name+' / original anatomical mesh and registered field costume'
    return joints


def architecture(s, region, kind):
    """Regional construction changes mesh silhouettes and physical materials."""
    if kind in ('shelter','workshop','exchange'):
        col=s.COLLECTIONS[kind+'_'+region]
        for obj in list(col.objects):
            if obj.type!='MESH':continue
            if region=='WN_TOWER' and obj.name.startswith(('Workshop main shell','Corrugated roof','Market counter')):
                obj.data.materials.clear();obj.data.materials.append(s.MATERIALS['wood'])
            elif region=='ENACT_HILLS' and obj.name.startswith('Workshop main shell'):
                obj.data.materials.clear();obj.data.materials.append(s.MATERIALS['plaster'])
            elif region=='CITY_CLOUD_S' and obj.name.startswith(('Tent roof','Front flap','Market awning')):
                obj.data.materials.clear();obj.data.materials.append(s.MATERIALS['metal'])
        if region=='WN_TOWER':
            s.mesh('Root-grown pitched cap',[(-1.08,-.70,1.35),(1.08,-.70,1.35),(0,-.70,1.88),(-1.08,.80,1.35),(1.08,.80,1.35),(0,.80,1.88)],[(0,3,5,2),(2,5,4,1)],'wood')
            for i in range(7):s.beam('Wood roof strip',(-.9+i*.30,-.72,1.40+(.9-abs(-.9+i*.30))*.46),(-.9+i*.30,.80,1.40+(.9-abs(-.9+i*.30))*.46),.025,'moss')
        elif region=='ENACT_HILLS' and kind=='shelter':
            for x in [-.81,.81]:s.cube('Earth shelter low wall',(x,0,.49),(.20,1.48,.75),'plaster',bevel=.075)
        elif region=='AETHERGALE':
            s.mesh('Tensioned cross canopy',[(-1.02,-.64,1.55),(1.02,-.64,1.55),(-.68,.74,1.95),(.68,.74,1.95)],[(0,1,3,2)],'canvas')
    if kind in ('shelter','workshop','exchange'):
        if region=='WN_TOWER':
            for x in [-.94,.94]:
                s.beam('Darkwood root buttress',(x,-.73,.12),(x*.85,.10,1.38),.095,'wood')
                for i in range(3):s.sphere('Living buttress leaf',(x,-.55+i*.16,.37+i*.24),(.19,.065,.025),'moss')
            s.beam('Living roof ridge',(-.8,.25,1.55),(.8,.25,1.55),.065,'wood')
        elif region=='CITY_CLOUD_S':
            for x in [-.85,.85]:
                s.cube('Armored corner',(x,-.31,.80),(.14,.14,1.36),'metal')
            for i in range(4):s.cube('Industrial louvre',(-.35,-.34,.70+i*.10),(.53,.10,.035),'brass')
            s.cube('Salvaged overhead tank',(.15,.48,1.60),(.72,.43,.30),'metal',bevel=.06)
        elif region=='ENACT_HILLS':
            for x in [-.85,.85]:
                for i in range(4):s.cube('Masonry pier',(x,-.40,.23+i*.25),(.28,.30,.21),'plaster',bevel=.035)
            s.beam('Weathered lintel',(-.9,-.43,1.31),(.9,-.43,1.31),.105,'wood')
            for i in range(7):s.cube('Roof clay course',(-.9+i*.28,.40,1.57),(.26,1.16,.08),'ochre_coat',bevel=.026)
        else:
            for x in [-.82,.82]:
                s.beam('Crystal strut',(x,-.7,.13),(x*.80,.15,1.66),.04,'brass')
                s.mesh('Smoky crystal fin',[(x,-.1,.26),(x+.15,.02,.35),(x+.02,.02,1.28),(x-.12,-.08,.48)],[(0,1,2),(0,2,3)],'stone')
            s.mesh('Wind screen',[(-.85,.78,.2),(.85,.78,.2),(.66,.78,1.66),(-.66,.78,1.66)],[(0,1,2,3)],'canvas')
    else:
        if region=='WN_TOWER':
            s.beam('Root sleeve',(-.65,.40,.1),(-.25,.40,.88),.075,'wood')
            for i in range(3):s.sphere('Root leaf',(-.52+i*.08,.43,.27+i*.17),(.17,.07,.035),'moss')
        elif region=='CITY_CLOUD_S':
            for x in [-.53,.53]:s.panel('Riveted service shielding',(x,-.30,.31),(.22,.10,.38),'metal')
            s.beam('Service conduit',(-.55,.35,.14),(.55,.35,.14),.047,'rust')
        elif region=='ENACT_HILLS':
            for x in [-.65,.65]:s.cube('Stone footing',(x,.12,.24),(.31,.4,.35),'plaster',bevel=.04)
            s.cube('Earthwork drain',(0,-.6,.11),(1.1,.22,.08),'ochre_coat')
        else:
            for x in [-.55,.55]:
                s.beam('Pilgrim outrigger',(x,-.4,.13),(x*.55,.3,.77),.025,'brass')
                s.mesh('Clear edge crystal',[(x,-.35,.15),(x+.10,-.2,.15),(x+.07,-.26,.8),(x-.08,-.24,.26)],[(0,1,2),(0,2,3)],'stone')
    # Separate geometry keys can be revealed in the worn animation state.
    worn=[]
    for i in range(4):
        obj=s.cube('Condition / exposed debris',(-.65+i*.31,-.90 if kind=='exchange' else -.56,.16),(.16,.085,.045),'rust',bevel=.005)
        obj.rotation_euler.z=i*.64;worn.append(obj)
    for i in range(3):
        offset=-.27 if kind=='exchange' else 0
        obj=s.beam('Condition / opened fracture',(-.35+i*.25,-.57+offset,.28),(-.29+i*.25,-.55+offset,.45),.012,'dark');worn.append(obj)
    return worn


def terrain(s, region):
    g=random.Random(417+sum(map(ord,region)))
    if region=='CITY_CLOUD_S':
        for x in range(-4,5):
            for y in range(-4,5):
                s.cube('Cracked street plate',(x*.86,y*.86,.005),(.81,.81,.018),'ground_city',bevel=.005)
        for i in range(12):
            x,y=g.uniform(-3,3),g.uniform(-3,3);s.beam('Lost cable',(x,y,.03),(x+.32,y+.13,.03),.012,'rust')
    elif region=='WN_TOWER':
        for i in range(40):
            x,y=g.uniform(-3.5,3.5),g.uniform(-3.5,3.5)
            s.beam('Root vein',(x,y,.02),(x+.35,y+.2,.045),.013,'wood')
            leaf=s.sphere('Leaf litter',(x+.15,y,.033),(.12,.055,.009),'moss');leaf.rotation_euler.z=g.random()*math.tau
    elif region=='ENACT_HILLS':
        for i in range(36):
            x,y=g.uniform(-3.5,3.5),g.uniform(-3.5,3.5)
            s.cube('Broken clay fragment',(x,y,.035),(.16,.10,.024),'ochre_coat',bevel=.015)
    else:
        for i in range(24):
            x,y=g.uniform(-3.5,3.5),g.uniform(-3.5,3.5)
            s.mesh('Contrail mineral shard',[(x-.1,y,.02),(x+.1,y,.02),(x,y+.1,.05),(x+.04,y+.04,.14)],[(0,1,2),(0,1,3),(1,2,3),(2,0,3)],'stone')


def obstacle(s, region):
    if region=='WN_TOWER':
        for i in range(5):s.beam('Dead root',(-.5+i*.2,.10,.1),(-.36+i*.16,.18,.65),.045,'wood')
        for i in range(4):s.sphere('Root moss',(-.3+i*.2,-.13,.23),(.15,.1,.04),'moss')
    elif region=='CITY_CLOUD_S':
        s.panel('Collapsed road machine',(.15,.05,.42),(.8,.50,.50),'rust')
        s.cylinder('Exposed axle',(.12,-.25,.26),.085,.64,'metal',rotation=(0,math.pi/2,0))
    elif region=='ENACT_HILLS':
        for i in range(4):s.cube('Buried masonry',(-.4+i*.22,-.12,.15+i*.07),(.3,.25,.16),'plaster',bevel=.026)
    else:
        for i in range(4):
            x=-.35+i*.21;s.mesh('Fractural crystal',[(x-.09,-.12,.15),(x+.10,-.12,.15),(x,.03,.15),(x+.02,-.03,.78-i*.1)],[(0,1,2),(0,1,3),(1,2,3),(2,0,3)],'stone')
