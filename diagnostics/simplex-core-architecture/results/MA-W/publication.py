from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-W'
NAMES = ['diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-W/STATUS.md.before-MA-W', 'diagnostics/simplex-core-architecture/results/MA-W/closure.json', 'diagnostics/simplex-core-architecture/results/MA-W/closure.py', 'diagnostics/simplex-core-architecture/results/MA-W/continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-W/continuation.json', 'diagnostics/simplex-core-architecture/results/MA-W/continuation.py', 'diagnostics/simplex-core-architecture/results/MA-W/entry.json', 'diagnostics/simplex-core-architecture/results/MA-W/entry.py', 'diagnostics/simplex-core-architecture/results/MA-W/evidence.json', 'diagnostics/simplex-core-architecture/results/MA-W/evidence.py', 'diagnostics/simplex-core-architecture/results/MA-W/host.json', 'diagnostics/simplex-core-architecture/results/MA-W/publication-names.json', 'diagnostics/simplex-core-architecture/results/MA-W/publication.json', 'diagnostics/simplex-core-architecture/results/MA-W/publication.py', 'diagnostics/simplex-core-architecture/results/MA-W/review-check.json', 'diagnostics/simplex-core-architecture/results/MA-W/review-check.py', 'diagnostics/simplex-core-architecture/results/MA-W/review.json', 'diagnostics/simplex-core-architecture/results/MA-W/review.md', 'diagnostics/simplex-core-architecture/results/MA-W/roadmap.md.before-MA-W', 'diagnostics/simplex-core-architecture/results/MA-W/work-ledger.md', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md', 'docs/superpowers/plans/2026-10-14-ma-denselu-complete-qualification.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
c=json.loads((D/'closure.json').read_text())
require(c['all_passed'] is True and all(sha(p)==v for p,v in c['sha256'].items()),'closure')
require(not git('diff','--cached','--name-only'),'prior stage')
selfname=str((D/'publication.json').relative_to(R));tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(NAMES==json.loads((D/'publication-names.json').read_text()) and len(NAMES)==len(set(NAMES)),'fixed names')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'untracked scope')
require(set(git('diff','--name-only','HEAD').splitlines())==tracked,'tracked scope')
other=[n for n in NAMES if n!=selfname]
o=dict(all_passed=True,scope='MA-W source/design only, no executable admission or new numerical run',exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in other},git_blobs={n:git('hash-object','--',n) for n in other})
with (D/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'staged names')
require(all(git('rev-parse',':'+n)==git('hash-object','--',n) for n in NAMES),'staged blobs')
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
require(r.returncode==0 and not r.stdout and not r.stderr,'diff check '+r.stdout+r.stderr)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(other),diff_clean=True)))
