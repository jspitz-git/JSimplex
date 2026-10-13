"""MA-G one-shot offline analysis of preserved MA-F measurements; no Julia."""
from pathlib import Path
import json, tomllib, hashlib, statistics as st
ROOT=Path(__file__).resolve().parents[4]
G=Path(__file__).resolve().parent
E=ROOT/'diagnostics/simplex-core-architecture/results/MA-E'
F=ROOT/'diagnostics/simplex-core-architecture/results/MA-F-repair'
pins={}
def read(p):
    b=p.read_bytes();pins[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return b
read(Path(__file__))
saved=json.loads(read(F/'summary.json'))['cases']
post=json.loads(read(F/'postprocess.json'))
raw={(p,side):tomllib.loads(read(F/f'attempt-2/pair{p:02d}-{side}/raw.toml').decode()) for p in range(4,11) for side in ['reference','candidate']}
ref=read(E/'overlays/reference/src/markowitz_factorization.jl').decode()
cand=read(E/'overlays/candidate/src/markowitz_factorization.jl').decode()
kernels=read(E/'kernels.jl').decode();driver=read(F/'driver.jl').decode()
read(E/'fixtures.toml');read(G/'host.json');read(G/'STATUS.md.before-MA-G');read(G/'roadmap.md.before-MA-G')
checks={};cases=[]
for s in saved:
    key=(s['name'],s['scalar']); pairs=[]
    for p in range(4,11):
        sides={side:next(r for r in raw[p,side]['records'] if (r['name'],r['scalar'])==key) for side in ['reference','candidate']}
        rr,cc=sides['reference'],sides['candidate']
        pairs.append({'pair':p,'full_ratio':cc['steady_full']['seconds']/rr['steady_full']['seconds'],
          'upper_reset_ratio':cc['steady_upper']['seconds']/rr['steady_upper']['seconds'],
          'reference':{w:rr[w] for w in ['steady_full','steady_upper']},
          'candidate':{w:cc[w] for w in ['steady_full','steady_upper']}})
    ratios=[p['full_ratio'] for p in pairs]; med=st.median(ratios)
    checks['summary_'+':'.join(key)]=med==s['median_ratio'] and min(ratios)==s['minimum_ratio'] and max(ratios)==s['maximum_ratio'] and sum(x<1 for x in ratios)==s['faster_pairs']
    m=rr['metadata']; c={'name':key[0],'scalar':key[1],'S':m['S'],'K':m['K'],'E':m['E'],'full_median_ratio':med,'upper_reset_median_ratio':st.median(p['upper_reset_ratio'] for p in pairs),'control_gate':s['control_gate'],'target_gate':s['target_gate'],'pairs':pairs}
    c['median_per_call']={side:{w:{metric:st.median(p[side][w][metric]/4 for p in pairs) for metric in ['seconds','bytes','allocations']} for w in ['steady_full','steady_upper']} for side in ['reference','candidate']}
    c['gc_windows']=[{'pair':p['pair'],'side':side,'window':w,'gc_seconds':p[side][w]['gc_seconds']} for p in pairs for side in ['reference','candidate'] for w in ['steady_full','steady_upper'] if p[side][w]['gc_seconds']]
    cases.append(c)
failed=[c for c in cases if c['control_gate'] is False]
checks['all48_cases']=len(cases)==48
checks['six_failed_controls']=len(failed)==6
checks['all_six_target_gates']=sum(c['target_gate'] is True for c in cases)==6 and not any(c['target_gate'] is False for c in cases)
checks['four_repetitions']= 'full_window!,out,b,rhs,4' in driver and 'upper_window!,upperfun,w,b,initial,4' in driver
checks['upper_includes_reset']='copyto!(w,initial);f(w,b.upper,b.diagonal,b.sparse_pivots)' in kernels
checks['hardware_generic_helper']= 'function _markowitz_upper_solve!(work, upper, diagonal, sparse_pivots)' in cand
checks['bigfloat_rounding_before_ma_loop']= 'if !_markowitz_ma_rounding_matches()' in cand and 'return _markowitz_ma_upper_solve!(work,upper,diagonal,sparse_pivots)' in cand
checks['lazy_scratch']= 'scratch = nothing' in cand and 'if isnothing(scratch)' in cand
checks['all_core_no_upper']=all(c['S']==c['K']==c['E']==0 for c in cases if c['name'].startswith('core'))
checks['all_failed_hardware_no_eligible']=all(c['E']==0 for c in failed if c['scalar'] in ['Float32','Float64'])
# Whole source inverse isolates helper insertion and one call replacement.
a=ref.index('function _backend_forward_solve!');b=ref.index('function _backend_transpose_solve!')
orig=ref[a:b]; lo=orig.index('    for pivot in sparse_pivots:-1:1');hi=orig.index('    for index in 1:n',lo)
loop=orig[lo:hi]
expected=orig[:lo]+'    _markowitz_upper_solve!(work, backend.upper, backend.diagonal, sparse_pivots)\n'+orig[hi:]
ca=cand.index('function _backend_forward_solve!');cb=cand.index('function _backend_transpose_solve!')
checks['forward_only_call_replacement']=cand[ca:cb]==expected
checks['no_other_factor_source_change']=ref[:a]==cand[:cand.index('function _markowitz_upper_solve!')] and ref[b:]==cand[cb:]
checks['all_steady_compile_zero']=all(p[side][w][v]==0 for c in cases for p in c['pairs'] for side in ['reference','candidate'] for w in ['steady_full','steady_upper'] for v in ['compile_seconds','recompile_seconds'])
out={'all_passed':all(checks.values()),'checks':checks,'cases':cases,'failed_controls':[{'name':c['name'],'scalar':c['scalar']} for c in failed],'sha256':pins,'scope':'New offline raw analysis only. Seven measured pairs; all GC/outliers retained. Division by four reports per-call window averages, not isolated call measurements. No causal attribution or revised acceptance.'}
with (G/'analysis.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':checks,'pins':len(pins)},indent=2))
for c in failed:
 print(c['name'],c['scalar'],'full',c['full_median_ratio'],'upper/reset',c['upper_reset_median_ratio'],'percall',c['median_per_call'],'GC',c['gc_windows'])
if not out['all_passed']:raise SystemExit(1)
