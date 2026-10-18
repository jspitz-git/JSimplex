import re
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
 return (type(p.get('returncode')) is int and type(sup.get('returncode')) is int and all(type(sup.get(k)) is bool for k in ['hard_timeout','child_kill','guard_term','guard_kill']) and p.get('reason')=='wall_time' and p.get('returncode') in (-15,-9) and p.get('pins_unchanged') is True and sup.get('returncode')==1 and not sup.get('hard_timeout') and not sup.get('child_kill') and not sup.get('guard_term') and not sup.get('guard_kill') and 'cleanup_error' not in sup and finite_nonnegative(elapsed) and elapsed<=limit and not re.search(r'warning|world[ -]age',log,re.I) and 'BEGIN matched policy cost ' in log and not any(x in log for x in ['FATAL COST:','ERROR:','TEST FAILURE:','Traceback','Measured compilation; stop','WARNING:','Warning:','world age']))


def int_metric(x):return type(x) is int and 0<=x<=2**63-1

def basic_counters_ok(c):
 keys=set(rd(D/'probe-inverse.json')['counts'])
 require(set(c)==keys and all(int_metric(x) for x in c.values()),'Exact nonoverflowing probe counters')
 require(c['row_handle_repairs']==c['tuple_writes'],'Tuple/handle writes')
 require(c['split_stage_reads']==32*c['splits'] and c['split_stage_writes']==c['split_final_writes']==33*c['splits'],'Split staging ledger')
 require(c['merge_stage_reads']==c['merge_stage_writes']==c['merge_tuple_moves'],'Merge staging ledger')
 return True

def basic_storage_ok(s,n):
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

def basic_growth_ok(v):
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

# Exact additional split schema, independent of runtime assertions.
def counters_ok(c):
 basic_counters_ok(c)
 require(c['target_calls']==c['reserve_requests']==c['exact_fit_requests']+c['free_splits'],'Reservation partition')
 require(sum(c['target_'+str(i)] for i in (1,2,4,8,16,32))==c['reserve_requests'],'Target histogram')
 require(sum(i*c['target_'+str(2**(i-1))] for i in range(1,7))==c['target_comparisons'],'Target comparison accounting')
 require(sum(c['remainder_'+str(i)] for i in range(1,33))==c['free_splits']==c['split_descriptors'] and c['remainder_32']==0,'Remainder histogram')
 require(c['reserve_requests']<=c['bin_inspections']<=32*c['reserve_requests'],'Bin inspection bounds')
 require(c['append_descriptors']==8*c['slab_appends'] and c['slab_new_payload']==4096*c['slab_appends'],'Slab descriptor/payload accounting')
 require(c['descriptor_copied_payload']==c['grown_copied_bytes'],'Descriptor copy accounting in no-copy schedules')
 require(c['cleared_cells']>=c['relocation_old_capacity_clears']>=c['relocations'],'Relocation clears')
 return True

def storage_ok(s,n):
 extra={'active_slack','bin_heads','column_heads','column_tails','extents'}
 require(extra<=set(s),'Split partition fields required')
 basic_storage_ok({k:v for k,v in s.items() if k not in extra},n)
 require(int_metric(s['active_slack']) and s['live']+s['active_slack']+s['free_capacity']==s['C'] and s['used']<=s['C'],'Whole capacity partition')
 require(len(s['extents'])==s['used'] and all(type(e) is list and len(e)==7 and all(int_metric(x) for x in e) for e in s['extents']),'Extent records')
 arrays={a['name']:a for a in s['arrays']};per_slab={i:[] for i in range(1,s['S']+1)}
 for b,e in enumerate(s['extents'],1):
  slab,start,cap,count,col,prev,nxt=e
  require(slab in per_slab and 1<=cap<=32 and 1<=start<=start+cap-1<=arrays[f'values[{slab}]']['length'] and count<=cap and col<=n and max(prev,nxt)<=s['used'],'Extent bounds')
  require((col==0 and count==0) or (col>0 and count>0),'Extent active/free')
  per_slab[slab].append((start,cap))
 for i,extents in per_slab.items():
  cursor=1
  for start,cap in sorted(extents):require(start==cursor,'No overlap/hole');cursor+=cap
  require(cursor==arrays[f'values[{i}]']['length']+1,'Exact slab partition')
 seen=set()
 def chain(head,kind,owner):
  require(int_metric(head) and head<=s['used'],'Chain head')
  b=head;previous=0
  while b:
   require(b not in seen,'No chain cycle/duplicate');seen.add(b)
   slab,start,cap,count,col,prev,nxt=s['extents'][b-1]
   require(prev==previous and ((col==0 and cap==owner) if kind=='free' else col==owner),'Chain membership/backlink')
   previous=b;b=nxt
  return previous
 require(len(s['bin_heads'])==32 and len(s['column_heads'])==len(s['column_tails'])==n,'Head lengths')
 for c,head in enumerate(s['bin_heads'],1):chain(head,'free',c)
 for c,head in enumerate(s['column_heads'],1):
  tail=s['column_tails'][c-1];require(int_metric(tail) and chain(head,'active',c)==tail,'Column tail')
 require(len(seen)==s['used'],'All descriptors reachable')
 require(sum(e[3] for e in s['extents'])==s['live'] and sum(e[4]!=0 for e in s['extents'])==s['live_blocks'] and sum(e[2] for e in s['extents'] if e[4]==0)==s['free_capacity'],'Extent totals')
 return True

def schedules_ok(schedules):
 specs=[('repeated4',8,0,8,8,9,list(range(9))),('monotone32',32,32,0,0,33,list(range(33))),('fragmented_refill',40,241,1,1,243,[0,1,2,42,82,122,162,202,242])]
 require(type(schedules) is list and len(schedules)==3,'Three fixed schedules')
 for v,(name,n,sets,reservations,claims,inv,steps) in zip(schedules,specs):
  require(set(v)==set('name n sets reservations claims invariant_checks states'.split()),'Structural schema')
  require(v['name']==name and all(type(v[k]) is int and v[k]==z for k,z in zip(['n','sets','reservations','claims','invariant_checks'],[n,sets,reservations,claims,inv])),'Structural fixed budget')
  require(len(v['states'])==len(steps),'Structural state count');previous=None;previous_storage=None
  for state,step in zip(v['states'],steps):
   require(set(state)=={'step','storage','counts'} and type(state['step']) is int and state['step']==step,'Structural checkpoint order')
   s=state['storage'];c=state['counts'];storage_ok(s,n);counters_ok(c)
   require(previous is None or all(previous[k]<=c[k] for k in c),'Structural monotone counters')
   if previous is None:require(all(x==0 for x in c.values()),'Counters reset after setup')
   else:
    require(s['used']-previous_storage['used']==c['append_descriptors']+c['split_descriptors']-previous['append_descriptors']-previous['split_descriptors'],'New descriptor IDs')
    require(s['C']-previous_storage['C']==256*(c['slab_appends']-previous['slab_appends']),'Slab capacity growth')
   if name=='repeated4':
    require(s['C']==32 and s['K']==16 and s['live']==step and s['R']==2*step and s['free_capacity']==32-4*step and s['active_slack']==3*step,'Repeated4 storage')
    require(c['free_splits']==min(step,7) and c['exact_fit_requests']==int(step==8) and c['reserve_requests']==step and c['target_comparisons']==3*step and c['bin_inspections']==sum(29-4*i for i in range(step)),'Repeated4 work')
    require(all(c['remainder_'+str(i)]==int(i in [32-4*j for j in range(1,min(step,7)+1)]) for i in range(1,33)),'Repeated4 remainders')
   elif name=='monotone32':
    require(s['live']==step and s['R']==2*step and s['C']==(0 if step==0 else 256),'Monotone storage')
    target=0 if step==0 else 1<<(step-1).bit_length();reloc=0 if step==0 else target.bit_length()-1
    require(c['relocations']==reloc and c['extent_tuple_moves']==c['relocation_old_capacity_clears']==max(0,target-1),'Monotone relocation work')
   else:
    require(s['live']==(1 if step==1 else 40 if step in (42,122,202) else 0),'Refill live')
    if step==0:require(s['C']==48 and s['used']==16 and s['K']==16,'Fragmented initial partition')
    if step==1:require(s['C']==304 and s['used']==25 and s['K']==36 and c['descriptor_growths']==2 and c['descriptor_new_payload']==28*(24+36) and c['descriptor_copied_payload']==28*(16+24) and c['descriptor_coexist_payload']==28*(24+36),'Fragmented double growth')
   previous=c;previous_storage=s
 return True

def growth_ok(v):
 require('schedules' in v,'Structural schedules required')
 basic_growth_ok({k:z for k,z in v.items() if k!='schedules'});schedules_ok(v['schedules']);return True
