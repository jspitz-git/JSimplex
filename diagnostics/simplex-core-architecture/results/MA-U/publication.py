from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-U'
NAMES = ['diagnostics/simplex-core-architecture/MA-ROUNDING-GUARD-PREPARATION.md', 'diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-U/JULIA-LICENSE.md', 'diagnostics/simplex-core-architecture/results/MA-U/STATUS.md.before-MA-U', 'diagnostics/simplex-core-architecture/results/MA-U/author-fix.json', 'diagnostics/simplex-core-architecture/results/MA-U/author-fix.py', 'diagnostics/simplex-core-architecture/results/MA-U/candidate.jl', 'diagnostics/simplex-core-architecture/results/MA-U/closure.json', 'diagnostics/simplex-core-architecture/results/MA-U/closure.py', 'diagnostics/simplex-core-architecture/results/MA-U/continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-U/continuation.py', 'diagnostics/simplex-core-architecture/results/MA-U/entry.json', 'diagnostics/simplex-core-architecture/results/MA-U/entry.py', 'diagnostics/simplex-core-architecture/results/MA-U/fixtures.toml', 'diagnostics/simplex-core-architecture/results/MA-U/guard-tests.jl', 'diagnostics/simplex-core-architecture/results/MA-U/guard-tests.jl.before-author', 'diagnostics/simplex-core-architecture/results/MA-U/host.json', 'diagnostics/simplex-core-architecture/results/MA-U/instrumented.jl', 'diagnostics/simplex-core-architecture/results/MA-U/prepare.py', 'diagnostics/simplex-core-architecture/results/MA-U/publication.json', 'diagnostics/simplex-core-architecture/results/MA-U/publication.py', 'diagnostics/simplex-core-architecture/results/MA-U/reference.jl', 'diagnostics/simplex-core-architecture/results/MA-U/review.json', 'diagnostics/simplex-core-architecture/results/MA-U/review.md', 'diagnostics/simplex-core-architecture/results/MA-U/roadmap.md.before-MA-U', 'diagnostics/simplex-core-architecture/results/MA-U/source-check.py', 'diagnostics/simplex-core-architecture/results/MA-U/source-green.json', 'diagnostics/simplex-core-architecture/results/MA-U/source-map.json', 'diagnostics/simplex-core-architecture/results/MA-U/source-red.json', 'diagnostics/simplex-core-architecture/results/MA-U/tests.jl', 'diagnostics/simplex-core-architecture/results/MA-U/whitespace.json', 'diagnostics/simplex-core-architecture/results/MA-U/work-ledger.md', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
c=json.loads((D/'closure.json').read_text())
require(c['all_passed'] is True and all(sha(p)==v for p,v in c['sha256'].items()),'Closure failure/drift')
require(not git('diff','--cached','--name-only'),'Prior stage')
selfname=str((D/'publication.json').relative_to(R));tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(len(NAMES)==len(set(NAMES))==33,'Fixed33names')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope')
require(set(git('diff','--name-only','HEAD').splitlines())==tracked,'Tracked scope')
other=[n for n in NAMES if n!=selfname]
o=dict(all_passed=True,scope='Offline candidate preparation only; no numerical qualification or promotion',exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in other},git_blobs={n:git('hash-object','--',n) for n in other})
with (D/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Staged names')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Staged blob '+n)
w=json.loads((D/'whitespace.json').read_text())
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
require(r.returncode==2 and r.stdout==w['stdout'] and not r.stderr,'Only exact preserved whitespace warning allowed')
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(other),authored_diff_clean=True,preserved_raw_EOF_warning=1)))
