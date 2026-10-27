from pathlib import Path
import sys,json,re,tomllib,statistics,math
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27/comparison-3');sys.path.insert(0,str(D));import common_ready as c
p=c.read('output/process.json');s=c.read('supervisor.json');done=c.read('completed.json');contract=c.read('contract-ready.json');log=(D/'output/run.log').read_text()
c.need(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and s['accepted'] is True and done['accepted'] is True,'exit/guards')
c.need(done['elapsed_shared_seconds']<=600,'600s')
m=re.search(r'^Virtual free pivot whole-function comparison\s*\|\s*(\d+)\s+(\d+)\s+',log,re.M);c.need(m and int(m[1])==int(m[2]) and int(m[1])>1000,'ordinary fullpass summary')
c.need('VIRTUAL_FREE_PIVOT_COMPARISON_COMPLETE cells=3328' in log,'completion')
data=tomllib.loads((D/'output/results.toml').read_text())
contexts=[(f'BF{bits}_RoundingMode{{:{mode}}}()','BigFloat') for bits in [64,128,256] for mode in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
expected=[]
for label,t in contexts:
 for n in [32,128]:
  for m in [4,16]:
   for scope in ['audit','virtual','virtual_transposed','pivot']:
    for density in ['sparse','dense']:
     for pattern in (['positive','negative','mixed','zero'] if t=='BigFloat' else ['mixed']):
      expected.append((label,t,n,scope,density,pattern,m,'C' if scope=='pivot' else 'A'))
 for n in [32,128]:
  for scope in ['enter_dantzig','enter_devex','partial_hit','partial_rebuild','summary']:
   for density in ['sparse','dense']:
    for pattern in (['positive','negative','mixed','bound'] if t=='BigFloat' else ['mixed']):expected.append((label,t,n,scope,density,pattern,4,'B'))
c.need(len(data['cells'])==len(expected)==contract['cases']==3328,'exact matrix length')
fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']
def validcost(v):return all(type(v[k]) in [int,float] and math.isfinite(v[k]) and v[k]>=0 for k in fields)
rows=[];gc=0
for cell,key in zip(data['cells'],expected):
 names=['context','type','n','scope','density','pattern','basis_rows','variant'];c.need(tuple(cell[k] for k in names)==key,'exact ordered matrix')
 c.need(cell['id']=='/'.join(map(str,[key[0],key[2],key[6],*key[3:6]])),'cell id')
 raw=cell['windows'];c.need(len(raw)==18,'nine pairs');ratios=[];arm=cell['variant']
 for k in range(1,10):
  pair=raw[2*k-2:2*k];c.need([w['arm'] for w in pair]==(['original',arm] if k%2 else [arm,'original']),'alternation')
  c.need(all(type(w['pair']) is int and w['pair']==k and type(w['sink']) is int and validcost(w) and w['compile_seconds']==w['recompile_seconds']==0 for w in pair),'typed costs/compilezero')
  c.need(pair[0]['sink']==pair[1]['sink'],'typed sink equality')
  if cell['scope']=='audit':c.need(all(w['sink']==1 for w in pair),'complete accurate audit path')
  if cell['scope'] in ['virtual','virtual_transposed']:c.need(all(w['sink']==4 for w in pair),'finite reliable exact dyadic quality path')
  if cell['scope']=='pivot':c.need(all(w['sink']==(3 if cell['pattern']=='zero' else 1) for w in pair),'complete pivot path')
  if cell['scope'].startswith('enter_') or cell['scope'].startswith('partial_'):c.need(all(w['sink']>0 for w in pair),'nonempty entering path')
  by={w['arm']:w for w in pair};c.need(by['original']['seconds']>0,'positive time');ratios.append(by[arm]['seconds']/by['original']['seconds']);gc+=sum(w['gc_seconds']>0 for w in pair)
 route=cell['scope'] if cell['scope'] in ['partial_hit','partial_rebuild'] and cell['n']+cell['basis_rows']>128 else ('full_fallback' if cell['scope'] in ['partial_hit','partial_rebuild'] else 'none')
 c.need(cell['pool_route']==route,'actual partial scope declaration')
 r={k:cell[k] for k in names};med=statistics.median(ratios);r.update(paired_ratio=med,ratio_MAD=statistics.median(abs(v-med) for v in ratios),ratio_min=min(ratios),ratio_max=max(ratios))
 for source,dest in [('original','original'),(arm,'candidate')]:r[dest]={k:statistics.median(w[k] for w in raw if w['arm']==source) for k in ['seconds','bytes','events']}
 for field in ['bytes','events']:r['all_pairs_lower_'+field]=all(next(w[field] for w in raw if w['pair']==k and w['arm']==arm)<next(w[field] for w in raw if w['pair']==k and w['arm']=='original') for k in range(1,10))
 rows.append(r)
prep=data['preparation'];c.need(len(prep)==3328+38 and sum('phase' not in v for v in prep)==3328,'all prep cells')
c.need([(v['context'],v['phase']) for v in prep if 'phase' in v]==[(label,phase) for label,t in contexts for phase in ['correctness_and_snapshots','context_GC']],'context preparation order')
c.need([v['cell'] for v in prep if 'phase' not in v]==[v['id'] for v in data['cells']],'prep cell linkage')
for v in prep:
 if 'phase' in v:c.need(validcost(v),'context prep')
 else:
  c.need(validcost(v['fixture']) and validcost(v['validation_and_snapshots']),'fixture/snapshot prep')
  for k,count in [('cold',2),('warm',6),('resets',18)]:c.need(len(v[k])==count and all(validcost(x) for x in v[k]),'prep '+k)
  c.need(len(v['route_checks'])==18 and all(validcost(x['before']) and validcost(x['after']) for x in v['route_checks']),'all route validation prep costs')
  c.need(all(validcost(x['preparation_reset']) for k in ['cold','warm'] for x in v[k]),'cold/warm reset prep costs')
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()];c.need(resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources),'resource samples')
from fractions import Fraction as F
oracles=data['native_oracles'];c.need(len(oracles)==12,'six native pairs')
for i,o in enumerate(oracles):
 n=o['rows'];c.need(n==4 and len(o['matrix'])==16 and all(type(v) is float for k in ['matrix','column','rhs','wanted'] for v in o[k]),'native typed snapshot')
 A=[[F(o['matrix'][i+n*j]) for j in range(n)] for i in range(n)];x=list(map(F,o['column']));rhs=list(map(F,o['rhs']));wanted=list(map(F,o['wanted']))
 residual=[sum(A[i][j]*x[j] for j in range(n))-rhs[i] for i in range(n)]
 bound=8*F(1,2**52)*max(F(1),max(sum(map(abs,row)) for row in A)*max(map(abs,x)),max(map(abs,rhs)))
 c.need([sum(A[i][j]*wanted[j] for j in range(n)) for i in range(n)]==rhs and list(map(F,o['residual']))==residual and F(o['bound'])==bound and max(map(abs,residual))<=bound and o['construction_exact'] is True and o['passed'] is True,'independent exact native oracle')
 if i%2:c.need(o==oracles[i-1],'original/candidate native snapshots equal')
c.unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];c.put('audit-host.json',c.host(extra));c.put('summary.json',dict(cases=rows,measured_windows=len(rows)*18,GC_affected_windows=gc))
c.put('audit.json',dict(accepted=True,assertions=int(m[1]),cells=len(rows),windows=len(rows)*18,GC_affected_windows=gc,elapsed_seconds=done['elapsed_shared_seconds'],min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),bindings={str(D/n):c.sha(D/n) for n in ['output/results.toml','output/run.log','output/process.json','pins-ready.json','summary.json','audit-ready.py']}))
print(json.dumps(c.read('audit.json')))
