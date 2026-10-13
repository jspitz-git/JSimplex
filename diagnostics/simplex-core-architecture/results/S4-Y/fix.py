"""One-use offline fix; initial sources/evidence retained; no Julia execution."""
from pathlib import Path
import hashlib,json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S4-Y'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
report=R/'diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-PREPARATION.md'
plan=R/'docs/superpowers/plans/2026-10-13-markowitz-retention-admission.md'
status=R/'diagnostics/simplex-core-architecture/STATUS.md'
roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
old=(D/'driver.jl').read_text()
needle='''Dict("forward_unit_solution" => isapprox(forward,expected;rtol=0,atol=bound),
         "transpose_unit_solution" => isapprox(transposed,expected;rtol=0,atol=bound))'''
replacement='''Dict("forward_unit_solution" => all(i -> abs(forward[i]-expected[i]) <= bound,eachindex(expected)),
         "transpose_unit_solution" => all(i -> abs(transposed[i]-expected[i]) <= bound,eachindex(expected)))'''
need(old.count(needle)==1,'initial oracle site')
red={'componentwise_oracle_present':replacement in old,'correct_helper_allocation_ledger':'ten solve-helper calls' in report.read_text()}
need(not any(red.values()),'structural RED not established')
for p,name in [(report,'report.before-review'),(plan,'plan.before-review'),(status,'STATUS.md.before-review'),(roadmap,'roadmap.md.before-review')]:
 with (D/name).open('xb') as f:f.write(p.read_bytes())
new=old.replace(needle,replacement)
with (D/'driver-reviewed.jl').open('x') as f:f.write(new)
t=report.read_text().replace('`results/S4-Y/driver.jl`','`results/S4-Y/driver-reviewed.jl`').replace('and twenty solve checks each allocate','and ten solve-helper calls each allocate').replace('one expected vector, two product RHS vectors and two destinations, plus library','one expected vector, two product RHS vectors and two destinations (50 explicit\nvector results total), plus library')
t=t.replace('Existing tests are read, not rerun:', '''Existing tests are read, not rerun. The September2026 Markowitz allocation-reuse
plan explicitly approves capacity retention. `test/markowitz_tests.jl:181–187`
already bounds the initial512 saved graph below250000B and backend graph below
one dense512-square Float64 matrix; both guards remain unchanged. The new gap is
sparse/dense shrink-history graph observations, not absence of memory guards.
Readtime bindings are separately saved in historical-retention.json.

Existing coverage:''')
t+='''
## Independent review correction

Initial review REJECTED the norm mismatch (Important) and doubled helper-vector
ledger (reviewer Minor, author Important because this is admission cost evidence).
One offline structural RED→GREEN fix replaces array isapprox by componentwise
absolute comparisons at the unchanged64*eps(Float64), and corrects10 helper
calls/50 explicit vector results versus20 backend solves/comparison predicates.
Initial driver.jl/report/plan/continuation/source.json and rejected review remain
preserved. driver-reviewed.jl is canonical and UNEXECUTED. This is textual
verification, not a Julia test or numerical counterexample. Initial source.json
live report/plan/STATUS/roadmap bindings map only to their Y before-review copies;
all its other hashes stay valid. No unresolved Minor is deliberately deferred.
'''
report.write_text(t)
plan.write_text(plan.read_text().replace('results/S4-Y/driver.jl','results/S4-Y/driver-reviewed.jl'))
status.write_text(status.read_text().replace('Separate UNEXECUTED driver:','Separate canonical UNEXECUTED driver-reviewed.jl (initial driver preserved):',1))
checks={'structural_red':not any(red.values()),'componentwise_green':replacement in new and 'isapprox(' not in new,'exact_inverse':new.replace(replacement,needle)==old,'unchanged_tolerance':'bound = 64*eps(Float64)' in new,'correct_helper_ledger':'ten solve-helper calls' in t and '50 explicit' in t,'history_guard_scope':'initial512' in t,'all_initial_bindings_preserved':True}
maps={str(report.relative_to(R)):'report.before-review',str(plan.relative_to(R)):'plan.before-review',str(status.relative_to(R)):'STATUS.md.before-review',str(roadmap.relative_to(R)):'roadmap.md.before-review'}
for p,h in json.loads((D/'source.json').read_text())['sha256'].items():
 need(sha(D/maps[p] if p in maps else R/p)==h,'initial hash:'+p)
need(all(checks.values()),'fix gate')
files=[D/'driver-reviewed.jl',D/'driver.jl',D/'fix.py',D/'review-initial.md',D/'historical-retention.json',report,plan,status,roadmap]+[D/n for n in maps.values()]
with (D/'fix.json').open('x') as f:json.dump({'red':red,'checks':checks,'all_passed':True,'sha256':{str(p.relative_to(R)):sha(p) for p in files},'initial_source_mapping':maps},f,indent=2);f.write('\n')
print(json.dumps({'fix_checks':len(checks),'bindings':len(files),'all_passed':True,'julia_executed':False}))
