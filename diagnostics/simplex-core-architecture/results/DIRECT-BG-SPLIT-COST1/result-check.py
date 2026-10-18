"""Independent saved-result review. No imports of author modules, no Julia or old scripts."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import csv,hashlib,json,math,os,re,statistics,struct,subprocess,time,tomllib,traceback
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION';E=D.parent/'DIRECT-BG-SPLIT-COST1';run=D/'runs/cost1-300';out=run/'output'
checks={};details={};residual_count=0;storage_count=0;counter_count=0;hashes={}
def rd(p):return json.loads(Path(p).read_text())
def tom(n):return tomllib.loads((out/n).read_text())
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def sha(p):
 p=Path(p)
 if str(p) not in hashes:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  hashes[str(p)]=h.hexdigest()
 return hashes[str(p)]
def bindings(j,key='sha256'):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in j[key].items())
def inv(j):
 paths={Path(p) for p in j['files']}
 for root in map(Path,j['trees']):
  assert root.is_dir() and not root.is_symlink()
  for p in root.rglob('*'):
   assert not p.is_symlink() or p.is_file()
   if p.is_file():paths.add(p)
 return {str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in paths}
@lru_cache(None)
def val(t):
 assert isinstance(t,str) and re.fullmatch('[0-9a-f]{16}',t)
 f=struct.unpack('>d',bytes.fromhex(t))[0];assert math.isfinite(f)
 return f.as_integer_ratio()
def vector(tokens):
 pairs=[val(t) for t in tokens];den=max((d for _,d in pairs),default=1)
 return [n*(den//d) for n,d in pairs],den
# Independent exact dense/sparse integer rows; denominators are powers of two.
def matrix(m,trans):
 n=m['n'];v,den=vector(m['nzval']);rows=[[] for _ in range(n)]
 assert len(m['colptr'])==n+1 and m['colptr'][0]==1 and m['colptr'][-1]==len(v)+1
 for col in range(n):
  inds=m['rowval'][m['colptr'][col]-1:m['colptr'][col+1]-1];assert inds==sorted(set(inds))
  for k in range(m['colptr'][col]-1,m['colptr'][col+1]-1):
   row=m['rowval'][k]-1;assert 0<=row<n
   i,j=(col,row) if trans else (row,col);rows[i].append((j,v[k]))
 return rows,den,max(sum(abs(v) for _,v in row) for row in rows)
def residual(mat,tokens,rhs):
 global residual_count
 rows,dm,mnorm=mat;x,dx=vector(tokens);b,db=vector(rhs);assert len(x)==len(b)==len(rows)
 common=max(dm*dx,db)
 error=max(abs(sum(v*x[j] for j,v in row)*(common//(dm*dx))-b[i]*(common//db)) for i,row in enumerate(rows))
 scale=max(Fraction(1),Fraction(mnorm*max(map(abs,x)),dm*dx),Fraction(max(map(abs,b)),db))
 assert Fraction(error,common)<=Fraction(128*len(rows),2**52)*scale
 residual_count+=1

def stats(xs):
 m=statistics.median(xs)
 return dict(median=m,mad=statistics.median([abs(x-m) for x in xs]),minimum=min(xs),maximum=max(xs),values=xs)
def counter(c,previous=None):
 global counter_count
 assert set(c)==counter_keys and all(type(v) is int and 0<=v<2**63 for v in c.values())
 if previous:assert all(c[k]>=previous[k] for k in c)
 assert c['row_handle_repairs']==c['tuple_writes']
 assert c['split_stage_reads']==32*c['splits'] and c['split_stage_writes']==c['split_final_writes']==33*c['splits']
 assert c['merge_stage_reads']==c['merge_stage_writes']==c['merge_tuple_moves']
 assert c['target_calls']==c['reserve_requests']==c['exact_fit_requests']+c['free_splits']
 assert sum(c['target_'+str(2**i)] for i in range(6))==c['reserve_requests']
 assert sum((i+1)*c['target_'+str(2**i)] for i in range(6))==c['target_comparisons']
 assert sum(c['remainder_'+str(i)] for i in range(1,33))==c['free_splits']==c['split_descriptors'] and c['remainder_32']==0
 assert c['reserve_requests']<=c['bin_inspections']<=32*c['reserve_requests']
 assert c['append_descriptors']==8*c['slab_appends'] and c['slab_new_payload']==4096*c['slab_appends']
 assert c['descriptor_copied_payload']==c['grown_copied_bytes']
 assert c['cleared_cells']>=c['relocation_old_capacity_clears']>=c['relocations']
 counter_count+=1

def storage(s,n):
 global storage_count
 C,Rr,K,S,Dd=(s[k] for k in ['C','R','K','S','D'])
 assert all(type(s[k]) is int and 0<=s[k]<2**63 for k in ['C','R','K','S','D','used','live','live_blocks','free_capacity','active_slack','gap_reserve','core_payload','outer_pointer_payload','struct_bytes','graph_bytes'])
 assert s['live']+s['gap_reserve']==Rr and s['live']+s['active_slack']+s['free_capacity']==C and s['live_blocks']<=s['used']<=min(K,C) and S<=Dd
 assert 32*K<=2**31-1 and max(C,Rr,K,S,Dd)<=2**31-1
 assert s['core_payload']==16*C+4*Rr+28*K+32*n+656 and s['outer_pointer_payload']==8*n+24*Dd
 tops='values row_ids row_backs slab start capacity count column prev next row_order row_position column_order column_position column_head column_tail rows gap_first gap_length bins scratch_value scratch_row scratch_back'.split()
 names=tops+[f'{key}[{i}]' for i in range(1,S+1) for key in ['values','row_ids','row_backs']]+[f'rows[{i}]' for i in range(1,n+1)]
 assert [a['name'] for a in s['arrays']]==names
 arrays={a['name']:a for a in s['arrays']}
 for a in arrays.values():
  assert set(a)==set('name length element_bytes backing_length backing_bytes graph_bytes'.split())
  assert all(type(v) is int and v>=0 for k,v in a.items() if k!='name')
  assert a['element_bytes'] in (4,8) and a['backing_length']>=a['length'] and a['backing_bytes']==a['backing_length']*a['element_bytes'] and a['graph_bytes']>=a['backing_bytes']
 for key in tops:
  length,width=(Dd,8) if key in ['values','row_ids','row_backs'] else ((n,8) if key=='rows' else ((K,4) if key in 'slab start capacity count column prev next'.split() else ((32,4) if key=='bins' else ((33,8 if key=='scratch_value' else 4) if key.startswith('scratch_') else (n,4)))))
  assert (arrays[key]['length'],arrays[key]['element_bytes'])==(length,width)
 assert sum(arrays[f'values[{i}]']['length'] for i in range(1,S+1))==C
 assert sum(arrays[f'rows[{i}]']['length'] for i in range(1,n+1))==Rr
 for i in range(1,n+1):assert arrays[f'rows[{i}]']['element_bytes']==4
 coverage={i:[] for i in range(1,S+1)};ext=s['extents'];assert len(ext)==s['used']
 for e in ext:
  assert len(e)==7 and all(type(v) is int and v>=0 for v in e)
  slab,start,cap,count,col,prev,nxt=e
  assert slab in coverage and 1<=cap<=32 and count<=cap and 0<=col<=n and prev<=len(ext) and nxt<=len(ext)
  assert 1<=start<=start+cap-1<=arrays[f'values[{slab}]']['length']
  assert (col==0 and count==0) or (col>0 and count>0)
  coverage[slab].append((start,cap))
 for i,entries in coverage.items():
  for key,width in [('values',8),('row_ids',4),('row_backs',4)]:assert arrays[f'{key}[{i}]']['length']==arrays[f'values[{i}]']['length'] and arrays[f'{key}[{i}]']['element_bytes']==width
  cursor=1
  for start,cap in sorted(entries):assert start==cursor;cursor+=cap
  assert cursor==arrays[f'values[{i}]']['length']+1
 seen=set()
 def chain(head,free,owner):
  last=0
  while head:
   assert type(head) is int and 1<=head<=len(ext) and head not in seen;seen.add(head)
   e=ext[head-1];assert e[5]==last and ((e[4]==0 and e[2]==owner) if free else e[4]==owner)
   last=head;head=e[6]
  return last
 assert len(s['bin_heads'])==32 and len(s['column_heads'])==len(s['column_tails'])==n
 for i,head in enumerate(s['bin_heads'],1):chain(head,True,i)
 for i,head in enumerate(s['column_heads'],1):assert chain(head,False,i)==s['column_tails'][i-1]
 assert len(seen)==len(ext) and sum(e[3] for e in ext)==s['live'] and sum(e[4]>0 for e in ext)==s['live_blocks'] and sum(e[2] for e in ext if e[4]==0)==s['free_capacity']
 storage_count+=1
try:
 s=rd(run/'sealed.json');lp=rd(run/'launch-pins.json');ad=rd(run/'admission.json');a=rd(run/'audit.json');cfg=rd(run/'config.json');pr=rd(out/'process.json');iv=rd(run/'invocation.json');cur=rd(out/'current.json');sup=iv['supervisor'];post=rd(run/'posthost.json')
 ok(inv(s)==s['inventory'] and inv(lp)==lp['inventory'] and rd(out/'pins.json')==lp,'sealed_launch_inventory_current')
 ok(ad['accepted'] is True and ad['findings']==[] and ad['scope']=='split BG matched cost admission' and ad['phase']=='cost1-300' and ad['pins_sha256']==sha(run/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')} and bindings(ad) and bindings(ad,'evidence_sha256'),'exact_admission_unchanged')
 ok(set(lp['files'])==set(s['files'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']} and lp['trees']==s['trees'],'launch_exact_membership')
 ok(bindings(a) and set(a['sha256'])=={str(p) for p in run.rglob('*') if p.is_file() and p.name!='audit.json'},'audit_exact_current_file_bindings')
 ok(a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='cost1-300' and not a['error'],'saved_diagnostic_acceptance')
 for name in ['preparation-pins.json','review.json','lineage.json']:ok(bindings(rd(D/name)),name+'_bindings')
 ok(bindings(rd(D/'review.json'),'evidence_sha256'),'preparation_supplement_bindings')
 names={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml','growth.toml'}|{f'{p}-{c}.toml' for c in range(1,9) for p in ['started','preflight','probe','cell']}|{f'window-{c}-{w}.toml' for c in range(1,9) for w in range(1,21)}
 ok(len(names)==199 and {p.name for p in out.iterdir()}==names and all(p.is_file() and not p.is_symlink() for p in out.iterdir()),'exact199_outputs')
 ok(cfg==s['config']==rd(D/'commands.json')['cost1-300'] and {p.name for p in (D/'runs').iterdir()}=={'cost1-300'},'one_exact_attempt')
 ok(iv['command']==pr['command']==cur['command']==cfg['command'] and iv['pins_sha256']==pr['pins_sha256']==cur['pins_sha256']==sha(run/'launch-pins.json'),'command_pin_linkage')
 ok(iv['review_sha256']==sha(run/'admission.json') and iv['reservation_sha256']==sha(run/'reservation.json'),'admission_reservation_hashes')
 ok(rd(run/'reservation.json')==dict(one_attempt=True,phase='cost1-300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300),'exact_reservation')
 expected_guard=[iv['python'],'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(out),'--seconds','292','--deadline',str(iv['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']]
 ok(iv['guard_command']==expected_guard and Path(iv['python']).resolve()==Path('/usr/bin/python3').resolve(),'absolute292guard')
 ok(pr['runner']==cur['runner']==sup['guard_identity'] and pr['child']==cur['child'],'process_identity_linkage')
 ok(pr['reason']=='exit0' and pr['returncode']==sup['returncode']==0 and sup['accepted'] is True and pr['pins_unchanged'] is True and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup,'successful_owned_exit')
 ok(0<pr['elapsed_including_launch']<292 and 0<sup['elapsed_seconds']<=iv['elapsed_seconds']<=300,'inclusive_deadlines')
 for role in ['runner','child']:
  ident=pr[role];ok(ident['pid']==ident['pgid']==ident['sid'] and ident['start_ticks']>0 and ident['command'] and ident['boot_id']==s['boot_id'] and ident['pgid'] in post['groups'] and ident['sid'] in post['groups'],role+'_identity')
 for n in ['host.json','prehost.json','posthost.json']:
  h=rd(run/n);ok(not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']) and set(s['groups'])<=set(h['groups']),n+'_closure')
 ok(len(post['groups'])==246,'246_closure_groups_sessions')
 log=(out/'run.log').read_text()+(run/'launcher.log').read_text();ok(not re.search(r'warning|world[ -]age|FATAL COST:|ERROR:|Traceback',log,re.I),'no_warning_error_logs')
 resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];ok(len(resources)==15 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[pr['terminal_memory']]),'resources')
 details['resources']={'inclusive_seconds':iv['elapsed_seconds'],'guard_seconds':pr['elapsed_including_launch'],'minimum_available_kib':min(x['available_kib'] for x in resources),'max_swap_kib':max(x['swap_used_kib'] for x in resources),'peak_child_rss_kib':pr['child_maxrss_kib'],'samples':len(resources)}
 loaded=rd(D/'loaded-paths.json')|{'JSimplex':str(Path(cfg['stage'])/'src/JSimplex.jl')};ok(tom('raw.toml')==dict(fatal='',windows=160,completed=True,threads=1,blas_threads=1,cells=8,phase='cost1-300',loaded=loaded),'raw_exact_loaded_completion')
 counter_keys=set(rd(D/'probe-inverse.json')['counts']);assert len(counter_keys)==83
 fixtures=rd(D/'inputs.json')['fixtures'];cells=[];gc=[];ci=0
 for f in fixtures:
  mats=[(matrix(m,False),matrix(m,True)) for m in f['matrices']]
  for backend in ['native','markowitz']:
   ci+=1;identity=dict(fixture=f['name'],manager='BG',backend=backend,policy='threshold_one' if backend=='native' else 'default')
   ok(tom(f'started-{ci}.toml')==identity and tom(f'cell-{ci}.toml')==identity|{'windows':20},f'cell{ci}_identity')
   pf=tom(f'preflight-{ci}.toml');assert pf['inputs_unchanged'] is True and [pf[k] for k in ['constructions','refactors','explicit_solves']]==[2,4,0] and len(pf['reference'])==len(pf['candidate'])==len(pf['modes'])==3
   for item in pf['reference']+pf['candidate']:
    assert item['kind']==backend and item['policy']==identity['policy']
    if backend=='native':
     assert len(item['control'])==20 and item['control']==item['expected_control'];vv=[Fraction(*val(t)) for t in item['control']];assert vv[3]==1 and vv[7]==0;val(item['strategy'])
    else:assert item['control']==item['expected_control']==[] and item['strategy']==''
   probe=tom(f'probe-{ci}.toml');assert probe['inputs_unchanged'] is True and [probe[k] for k in ['constructions','refactors','updates','ftran','btran','copies']]==[3,6,24,48,24,0]
   assert len(probe['outputs'])==3 and probe['outputs'][0]==probe['outputs'][1]==probe['outputs'][2] and all(len(x)==24 for x in probe['outputs'])
   prev=None;seq=[(0,False)]+[(k,b) for k in range(1,9) for b in ([False,True] if k in [4,8] else [False])];assert len(probe['states'])==len(seq)==11
   for state,(k,refactored) in zip(probe['states'],seq):
    assert (state['step'],state['refactored'],state['equal'])==(k,refactored,True) and state['history_length']==(0 if k==0 or refactored else (k-1)%4+1)
    assert len(state['graphs'])==3 and all(type(x) is int and x>=0 for x in state['graphs']) and state['storage']['graph_bytes']<=state['graphs'][1]
    storage(state['storage'],f['n']);counter(state['counts'],prev);prev=state['counts']
   assert prev==probe['counts']
   for outputs in probe['outputs']:
    for k,step in enumerate(f['steps']):
     residual(mats[k][0],outputs[3*k],step['a']);residual(mats[k][0],outputs[3*k+1],step['dse']);residual(mats[k+1][1],outputs[3*k+2],step['unit'])
   ok(True,f'cell{ci}_preflight_probe_exact_residuals_counters_storage')
   rows=[tom(f'window-{ci}-{w}.toml') for w in range(1,21)]
   for w,row in enumerate(rows,1):
    pair=(w+1)//2;order=(w-1)%2+1;side=('reference' if pair%2 else 'candidate') if order==1 else ('candidate' if pair%2 else 'reference')
    assert (row['pair'],row['order'],row['side'],row['measured'],row['policy'])==(pair,order,side,pair>3,identity['policy']) and row['correct'] is True and row['inputs_unchanged'] is True
    assert set(row)==set('pair order side measured policy correct inputs_unchanged modes seconds bytes events gc_seconds compile_seconds recompile_seconds retained_bytes nested_seconds outputs'.split())
    assert len(row['modes'])==3 and all(x in ['direct','normalized','fallback'] for x in row['modes'])
    assert all(type(row[k]) in (int,float) and math.isfinite(row[k]) and row[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','retained_bytes']) and row['seconds']>0
    assert all(type(row[k]) is int for k in ['bytes','events','retained_bytes'])
    assert len(row['nested_seconds'])==6 and all(x>=0 and math.isfinite(x) for x in row['nested_seconds']) and sum(row['nested_seconds'])<=row['seconds']+1e-9
    assert not row['measured'] or (row['compile_seconds']==row['recompile_seconds']==0)
    assert len(row['outputs'])==24
    for k,step in enumerate(f['steps']):
     residual(mats[k][0],row['outputs'][3*k],step['a']);residual(mats[k][0],row['outputs'][3*k+1],step['dse']);residual(mats[k+1][1],row['outputs'][3*k+2],step['unit'])
    if row['measured'] and row['gc_seconds']>0:gc.append(dict(fixture=f['name'],backend=backend,pair=pair,side=side,seconds=row['seconds'],gc_seconds=row['gc_seconds']))
   for i in range(0,20,2):assert rows[i]['outputs']==rows[i+1]['outputs'] and rows[i]['modes']==rows[i+1]['modes']
   ok(True,f'cell{ci}_all_windows_exact_residuals_bits_inputs_compile')
   pairs=[{r['side']:r for r in rows[2*(p-1):2*p]} for p in range(4,11)];st={}
   for metric in ['seconds','bytes','events','retained_bytes','gc_seconds','compile_seconds','recompile_seconds']:
    xs=[p['reference'][metric] for p in pairs];ys=[p['candidate'][metric] for p in pairs]
    st[metric]={'reference':stats(xs),'candidate':stats(ys)}
    if all(xs):st[metric]['paired_ratio']=stats([y/x for x,y in zip(xs,ys)])
   st['nested_seconds']=[{side:stats([p[side]['nested_seconds'][i] for p in pairs]) for side in ['reference','candidate']} for i in range(6)]
   st['faster_pairs']=sum(p['candidate']['seconds']<p['reference']['seconds'] for p in pairs)
   st['time_median_gate']=st['seconds']['paired_ratio']['median']<=.95
   st['allocation_gate']=all(st[k]['candidate']['median']<=st[k]['reference']['median'] for k in ['bytes','events'])
   st['probe_memory_gate']=all(10*x['graphs'][1]<=11*x['graphs'][0] for x in probe['states'])
   st['memory_gate']=st['probe_memory_gate'] and all(10*p['candidate']['retained_bytes']<=11*p['reference']['retained_bytes'] for p in pairs)
   expected=identity|dict(preflight=pf,probe=probe,modes=[r['modes'] for r in rows],statistics=st)
   ok(a['cells'][ci-1]==expected,f'cell{ci}_independent_complete_audit_reconstruction')
   cells.append(identity|dict(statistics=st,first_gate=all(st[k] for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']) and st['faster_pairs']>=3))
 ok(residual_count==4416 and a['counts']==dict(cells=8,windows=160,exact_residuals=4416),'all4416_exact_residuals')
 ok([c['first_gate'] for c in cells]==[False]*6+[True]*2,'fixed_design_performance_rejected')
 ok(gc==rd(E/'gc-windows.json') and len(gc)==5,'all_five_measured_GC_retained')
 details['cells']=cells;details['gc_windows']=gc
 g=tom('growth.toml');assert g['complete'] is True and [g[k] for k in ['n','insertions','factorizations','solves']]==[64,64,0,0] and len(g['states'])==64
 cap=0;growths=0;copied=0;prev=None
 for i,state in enumerate(g['states'],1):
  if i>cap:copied+=4*(i-1);cap=i+min(8,max(1,cap//8));growths+=1
  assert state['insertions']==i and state['row_capacity']==cap;counter(state['counts'],prev);prev=state['counts']
  assert prev['row_growths']==growths and prev['row_copied_bytes']==copied
 assert g['counts']==prev;storage(g['storage'],64);assert g['storage']['live']==64 and g['storage']['R']==cap
 ok(True,'row_growth_all64')
 specs=[('repeated4',8,0,8,8,9,list(range(9))),('monotone32',32,32,0,0,33,list(range(33))),('fragmented_refill',40,241,1,1,243,[0,1,2,42,82,122,162,202,242])];assert len(g['schedules'])==3
 for z,(name,n,sets,reserve,claims,invariants,steps) in zip(g['schedules'],specs):
  assert [z[k] for k in ['name','n','sets','reservations','claims','invariant_checks']]==[name,n,sets,reserve,claims,invariants] and len(z['states'])==len(steps)
  prev=None;prevstore=None
  for state,step in zip(z['states'],steps):
   assert state['step']==step;s0=state['storage'];c=state['counts'];storage(s0,n);counter(c,prev)
   if prev is None:assert not any(c.values())
   else:assert s0['used']-prevstore['used']==c['append_descriptors']+c['split_descriptors']-prev['append_descriptors']-prev['split_descriptors'] and s0['C']-prevstore['C']==256*(c['slab_appends']-prev['slab_appends'])
   if name=='repeated4':
    assert (s0['C'],s0['K'],s0['live'],s0['R'],s0['free_capacity'],s0['active_slack'])==(32,16,step,2*step,32-4*step,3*step)
    assert c['free_splits']==min(step,7) and c['exact_fit_requests']==int(step==8) and c['reserve_requests']==step and c['target_comparisons']==3*step and c['bin_inspections']==sum(29-4*i for i in range(step))
    assert all(c['remainder_'+str(i)]==int(i in [32-4*j for j in range(1,min(step,7)+1)]) for i in range(1,33))
   elif name=='monotone32':
    target=0 if step==0 else 2**((step-1).bit_length());assert s0['live']==step and s0['R']==2*step and s0['C']==(0 if step==0 else 256)
    assert c['relocations']==(0 if step==0 else target.bit_length()-1) and c['extent_tuple_moves']==c['relocation_old_capacity_clears']==max(0,target-1)
   else:
    assert s0['live']==(1 if step==1 else 40 if step in [42,122,202] else 0)
    if step==0:assert (s0['C'],s0['used'],s0['K'])==(48,16,16)
    if step==1:assert (s0['C'],s0['used'],s0['K'],c['descriptor_growths'],c['descriptor_new_payload'],c['descriptor_copied_payload'],c['descriptor_coexist_payload'])==(304,25,36,2,1680,1120,1680)
   prev=c;prevstore=s0
  ok(True,'structural_'+name+'_all_saved_states')
 details['structural_final']={z['name']:dict(storage={k:z['states'][-1]['storage'][k] for k in ['C','R','K','used','live','free_capacity','active_slack']},counts=z['states'][-1]['counts']) for z in g['schedules']}
 ok(storage_count==140 and counter_count==203,'complete_saved_storage_counter_coverage')
 # Saved CSV and Markdown values exactly match independently recomputed rounded statistics.
 csvrows=list(csv.DictReader((E/'summary.csv').open()));report=(E/'REPORT.md').read_text();assert len(csvrows)==8
 for row,c in zip(csvrows,cells):
  st=c['statistics'];q=st['seconds']['paired_ratio']
  expect={'Fixture':c['fixture'],'Backend':c['backend'],'Paired time ratio':f"{q['median']:.6f}",'Range':f"{q['minimum']:.6f}–{q['maximum']:.6f}",'MAD':f"{q['mad']:.6f}",'Bytes ratio':f"{st['bytes']['paired_ratio']['median']:.6f}",'Events ratio':f"{st['events']['paired_ratio']['median']:.6f}",'Final graph ratio':f"{st['retained_bytes']['paired_ratio']['median']:.6f}",'Faster/7':str(st['faster_pairs']),'All first gates':str(c['first_gate'])}
  assert row==expect and '|'+ '|'.join(expect.values())+'|' in report
 ok(True,'report_CSV_statistics_exact')
 ok(rd(E/'postcheck.json')['all_passed'] is True and bindings(rd(E/'postcheck.json')),'supplement_postcheck_bindings')
 # Current host independent of stored posthost: all group AND session IDs plus visible Julia.
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(post['groups']);procs=[];matches=[];unreadable=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   obj=dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot,comm=comm,exe=exe);procs.append(obj)
   if obj['pgid'] in groups or obj['sid'] in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(obj)
  except (FileNotFoundError,ProcessLookupError):pass
 save(E/'result-check-host.json',dict(time=time.time(),boot_id=boot,groups=sorted(groups),processes=procs,matches=matches,unreadable_exe_pids=unreadable))
 ok(boot==s['boot_id'] and not matches and len(groups)==246,'fresh246_groups_sessions_noJulia')
 def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
 ok(git('rev-parse','HEAD')==s['head'] and git('rev-parse','master')==s['master'] and not git('diff','--name-only') and not git('diff','--cached','--name-only'),'fresh_refs_tracked_index')
 for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
  b=rd(D/'baseline.json')[label];ok(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b) and all(sha(root/n)==v for n,v in b.items()),'unchanged_baseline_'+label)
 ok({k:os.environ.get(k) for k in rd(D/'environment.json')}==rd(D/'environment.json'),'environment_unchanged')
 details.update(exact_residuals=residual_count,storage_records=storage_count,counter_records=counter_count,unique_hashed_files=len(hashes),first_process_viable=False)
 save(E/'result-check.json',dict(accepted=True,checks=checks,check_count=len(checks),details=details,scope='Independent saved-result integrity/numerical/work/memory review; fixed design performance rejected. No Julia or author code execution.'))
 print('PASS',len(checks),'checks;',residual_count,'exact residuals;',storage_count,'storage;',counter_count,'counter records; performance rejected')
except Exception:
 save(E/'result-check.json',dict(accepted=False,checks=checks,check_count=len(checks),details=details,error=traceback.format_exc()))
 raise
