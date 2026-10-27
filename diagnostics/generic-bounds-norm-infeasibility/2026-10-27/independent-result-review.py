from pathlib import Path
import sys,json,tomllib,statistics as st,math
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');Q=D/'comparison-2';K=D/'correctness-qualification';sys.path.insert(0,str(K));import common as c
c.unchanged()
for path in [Q/'audit-qualified.json',Q/'cost-qualification-review.json',K/'result-review.json',K/'audit.json']:
 obj=json.loads(path.read_text());assert obj['accepted']
 for n,v in obj['bindings'].items():assert c.sha(n)==v
au=json.loads((Q/'audit-qualified.json').read_text());assert au['original_run_accepted'] is False and au['raw_original_failures']==18 and au['qualification_assertions']==15881
p=json.loads((Q/'output/process.json').read_text());s=json.loads((Q/'supervisor.json').read_text());assert p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] and s['accepted'] is False and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s
co=json.loads((Q/'contract.json').read_text());g=json.loads((Q/'output/gate.json').read_text());cur=json.loads((Q/'output/current.json').read_text());pm=json.loads((Q/'output/permit.json').read_text())
assert co['command']==p['command']==g['command']==cur['command']==pm['command'] and g['parent_death_signal']==9
assert s['guard_identity']==p['runner']==g['parent']==cur['runner'] and p['child']==g['identity']==cur['child']
assert g['current_sha256']==c.sha(Q/'output/current.json')==pm['current_sha256'] and g['permit_sha256']==c.sha(Q/'output/permit.json')
assert c.sha(Q/'pins.json')==c.sha(Q/'output/pins.json')==p['pins_sha256'] and s['elapsed_seconds']<600
resources=[json.loads(l) for l in (Q/'output/resources.jsonl').read_text().splitlines()];assert resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources)
r=tomllib.loads((Q/'output/results.toml').read_text());published=json.loads((Q/'summary-qualified.json').read_text());assert len(r['cells'])==len(published)==1632
contexts=[(f'BF{b}_RoundingMode{{:{m}}}()','BigFloat') for b in [64,128,256] for m in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
expected=[]
for label,t in contexts:
 for n in [16,64]:
  for den in ['sparse','dense']:
   for shape in (['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):
    for arm,scopes in [('A',['snap','step','ratio']),('B',['norm','init','solve'])]:
     for scope in scopes:expected.append((label,t,n,den,shape,scope,arm,True,'finite'))
 for n in [16,64]:
  for den in ['sparse','dense']:
   for below in [True,False]:
    for mode in ['finite','one_sided','zero_tol']:expected.append((label,t,n,den,'positive','cert','C',below,mode))
rows=[];gc=0;windows=0
for cell,pub,key in zip(r['cells'],published,expected):
 assert tuple(cell[k] for k in ['context','type','n','density','shape','scope','variant','below','mode'])==key
 assert cell['id']==pub['id'];w=cell['windows'];assert len(w)==18;windows+=len(w)
 row={k:v for k,v in cell.items() if k!='windows'}
 for i in range(9):assert [v['pair'] for v in w[2*i:2*i+2]]==[i+1,i+1] and [v['arm'] for v in w[2*i:2*i+2]]==(['original',cell['variant']] if i%2==0 else [cell['variant'],'original']) and w[2*i]['sink']==w[2*i+1]['sink']
 for v in w:
  assert v['compile_seconds']==v['recompile_seconds']==0
  assert all(type(v[f]) in [int,float] and math.isfinite(v[f]) and v[f]>=0 for f in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'])
  gc+=v['gc_seconds']>0
 a=[v for v in w if v['arm']=='original'];b=[v for v in w if v['arm']!='original']
 for f in ['seconds','bytes','events']:
  ratios=[bv[f]/av[f] if av[f] else 1 if bv[f]==0 else math.inf for av,bv in zip(a,b)];med=st.median(ratios)
  result=dict(before=st.median(v[f] for v in a),after=st.median(v[f] for v in b),paired_median=med,paired_min=min(ratios),paired_max=max(ratios),paired_MAD=st.median(abs(x-med) for x in ratios))
  assert result==pub[f];row[f]=result
 rows.append(row)
assert windows==29376 and gc==25
prep=r['preparation'];assert len(prep)==1670 and [x['cell'] for x in prep if 'cell' in x]==[x['id'] for x in rows]
assert all(len(x['cold'])==2 and len(x['warm'])==6 and len(x['resets'])==18 for x in prep if 'cell' in x)
def stats(z):
 return dict(cells=len(z),metrics={f:dict(median=st.median(x[f]['paired_median'] for x in z),minimum=min(x[f]['paired_median'] for x in z),maximum=max(x[f]['paired_median'] for x in z),higher=sum(x[f]['paired_median']>1 for x in z),equal=sum(x[f]['paired_median']==1 for x in z),median_absolute_before=st.median(x[f]['before'] for x in z),median_absolute_after=st.median(x[f]['after'] for x in z),savings=sorted(set(x[f]['before']-x[f]['after'] for x in z))) for f in ['seconds','bytes','events']})
groups={}
for t in ['BigFloat','Rational{BigInt}','Float32','Float64','Rational{Int64}']:
 for scope in ['snap','step','ratio','norm','init','solve','cert']:groups[t+'/'+scope]=stats([x for x in rows if x['type']==t and x['scope']==scope])
for below in [True,False]:
 for mode in ['finite','one_sided','zero_tol']:groups[f'BigFloat/cert/{below}/{mode}']=stats([x for x in rows if x['type']=='BigFloat' and x['scope']=='cert' and x['below']==below and x['mode']==mode])
impacted=[x for x in rows if x['type']=='BigFloat' or x['type']=='Rational{BigInt}' and x['variant']=='A']
assert all(x[f]['after']<x[f]['before'] for x in impacted for f in ['bytes','events'])
kp=json.loads((K/'output/process.json').read_text());h=c.host([kp[k][v] for k in ['runner','child'] for v in ['pgid','sid']]);assert len(h['groups'])==643
with (D/'independent-result-host.json').open('x') as f:json.dump(h,f,indent=2)
with (D/'independent-cost-analysis.json').open('x') as f:json.dump(dict(groups=groups,all_cells_recomputed=True,windows=windows,gc_windows=gc),f,indent=2)
report='''# Independent per-variant result decision

Accept A, B and C for production integration preparation, subject to prospective permanent correctness/allocation gates, original RED, implementation review and planned GREEN/MASTER checks. This is not completed integration, release approval or an end-to-end solver speedup claim.

Evidence status is explicit: original comparison-2 remains FAILED (51,891 passes, 18 faulty cap-oracle failures, exit1 and rejected supervisor). The independent source correction and separate correctness-only qualification passed 15,881 assertions, including the 18 expected NaNs and 72 caps. The new post-exit auditor qualifies existing cost data only. I independently rechecked its bindings, guard/gate/permit/source/resource state, all 1,632 ordered cells and 29,376 windows, recomputed every published per-cell cost summary and retained all 25 GC windows. Compilation and recompilation were zero in every measured window. No Julia, remeasurement or old auditor was executed.

Ratios below are medians across cells of each cell's nine paired ratios, not confidence intervals or pooled workload speedups. All cold, three warm, fixture/reset/snapshot/correctness and explicit-GC costs remain separately retained in 1,670 preparation entries. Sparse/dense dimensions 16/64, BigFloat64/128/256 and five rounding modes plus native/exact controls are included. These short kernels on one host/run cannot establish broad timing or retained-memory claims.

| Variant/path | Time ratio | Byte ratio | Event ratio | Decision |
|---|---:|---:|---:|---|
| A BigFloat snap | 0.74599 | 0.70336 | 0.71571 | accept |
| A BigFloat step | 0.74180 | 0.69520 | 0.70881 | accept |
| A BigFloat whole ratio | 0.95183 | 0.93836 | 0.93932 | accept |
| A Rational BigInt snap | 0.91534 | 0.91412 | 0.89644 | accept |
| A Rational BigInt step | 0.88869 | 0.89898 | 0.87087 | accept |
| A Rational BigInt ratio | 0.98089 | 0.97909 | 0.97379 | accept, timing modest |
| B BigFloat direct norm | 0.98900 | 0.98535 | 0.98849 | allocation benefit; timing unproved |
| B BigFloat initialization | 0.96542 | 0.93678 | 0.94927 | accept |
| B BigFloat checked FTRAN maintenance | 0.99656 | 0.99411 | 0.99568 | accept allocation benefit; timing unproved |
| C BigFloat full certificate | 0.97298 | 0.97700 | 0.97094 | accept; outcome-dependent timing |

A has lower median bytes/events in every impacted cell and no slower BigFloat cell median among 540 cells. BigFloat snap/step save 100 or 420 measured allocation events; whole ratio saves 60 or 252. Rational BigInt controls show reductions too, but only four cells per A path. One Rational ratio cell ties in time. Sharing the private read-only zero preserves Boolean results and avoids repeated constructors; lazy readiness adds a per-row branch and must remain counted.

B saves exactly five measured events and 176/208/240 bytes per direct norm or checked FTRAN call at the tested precisions. Initialization saves 85 or 325 events (existing column norms plus row norm). The unchanged checked basis solve dominates maintenance, so the tiny aggregate time change is not a demonstrated FTRAN speedup. Direct norm has 29/180 slower cell medians and 27 ties (range 0.77752–1.03896); checked FTRAN has 24/180 slower and 30 ties (range 0.96455–1.19899). These are retained, not filtered. Initialization medians are lower across 180 cells, but remain single-run evidence. Positive overflow still constructs the fresh cap; source removal counts are not claimed as universal allocation counts.

C has lower bytes/events in all 360 cells, saving 4–772 events depending on branch/orientation. It has 42 slower time medians and 12 ties, with cell median range 0.85487–1.01299. Below=true finite and one-sided controls have respective time/byte ratios 0.93940/0.95468 and 0.91736/0.93083; below=false finite and one-sided ratios are 0.98437/0.98813 and 0.95951/0.96220. Zero-tolerance paths have time ratios about 0.99848 and 1.00000, byte ratios about 0.99913: no meaningful timing benefit claimed. Both orientations and the invalid/straddling certificate controls remain covered; interval widening and all numerical safeguards are unchanged.

Native/exact unaffected routes retain baseline methods and measured event counts. Their time medians vary with coarse timer resolution/noise, and Rational byte counters show small variation despite unchanged methods: examples include Rational Int64 ratio byte ratios up to 1.00885 and norm up to 1.01276, and Rational BigInt certificate up to 1.00034. Those observations remain in independent-cost-analysis.json; they do not justify claiming every control improves or is byte-identical. No causal speed claim is based on unchanged allocations alone.

Computational work/memory review: no unnecessary new full-vector/matrix scan, basis solve, copy, conversion, repeated invariant check or retained data cache found. A remains O(rows), B retains two norm scans and the existing solve, C remains O(nnz+variables). New readiness branches and specialized-method compilation/code metadata are real costs; cold/warm and preparation measurements remain separated. Numeric safeguards take precedence and none were relaxed. Reduced measured Julia allocation events/bytes do not prove native limb freeing, reduced peak RSS or long-lived retained-memory improvements.

Prospective fixed three-pair permanent gates should require lower allocation events and lower median bytes, with no timing gate: A snap/step/whole ratio for BigFloat and Rational BigInt; B initialization and genuine checked-FTRAN maintenance for BigFloat (direct norm optional); C finite and one-sided full certificates for BigFloat below=true. Retain broader correctness/unchanged-route controls without demanding cost reductions from paths that do not change. These gates must witness original RED before candidate staging; their future outcome is not asserted here.
'''
with (D/'RESULT-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-result-review.py').open('x') as f:f.write(Path(__file__).read_text())
paths=[Q/'audit-qualified.json',Q/'audit-qualified.py',Q/'summary-qualified.json',Q/'output/results.toml',Q/'output/process.json',Q/'output/run.log',K/'result-review.json',K/'audit.json',D/'changes.json',D/'RESULT-REVIEW.md',D/'independent-cost-analysis.json',D/'independent-result-host.json',D/'independent-result-review.py']
decisions={v:dict(accepted=True,basis='qualified numerical parity plus lower measured bytes/events on every impacted cell',timing_limitations=('direct norm and checked FTRAN timing not demonstrated' if v=='B' else 'zero-tolerance and some orientations/cells have no clear timing benefit' if v=='C' else 'single-host short-run evidence, four Rational cells per path'),integration_pending=True) for v in ['A','B','C']}
with (D/'result-review.json').open('x') as f:json.dump(dict(accepted=True,findings=[],accepted_variants=['A','B','C'],decisions=decisions,original_comparison_accepted=False,qualification_assertions=15881,cases=1632,windows=windows,gc_windows=gc,Julia_executed=False,bindings={str(p):c.sha(p) for p in paths}),f,indent=2);f.write('\n')
print('accepted A/B/C for integration preparation; all summaries independently recomputed; original run remains failed')
