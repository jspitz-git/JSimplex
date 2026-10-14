from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK'
NAMES = ['diagnostics/simplex-core-architecture/MA-DENSELU-COMPLETE-FALLBACK-ANALYSIS.md', 'diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/STATUS.md.before-MA-Y-FALLBACK', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/analysis.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/analyze.py', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/closure.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/closure.py', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/continuation.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/continuation.py', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/entry.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/entry.py', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/host.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/publication-names.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/publication.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/publication.py', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/review-check.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/review-check.py', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/review.initial-cs.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/review.initial-cs.md', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/review.json', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/review.md', 'diagnostics/simplex-core-architecture/results/MA-Y-FALLBACK/roadmap.md.before-MA-Y-FALLBACK', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
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
o=dict(all_passed=True,scope='MA-Y-FALLBACK stored-result/source analysis only; no new measurement; qualification remains rejected',exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in other},git_blobs={n:git('hash-object','--',n) for n in other})
with (D/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'staged names')
require(all(git('rev-parse',':'+n)==git('hash-object','--',n) for n in NAMES),'staged blobs')
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
require(r.returncode==0 and not r.stdout and not r.stderr,'diff check '+r.stdout+r.stderr)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(other),diff_clean=True)))
