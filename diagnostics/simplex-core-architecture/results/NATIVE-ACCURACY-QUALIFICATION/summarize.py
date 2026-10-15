"""Saved-results-only tradeoffs and paired crossover; no numerical replay."""
from pathlib import Path
import json,tomllib,struct,statistics as st,hashlib
Q=Path(__file__).resolve().parent;D=Q.parent/'NATIVE-ACCURACY-PREPARATION'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def val(t):return struct.unpack('>d',bytes.fromhex(t))[0]
def stats(x):
 m=st.median(x);return dict(median=m,min=min(x),max=max(x),mad=st.median(abs(v-m) for v in x))
a=rd(Q/'accuracy-audit.json');r=a['result'];rows={};refinement={};factor_equal={}
for name in ('sparse32','dense32','sparse96','dense96'):
 p=r['cost'][name+':P:construction']['samples'];q=r['cost'][name+':R:construction']['samples'];ps=r['cost'][name+':P:solve']['samples'];rs=r['cost'][name+':R:solve']['samples']
 initial=[p[str(k)]['seconds']-q[str(k)]['seconds'] for k in range(4,12)];saving=[(rs[str(k)]['seconds']-ps[str(k)]['seconds'])/16 for k in range(4,12)]
 paired=[max(0,c/s) for c,s in zip(initial,saving)] if min(saving)>0 else None
 rows[name]=dict(P_minus_R_construction_seconds=stats(initial),R_minus_P_per_triplet_seconds=stats(saving),denominator_positive_all_pairs=min(saving)>0,paired_break_even_triplets=stats(paired) if paired is not None else None,conservative_observed_spread_upper=max(0,max(initial))/min(saving) if min(saving)>0 else None,interpretation='Empirical paired break-even and observed-spread bound only, not confidence bound; tiny constructor differences and a single process prevent universal crossover claims')
 windows=[tomllib.loads(p.read_text()) for p in sorted((Q/'accuracy-run').glob('window-*.toml')) if tomllib.loads(p.read_text())['schedule']['fixture']==name]
 last={v['schedule']['arm']:v['factor'] for v in windows if v['schedule']['round']==11}
 keys=('L','U','p','q','Rs','do_recip')
 factor_equal[name]=dict(P_equals_C=all(last['P'][k]==last['C'][k] for k in keys),R_equals_C=all(last['R'][k]==last['C'][k] for k in keys))
 for arm in 'CPR':
  for ix,rhs in enumerate(('a','dse','unit')):
   vv=[v['info'][k] for v in windows if v['schedule']['arm']==arm for k in range(ix,48,3)];attempt=[int(val(x[2])) for x in vv];taken=[int(val(x[1])) for x in vv]
   refinement[name+':'+arm+':'+rhs]=dict(calls=len(vv),attempted=sum(attempt),taken=sum(taken),maximum_attempts=max(attempt),histogram={str(n):attempt.count(n) for n in sorted(set(attempt))})
resources=[json.loads(s) for s in (Q/'accuracy-run/resources.jsonl').read_text().splitlines()];proc=rd(Q/'accuracy-run/process.json');resources.append(proc['terminal_memory'])
summary=dict(integrity=a['all_passed'],accuracy=r['accuracy'],per_arm_calls=2126,failures={arm:sum(not x['passed'] for x in r['residuals'] if x['arm']==arm) for arm in 'CPR'},max_residual_ratio={arm:max(x['ratio'] for x in r['residuals'] if x['arm']==arm) for arm in 'CPR'},crossover=rows,refinement=refinement,factor_bits=factor_equal,min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),resource_samples=len(resources)-1,terminal_peak_rss_kib=proc['child_maxrss_kib'],sha256={str(p):sha(p) for p in [Path(__file__),Q/'accuracy-audit.json',Q/'accuracy-run/process.json',Q/'accuracy-run/resources.jsonl']})
with (Q/'summary.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('refinement','sha256')},indent=2));print('R refinement', {k:v for k,v in refinement.items() if ':R:' in k})
