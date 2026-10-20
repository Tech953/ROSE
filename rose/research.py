"""Systems measurements and provenance, scoped to implemented game models."""
import copy
import json
import math
from pathlib import Path

import engine
import photonics
import vrex

PROTOCOL=json.loads((Path(__file__).parent/'reference/vrex-systems-v012.json').read_text(encoding='utf-8'))
HISTORY_LIMIT=16
TOLERANCE=1e-9


def energy_audit(f):
    ph=f.get('photonics',{})
    values={key:ph.get(key,0.) for key in ['input_energy','energy','emitted_energy','heat_energy']}
    invalid=[key for key,value in values.items() if type(value) not in {int,float} or not math.isfinite(value) or value<0]
    valid=not invalid and values['energy']<=photonics.CAPACITY+TOLERANCE
    residual=values['input_energy']-values['energy']-values['emitted_energy']-values['heat_energy'] if valid else None
    scale=sum(abs(value) for value in values.values())+1e-12 if valid else None
    normalized=abs(residual)/scale if valid else None
    status='FAIL' if not valid or normalized>TOLERANCE else 'EMPTY' if values['input_energy']==0 else 'PASS'
    return dict(status=status,scope='Rose finite optical ledger only',units='optical game units',
        values={key:None if key in invalid else value for key,value in values.items()},
        residual=residual,normalized_residual=normalized,tolerance=TOLERANCE,
        valid_bounds=valid,invalid_fields=invalid,has_input=valid and values['input_energy']>0)


def gates(f=None):
    report=(f or {}).get('vrex',{}).get('diagnostics') or {}
    stale=bool(report and report.get('configuration_hash')!=vrex.configuration_hash((f or {}).get('vrex')))
    mapping={'A':'order','B':'topology','C':'load','D':'sustained','E':'laboratory'}
    return [dict(**copy.deepcopy(gate),status='STALE / RERUN' if stale and gate['id']!='E' else report.get(mapping[gate['id']],{}).get('status','NOT RUN'),
        scope='Laboratory' if gate['id']=='E' else 'Software model diagnostics') for gate in PROTOCOL['gates']]


def convergence_status(f):
    report=f.get('vrex',{}).get('diagnostics') or {}
    if report and report.get('configuration_hash')!=vrex.configuration_hash(f.get('vrex')):return 'STALE / RERUN'
    return report.get('convergence',{}).get('status','NOT RUN')


def capture(w,f,p,node,interpretation):
    ph=photonics.ensure(f)
    ph['research_serial']=ph.get('research_serial',0)+1
    record=dict(id='audit-'+str(ph['research_serial']),schema=2,tick=w['tick'],
        seed=w['seed'],field=f['address'],actor=p['id'],actor_name=p['name'],workshop=node['id'],
        source_node=ph['source_node'],vrex_source_node=f.get('vrex',{}).get('source_node'),engine_version=engine.VERSION,classification='SYSTEMS MEASUREMENT',
        source=copy.deepcopy(PROTOCOL['source']),interpretation=bool(interpretation),
        band=ph['band'],mode=ph['mode'],energy_audit=energy_audit(f),gates=gates(f),
        vrex_energy=vrex.audit(f.get('vrex')),vrex_diagnostics=copy.deepcopy(f.get('vrex',{}).get('diagnostics')),
        legacy_detector='NOT REPRODUCED',convergence=convergence_status(f))
    ph['research_runs']=(ph.get('research_runs',[])+[record])[-HISTORY_LIMIT:]
    return copy.deepcopy(record)


def public(f):
    ph=f.get('photonics',{})
    return dict(protocol=PROTOCOL['title'],source=copy.deepcopy(PROTOCOL['source']),
        energy_audit=energy_audit(f),gates=gates(f),legacy_record=copy.deepcopy(PROTOCOL['legacy_record']),
        runs=copy.deepcopy(ph.get('research_runs',[])),history_limit=HISTORY_LIMIT,
        convergence=convergence_status(f),classification='SYSTEMS MEASUREMENT')


def export(f):
    records=f.get('photonics',{}).get('research_runs',[])
    if not records:raise ValueError('Record a workshop systems measurement before exporting it.')
    return dict(format='Rose-research-audit',schema=1,record=copy.deepcopy(records[-1]))
