from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl'); Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-PLAN'
s=R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md'; p=R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
with (Q/'author.py').open('xb') as f:f.write(Path(__file__).read_bytes())
a=s.read_text();b=p.read_text();e=json.loads((Q/'entry.json').read_text());fix=json.loads((Q/'review-fix.json').read_text())
checks={
'entry_sources_unchanged':all(sha(R/n)==h for n,h in e['sha256'].items()),
'fix_bindings':all(sha(Path(n))==h for n,h in fix['sha256'].items()),
'planning_only':all(x in b for x in ['Planning only now','No candidate, Julia text implementation','Task1 OFFLINE']),
'pivot_policy':all(x in a for x in ['_pivot_magnitude(b)>_pivot_magnitude(a)','strict-tie','No `@fastmath`']),
'spike_witness':all(x in a for x in ['AFTER the original entering-spike','independent original-B solve','U_after-T*H']),
'bounded_fallback':all(x in a for x in ['At most one rejected panel','at most8 attempted steps','No catch-all']),
'concrete_write_strategy':all(x in a for x in ['fresh exact-length','no resize!, insert!, delete!','2*new_length','source element-operation cap']),
'cost_complexity':all(x in a for x in ['TWO separate band read passes','O(n^2 log n/b)','O(n+h*w)','O(n^3/b)']),
'memory_budget':all(x in a for x in ['72n+16*cld(9n,64)+256+4096','old and fresh column arrays simultaneously','Copied factors start cache-empty']),
'boundary_tests':all(x in b for x in ['one store above2*h*w','adversarial repeated panels','old/new live-array coexistence']),
'numerical_and_cost_gates':all(x in a for x in ['128*n*eps(Float64)','WHOLE time <=0.95','WHOLE ratio<=1.05','allocation events and bytes <=reference','<=1.10reference','<=1.25matched reference']),
'no_julia_files':not list(Q.rglob('*.jl')),
'rejections_preserved':json.loads((Q/'review-initial.json').read_text())['accepted'] is False and all((Q/n).is_file() for n in ['spec.before-R2.md','plan.before-R2.md','spec.before-author-clarification.md','plan.before-author-clarification.md']),
}
files=[s,p,Q/'DECISIONS.md',Q/'REVIEW-FIX.md',Q/'review-fix.json',Q/'author.py']
result={'all_passed':all(checks.values()),'checks':checks,'sha256':{str(x):sha(x) for x in files},'scope':'Offline author consistency checks; not a numerical correctness or performance proof'}
with (Q/'author.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(checks));raise SystemExit(0 if result['all_passed'] else 1)
