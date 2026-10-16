"""New saved-data exact oracles. No launch or Julia invocation."""
from control_reviewed import *
from analysis_reviewed import matrix,window_ok,summarize,qualify,number,finite_nonnegative
import tomllib
BASE={'pins.json','current.json','process.json','resources.jsonl','run.log'}
def expected_names():
 return BASE|{'raw.toml'}|{f'{p}-{c}.toml' for c in range(1,9) for p in ['started','preflight','probe','cell']}|{f'window-{c}-{w}.toml' for c in range(1,9) for w in range(1,21)}
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
 fixtures=rd(D/'inputs.json')['fixtures'];results=[];visited=set();cell=0;finished=0;windows=0
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
    pr=tomllib.loads((out/probe).read_text());probe_ok(pr,f,matrices);visited.add(probe)
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
 return results,dict(cells=finished,windows=windows,exact_residuals=24*windows)

def timeout_ok(p,sup,log,elapsed,limit):
 return (type(p.get('returncode')) is int and type(sup.get('returncode')) is int and all(type(sup.get(k)) is bool for k in ['hard_timeout','child_kill','guard_term','guard_kill']) and p.get('reason')=='wall_time' and p.get('returncode') in (-15,-9) and p.get('pins_unchanged') is True and sup.get('returncode')==1 and not sup.get('hard_timeout') and not sup.get('child_kill') and not sup.get('guard_term') and not sup.get('guard_kill') and 'cleanup_error' not in sup and finite_nonnegative(elapsed) and elapsed<=limit and 'BEGIN matched policy cost ' in log and not any(x in log for x in ['FATAL COST:','ERROR:','TEST FAILURE:','Traceback','Measured compilation; stop']))

def probe_ok(v,f,matrices):
 from analysis_reviewed import residual
 require(set(v)==set('states outputs inputs_unchanged constructions refactors updates ftran btran copies counts'.split()),'Probe schema')
 require(v['inputs_unchanged'] is True and [v[k] for k in ['constructions','refactors','updates','ftran','btran','copies']]==[3,6,24,48,24,0],'Probe API budget')
 require(all(type(v[k]) is int for k in ['constructions','refactors','updates','ftran','btran','copies']),'Probe API types')
 expected=[(0,False)]+[(k,r) for k in range(1,9) for r in ([False,True] if k in (4,8) else [False])]
 require(len(v['states'])==11 and len(v['counts'])==6,'Probe checkpoints')
 previous=[0]*6
 for s,(k,r) in zip(v['states'],expected):
  require(set(s)==set('step refactored equal graphs capacity live arena_graph_bytes array_graph_bytes requested_payload_bytes copy_arena_payload_bound history_length counts'.split()),'Checkpoint schema')
  require(type(s['step']) is int and s['step']==k and s['refactored'] is r and s['equal'] is True,'Checkpoint order/equality')
  ints=[s[n] for n in ['capacity','live','arena_graph_bytes','requested_payload_bytes','copy_arena_payload_bound','history_length']]+s['graphs']+s['array_graph_bytes']+s['counts']
  require(all(type(x) is int and x>=0 for x in ints),'Checkpoint metrics')
  require(len(s['graphs'])==3 and len(s['array_graph_bytes'])==15 and len(s['counts'])==6 and s['live']<=s['capacity'],'Checkpoint dimensions')
  require(s['requested_payload_bytes']==56*s['capacity']+64*f['n'] and s['copy_arena_payload_bound']==2*s['requested_payload_bytes'],'Payload algebra')
  require(all(a<=b for a,b in zip(previous,s['counts'])),'Probe cumulative counters');previous=s['counts']
  require(s['history_length']==(0 if r or k==0 else (k-1)%4+1),'Probe update history')
 require(previous==v['counts'] and previous[0]==previous[4] and previous[1]<=previous[0] and previous[4]>0,'Reserve/link accounting')
 require(len(v['outputs'])==3 and v['outputs'][0]==v['outputs'][1]==v['outputs'][2] and all(len(x)==24 for x in v['outputs']),'Probe outputs equality/count')
 for side in v['outputs']:
  for k,s in enumerate(f['steps']):
   require(residual(matrices[k][0],side[3*k],s['a']) and residual(matrices[k][0],side[3*k+1],s['dse']) and residual(matrices[k+1][1],side[3*k+2],s['unit']),'Probe exact residual')
 return True
