"""Compile a traceable art-direction register without rewriting its source corpus."""
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ['reference/visual-corpus/catalog.json', 'reference/lore-record-v012.json',
          'reference/lore-transport/catalog.json', 'docs/WORLD-LORE-AND-PARTICLE-INTEGRATION.md']

PRINCIPLES = [
    'Build tactile, muted faux-realism: material volume, seams and handling precede small functional light signatures.',
    'Use the broad druid / nano / neon spectrum without treating a genre, material or culture as a rank of superiority.',
    'Keep natural ground continuous. The hidden local hex grid supports movement; existing optional tactical overlays remain available.',
    'Preserve the locked orthographic projection, 0.52 ground compression, six facings, foot anchors, palette and optional CRT presentation.',
    'Express vast scale through body, service detail, inhabited terrace, monolith and atmospheric horizon; source dimensions do not recalibrate the map.',
    'Individual characters retain their registered body, appearance, personal items, history, speech, attitude and current engagement.',
    'Growth, weathering, repair, construction, contact and destruction follow saved outcomes and finite inputs.',
    'Keep particulate measurements and engineering concepts off screen during ordinary play; preserve uncertainty in authoring sources.',
    'Text and current state define meaning and behavior. Images guide presentation; conflicting source depictions remain variants.',
]

# Each rule records a visual translation and the simulation boundary it cannot cross.
RULES = {
 'material': dict(terms=['metal','wood','clay','stone','crystall','bio-plast','bio-glass','ceramic','alloy'],
   draw='Give each established material thickness, joints, roughness and a readable pattern of handling.',
   animate='Use existing condition, contact and maintenance states.',
   preserve='Do not change physical hardness, salvage, stock or durability from a picture.'),
 'contracts': dict(terms=['contract','corporat','institution','regulat','provision','vendor','commerce','econom'],
   draw='Make service architecture, maintained tools and small institutional marks legible at body scale.',
   animate='Use established work cycles, trade and dialogue outcomes.',
   preserve='A visual identity does not issue a contract, free goods, currency policy or access.'),
 'credentials': dict(terms=['black.dot','merc tag','certif','clearance','access','screening','restricted'],
   draw='Use modest verification marks and legible thresholds rather than giant interface overlays.',
   animate='Show feedback only after an authoritative access or skill check.',
   preserve='Retain existing permissions, reputation, refusal and faction requirements.'),
 'monument': dict(terms=['tower','mountain','scale','peak','atmospher','monument','continent','planet','apogean'],
   draw='Nest human service detail inside inhabited terraces, a continuous massive form and atmospheric distance.',
   animate='Hold the camera and foundations steady; use existing moving units to communicate scale.',
   preserve='Illustrated dimensions, ring or peak counts and heights establish no calibrated geography or reachable floors.'),
 'network': dict(terms=['greatweb','great web','great-web','fractech','pillar','internode','omnipillar','signator','pyry','pyri','kho'],
   draw='Embed sparse verification nodes and deliberate signature marks in substantial material housings.',
   animate='Use existing paid power and network events for pulses.',
   preserve='Networks add no public omniscience, free energy, clearance or luminous ground grid.'),
 'projection': dict(terms=['lightprokt','lightprkt','light projection','driven-light','optical','faceted','spectral','resonance'],
   draw='Separate bounded luminous interfaces and facets from their darker structural supports.',
   animate='Follow actual paid excitation, quenching, exposure and paused state.',
   preserve='A source illustration is not an emitter or a second optical simulation.'),
 'weather': dict(terms=['wind','storm','aether','contrail','dust','sand','rain','weather'],
   draw='Contrast scoured solid surfaces with restrained fabric and crystalline material; keep jade and rose accents local.',
   animate='Read actual wetness, dust, wind, restraint and fitted hardware state.',
   preserve='A source storm is background reference, not a current weather event.'),
 'ecology': dict(terms=['growth','decay','harvet','forest','tree','organic','mollusk','garden','bio-nano','eunix'],
   draw='Distinguish grown, cultivated, worked, exhausted and recovering surfaces through material and spacing.',
   animate='Use saved soil, moisture, growth, decay and construction stages.',
   preserve='A concept image supplies no organisms, new physiology or free resources.'),
 'identity': dict(terms=['character','companion','autonomy','appearance','persona','life-string','immunix','endcap','meta-fingers'],
   draw='Keep the registered body, appearance, clothing, personal tools and history recognizable.',
   animate='Let established speech, refusal, attitude and engagement cycles determine behavior.',
   preserve='Source personae do not replace player identity, equipped objects or living NPC status.'),
 'percept': dict(terms=['particul','percept','semblance','void','continuity','substrate','strain','infi','mmtx'],
   draw='Resolve tangible local surfaces with selective geometric limits and coherent return landmarks.',
   animate='Preserve individual identity, committed movement and return continuity.',
   preserve='Conceptual language does not introduce a new equation, physical law or ordinary measurement overlay.'),
 'archives': dict(terms=['gravesite','grave_site','burial','archiv','digiprint','necramanc'],
   draw='Use restrained sealed mass, archival detail and small guarded interfaces.',
   animate='Show only established handling, access checks and recorded responses.',
   preserve='Depicted engrams do not resurrect or establish a missing person as present.'),
 'travel': dict(terms=['transit','pilgrim','route','overworld','hex','travel','trail','framegen','freeway'],
   draw='Distinguish local paths, civic circulation and distant logistics through scale and construction.',
   animate='Follow committed six-direction local movement and the existing free-selection world map.',
   preserve='Source arrows do not become routes, destinations, teleportation or new map coordinates.'),
 'unresolved': dict(terms=[],draw='Keep the visual interpretation incomplete and provisional.',
   animate='Use only already implemented outcomes.',preserve='Preserve fragments and unresolved theory without completing their mechanism.'),
 'offscreen': dict(terms=[],draw='Keep this engineering or systems record in authoring and research context.',
   animate='Expose only effects already owned by the existing simulation.',preserve='Do not display measurements or derive ordinary visual events from this record.'),
 'source_detail': dict(terms=[],draw='Preserve the source wording and evidence status as a bounded authoring brief.',
   animate='Use existing state only.',preserve='Do not fill absent topology, chronology, mechanisms or outcomes.'),
 'independent_identity': dict(terms=[],draw='Give KHO.DEV its own manufacturer and service identity.',
   animate='Use only its established service context.',preserve='KHO.DEV is not KHO intelligence; similar spelling does not merge identities.'),
}
CATEGORY_RULES = {
 'material':['products','architecture','regions'], 'contracts':['products','infrastructure'],
 'credentials':['products','architecture','infrastructure'], 'monument':['architecture','regions','unassigned'],
 'network':['architecture','infrastructure','framework'], 'projection':['regions','infrastructure','framework'],
 'weather':['regions','reported_landscapes'], 'ecology':['regions','unassigned','framework'],
 'identity':['products','framework'], 'percept':['framework','reported_landscapes','unassigned'],
 'archives':['regions','architecture'], 'travel':['infrastructure','regions'],
 'unresolved':['reported_landscapes','unassigned'], 'independent_identity':['products'],
}
ROLES = {
 'architecture':('monument_and_inhabited_detail','Continuous mass, readable service detail, material and scale variants.'),
 'regions':('regional_material_and_scale','Regional surfaces, light signatures and layered scale; named profile only.'),
 'products':('individual_unit_materials','Individual silhouette, fabrication, service face and brand detail; qualitative specifications only.'),
 'infrastructure':('functional_circulation','Circulation and service readability; no automatic route or clearance.'),
 'framework':('conceptual_interpretation','Authoring vocabulary for percept and continuity; no numeric physics or need grants.'),
 'combat':('contact_and_silhouette','Contact poses and differentiated silhouettes; depicted factions and Node 7B remain scenario-only.'),
 'unassigned':('unassigned_form_study','Unassigned tree or sphere form study; do not place in named live regions.'),
 'reported_landscapes':('reported_construct_readability','Readability of reported constructs; preserve report status, not current observation.'),
}
SUBJECTS = {
 'water':('A contained source, serviced basin and body-scale draw point.','Use actual stock, operation and service condition; no free water.'),
 'power':('A heavy housing, grounded cabling and restrained service interface.','Only existing online fixtures emit; no added energy source.'),
 'relay':('A substantial vertical spine and small verification face.','Do not confer clearance, knowledge or a new network link.'),
 'workshop':('Joined repairs, readable work contacts and fitted machine housings.','Show actual fitted mechanisms and paid drive state.'),
 'exchange':('A service counter with provision storage and visible local maintenance.','Use actual stock, contracts, reputation and access checks.'),
 'shelter':('A body-scale entrance, structural supports and patched fabric or bio-plast.','Use actual anchors, material condition and saved weather.'),
 'garden':('Cultivation with legible plant spacing and worked versus exhausted soil.','Use saved soil, moisture and growth; introduce no free organisms.'),
 'rock':('A continuous natural fracture surface with grounded contact.','Keep existing collision, silhouette and hidden grid; no hex-outline terrain.'),
 'actor':('A registered body, appearance, clothes and personally held tools.','Preserve identity, skin, equipment, attitude, speech and autonomy.'),
 'landmark':('A continuous monumental solid with inhabited detail and atmospheric distance.','Source scale creates no topology, new floors or traversable destinations.'),
}
FINISH = {
 'wood':dict(label='Mineralized neural-wood / handled grain',shadow=[58,51,41],light=[169,150,114],mix=.28,contrast=.07,grain=2),
 'metal':dict(label='Repaired alloy / restrained reflections',shadow=[48,53,56],light=[168,172,166],mix=.30,contrast=.08,grain=1),
 'stone':dict(label='Worked charcoal stone / embedded earth',shadow=[52,51,47],light=[157,150,131],mix=.34,contrast=.09,grain=2.4),
 'crystal':dict(label='Dense crystalline solid / cold facet response',shadow=[44,62,69],light=[171,201,195],mix=.20,contrast=.08,grain=.5),
 'fabric':dict(label='Woven refuge fabric / broad handling marks',shadow=[65,58,45],light=[179,160,123],mix=.29,contrast=.04,grain=1.8),
 'polymer':dict(label='Patched bio-polymer / matte structural skin',shadow=[46,50,44],light=[153,159,137],mix=.24,contrast=.05,grain=1.1),
}

def classify(text, status='', hidden=False):
    if hidden:return ['offscreen']
    if status in {'unresolved_theory','source_fragment'}:return ['unresolved']
    text=text.lower()
    if 'kho.dev' in text:return ['independent_identity']
    return [k for k,v in RULES.items() if any(term in text for term in v['terms'])] or ['source_detail']

def compile_register():
    visual,lore,biomes=[json.loads((ROOT/p).read_text()) for p in INPUTS[:3]]
    images=visual['references']
    def image_ids(rules):
        cats={c for r in rules for c in CATEGORY_RULES.get(r,[])}
        return [r['id'] for r in images if r['category'] in cats]
    def translate(rules):return [{k:v for k,v in RULES[r].items() if k!='terms'} for r in rules]
    profiles={}
    for p in biomes['profiles']:
        v=visual['profile_briefs'].get(p['id'],{})
        sources=[r['id'] for r in images if p['id'] in r['profiles'] and r['category'] not in {'framework','combat','unassigned'}]
        profiles[p['id']]=dict(label=p['label'],placement=p['placement'],engine_region=p['engine_region'],
            materials=v.get('materials',p['material_motifs']), lighting=v.get('lighting',[p['lighting']['direction']]),
            scale=v.get('scale','Unplaced text-only profile. Establish scale through the source context; no new map position is inferred.'),
            image_sources=sources,source_constraints=p['constraints'],
            text_sources=[s for f in p['facts'] for s in f['sources']])
    record=dict(schema=1,version='0.18.0',title='Rose / material, signature and percept',primary_text=INPUTS[3],
      sources=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in INPUTS],
      global_rules=PRINCIPLES,interpretation_rules=RULES,profiles=profiles)
    record['image_contributions']=[dict(image_id=r['id'],filename=r['filename'],role=ROLES[r['category']][0],
        application=ROLES[r['category']][1],profiles=r['profiles'],status=r['status'],observed=r['observed'],
        generation_use=r['generation_use'],conflicts=r['conflicts'],
        ordinary_region_source=r['category'] in {'architecture','regions'} and bool(r['profiles'])) for r in images]
    record['lore_crosswalk']=[]
    for r in lore['records']:
        tags=classify(r['text'],r['status'],r['id'].startswith('vrex-') or r['id'] in {'aurora','research','engram-json-capacity'})
        record['lore_crosswalk'].append(dict(record_id=r['id'],source=INPUTS[1],source_text=r['text'],
          evidence_status=r['status'],rules=tags,interpretation=translate(tags),image_sources=image_ids(tags),scope='authoring; not current observation'))
    record['biome_crosswalk']=[]
    for p in biomes['profiles']:
        for i,f in enumerate(p['facts'],1):
            tags=classify(f['text'],f['status'])
            record['biome_crosswalk'].append(dict(id=f"{p['id']}:{i}",profile=p['id'],source_text=f['text'],
              evidence_status=f['status'],sources=f['sources'],rules=tags,visual_translation=translate(tags),image_sources=profiles[p['id']]['image_sources']))
    record['unit_recipes']=[dict(id=f'{pid}:{kind}',profile=pid,subject=kind,placement=p['placement'],
       composition=values[0],materials=p['materials'],lighting=p['lighting'],image_sources=p['image_sources'],
       text_sources=p['text_sources'],state_constraint=values[1],
       production='Authoring recipe. Model each approved unit in the locked projection; bake six facings, condition states, contact-timed clips, alpha and foot anchors. Not a new modeled asset.')
       for pid,p in profiles.items() for kind,values in SUBJECTS.items()]
    record['product_briefs']=[dict(id=p['id'],designation=p['fields']['designation'],kind=p['kind'],
       source_specification=p['fields'],text_sources=p['sources'],
       image_sources=[r['id'] for r in images if r['category']=='products'],
       art_brief='Individual unit silhouette and service face. Use the exact qualitative materials, contractor and manufacturer; shared product images are family guidance, not a claim that this specific unit is depicted.',
       status='authoring only; no new playable item or numeric statistic') for p in biomes['product_records']]
    record['coverage']=dict(unique_images=len(images),uploaded_names=visual['coverage']['uploaded_files'],
       lore_records=len(lore['records']),biome_profiles=len(profiles),biome_facts=len(record['biome_crosswalk']),
       unit_recipes=len(record['unit_recipes']),product_briefs=len(record['product_briefs']))
    record['conflicts']=visual['conflict_register']
    record['overrides']=['Current user direction uses druid / nano / neon rather than the historical genre label retained verbatim in source records.']
    record['implementation']=dict(runtime='Bounded RGB material finish on existing rendered structures and rocks; read-only current-region narrator guidance and public blueprint summary.',
       preserved='Original source bytes, baked sprite sheets, alpha, skin, picking, world geography, simulation and power ownership.',
       pending=['Approved regional ring/peak morphology','New individual modeled units and character/portrait assets','Directional and condition animation bakes','Full-browser and art-reviewed native-size sign-off'])
    return record,visual

def write_outputs():
    r,visual=compile_register()
    def write(p,text):
        target=ROOT/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
    write('reference/art-direction/direction-v018.json',json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    runtime=dict(schema=1,version=r['version'],scope='Artistic RGB finish; not physics, emission or numerical measurement.',materials=FINISH,
       regions={k:dict(name=v['label'],material_sources=v['image_sources']) for k,v in r['profiles'].items() if v['engine_region']})
    write('static/art-direction-runtime.json',json.dumps(runtime,indent=2,ensure_ascii=False)+'\n')
    guide=make_guide(r)
    write('docs/ART-DIRECTION-AND-TEXT-INTERPRETATION.md',guide)
    write('static/art-direction.html',make_page(r,visual))
    print(json.dumps(r['coverage'],sort_keys=True))

def make_guide(r):
    c=r['coverage'];lines=['# Rose 0.18.0 — Art direction and text interpretation','',
      'The existing world-lore text is the primary interpretation source: `docs/WORLD-LORE-AND-PARTICLE-INTEGRATION.md`, together with the later biome documents and exact paragraph citations. No separately named new text file was supplied for this pass.',
      '',f"The register accounts for all {c['unique_images']} distinct images ({c['uploaded_names']} uploaded names), {c['lore_records']} current lore records, {c['biome_facts']} biome facts and {c['biome_profiles']} profiles. Thirteen duplicate image aliases retain their names without receiving extra weight. It provides {c['unit_recipes']} unit recipes and {c['product_briefs']} named product briefs.",
      '', '## Shared visual grammar','']
    lines += ['- '+x for x in r['global_rules']]
    lines += ['', 'This is a coherent direction for the broad druid / nano / neon spectrum. Original source text remains intact where it uses an older genre label; current user direction governs new art. Dark surfaces must retain material separation and readable contact. Tiny windows, access points and maintained equipment make immense architecture credible.',
       '', '## Text into visual decisions','', '| Source meaning | Visual translation | Behavior retained |','| --- | --- | --- |',
       '| WN_TOWER is inhabited institutional infrastructure | Continuous opaque mass, embedded habitation, neural-wood and repaired bio-plast at service scale; sparse amber, cyan and white-gold | No new floors, bridges or permissions |',
       '| ENACT combines domestic terraces with guarded archives | Worked charcoal stone, modest civic thresholds, repair seams and sealed burial detail | Existing access checks and authored archive status |',
       '| City_Cloud_S contains mountain metallurgy and education | Salvaged iron and tarnished copper below, graphite repairs and refined upper service work, localized cyan interfaces | Original interpreted map; conflicting poster orientations remain variants |',
       '| AETHERGALE uses fabric, crystal and jade/rose motifs | Dense crystalline solids contrasted with worn refuge cloth and restrained accent colors | Actual weather, anchors, wetness and fitted hardware |',
       '| Contract and credential systems shape service | Body-scale counters, provision storage, small verification marks and readable thresholds | Reputation, skill checks, stock and refusal |',
       '| Growth, decay and construction are processes | Distinct worked, exhausted, cultivated, repaired and ruined surfaces | Saved lifecycle and finite materials, not spontaneous scenery |',
       '| Particulate and percept language describes continuity | Tangible local resolved surfaces and return landmarks at vast implied scale | Existing physics and identity; no numerical overlay |',
       '| Character autonomy and history matter | Registered appearance, personal equipment, body silhouette and conversational demeanor | Existing NPC life and engagement cycles; no source-persona substitution |',
       '', 'The full register preserves every original lore/fact text, evidence status, citation, selected interpretation rule and image association. An association is a proposed authoring use, not proof that a source image depicts a particular sentence. KHO.DEV retains its independent identity and is not merged with KHO intelligence.',
       '', '## Regional briefs','', '| Profile | Materials | Light | Placement |','| --- | --- | --- |']
    for pid,p in r['profiles'].items():
        lines.append('| '+pid+' | '+'; '.join(p['materials'])+' | '+'; '.join(p['lighting'])+' | '+p['placement']+' |')
    lines += ['', 'Scale is documented per profile in the register. Human-scale service contacts sit inside terrace, monolith and atmospheric layers; inconsistent kilometers, heights, ring counts and peak counts do not change collisions or map coordinates. ENACT remains upper left; Red Gate and Scarlet Plateau remain toward the lower right under the original interpreted map.',
       '', 'Snail Wood, IO_COMBI_OI and Mollusk Crescent Moonland have text-only briefs. Unassigned tree and sphere studies remain unassigned. A labeled AquiSphere tree variant is not silently selected over the distinct sphere variant. Mesas panorama labels do not transplant WN_REZ or Lower Burgs. Scenario-only combat images do not add the Fractbound Covenant, Enneract Trinode, Duskvoid Syndicate or Node 7B to the current world.',
       '', '## Implemented renderer pass','',
       'The default Text + Image Direction setting applies a bounded, deterministic RGB finish to the existing rendered structures and rocks in the four active source-backed regions. It reads the object’s existing physical material identity: wood, metal, stone, crystal, fabric or polymer. A stable per-object variation keeps repeated units from receiving a single flat color.',
       '', 'The finish deepens material separation and handling grain while preserving the prepared silhouette, alpha, soft shadows, foot anchor, frame timing, scale, original geometry and saturated practical-light pixels. Live weather and powered hardware remain later passes. The finish creates no emission, resources, interactions or simulation ticks. Actor bodies, skin, projects, unplaced regions, remote views, void percepts and historical art styles retain their existing rendering.',
       '', 'Materials → Baked Surfaces provides a reversible comparison and persists locally. The bounded cache holds at most 48 frames and failures fall back to baked surfaces. This pass does not manufacture new 3D assets or turn image concepts into rigs. The included comparison is drawn by the actual native canvas renderer from matched authored regional fixtures with the same frozen layout.',
       '', '## Engine and authoring integration','',
       'Current-region optional narration receives a defensive, read-only materials/light/scale brief and the shared principles. Facts remain background rather than completed actions or current observations. Remote and void narration receives no ordinary regional context. The blueprint exports a public source-register link, principles and recipe count without character or session data.',
       '', 'Open Art direction and text interpretation from the map/reference links. Its register, source images, guide and matched comparison are accessible through fixed local host routes. No request filename is joined to arbitrary reference paths.',
       '', '## Unit production','',
       'Each of the eleven profiles has separate recipes for water, power, relay, workshop, exchange, shelter, garden, rock, actor and landmark. These are 110 production briefs, not 110 finished models. The 43 named product briefs retain designation, qualitative classification, materials/disciplines, contractor, manufacturer and capability wording with exact citations. They do not invent damage, AP, price, speed or an equipment grant.',
       '', 'Model approved units individually using the existing orthographic camera and ground compression. Keep a distinct silhouette, structural surface, body-scale service contact and functional light channel. Bake the required six directions, condition states and contact-timed clips with explicit alpha and stable foot anchors. Inspect native-size palette/CRT presentation, occlusion, clearance, solid-pixel picking and contact timing before replacing any original sheet.',
       '', '## Contribution coverage','', '| Image role | Distinct images |','| --- | ---: |']
    for role,count in sorted(Counter(x['role'] for x in r['image_contributions']).items()):lines.append(f'| {role.replace("_"," ")} | {count} |')
    lines += ['', 'Every image appears once in the contribution register. Framework studies supply authoring vocabulary; combat studies supply contact/silhouette guidance; reported landscapes retain their report status. No unassigned, framework or combat image becomes a named live-region profile source.',
       '', '## Retained source tensions','']
    for key,value in r['conflicts'].items():lines += [f'- **{key.replace("_"," ")}:** {value}']
    lines += ['', '## Rebuild and practical limits','', '`python3 tools/build_art_direction.py` regenerates the register, runtime finish configuration, guide and authoring page. Four input SHA-256 values make the interpretation reproducible against the supplied source corpus. Original images, lore documents, map sources, prepared art and numerical kernels remain unchanged.',
       '', 'New individually modeled regional buildings, portraits and animation bakes remain production work. A full interactive browser and final native-size art review remain separate sign-off steps. See `docs/validation-results-v018.json` for the completed automated verification and its scope.','']
    return '\n'.join(lines)

def make_page(r,visual):
    e=lambda s:html.escape(str(s),quote=True)
    imgs={x['id']:x for x in visual['references']}
    def source_links(ids):return ' · '.join(f'<a href="{e(imgs[i]["url"])}" target="_blank" rel="noopener">{e(imgs[i]["filename"])}</a>' for i in ids) or 'Text-only brief; no labeled image source.'
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Rose / Art direction</title><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/visual-references.css"></head><body><main class="reference-archive">',
      '<nav><a href="/">Return to Rose</a> · <a href="/visual-references.html">All reference images</a> · <a href="/art-direction-register.json">Interpretation register</a> · <a href="/art-direction-guide.txt">Complete guide</a></nav>',
      '<header><p class="overline">ROSE 0.18 / SOURCE INTO SURFACE</p><h1>Material, signature and percept</h1><p>Text defines meaning and behavior. Images guide tactile materials, individual silhouettes, functional light and immense scale.</p></header>',
      '<p>80 distinct images · 93 source names · 44 lore records · 58 biome facts · 110 unit recipes · 43 product briefs.</p>',
      '<h2>Shared direction</h2><ul>'+''.join('<li>'+e(x)+'</li>' for x in r['global_rules'])+'</ul>',
      '<h2>Matched engine scenes</h2><p>Left: original baked surfaces. Right: text + image material direction. Each pair is an authored regional fixture using the same frozen layout, camera, geometry and lighting. This is a material pass on existing assets; new individually modeled units remain production work.</p><figure class="art-direction-comparison"><img src="/art-direction-preview.png" alt="Four matched regional scenes comparing baked surfaces and the source-guided material pass" width="2060" height="2740" loading="lazy"></figure>',
      '<h2>Regional briefs</h2>']
    for pid,p in r['profiles'].items():
        parts += [f'<section><h3>{e(p["label"])}</h3><p>{e(p["placement"])}</p><p><strong>Material:</strong> {e("; ".join(p["materials"]))}</p><p><strong>Light:</strong> {e("; ".join(p["lighting"]))}</p><p>{e(p["scale"])}</p><p>{source_links(p["image_sources"])}</p></section>']
    parts += ['<h2>Text interpretation examples</h2><p>The existing world-lore corpus is the primary text. Original evidence status remains attached; these are authoring translations, not current observations. New art uses the broad druid / nano / neon spectrum.</p>']
    examples=[x for x in r['lore_crosswalk'] if x['record_id'] in {'presentation','scale','institutions','great-web','eunix','druid','void'}]
    for x in examples:
        parts += [f'<section><h3>{e(x["record_id"])}</h3><blockquote>{e(x["source_text"])}</blockquote><p>{e(x["evidence_status"])}</p><ul>'+''.join('<li>'+e(y['draw'])+' '+e(y['preserve'])+'</li>' for y in x['interpretation'])+'</ul></section>']
    parts += ['<h2>Every image has a contribution</h2><p>Duplicates do not increase influence. Unassigned studies, conceptual frameworks and combat scenarios stay outside named ordinary-region sources.</p>']
    for x in r['image_contributions']:
        parts += [f'<details><summary>{e(x["filename"])} / {e(x["role"].replace("_"," "))}</summary><p>{e(x["application"])}</p><p>{e(" ".join(x["observed"]))}</p><ul>'+''.join('<li>'+e(y)+'</li>' for y in x['generation_use'])+f'</ul><p>{source_links([x["image_id"]])}</p></details>']
    parts += ['<h2>Production status</h2><p>'+e(r['implementation']['runtime'])+'</p><p>Pending: '+e('; '.join(r['implementation']['pending']))+'.</p></main></body></html>']
    return '\n'.join(parts)+'\n'

if __name__=='__main__':write_outputs()
