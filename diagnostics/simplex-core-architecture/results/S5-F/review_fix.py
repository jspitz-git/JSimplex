from pathlib import Path
import hashlib,json,textwrap
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S5-F'
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
old=(o/'driver.jl').read_text();new=(o/'driver-reviewed.jl').read_text()
tokens=['stop_flag=flag[]','returned_type=string(typeof(returned))','caught_type=string(typeof(caught))','cause_identity=caught isa','sentinel_identity=identity_token(sentinel)','ambient_after=(precision=precision(BigFloat)','scalar_type=string(eltype(ws.costs))']
red={t:t in old for t in tokens};green={t:t in new for t in tokens}
e=json.loads((o/'evidence.json').read_text());i=json.loads((o/'independent.json').read_text())
remap={'diagnostics/simplex-core-architecture/S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER.md':o/'report-before-review.md','docs/superpowers/plans/2026-10-13-precision-journal-interruption-qualification.md':o/'qualification-plan-before-review.md'}
fixture=lambda s:s.split('    # BEGIN EXISTING FIXTURE')[1].split('    # END EXISTING FIXTURE')[0]
callback=lambda s:s.split('    observer=(reason,trial)->begin')[1].split('    stop=()->begin')[0]
checks={'RED_seven_missing':not any(red.values()),'GREEN_seven_present':all(green.values()),'initial170_unchanged':all(sha(p)==h for p,h in e['sha256'].items()),'initial_five_artifacts_reconciled':all(sha(remap.get(p,r/p))==h for p,h in i['sha256'].items()),'fixture_callback_unchanged':fixture(old)==fixture(new) and callback(old)==callback(new),'same_three_captures':old.count('=snapshot(')==new.count('=snapshot(')==3,'same_two_cases':new.count('for mode in (:stop,:throw)')==1 and new.count('JS.transfer_precision(')==1,'raw_saved':all(t in new for t in ['observed_outcome=observed_outcome','ambient_after=ambient_after','metadata=(workspace=identity_token(ws),scalar_type=']), 'scoped_import_wording':'Ordinary import/initialization workload\nremains unqualified' in (r/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-qualification.md').read_text()}
paths=set(map(Path,e['sha256']));paths.update([o/'driver-reviewed.jl',o/'review_fix.py',o/'report-before-review.md',o/'qualification-plan-before-review.md',d/'S5-PRECISION-JOURNAL-INTERRUPTION-DRIVER.md',r/'docs/superpowers/plans/2026-10-13-precision-journal-interruption-qualification.md'])
pins={str(p):sha(p) for p in sorted(paths)}
with (o/'source-pins-reviewed.toml').open('x') as f:
 f.write('[sha256]\n');f.writelines(json.dumps(p)+' = '+json.dumps(h)+'\n' for p,h in pins.items())
with (o/'review-fix.json').open('x') as f:json.dump(dict(checks=checks,all_passed=all(checks.values()),RED=red,GREEN=green,sha256=pins,manifest_sha256=sha(o/'source-pins-reviewed.toml')),f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pins':len(pins),'all_passed':all(checks.values())}));assert all(checks.values())
