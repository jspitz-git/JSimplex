from pathlib import Path
import json,sys,tomllib,re,math,statistics as st,hashlib
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import common_complete as c
c.unchanged();c.need(c.read('completed.json')['accepted'],'supervisor completion')
p=c.read('output/process.json');c.need(p['returncode']==0 and p['pins_unchanged'],'exit/pins')
extra=[p[k][f] for k in ['runner','child'] for f in ['pgid','sid']];c.put('audit-host.json',c.host(extra))
log=(D/'output/run.log').read_text();c.need('RATIO_MONITOR_COMPARISON_COMPLETE cells=1225' in log,'terminal marker')
c.need('Test Failed' not in log and 'Error During Test' not in log,'ordinary test failed')
data=tomllib.loads((D/'output/results.toml').read_text());c.need(len(data['cells'])==1225,'all cells')
contexts=[(f'BF{b}_{m}','BigFloat') for b in [64,128,256] for m in ['RoundingMode{:Nearest}()','RoundingMode{:Down}()','RoundingMode{:Up}()','RoundingMode{:ToZero}()','RoundingMode{:FromZero}()']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
# Context display is checked from actual fixed Julia names below rather than inferred TOML types.
expected=set()
for label,t in contexts:
 shapes=['positive','negative','mixed'] if t=='BigFloat' else ['mixed']
 for n in [16,64]:
  for density in ['sparse','dense']:
   for shape in shapes:expected.add((label,t,n,density,shape,'ratio','A','end'))
 for arm in ['B','C','BC']:
  for phase in ['first','ordinary','end']:
   for shape in shapes:expected.add((label,t,16,'sparse',shape,'progress',arm,phase))
  for n in [16,64]:
   for density in ['sparse','dense']:
    for shape in shapes:expected.add((label,t,n,density,shape,'workspace',arm,'end'))
actual={(x['context'],x['type'],x['n'],x['density'],x['shape'],x['scope'],x['variant'],x['phase']) for x in data['cells']}
c.need(actual==expected and len(actual)==1225,'exact grid')
fields=['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'];summary=[];gc=0
for x in data['cells']:
 rows=x['windows'];c.need(len(rows)==18,'18 windows')
 for pair in range(1,10):
  q=[w for w in rows if w['pair']==pair];c.need([w['arm'] for w in q]==(['original',x['variant']] if pair%2 else [x['variant'],'original']),'pair/order')
  c.need(q[0]['sink']==q[1]['sink'],'same consumed outputs')
 for w in rows:
  for f in fields:c.need(type(w[f]) in (float,int) and math.isfinite(w[f]) and w[f]>=0,'nonnegative finite metric')
  c.need(type(w['bytes']) is int and type(w['events']) is int,'integer counters');c.need(w['compile_seconds']==w['recompile_seconds']==0,'compilezero');gc+=w['gc_seconds']>0
 a=[w for w in rows if w['arm']=='original'];b=[w for w in rows if w['arm']==x['variant']]
 q={k:v for k,v in x.items() if k!='windows'}
 for f in ['seconds','bytes','events']:
  meda=st.median(w[f] for w in a);medb=st.median(w[f] for w in b);ratios=[b[i][f]/a[i][f] if a[i][f] else 1 if not b[i][f] else math.inf for i in range(9)]
  q[f]=dict(before=meda,after=medb,paired_median=st.median(ratios),paired_min=min(ratios),paired_max=max(ratios),paired_MAD=st.median(abs(r-st.median(ratios)) for r in ratios))
 summary.append(q)
c.need(len(data['preparation'])==1225+38,'prep count')
c.need([x['cell'] for x in data['preparation'] if 'cell' in x]==[x['id'] for x in data['cells']],'exact ordered prep cell identity')
c.need([(x['context'], 'correctness' if 'correctness' in x else 'GC') for x in data['preparation'] if 'cell' not in x]==[(label,phase) for label,t in contexts for phase in ['correctness','GC']],'exact context prep identity')
for prep in data['preparation']:
 if 'cell' not in prep:continue
 c.need(len(prep['cold'])==2 and len(prep['warm'])==6 and len(prep['resets'])==18,'all cold/warm/reset preparation')
 for z in [prep['fixture'],prep['validation'],*prep['resets'],*[v for q in prep['cold']+prep['warm'] for v in [q['cost'],q['reset']]]]:
  for f in fields:c.need(type(z[f]) in (float,int) and math.isfinite(z[f]) and z[f]>=0,'valid preparation metric')
c.put('summary.json',summary)
c.put('audit.json',dict(accepted=True,cases=1225,windows=22050,compilezero=True,gc_windows=gc,all_preparation_preserved=True,raw_sha256=c.sha(D/'output/results.toml'),log_sha256=c.sha(D/'output/run.log'),bindings={str(D/n):c.sha(D/n) for n in ['contract-complete.json','pins-complete.json','admission-complete.json','completed.json','output/process.json','output/results.toml','output/run.log','summary.json']},auditor_is_postexit_not_launch_pin=True))
print('PASS',1225,'cells',22050,'windows','GC',gc)
