"""One fail-closed exact diagnostic publication; no Julia, commit or push here."""
from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
N=['ADMISSION.md', 'ADMISSION.md.after-rendering-fix', 'ADMISSION.md.before-review', 'REPORT.md', 'REPORT.md.after-rendering-fix', 'REPORT.md.before-review', 'adapted-files.json', 'audit.py', 'baseline.json', 'bind-final.py', 'closure.json', 'closure.py', 'control.py', 'copied-files.json', 'driver.jl', 'environment.json', 'final-mappings.json', 'final-prepare.py', 'guard.py', 'historical-groups.json', 'host-entry.json', 'launch.py', 'loaded-paths.json', 'oracle.py', 'oracle.py.before-review', 'outer.py', 'pin-preparation.py', 'post-return.py', 'preparation-pins.json', 'preparation-pins.json.before-final-mapping', 'preparation-pins.json.before-review', 'prepare.py', 'progress.md.after-p011-harness', 'progress.md.before-p011-harness', 'publication.json', 'publication.py', 'recorder.jl', 'required-paths.json', 'required-paths.json.before-final-mapping', 'required-paths.json.before-review', 'review-fix-2.py', 'review-fix-check.json', 'review-fix-failure.json', 'review-fix-provenance.json', 'review-fix.py', 'review.json', 'review.json.before-review', 'review.md', 'review.md.before-review', 'reviewer-checks.py', 'reviewer-regression-results.json', 'reviewer-regression.py', 'reviewer-results.json', 'runtime-inputs-complete.json', 'seal.py', 'source-check.json', 'stages.json', 'supervisor.py', 'tests-reviewed.json', 'tests-reviewed.py', 'tests.json', 'tests.py', 'verify-preparation.py']
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,m):
 if not v:raise RuntimeError(m)
v=json.loads((D/'closure.json').read_text())
require(v['all_passed'] is True and all(v['checks'].values()),'PASS closure')
require(all(sha(n)==h for n,h in v['sha256'].items()),'Closure input drift')
require(git('rev-parse','HEAD')=='42ebde242bf900cec375f970982f97469f013559','Entry HEAD')
require(git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205','Master')
require(git('diff','--name-only')=='' and git('diff','--cached','--name-only')=='','Tracked/index changes')
require(sorted(p.name for p in D.iterdir())==sorted(set(N)-{'publication.json'}),'Exact directory roster')
require(all((D/n).is_file() and not (D/n).is_symlink() for n in N if n!='publication.json'),'Regular exact inputs')
paths=[str((D/n).relative_to(R)) for n in N]
with (D/'publication.json').open('x') as f:
 json.dump(dict(scope='Offline P011 RED/GREEN harness only; no runtime or production change',closure_passed=True,exact_names=paths,listed_blobs={p:git('hash-object',p) for p in paths if p!=str((D/'publication.json').relative_to(R))}),f,indent=2);f.write('\n')
git('add','--',*paths)
require(sorted(git('diff','--cached','--name-only').splitlines())==sorted(paths),'Exact staged names')
diff=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
require(diff.returncode==0 and diff.stdout==diff.stderr=='','Authored and copied whitespace clean')
expected={p:git('hash-object',p) for p in paths}
require(all(git('rev-parse',':'+p)==b for p,b in expected.items()),'Exact staged blobs')
receipt=Path('/tmp/p011-typed-harness-exact-staged-blobs.json')
with receipt.open('x') as f:json.dump(expected,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,exact_staged_names_and_blobs=len(paths),listed_blobs=len(paths)-1,receipt=str(receipt))))
