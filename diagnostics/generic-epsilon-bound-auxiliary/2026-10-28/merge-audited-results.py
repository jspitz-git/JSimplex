from pathlib import Path
import sys,json,shutil,statistics as st
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
p=c.read('audit-prefix.json');r=c.read('remaining-qualified/audit.json');c.need(p['accepted'] and p['original_attempt_accepted'] is False and r['accepted'],'both scoped audits')
for a in [p,r]:
 for n,h in a['bindings'].items():c.need(c.sha(n)==h,'audit binding '+n)
rows=c.read('summary-prefix.json')+c.read('remaining-qualified/summary.json');grid=[v for v in c.read('expected-cases.json') if not(v['variant']=='C' and v['context'].startswith('Rational'))]
c.need(len(rows)==len(grid)==1226 and all(all(x[k]==v for k,v in g.items()) for x,g in zip(rows,grid)),'exact supported grid union/order');c.put('summary.json',rows)
groups=[]
for arm in 'ABC':
 for context in sorted(set('BigFloat' if x['context'].startswith('BF') else x['context'] for x in rows if x['variant']==arm)):
  for mode in sorted(set(x['mode'] for x in rows if x['variant']==arm and ('BigFloat' if x['context'].startswith('BF') else x['context'])==context)):
   a=[x for x in rows if x['variant']==arm and ('BigFloat' if x['context'].startswith('BF') else x['context'])==context and x['mode']==mode];rat=[x['seconds']['paired_median'] for x in a];ev=[x['events']['before']-x['events']['after'] for x in a];bs=[x['bytes']['before']-x['bytes']['after'] for x in a]
   groups.append(dict(arm=arm,context=context,mode=mode,cells=len(a),median_of_cell_paired_time_medians=st.median(rat),minimum_cell_time_median=min(rat),maximum_cell_time_median=max(rat),slower_cells=sum(v>1 for v in rat),cell_median_event_saving_min=min(ev),cell_median_event_saving_max=max(ev),cell_median_byte_saving_min=min(bs),cell_median_byte_saving_max=max(bs),timing_interpretation='single process per disjoint subset; short whole-call fixed9pairs; no endtoend/universal/platform claim'))
c.put('groups.json',groups)
c.put('audit.json',dict(accepted=True,scope='supported complete-cell union ONLY; original root remains failed',original_root_pass=55626,original_root_fail=1,original_root_errors=2,original_root_accepted=False,completion_assertions=1428,cases=1226,windows=22068,contexts=19,measured_compile_zero=True,measured_gc_windows=p['gc_windows']+r['gc_windows'],supported_correctness_assertions=7153,unsupported_C_exact_types=['Rational{BigInt}','Rational{Int64}'],unexecuted_rational_C_cells=8,bindings={str(D/n):c.sha(D/n) for n in ['audit-prefix.json','remaining-qualified/audit.json','route-review.json','route-supplement.json','summary.json','groups.json']}))
shutil.copyfile(__file__,D/'merge-audited-results.py')
for x in groups:
 if x['context'] in ['BigFloat','Rational{BigInt}'] or x['arm']=='C':print(x['arm'],x['context'],x['mode'],x['cells'],round(x['median_of_cell_paired_time_medians'],4),'median events',x['cell_median_event_saving_min'],x['cell_median_event_saving_max'],'median bytes',x['cell_median_byte_saving_min'],x['cell_median_byte_saving_max'])
