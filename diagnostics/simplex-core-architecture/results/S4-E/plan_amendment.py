"""One offline review fix; preserve the before plan. Never rerun."""
from pathlib import Path
import json,hashlib
p=Path('docs/superpowers/plans/2026-10-12-native-hh-symbolic-boundary.md');o=Path('diagnostics/simplex-core-architecture/results/S4-E');s=p.read_text()
def checks(t):
 return {'separate_owned_targets':'Separate owned B0/B1 CSC arrays per side' in t,'metadata_work_budget':'Exactly10 combined metadata extractions and10 graph summaries' in t,'reference_convention_stop':'reference-side scaling-convention mismatch' in t}
before=checks(s)
assert not any(before.values())
with (o/'boundary-plan-before-review.md').open('x') as f:f.write(s)
s=s.replace('All input values below are exact dyadics.','Separate owned B0/B1 CSC arrays per side are mandatory; no reference/candidate\narray sharing. Assert !Base.mightalias for colptr/rowval/nzval across both targets\nbefore the first refactor. Never give a sentinel-mutated target to the other side.\nAll input values below are exact dyadics.')
s=s.replace('No setup solves, HH extraction, workspace, public solver, updates,','Exactly10 combined metadata extractions and10 graph summaries are additional\ninspection entries outside the12+12+20 numerical budget and measured call scopes.\nEach metadata access uses the already-present successful numeric object; no new\nnumeric factorization is permitted. Zero metadata/graph entries for singular sides.\nNo setup solves, HH extraction, workspace, public solver, updates,')
s=s.replace('not a required bitwise match. Do not enlarge bounds after observing failure.','not a required bitwise match. Do not enlarge bounds after observing failure.\nThe installed wrapper passes C_NULL for do_recip. A reference-side scaling-convention mismatch\nis an oracle mismatch: preserve/stop, do not blame symbolic reuse or silently\nswitch multiplication to division. This fixed small-fixture bound is not a\ngeneral proof of the native scaling convention.')
after=checks(s);assert all(after.values());p.write_text(s)
r={'red_missing':sum(not v for v in before.values()),'green_checks':after,'all_passed':all(after.values()),'before_sha256':hashlib.sha256((o/'boundary-plan-before-review.md').read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'offline text RED/GREEN only; zero Julia calls; author regraded plan execution ambiguities Important'}
with (o/'plan-amendment.json').open('x') as f:json.dump(r,f,indent=2)
print(json.dumps(r))
