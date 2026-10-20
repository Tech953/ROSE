"""Original sculpted anatomy and practical details for the fidelity-v4 bake."""
import math
import random


def smooth(obj):
    obj.modifiers.clear()
    for face in obj.data.polygons:face.use_smooth=True
    return obj


def remove(s,col,names):
    for obj in list(col.objects):
        if obj.name.split('.')[0] in names:s.bpy.data.objects.remove(obj,do_unlink=True)


def rings(s,name,sections,material,parent,segments=32):
    verts=[]
    for z,w,d,center in sections:
        for i in range(segments):
            a=i*math.tau/segments
            verts.append((math.cos(a)*w,center+math.sin(a)*d,z))
    faces=[tuple(range(segments-1,-1,-1))]
    for row in range(len(sections)-1):
        for i in range(segments):faces.append((row*segments+i,row*segments+(i+1)%segments,(row+1)*segments+(i+1)%segments,(row+1)*segments+i))
    faces.append(tuple(range((len(sections)-1)*segments,len(sections)*segments)))
    return smooth(s.mesh(name,verts,faces,material,parent))


def curved(s,name,points,radius,material,parent=None):
    for start,end in zip(points,points[1:]):s.beam(name,start,end,radius,material,parent)


def body(s,name,joints):
    col=s.COLLECTIONS[name];s.bpy.context.view_layer.active_layer_collection=s.bpy.context.view_layer.layer_collection.children[col.name]
    head,torso=joints['head'],joints['body'];metal=name=='metal_kin';broad=name in ('artisan','metal_kin')
    skin='canvas' if metal else 'skin_light' if name in ('traveler','artisan') else 'skin_deep'
    coat={'traveler':'olive_coat','archivist':'slate_coat','artisan':'ochre_coat','mediator':'burgundy_coat','metal_kin':'metal'}[name]
    remove(s,col,{'Tailored torso / five anatomical sections','Cranium','Jaw','Cheekbone','Eye socket','Eye','Brow','Mouth','Sculpted hair','Short beard','Finger crease','Hand','Continuous fitted torso','Soft folded lapel','Compressed cloth fold','Continuous facial sculpt','Inset eye shadow','Small corneal plane','Sculpted eyelid','Natural brow ridge','Ear cartilage','Sculpted nose bridge','Upper lip','Lower lip','Fitted hair cap','Swept hair locks','Trimmed beard strand','Palm anatomy','Individual curled finger','Finger knuckle','Opposed thumb','Sleeve seam','Sleeve compression fold','Boot toe reinforcement','Boot welt stitching','Boot upper','Anatomical boot','Boot sole','Continuous leather boot shaft','Rounded boot vamp','Boot welt sole','Worn boot fold'})
    if not metal:remove(s,col,{'Kneecap'})
    remove(s,col,{'Wrinkled lower coat hem','Tailored trouser thigh','Continuous trouser shin'})
    if not metal:remove(s,col,{'Thigh','Shin'})
    width=.29 if broad else .235
    rings(s,'Continuous fitted torso',[(-.14,width+.017,.151,0),(-.07,width-.016,.142,0),(.06,width-.022,.14,0),(.19,width-.018,.155,0),(.32,width+.006,.16,.003),(.40,width+.010,.152,.01),(.46,width*.91,.135,.015),(.51,width*.69,.111,.01)],coat,torso)
    for sign in [-1,1]:
        smooth(s.mesh('Soft folded lapel',[(sign*.035,-.13,.49),(sign*.17,-.151,.42),(sign*.092,-.168,.29),(sign*.036,-.161,.39)],[(0,1,2,3)],coat,torso))
        for i in range(3):
            x=sign*(.15+i*.014);curved(s,'Compressed cloth fold',[(x,-.16,.17),(x+sign*.03,-.168,.135),(x+sign*.018,-.16,.09)],.0035,coat,torso)
        curved(s,'Wrinkled lower coat hem',[(sign*.18,-.13,-.05),(sign*.15,-.152,-.09),(sign*.20,-.14,-.125)],.004,coat,torso)
    # One continuous facial volume replaces intersecting skull/jaw/cheek balls.
    jaw=1.06 if broad else .96;skull=1.0 if broad else .95
    rings(s,'Continuous facial sculpt',[(-.15,.032*jaw,.035,-.033),(-.13,.074*jaw,.071,-.025),(-.09,.108*jaw,.09,-.02),(-.04,.125*jaw,.105,-.005),(.015,.141*skull,.115,0),(.066,.143*skull,.121,.002),(.118,.143*skull,.117,.009),(.17,.129*skull,.102,.018),(.21,.096*skull,.075,.02),(.23,.029*skull,.023,.02)],skin,head)
    for sign in [-1,1]:
        x=sign*.057
        s.sphere('Inset eye shadow',(x,-.116,.061),(.024,.009,.012),'skin_shadow' if not metal else 'dark',head)
        s.sphere('Small corneal plane',(x,-.123,.061),(.011,.0045,.006),'dark',head)
        curved(s,'Sculpted eyelid',[(x-.024,-.12,.062),(x,-.129,.073),(x+.024,-.12,.062)],.005,skin,head)
        curved(s,'Natural brow ridge',[(x-sign*.028,-.122,.086),(x,-.133,.095),(x+sign*.026,-.121,.087)],.005,'hair' if not metal else 'metal',head)
        s.sphere('Ear cartilage',(sign*.142,-.009,.009),(.015,.019,.029),skin,head)
    remove(s,col,{'Bridge and tip of nose'})
    smooth(s.mesh('Sculpted nose bridge',[(-.018,-.125,.10),(.018,-.125,.10),(-.021,-.15,.01),(.021,-.15,.01),(-.016,-.171,.009),(.016,-.171,.009),(0,-.18,.022)],[(0,1,6),(0,6,4,2),(1,3,5,6),(2,4,5,3),(4,6,5)],skin,head))
    s.sphere('Upper lip',(0,-.13,-.060),(.035,.008,.006),'skin_lip' if not metal else 'metal',head)
    s.sphere('Lower lip',(0,-.128,-.073),(.031,.008,.007),skin,head)
    if name not in ('mediator','metal_kin'):
        hair='hair_gray' if name=='traveler' else 'hair'
        rings(s,'Fitted hair cap',[(.135,.137,.112,.022),(.178,.128,.102,.022),(.218,.09,.073,.02),(.239,.03,.026,.018)],hair,head)
        for i in range(9):
            x=-.10+i*.025;curved(s,'Swept hair locks',[(x,-.072,.163),(x*.82,-.03,.219),(x*.66,.06,.208)],.0025,'hair' if hair=='hair_gray' else 'leather',head)
        if name=='artisan':
            for i in range(7):
                x=-.08+i*.026;s.sphere('Trimmed beard strand',(x,-.10,-.099),(.023,.015,.033),'hair',head)
    for side,sign in [('L',-1),('R',1)]:
        elbow=joints['elbow'+side]
        s.sphere('Palm anatomy',(0,-.012,-.258),(.046,.033,.055),skin,elbow)
        for i in range(4):
            x=-.03+i*.020
            s.sphere('Individual curled finger',(x,-.033,-.295),(.010,.016,.025 if i in (1,2) else .021),skin,elbow)
            s.sphere('Finger knuckle',(x,-.038,-.271),(.010,.009,.010),skin,elbow)
        s.sphere('Opposed thumb',(sign*.045,-.012,-.266),(.015,.018,.030),skin,elbow)
        curved(s,'Sleeve seam',[(0,-.073,-.02),(.027,-.075,-.07),(.02,-.071,-.18)],.003,coat,elbow)
        for i in range(3):s.beam('Sleeve compression fold',(-.048,-.065,-.05-i*.022),(.035,-.074,-.045-i*.022),.003,coat,elbow)
        knee=joints['knee'+side]
        if not metal:
            hip=joints['leg'+side]
            rings(s,'Tailored trouser thigh',[(.012,.075,.080,0),(-.07,.09 if broad else .085,.097,0),(-.20,.092 if broad else .082,.095,0),(-.32,.077,.079,0),(-.42,.073,.076,0)],'trousers',hip)
            rings(s,'Continuous trouser shin',[(.055,.074,.077,0),(0,.078,.079,-.008),(-.10,.074,.075,0),(-.24,.064,.069,0),(-.335,.059,.066,0)],'trousers',knee)
        rings(s,'Continuous leather boot shaft',[(-.235,.076,.073,0),(-.285,.085,.085,-.002),(-.34,.082,.085,-.008),(-.385,.077,.095,-.023),(-.435,.08,.098,-.032)],'metal' if metal else 'leather',knee)
        s.sphere('Rounded boot vamp',(0,-.071,-.455),(.094,.143,.052),'metal' if metal else 'leather',knee)
        s.cube('Boot welt sole',(0,-.067,-.493),(.187,.288,.026),'dark',knee,.035)
        for z in [-.31,-.35,-.39]:curved(s,'Worn boot fold',[(-.059,-.067,z),(-.01,-.09,z-.013),(.056,-.066,z-.006)],.003,'leather',knee)
        for i in range(3):s.beam('Boot welt stitching',(-.065+i*.06,-.202,-.462),(-.05+i*.06,-.202,-.462),.0025,'canvas',knee)


def architecture(s,region,kind):
    col=s.COLLECTIONS[kind+'_'+region];s.bpy.context.view_layer.active_layer_collection=s.bpy.context.view_layer.layer_collection.children[col.name]
    if kind in ('workshop','exchange','shelter'):
        front=-.35 if kind=='workshop' else -.826
        if kind=='workshop':
            s.cube('Recessed glazed workshop window',(-.41,front,.95),(.45,.035,.37),'dark',bevel=.006)
            for x in [-.65,-.4,-.17]:s.beam('Window mullion',(x,front-.025,.76),(x,front-.025,1.15),.015,'wood' if region=='WN_TOWER' else 'metal')
            s.beam('Window sill',(-.67,front-.05,.75),(-.14,front-.05,.75),.025,'wood')
        for i in range(8):
            x=-.89+i*.25
            if region=='WN_TOWER':s.cube('Individual weathered front plank',(x,front,.45),(.022,.02,.50),'wood',bevel=.004)
            elif region=='CITY_CLOUD_S':s.sphere('Fastened panel rivet',(x,front,.46),(.013,.008,.013),'brass')
            elif region=='ENACT_HILLS':s.beam('Mortar course',(x,front,.24),(x+.19,front,.24),.007,'concrete')
        if kind=='exchange':
            for i in range(3):
                x=-.56+i*.55;s.sphere('Canvas provisions sack',(x,.15,.70),(.18,.17,.22),'cloth');s.cylinder('Tied sack neck',(x,.15,.91),.04,.10,'leather')
            for i in range(6):s.cube('Counter plank joint',(-.77+i*.30,-.824,.51),(.012,.018,.55),'leather',bevel=.003)
        if kind=='shelter':
            for sign in [-1,1]:
                for i in range(4):curved(s,'Sagged stitched canvas',[(sign*.16,-.836,1.42-i*.21),(sign*.26,-.851,1.19-i*.21),(sign*.30,-.839,1.03-i*.21)],.004,'cloth')
    elif kind=='water':
        for i in range(14):
            a=i*math.tau/14;s.sphere('Tank flange bolt',(math.cos(a)*.47,math.sin(a)*.34,1.22),(.015,.015,.015),'brass')
        for height in [.43,.91]:
            for i in range(12):
                a=i*math.tau/12;s.sphere('Tank seam fastener',(math.cos(a)*.486,math.sin(a)*.35,height),(.01,.01,.013),'metal')
    elif kind=='garden':
        for x in [-.65,0,.65]:
            for y in [-.4,.3]:
                for i in range(3):
                    a=i*2.1;s.mesh('Curved growing leaf',[(x,y,.48),(x+math.cos(a)*.21,y+math.sin(a)*.21,.60),(x+math.cos(a+.22)*.29,y+math.sin(a+.22)*.29,.56),(x+math.cos(a)*.12,y+math.sin(a)*.12,.50)],[(0,1,2),(0,2,3)],'leaf')
    elif kind=='relay':
        for height in [1.95,2.16,2.40]:
            for x in [-.22,.22]:s.cylinder('Ceramic signal insulator',(x,.25,height),.045,.09,'ivory')
        curved(s,'Signal service cable',[(.26,-.15,.5),(.34,-.15,.8),(.18,.12,1.2),(0,.25,1.5)],.012,'dark')
    elif kind=='power':
        for x in [-.22,.22]:
            for y in [-.14,.14]:s.sphere('Collector base bolt',(x,y,.34),(.019,.019,.014),'brass')


def terrain(s,region):
    s.bpy.context.view_layer.active_layer_collection=s.bpy.context.view_layer.layer_collection.children['ground_'+region]
    rng=random.Random(710+sum(map(ord,region)))
    for i in range(46):
        x,y=rng.uniform(-3.5,3.5),rng.uniform(-3.5,3.5)
        if region=='WN_TOWER':
            s.mesh('Dry curled leaf',[(x-.05,y,.02),(x+.02,y-.055,.022),(x+.12,y,.042),(x+.01,y+.045,.025)],[(0,1,2),(0,2,3)],'canvas')
        elif region=='ENACT_HILLS':
            curved(s,'Fine earth fissure',[(x,y,.019),(x+.09,y+.08,.019),(x+.22,y+.04,.019)],.004,'soil')
        elif region=='CITY_CLOUD_S':s.sphere('Road aggregate',(x,y,.015),(.025,.018,.008),'stone')
        else:s.sphere('Mineral grit',(x,y,.022),(.037,.023,.012),'ivory')
