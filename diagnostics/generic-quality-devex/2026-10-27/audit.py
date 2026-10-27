from pathlib import Path
import sys,json,re,tomllib,statistics,math
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');sys.path.insert(0,str(D));import common as c
p=c.read('output/process.json');s=c.read('supervisor.json');done=c.read('completed.json');contract=c.read('contract.json');log=(D/'output/run.log').read_text()
c.need(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and s['accepted'] is True and done['accepted'] is True,'exit/guards')
c.need(done['elapsed_shared_seconds']<=600,'600s')
m=re.search(r'^Quality and Devex complete comparison\s*\|\s*(\d+)\s+(\d+)\s+',log,re.M);c.need(m and int(m[1])==int(m[2]) and int(m[1])>1000,'ordinary fullpass summary')
c.need('QUALITY_DEVEX_COMPARISON_COMPLETE cells=1160' in log,'completion')
data=tomllib.loads((D/'output/results.toml').read_text())
contexts=[(f'BF{bits}_RoundingMode{{:{mode}}}()','BigFloat') for bits in [64,128,256] for mode in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
expected=[]
for label,t in contexts:
 scopes=['direction','row','quality','quality_transposed','devex_shared','devex_solved'] if t in ['BigFloat','Float32','Float64'] else ['quality','quality_transposed','devex_shared','devex_solved']
 for n in [32,128]:
  for scope in scopes:
   for density in ['sparse','dense']:
    for pattern in ['positive','negative','mixed'] if t=='BigFloat' else ['mixed']:expected.append((label,t,n,scope,density,pattern))
c.need(len(data['cells'])==len(expected)==contract['cases']==1160,'exact matrix length')
fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']
def validcost(v):return all(type(v[k]) in [int,float] and math.isfinite(v[k]) and v[k]>=0 for k in fields)
rows=[];gc=0
for i,(cell,key) in enumerate(zip(data['cells'],expected)):
 c.need(tuple(cell[k] for k in ['context','type','n','scope','density','pattern'])==key,'exact ordered matrix')
 c.need(cell['id']=='/'.join(map(str,[key[0],key[2],*key[3:]])),'cell id')
 raw=cell['windows'];c.need(len(raw)==18,'nine pairs');ratios=[]
 for k in range(1,10):
  pair=raw[2*k-2:2*k];c.need([w['arm'] for w in pair]==(['original','candidate'] if k%2 else ['candidate','original']),'alternation')
  c.need(all(type(w['pair']) is int and w['pair']==k and type(w['sink']) is int and validcost(w) and w['compile_seconds']==w['recompile_seconds']==0 for w in pair),'typed costs/compilezero')
  c.need(pair[0]['sink']==pair[1]['sink'],'typed sink equality')
  by={w['arm']:w for w in pair};c.need(by['original']['seconds']>0,'positive time');ratios.append(by['candidate']['seconds']/by['original']['seconds'])
  gc+=sum(w['gc_seconds']>0 for w in pair)
 r={k:cell[k] for k in ['context','type','n','scope','density','pattern']};med=statistics.median(ratios);r.update(paired_ratio=med,ratio_MAD=statistics.median(abs(v-med) for v in ratios),ratio_min=min(ratios),ratio_max=max(ratios))
 for arm in ['original','candidate']:r[arm]={k:statistics.median(w[k] for w in raw if w['arm']==arm) for k in ['seconds','bytes','events']}
 r['all_pairs_lower_bytes']=all(next(w['bytes'] for w in raw if w['pair']==k and w['arm']=='candidate')<next(w['bytes'] for w in raw if w['pair']==k and w['arm']=='original') for k in range(1,10))
 r['all_pairs_lower_events']=all(next(w['events'] for w in raw if w['pair']==k and w['arm']=='candidate')<next(w['events'] for w in raw if w['pair']==k and w['arm']=='original') for k in range(1,10));rows.append(r)
prep=data['preparation'];c.need(sum('phase' not in v for v in prep)==1160,'prep cells')
for v in prep:
 if 'phase' in v:c.need(validcost(v),'context prep')
 else:
  c.need(validcost(v['fixture']) and validcost(v['validation_and_snapshots']),'fixture/snapshot prep')
  for k,count in [('cold',2),('warm',6),('resets',18)]:c.need(len(v[k])==count and all(validcost(x) for x in v[k]),'prep '+k)
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()];c.need(resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources),'resource samples')
c.unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];c.put('audit-host.json',c.host(extra));c.put('summary.json',dict(cases=rows,measured_windows=len(rows)*18,GC_affected_windows=gc))
c.put('audit.json',dict(accepted=True,assertions=int(m[1]),cells=len(rows),windows=len(rows)*18,GC_affected_windows=gc,elapsed_seconds=done['elapsed_shared_seconds'],min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),bindings={str(D/n):c.sha(D/n) for n in ['output/results.toml','output/run.log','output/process.json','pins.json','summary.json','audit.py']}))
print(json.dumps(c.read('audit.json')))
