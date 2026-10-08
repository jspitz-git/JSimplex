"""Summarize retained replay attempts without counting process exit as accuracy."""
import hashlib,json,sys,tomllib
from pathlib import Path
raw=Path(sys.argv[1]); output=Path(sys.argv[2])
records=[]
for path in sorted([*raw.glob('baseline-*.toml'),*raw.glob('fixed-*.toml')]):
    d=tomllib.loads(path.read_text()); samples=d['records']
    assert [r['step'] for r in samples]==list(range(80,d['steps']+1,80))
    assert d['scheduled_refactors']==(d['steps']-1)//d['interval']
    assert all({c['operation'] for c in r['checks']}=={'entering','dense','unit'} and len(r['checks'])==3 for r in samples)
    probes=[c for r in samples for c in r['checks']]
    valid=all(max(c['residual'],c['reference_residual'])<=1e-10 and c['difference']<=1e-6 for c in probes)
    assert valid==d['valid']
    if path.name.startswith('fixed-'):assert valid and d['maximum_multiplier']<=1.0
    else:assert not valid
    record={k:d[k] for k in ('arm','interval','steps','scheduled_refactors','history_sha256','source_sha256','swaps','maximum_multiplier','elapsed','memory')}
    record.update(attempt=path.stem,report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),valid=valid,
        probe_count=len(probes),first_failed_step=next((r['step'] for r in samples if not r['valid']),None),
        maximum_residual=max(c['residual'] for c in probes),maximum_reference_residual=max(c['reference_residual'] for c in probes),
        maximum_difference=max(c['difference'] for c in probes))
    records.append(record)
assert len(records)==9
fixed=[r for r in records if r['attempt'].startswith('fixed-')]
assert len({r['source_sha256'] for r in fixed})==1
for old in (r for r in records if r['attempt'].startswith('baseline-')):
    new=next(r for r in fixed if r['arm']==old['arm'] and r['history_sha256']==old['history_sha256'] and r['interval']==old['interval'])
    assert old['steps']==new['steps'] and old['scheduled_refactors']==new['scheduled_refactors']
output.write_text(json.dumps({'records':records},indent=2)+'\n')
print('Audited',len(fixed),'repaired and',len(records)-len(fixed),'baseline replays;',sum(r['probe_count'] for r in fixed),'repaired probes')
