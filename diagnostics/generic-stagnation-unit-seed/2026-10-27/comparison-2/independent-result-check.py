from pathlib import Path
import json, tomllib, math, statistics as stat, collections, hashlib, re

Q = Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27/comparison-2')
def read(name): return json.loads((Q/name).read_text())
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
raw = tomllib.loads((Q/'output/results.toml').read_text())
summary = read('summary.json')
audit = read('audit.json')
process = read('output/process.json')
contract = read('contract-reviewed.json')
assert process['returncode'] == 0 and process['reason'] == 'exit0' and process['pins_unchanged'] is True
assert process['command'] == contract['command']
assert process['pins_sha256'] == sha(Q/'pins-reviewed.json')
assert read('completed.json')['elapsed_shared_seconds'] <= 600
assert read('completed.json')['accepted'] and read('supervisor.json')['accepted']
log = (Q/'output/run.log').read_text()
assert re.search(r'^Stagnation unit seed whole-function comparison\s*\|\s*105921\s+105921\s+', log, re.M)
assert 'Error During Test' not in log and 'Test Failed at ' not in log and not re.search(r'^ERROR:', log, re.M)
assert 'STAGNATION_UNIT_SEED_COMPARISON_COMPLETE cells=3415' in log
for name, digest in audit['bindings'].items(): assert sha(name) == digest
fields = ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']
assert raw['cost_fields'] == fields and raw['window_fields'] == ['pair','arm',*fields,'sink']
contexts = [(f'BF{bits}_RoundingMode{{:{mode}}}()', 'BigFloat') for bits in (64,128,256) for mode in ('Nearest','Down','Up','ToZero','FromZero')]
contexts += [(t,t) for t in ('Float32','Float64','Rational{BigInt}','Rational{Int64}')]
expected = []
for label, typ in contexts:
    for n in (32,128):
        for m in (8,32):
            for scope in ('values','observe','observe_dual'):
                for density in ('sparse','dense'):
                    for shape in (('bounded','unbounded','free') if typ == 'BigFloat' else ('free',)):
                        expected.append((label,typ,n,m,scope,density,shape,'A'))
    for n in (8,32):
        for m in (8,32):
            for density in ('sparse','dense'):
                for shape in (('positive','negative','mixed','slack') if typ in ('BigFloat','Rational{BigInt}') else ('mixed',)):
                    expected.append((label,typ,n,m,'unit',density,shape,'B'))
                    expected.extend((label,typ,n,m,'init',density,shape,arm) for arm in ('B','C','BC'))
    expected.extend((label,typ,32,8,scope,'sparse','free','A') for scope in ('observe_cold','observe_same'))
    expected.extend((label,typ,32,8,'init_ready','sparse','slack',arm) for arm in ('B','C','BC'))
assert len(expected) == len(raw['cells']) == len(summary['cases']) == 3415
names = ['context','type','n','rows','scope','density','shape','variant']
def cost(v):
    assert len(v) == 6 and all(type(x) in (int,float) and math.isfinite(x) and x >= 0 for x in v)
    assert type(v[1]) is type(v[2]) is int
    return v
phases = collections.defaultdict(list)
verified = []
gc_windows = 0
for cell, key, s in zip(raw['cells'], expected, summary['cases']):
    assert tuple(cell[n] for n in names) == key == tuple(s[n] for n in names)
    assert cell['id'] == '/'.join(map(str,(key[0],*key[2:])))
    ws = cell['windows']; assert len(ws) == 18
    ratios=[]; byte_deltas=[]; event_deltas=[]
    for pair in range(1,10):
        z=ws[(pair-1)*2:pair*2]
        assert [v[1] for v in z] == (['original',key[-1]] if pair%2 else [key[-1],'original'])
        for v in z:
            assert len(v)==9 and type(v[0]) is int and v[0]==pair
            cost(v[2:8]); assert v[6]==v[7]==0 and type(v[8]) is int and v[8]==(7 if key[4]=='values' else 1)
            phases['measured'].append(v[2:8]); gc_windows += v[5]>0
        by={v[1]:v for v in z}; old,new=by['original'],by[key[-1]]
        assert old[2]>0;ratios.append(new[2]/old[2]);byte_deltas.append(old[3]-new[3]);event_deltas.append(old[4]-new[4])
    med=stat.median(ratios)
    assert s['paired_ratio']==med and s['ratio_MAD']==stat.median(abs(x-med) for x in ratios)
    assert s['ratio_min']==min(ratios) and s['ratio_max']==max(ratios)
    for arm,label in [('original','original'),(key[-1],'candidate')]:
        for i,f in enumerate(fields[:3]):assert s[label][f]==stat.median(v[i+2] for v in ws if v[1]==arm)
    assert s['all_pairs_lower_bytes']==all(v>0 for v in byte_deltas)
    assert s['all_pairs_lower_events']==all(v>0 for v in event_deltas)
    verified.append(dict(s,raw_byte_saving_min=min(byte_deltas),raw_byte_saving_max=max(byte_deltas),raw_event_saving_min=min(event_deltas),raw_event_saving_max=max(event_deltas),raw_pairs_bytes_equal=sum(v==0 for v in byte_deltas),raw_pairs_bytes_increase=sum(v<0 for v in byte_deltas),raw_pairs_events_increase=sum(v<0 for v in event_deltas)))
assert gc_windows == 23 == audit['GC_affected_windows'] == summary['GC_affected_windows']
prep=raw['preparation'];assert len(prep)==3453
assert [(p['context'],p['phase']) for p in prep if 'phase' in p]==[(label,phase) for label,t in contexts for phase in ('correctness_and_snapshots','context_GC')]
assert [p['cell'] for p in prep if 'cell' in p]==[c['id'] for c in raw['cells']]
for p in prep:
    if 'phase' in p: phases[p['phase']].append(cost(p['cost']));continue
    for key in ('fixture','validation_and_snapshots'):phases[key].append(cost(p[key]))
    assert len(p['resets'])==18
    phases['measured_resets'].extend(cost(v) for v in p['resets'])
    for key,num in [('cold',2),('warm',6)]:
        assert len(p[key])==num
        for v in p[key]:
            assert len(v)==13 and type(v[6]) is int
            phases[key].append(cost(v[:6]));phases[key+'_resets'].append(cost(v[7:]))
def aggregate(cs):
    return dict(cells=len(cs),median_paired_ratio=stat.median(c['paired_ratio'] for c in cs),cell_paired_ratio_range=[min(c['paired_ratio'] for c in cs),max(c['paired_ratio'] for c in cs)],median_within_cell_MAD=stat.median(c['ratio_MAD'] for c in cs),median_original_us=stat.median(c['original']['seconds'] for c in cs)*1e6,median_candidate_us=stat.median(c['candidate']['seconds'] for c in cs)*1e6,cell_median_byte_saving_range=[min(c['original']['bytes']-c['candidate']['bytes'] for c in cs),max(c['original']['bytes']-c['candidate']['bytes'] for c in cs)],cell_median_event_saving_range=[min(c['original']['events']-c['candidate']['events'] for c in cs),max(c['original']['events']-c['candidate']['events'] for c in cs)],cells_all_pairs_bytes_lower=sum(c['all_pairs_lower_bytes'] for c in cs),cells_all_pairs_events_lower=sum(c['all_pairs_lower_events'] for c in cs),raw_pairs_bytes_increase=sum(c['raw_pairs_bytes_increase'] for c in cs),raw_pairs_bytes_equal=sum(c['raw_pairs_bytes_equal'] for c in cs),raw_pairs_events_increase=sum(c['raw_pairs_events_increase'] for c in cs))
groups={}
for dims in [('variant','type','scope'),('variant','type','scope','shape'),('variant','type','scope','density'),('variant','type','scope','rows')]:
    g=collections.defaultdict(list)
    for c in verified:g[tuple(c[d] for d in dims)].append(c)
    groups['/'.join(dims)]=[dict(zip(dims,key),**aggregate(cs)) for key,cs in g.items()]
resources=[json.loads(line) for line in (Q/'output/resources.jsonl').read_text().splitlines()]
assert resources and all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources)
pins=read('pins-reviewed.json');assert len(pins['inventory'])==1290
for path,v in pins['inventory'].items():assert str(Path(path).resolve(strict=True))==v['resolved'] and sha(path)==v['sha256'],path
for tree in pins['trees']:assert {str(p) for p in Path(tree).rglob('*') if p.is_file()}=={p for p in pins['inventory'] if Path(p).is_relative_to(tree)}
result=dict(verified=True,assertions=105921,cells=3415,windows=61470,GC_affected_windows=gc_windows,compile_seconds_all_measured=0,recompile_seconds_all_measured=0,pins=1290,groups=groups,phase_costs={key:dict(count=len(values),totals=dict(zip(fields,[sum(v[i] for v in values) for i in range(6)]))) for key,values in phases.items()},byte_variation_cells=[c for c in verified if c['raw_pairs_bytes_increase']],slowest_target_cells=[max([c for c in verified if c['type']=='BigFloat' and c['variant']==arm and c['scope']==scope],key=lambda c:c['paired_ratio']) for arm,scope in [('A','values'),('A','observe'),('A','observe_dual'),('B','init'),('C','init'),('BC','init')]],min_available_kib=min(r['available_kib'] for r in resources),max_swap_kib=max(r['swap_used_kib'] for r in resources),bindings={str(Q/n):sha(Q/n) for n in ['output/results.toml','output/run.log','output/process.json','summary.json','audit.json','pins-reviewed.json','driver-reviewed.jl','fixtures-reviewed.jl','extra-tests-reviewed.jl','boundary-tests.jl','admission.json']})
with (Q/'independent-result-check.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({key:result[key] for key in ['verified','assertions','cells','windows','GC_affected_windows','pins','min_available_kib','max_swap_kib']}))
