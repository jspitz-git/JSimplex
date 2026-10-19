from pathlib import Path
import json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results';D=E/'DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';H=E/'DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
put('prepare-controls.py',Path(__file__).read_text())
p=D/'driver.jl';s=p.read_text().replace(', Statistics','').replace(',Statistics','');s=s.replace('function allocation_tests()','median7(x)=length(x)==7 ? sort(x)[4] : error("Expected seven observed samples")\nfunction allocation_tests()').replace('median(', 'median7(');p.write_text(s)
# Validate every complete prefix window even on timeout; half-written files fail TOML parsing.
p=D/'allocation_oracle.py';s=p.read_text();s+='''
def partial_windows(rows,fixtures):
 selected=[f for f in fixtures if f['name'] in CELLS]
 require(tuple(f['name'] for f in selected)==CELLS,'Partial fixture order')
 schedule=[f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)]
 require(set(rows)==set(schedule[:len(rows)]),'Noncontiguous partial windows')
 for cell,f in enumerate(selected,1):
  matrices=None
  for w in range(1,21):
   name=f'window-{cell}-{w}.toml'
   if name not in rows:break
   if matrices is None:matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']]
   r=rows[name];pair=(w+1)//2;order=(w-1)%2+1
   window_ok(r,f,1,pair,order,matrices);require(r['policy']=='threshold_one','Partial policy')
   if order==2:
    a=rows[f'window-{cell}-{w-1}.toml']
    require(a['outputs']==r['outputs'] and a['modes']==r['modes'],'Partial paired bits/modes')
 return True
''';p.write_text(s)
p=D/'audit.py';s=p.read_text().replace("pure=timeout_only(","from allocation_oracle import partial_windows\n partial_windows({n:tomllib.loads((out/n).read_text()) for n in names & windows},rd(D/'inputs.json')['fixtures'])\n pure=timeout_only(");p.write_text(s)
# New copy of synthetic tests, never run old checker or write its evidence.
s=(H/'offline-tests.py').read_text().replace('BEGIN BG export workspace driver ','BEGIN BG specialization driver ')
s=s.replace("with (D/'offline-tests.json').open('x')", "with (D/'offline-tests.json').open('x')")
# Additional malformed cost gate tests: synthetic exact diagonal fixtures, no numerical solver.
extra='''
from allocation_oracle import allocation_results,partial_windows
import struct
bt=lambda x:struct.pack('>d',float(x)).hex()
fixtures=[];rows={}
for cell,name in enumerate(('sparse32','dense32','sparse96'),1):
 m=dict(n=1,colptr=[1,2],rowval=[1],nzval=[bt(1)])
 f=dict(name=name,n=1,matrices=[copy.deepcopy(m) for _ in range(9)],steps=[dict(j=1,a=[bt(1)],dse=[bt(1)],unit=[bt(1)]) for _ in range(8)])
 fixtures.append(f)
 for pair in range(1,11):
  for order in (1,2):
   side=('reference','candidate')[(order-1) if pair%2 else (2-order)]
   rows[f'window-{cell}-{2*(pair-1)+order}.toml']=dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.,bytes=100 if side=='reference' else 90,events=10 if side=='reference' else 9,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.1]*6,outputs=[[bt(1)] for _ in range(24)])
check(len(allocation_results(rows,fixtures,'green'))==3,'allocation_green_positive')
redrows=copy.deepcopy(rows)
for r in redrows.values():
 if r['side']=='candidate':r['events']=11
check(len(allocation_results(redrows,fixtures,'red'))==3,'allocation_red_three_failures')
reject(lambda:allocation_results(rows,fixtures,'red'),'red_unexpected_pass')
reject(lambda:allocation_results(redrows,fixtures,'green'),'green_increase')
for name,mut in {
 'missing_window':lambda r:r.pop('window-1-1.toml'),
 'bad_order':lambda r:r['window-1-1.toml'].update(order=2),
 'nan_time':lambda r:r['window-1-1.toml'].update(seconds=float('nan')),
 'compilation':lambda r:r['window-1-7.toml'].update(compile_seconds=.1),
 'bad_residual':lambda r:r['window-1-1.toml']['outputs'][0].__setitem__(0,bt(2)),
 'input_mutated':lambda r:r['window-1-1.toml'].update(inputs_unchanged=False),
 'mode_difference':lambda r:r['window-1-1.toml'].update(modes=['direct']*3),
 'policy':lambda r:r['window-1-1.toml'].update(policy='default'),
 'boolean_count':lambda r:r['window-1-1.toml'].update(events=True),
 'nested_overflow':lambda r:r['window-1-1.toml'].update(nested_seconds=[1.]*6),
 'false_correctness':lambda r:r['window-1-1.toml'].update(correct=False)}.items():
 x=copy.deepcopy(rows);mut(x);reject(lambda:allocation_results(x,fixtures,'green'),'allocation_'+name)
check(partial_windows({},fixtures),'empty_prefix')
check(partial_windows({k:rows[k] for k in ['window-1-1.toml','window-1-2.toml']},fixtures),'valid_prefix')
reject(lambda:partial_windows({'window-1-2.toml':rows['window-1-2.toml']},fixtures),'partial_missing_first')
# Hash and stage refusal uses temporary files only, not seal/launch.
with tempfile.TemporaryDirectory(prefix='bgxs-hash-') as td:
 p=Path(td)/'stage';p.mkdir();f=p/'source';f.write_text('original')
 pins=dict(files=[str(f)],trees=[str(p)],inventory=c.guard.inventory([str(f)],[str(p)]),inputs=[])
 check(c.guard.pins_match(pins),'hash_stage_valid')
 f.write_text('changed');check(not c.guard.pins_match(pins),'hash_refusal');f.write_text('original')
 (p/'extra').write_text('extra');check(not c.guard.pins_match(pins),'stage_membership_refusal')
'''
s=s.replace("with (D/'offline-tests.json').open('x')",extra+"\nwith (D/'offline-tests.json').open('x')")
put('offline-tests.py',s)
print('Prepared new offline tests and partial-output validation; no Julia.')
