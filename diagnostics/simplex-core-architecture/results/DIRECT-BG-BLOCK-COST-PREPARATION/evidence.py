"""New saved-data exact oracles. No launch or Julia invocation."""
from control import *
from analysis import matrix,window_ok,summarize,qualify,number,finite_nonnegative
import tomllib
BASE={'pins.json','current.json','process.json','resources.jsonl','run.log'}
def expected_names():
 return BASE|{'raw.toml','growth.toml'}|{f'{p}-{c}.toml' for c in range(1,9) for p in ['started','preflight','probe','cell']}|{f'window-{c}-{w}.toml' for c in range(1,9) for w in range(1,21)}
def preflight_ok(v,backend):
 require(set(v)==set('reference candidate modes inputs_unchanged constructions refactors explicit_solves'.split()),'Preflight schema')
 require(v['inputs_unchanged'] is True and [v[k] for k in ['constructions','refactors','explicit_solves']]==[2,4,0] and all(type(v[k]) is int for k in ['constructions','refactors','explicit_solves']),'Preflight work/inputs')
 require(len(v['reference'])==len(v['candidate'])==len(v['modes'])==3,'Preflight shape')
 require(all(m in ['normalized','direct','fallback'] for m in v['modes']),'Preflight mode')
 for item in v['reference']+v['candidate']:
  require(set(item)==set('kind policy control expected_control strategy'.split()),'Policy schema')
  require(item['kind']==backend and item['policy']==('threshold_one' if backend=='native' else 'default'),'Policy identity')
  if backend=='native':
   require(len(item['control'])==len(item['expected_control'])==20 and item['control']==item['expected_control'],'Default control equality')
   values=[number(s) for s in item['control']];require(values[3]==1 and values[7]==0,'Native pivot/IR controls');number(item['strategy'])
  else:require(item['control']==item['expected_control']==[] and item['strategy']=='','Markowitz fields')
 return True

def output_checks(out,cfg,partial=False):
 names={p.name for p in out.iterdir()};require(BASE<=names<=expected_names(),'Output membership')
 require(all(p.is_file() and not p.is_symlink() for p in out.iterdir()),'Output file type')
 if not partial:require(names==expected_names(),'Incomplete output')
 fixtures=rd(D/'inputs.json')['fixtures'];results=[];visited=set();cell=0;finished=0;windows=0;probes=0
 if 'growth.toml' in names:
  growth_ok(tomllib.loads((out/'growth.toml').read_text()));visited.add('growth.toml')
 else:require(not any(n.startswith('started-') for n in names),'Cells before growth probe')
 for f in fixtures:
  matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']]
  for manager in ['BG']:
   for backend in ['native','markowitz']:
    cell+=1;start=f'started-{cell}.toml';pre=f'preflight-{cell}.toml';end=f'cell-{cell}.toml';probe=f'probe-{cell}.toml'
    if start not in names:continue
    require(cell==finished+1,'Nonsequential cell prefix');visited.add(start)
    identity=dict(fixture=f['name'],manager=manager,backend=backend,policy='threshold_one' if backend=='native' else 'default')
    require(tomllib.loads((out/start).read_text())==identity,'Cell identity')
    if pre not in names:continue
    observation=tomllib.loads((out/pre).read_text());preflight_ok(observation,backend);visited.add(pre);rows=[]
    if probe not in names:continue
    pr=tomllib.loads((out/probe).read_text());probe_ok(pr,f,matrices);visited.add(probe);probes+=1
    for w in range(1,21):
     n=f'window-{cell}-{w}.toml'
     if n not in names:break
     row=tomllib.loads((out/n).read_text());require(row['policy']==identity['policy'],'Window policy')
     window_ok(row,f,cfg['process'],(w+1)//2,1+(w-1)%2,matrices);rows.append(row);visited.add(n);windows+=1
    # Every completed pair is checked even before cell completion/timeout.
    for pair in range(1,len(rows)//2+1):
     a,b=rows[2*(pair-1):2*pair];require(a['outputs']==b['outputs'] and a['modes']==b['modes'],'Direct bitwise paired outputs/modes')
    if end in names:
     require(len(rows)==20 and tomllib.loads((out/end).read_text())==dict(identity,windows=20),'Cell completion')
     visited.add(end);finished+=1
     st=summarize(rows);st['probe_memory_gate']=all(10*s['graphs'][1]<=11*s['graphs'][0] for s in pr['states']);st['memory_gate'] &= st['probe_memory_gate']
     results.append(dict(identity,preflight=observation,probe=pr,modes=[r['modes'] for r in rows],statistics=st))
 require(visited==names-BASE-{'raw.toml'},'Non-prefix/unvalidated output')
 if partial:
  require('raw.toml' not in names and (finished<8 or windows<160),'Completed/malformed raw is not timeout qualification')
 else:
  raw=tomllib.loads((out/'raw.toml').read_text())
  require(raw==dict(phase=cfg['phase'],loaded=loaded_for(cfg),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1),'Raw schema/count/path')
  require(raw['completed'] is True and type(raw['cells']) is int and type(raw['windows']) is int and type(raw['threads']) is int and type(raw['blas_threads']) is int,'Raw count types')
  require(finished==8 and windows==160,'All windows')
 return results,dict(cells=finished,windows=windows,exact_residuals=24*windows+72*probes)

def timeout_ok(p,sup,log,elapsed,limit):
 return (type(p.get('returncode')) is int and type(sup.get('returncode')) is int and all(type(sup.get(k)) is bool for k in ['hard_timeout','child_kill','guard_term','guard_kill']) and p.get('reason')=='wall_time' and p.get('returncode') in (-15,-9) and p.get('pins_unchanged') is True and sup.get('returncode')==1 and not sup.get('hard_timeout') and not sup.get('child_kill') and not sup.get('guard_term') and not sup.get('guard_kill') and 'cleanup_error' not in sup and finite_nonnegative(elapsed) and elapsed<=limit and 'BEGIN matched policy cost ' in log and not any(x in log for x in ['FATAL COST:','ERROR:','TEST FAILURE:','Traceback','Measured compilation; stop','WARNING:','Warning:','world age']))


def int_metric(x):return type(x) is int and 0<=x<=2**63-1

def counters_ok(c):
 keys=set(rd(D/'probe-inverse.json')['counts'])
 require(set(c)==keys and all(int_metric(x) for x in c.values()),'Exact nonoverflowing probe counters')
 require(c['row_handle_repairs']==c['tuple_writes'],'Tuple/handle writes')
 require(c['split_stage_reads']==32*c['splits'] and c['split_stage_writes']==c['split_final_writes']==33*c['splits'],'Split staging ledger')
 require(c['merge_stage_reads']==c['merge_stage_writes']==c['merge_tuple_moves'],'Merge staging ledger')
 return True

def storage_ok(s,n):
 keys='C R K S D used live live_blocks free_capacity gap_reserve core_payload outer_pointer_payload struct_bytes graph_bytes arrays'.split()
 require(set(s)==set(keys) and all(int_metric(s[k]) for k in keys if k!='arrays'),'Storage schema/types/overflow')
 C,R,K,S,Dd=(s[k] for k in ['C','R','K','S','D'])
 require(s['live']<=C and s['live']+s['gap_reserve']==R and s['live_blocks']<=s['used']<=K and S<=Dd,'Storage capacities')
 require(s['live']+s['free_capacity']<=C and K*32<=2**31-1 and all(x<=2**31-1 for x in [C,R,K,S,Dd]),'Handle/capacity bounds')
 require(s['core_payload']==16*C+4*R+28*K+32*n+656 and s['outer_pointer_payload']==8*n+24*Dd,'Complete payload formula')
 top='values row_ids row_backs slab start capacity count column prev next row_order row_position column_order column_position column_head column_tail rows gap_first gap_length bins scratch_value scratch_row scratch_back'.split()
 expected=top+[f'{key}[{i}]' for i in range(1,S+1) for key in ['values','row_ids','row_backs']]+[f'rows[{i}]' for i in range(1,n+1)]
 require([a['name'] for a in s['arrays']]==expected,'All Vector objects enumerated')
 arrays={a['name']:a for a in s['arrays']}
 for a in s['arrays']:
  require(set(a)==set('name length element_bytes backing_length backing_bytes graph_bytes'.split()),'Array schema')
  require(all(int_metric(a[k]) for k in a if k!='name'),'Array metadata overflow/type')
  require(a['element_bytes'] in (4,8) and a['backing_length']>=a['length'] and a['backing_bytes']==a['backing_length']*a['element_bytes'] and a['graph_bytes']>=a['backing_bytes'],'Backing Memory capacity')
 for key in ['values','row_ids','row_backs']:require(arrays[key]['length']==Dd and arrays[key]['element_bytes']==8,'Directory pointers')
 require(arrays['rows']['length']==n and arrays['rows']['element_bytes']==8,'Row directory')
 for key in ['slab','start','capacity','count','column','prev','next']:require(arrays[key]['length']==K and arrays[key]['element_bytes']==4,'Descriptor arrays')
 for key in ['row_order','row_position','column_order','column_position','column_head','column_tail','gap_first','gap_length']:require(arrays[key]['length']==n and arrays[key]['element_bytes']==4,'Map arrays')
 require(arrays['bins']['length']==32 and arrays['bins']['element_bytes']==4,'Bins')
 for key,width in [('scratch_value',8),('scratch_row',4),('scratch_back',4)]:require(arrays[key]['length']==33 and arrays[key]['element_bytes']==width,'Scratch')
 for i in range(1,S+1):
  require(len({arrays[f'{key}[{i}]']['length'] for key in ['values','row_ids','row_backs']})==1,'Slab lengths')
  for key,width in [('values',8),('row_ids',4),('row_backs',4)]:require(arrays[f'{key}[{i}]']['element_bytes']==width,'Slab width')
 require(sum(arrays[f'values[{i}]']['length'] for i in range(1,S+1))==C and sum(arrays[f'rows[{i}]']['length'] for i in range(1,n+1))==R,'C/R accounting')
 require(all(arrays[f'rows[{i}]']['element_bytes']==4 for i in range(1,n+1)),'Row widths')
 return True

def probe_ok(v,f,matrices):
 from analysis import residual
 require(set(v)==set('states outputs inputs_unchanged constructions refactors updates ftran btran copies counts'.split()),'Probe schema')
 require(v['inputs_unchanged'] is True and [v[k] for k in ['constructions','refactors','updates','ftran','btran','copies']]==[3,6,24,48,24,0],'Probe API budget')
 require(all(type(v[k]) is int for k in ['constructions','refactors','updates','ftran','btran','copies']),'Probe API types')
 expected=[(0,False)]+[(k,r) for k in range(1,9) for r in ([False,True] if k in (4,8) else [False])]
 require(len(v['states'])==11,'Eleven checkpoints');previous=None
 for s,(k,r) in zip(v['states'],expected):
  require(set(s)==set('step refactored equal graphs storage history_length counts'.split()),'Checkpoint schema')
  require(type(s['step']) is int and s['step']==k and s['refactored'] is r and s['equal'] is True,'Checkpoint order/equality')
  require(len(s['graphs'])==3 and all(int_metric(x) for x in s['graphs']) and int_metric(s['history_length']),'Graphs')
  storage_ok(s['storage'],f['n']);counters_ok(s['counts'])
  require(s['storage']['graph_bytes']<=s['graphs'][1],'Factor includes upper graph')
  require(previous is None or all(previous[key]<=s['counts'][key] for key in previous),'Monotone counters');previous=s['counts']
  require(s['history_length']==(0 if r or k==0 else (k-1)%4+1),'History')
 require(previous==v['counts'],'Final counts')
 require(len(v['outputs'])==3 and v['outputs'][0]==v['outputs'][1]==v['outputs'][2] and all(len(x)==24 for x in v['outputs']),'Probe bitwise outputs')
 for side in v['outputs']:
  for k,s in enumerate(f['steps']):
   require(residual(matrices[k][0],side[3*k],s['a']) and residual(matrices[k][0],side[3*k+1],s['dse']) and residual(matrices[k+1][1],side[3*k+2],s['unit']),'Probe exact residual')
 return True

def growth_ok(v):
 require(set(v)==set('complete n insertions factorizations solves states storage counts'.split()),'Growth schema')
 require(v['complete'] is True and [v[k] for k in ['n','insertions','factorizations','solves']]==[64,64,0,0] and all(type(v[k]) is int for k in ['n','insertions','factorizations','solves']),'Growth budget')
 require(len(v['states'])==64,'Growth prefix')
 cap=0;growths=0;copied=0;previous=None
 for i,s in enumerate(v['states'],1):
  if i>cap:copied+=4*(i-1);cap=i+min(8,max(1,cap//8));growths+=1
  require(set(s)=={'insertions','row_capacity','counts'} and type(s['insertions']) is int and type(s['row_capacity']) is int and s['insertions']==i and s['row_capacity']==cap,'Fixed repeated row reserve rule')
  counters_ok(s['counts']);require(s['counts']['row_growths']==growths and s['counts']['row_copied_bytes']==copied,'Repeated row copy accounting')
  require(previous is None or all(previous[k]<=s['counts'][k] for k in previous),'Growth counters monotone');previous=s['counts']
 require(v['counts']==previous,'Growth final counters');storage_ok(v['storage'],64)
 require(v['storage']['live']==64 and v['storage']['R']==cap,'Growth final storage')
 return True
