from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-T'
NAMES = ['diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-T/STATUS.before-review', 'diagnostics/simplex-core-architecture/results/MA-T/STATUS.md.before-MA-T', 'diagnostics/simplex-core-architecture/results/MA-T/closure.json', 'diagnostics/simplex-core-architecture/results/MA-T/closure.py', 'diagnostics/simplex-core-architecture/results/MA-T/continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-T/continuation.py', 'diagnostics/simplex-core-architecture/results/MA-T/entry.json', 'diagnostics/simplex-core-architecture/results/MA-T/entry.py', 'diagnostics/simplex-core-architecture/results/MA-T/host.json', 'diagnostics/simplex-core-architecture/results/MA-T/plan.before-review', 'diagnostics/simplex-core-architecture/results/MA-T/publication.json', 'diagnostics/simplex-core-architecture/results/MA-T/publication.py', 'diagnostics/simplex-core-architecture/results/MA-T/review-final.json', 'diagnostics/simplex-core-architecture/results/MA-T/review-final.md', 'diagnostics/simplex-core-architecture/results/MA-T/review-fix.json', 'diagnostics/simplex-core-architecture/results/MA-T/review-fix.py', 'diagnostics/simplex-core-architecture/results/MA-T/review.json', 'diagnostics/simplex-core-architecture/results/MA-T/review.md', 'diagnostics/simplex-core-architecture/results/MA-T/roadmap.before-review', 'diagnostics/simplex-core-architecture/results/MA-T/roadmap.md.before-MA-T', 'diagnostics/simplex-core-architecture/results/MA-T/source.json', 'diagnostics/simplex-core-architecture/results/MA-T/source.py', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md', 'docs/superpowers/plans/2026-10-14-ma-rounding-guard.md', 'docs/superpowers/specs/2026-10-14-ma-rounding-guard-design.md']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
c=json.loads((D/'closure.json').read_text())
require(c['all_passed'] is True and all(sha(p)==v for p,v in c['sha256'].items()),'Closure failure/drift')
require(not git('diff','--cached','--name-only'),'Prior staging')
selfname=str((D/'publication.json').relative_to(R));tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(len(NAMES)==len(set(NAMES))==26,'Fixed26 names')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope')
require(set(git('diff','--name-only','HEAD').splitlines())==tracked,'Tracked scope')
other=[n for n in NAMES if n!=selfname]
o=dict(all_passed=True,scope='Plan only; no numerical qualification or candidate promotion',exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in other},git_blobs={n:git('hash-object','--',n) for n in other})
with (D/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Staged names')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Staged blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(other),diff_clean=True)))
