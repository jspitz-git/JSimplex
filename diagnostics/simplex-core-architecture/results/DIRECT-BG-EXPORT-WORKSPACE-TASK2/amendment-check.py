"""Independent author supplement: preserve original checker, verify actual before hashes."""
from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-export-workspace/reproduce'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
a=json.loads((E/'source-check.json').read_text());v=json.loads((E/'review.json').read_text());lin=json.loads((E/'lineage.json').read_text());mapping=lin['before_mapping']
def verify(bindings):return all(sha(mapping.get(p,p))==h for p,h in bindings.items())
checks=dict(actual_all_original_author_hashes=verify(a['readtime_sha256']),actual_all_initial_reviewer_hashes=verify(v['readtime_sha256']),exactly_four_before_copies=len(mapping)==4 and all(a['readtime_sha256'][p]==sha(before) for p,before in mapping.items()),all_lineage_current_and_before=all(sha(p)==h for p,h in lin['sha256'].items()),task1_unchanged=all(sha(p)==h for p,h in json.loads((C/'overlay-manifest.json').read_text())['candidate_task1_frozen'].items()))
paths=set(a['readtime_sha256'])|set(v['readtime_sha256'])|set(lin['sha256'])|{str(E/n) for n in ('review-fix.json','lineage.json','amendment-check.py')}
out=dict(all_passed=all(checks.values()),checks=checks,readtime_sha256={p:sha(p) for p in sorted(paths)},note='review-fix green all_original_bytes_preserved used a vacuous empty-generator branch; it is NOT preservation evidence. This separate actual hash verification supersedes only that proof claim, preserving original script and result. No old checker or Julia rerun.')
with (E/'amendment-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),hashes=len(paths))))
if not out['all_passed']:raise SystemExit(1)
