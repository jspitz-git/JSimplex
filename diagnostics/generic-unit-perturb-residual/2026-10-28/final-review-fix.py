from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28')
s=(D/'finalize.py').read_text();needle="g=c.read('GREEN-run/audit.json')"
insert="""c.need(c.git(['branch','--show-current'])=='master' and c.git(['rev-parse','master'])==target,'current master branch/ref before finalization')
c.need(c.git(['branch','--show-current'],R)=='codex/simplex-core-architecture','current diagnostic branch before finalization')
expected_diagnostic=c.read('host-before.json')['diagnostic_head']
c.need(c.git(['rev-parse','HEAD'],R)==c.git(['rev-parse','origin/codex/simplex-core-architecture'],R)==c.git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]==expected_diagnostic,'diagnostic local/tracking/live refs before first mutation')
"""
assert s.count(needle)==1;s=s.replace(needle,insert+needle);compile(s,str(D/'finalize-reviewed.py'),'exec');(D/'finalize-reviewed.py').write_text(s)
s=(D/'closure.py').read_text().replace("reviews=['source-production-review.json','test-control-review.json'","reviews=['test-control-review.json'")
needle="c.need(c.read('independent-source-admission-rejected.json')"
insert="""# Source-only report has its own provisional schema; actual production and numerical admissions above are independently required.
source_report=c.read('source-production-review.json')
c.need(source_report['execution']['julia_launched'] is False and set(source_report['variants'])==set('ABC'),'source-only report scope')
c.need(source_report['numerical_verdict'] and source_report['work_memory_verdict'] and all(x['status']=='corrected and independently verified' for x in source_report['findings']),'resolved source-only findings')
for p,h in source_report['source_bindings'].items():before(p,h)
for p,h in source_report.get('prior_review_binding',{}).items():before(p,h)
"""
assert s.count(needle)==1;s=s.replace(needle,insert+needle);compile(s,str(D/'closure-reviewed.py'),'exec');(D/'closure-reviewed.py').write_text(s)
(D/'final-review-fix.py').write_bytes(Path(__file__).read_bytes());print('separate finalization and closure revisions prepared UNEXECUTED')
