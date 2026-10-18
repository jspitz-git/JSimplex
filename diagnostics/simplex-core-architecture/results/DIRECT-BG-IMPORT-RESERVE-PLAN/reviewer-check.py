from pathlib import Path
import hashlib,json,tomllib,statistics,math
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-IMPORT-RESERVE-PLAN'
bindings={}
def read(p):
 p=Path(p); b=p.read_bytes(); bindings[str(p)]=hashlib.sha256(b).hexdigest(); return b
def js(p):return json.loads(read(p))
def tom(p):return tomllib.loads(read(p).decode())
a=js(E/'author-check.json'); checks={}
for p,h in a['readtime_sha256'].items(): checks['binding:'+p]=hashlib.sha256(read(p)).hexdigest()==h
checks['146_bindings']=len(a['readtime_sha256'])==146
run=E.parent/'DIRECT-BG-SPLIT-COST-PREPARATION/runs/cost1-300'; out=run/'output'; old=js(run/'result-review.json'); seal=js(run/'sealed.json')
for p in a['readtime_sha256']:
 if p in seal['inventory']:
  checks['seal:'+p]=bindings[p]==seal['inventory'][p]['sha256'] and str(Path(p).resolve())==seal['inventory'][p]['resolved']
checks['old_accepted']=old['accepted'] and old['findings']==[]
records=[]
for c in range(1,9):
 data=tom(out/f'probe-{c}.toml'); ac=a['cells'][c-1]; imports=[]
 for state in data['states']:
  if state['step'] not in (0,4,8) or (state['step'] and not state['refactored']):continue
  u=state['storage']; tails=[b for b in u['column_tails'] if b]; counts=[u['extents'][b-1][3] for b in tails]
  delta=counts.count(1)+2*counts.count(2)+counts.count(3)
  ai=next(i for i in ac['imports'] if i['step']==state['step'])
  checks[f'import:{c}:{state["step"]}']=delta==ai['added_slots'] and 16*delta==ai['added_payload'] and delta<=2*len(u['column_tails']) and u['C']+delta<=32*u['K'] and math.isclose((state['graphs'][1]+16*delta)/state['graphs'][0],ai['payload_only_graph_projection'])
  imports.append({'step':state['step'],'delta':delta,'payload':16*delta})
 rows={}
 for p in out.glob(f'window-{c}-*.toml'):
  w=tom(p)
  if w['measured']:
   checks['sealed_result:'+p.name]=bindings[str(p)]==old['sha256'][str(p)]
   rows[(w['pair'],w['side'])]=w
 checks[f'pairs:{c}']=set(rows)=={(i,s) for i in range(4,11) for s in ('candidate','reference')}
 for field in ('bytes','events'):
  x=statistics.median(rows[i,'candidate'][field]-rows[i,'reference'][field] for i in range(4,11));checks[f'{field}:{c}']=x==ac['median_paired_delta_'+field]
 phase=[statistics.median((rows[i,'candidate']['nested_seconds'][j]-rows[i,'reference']['nested_seconds'][j])*1e6 for i in range(4,11)) for j in range(6)]
 checks[f'phase:{c}']=all(math.isclose(x,y,abs_tol=1e-9) for x,y in zip(phase,ac['median_paired_phase_delta_microseconds']))
 checks[f'counters:{c}']=data['counts']==ac['counts'] and {k:data['states'][1]['counts'][k]-data['states'][0]['counts'][k] for k in data['counts']}==ac['first_update_counter_delta']
 records.append({'cell':c,'imports':imports,'update_delta_us':phase[3]})
# Independent direct layout arithmetic, including stable traversal of reversed input columns.
for lengths in ([0,1,2,3,4,31,32,33,34,35,36,64],list(range(257))):
 cursor=0; live=0; blocks=0; slack=0
 for length in reversed(lengths):
  left=length
  while left:
   count=min(32,left); cap={1:2,2:4,3:4}.get(count,count)
   cursor+=cap;live+=count;blocks+=1;slack+=cap-count;left-=count
 checks['geometry:'+str(len(lengths))]=cursor==live+slack and cursor<=32*blocks and slack<=2*len(lengths)
for p in ['diagnostics/direct-lu-policy-adapters/reproduce/direct-factor.jl','src/triangular_indices.jl','src/triangular_factorization.jl','src/bartels_golub_rows.jl','diagnostics/direct-bg-split-upper/reproduce/split-upper-tests.jl','diagnostics/direct-bg-split-upper/reproduce/split-bg-tests.jl'] :read(R/p)
read(Path(__file__).resolve())
result={'accepted':all(checks.values()),'checks':checks,'readtime_sha256':bindings,'records':records,'limits':'Offline source and stored-data verification only; no old checker imported or executed; no Julia, numerical execution, allocation measurement or new candidate.'}
with (E/'reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'accepted':result['accepted'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v]}))
