from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/MA-Q'
NAMES=[
 'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PLAN.md',
 'diagnostics/simplex-core-architecture/STATUS.md',
 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',
 'docs/superpowers/plans/2026-10-14-ma-denselu-bigfloat.md',
 'docs/superpowers/specs/2026-10-14-ma-denselu-bigfloat-design.md',
 'diagnostics/simplex-core-architecture/results/MA-Q/STATUS.md.before-MA-Q',
 'diagnostics/simplex-core-architecture/results/MA-Q/STATUS.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-Q/closure.py',
 'diagnostics/simplex-core-architecture/results/MA-Q/closure.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/complete-plan.py',
 'diagnostics/simplex-core-architecture/results/MA-Q/completion-check.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/completion-map.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/continuation-map.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/host.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/report.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-Q/review.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/review.md',
 'diagnostics/simplex-core-architecture/results/MA-Q/roadmap.md.before-MA-Q',
 'diagnostics/simplex-core-architecture/results/MA-Q/roadmap.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-Q/source-check.json',
 'diagnostics/simplex-core-architecture/results/MA-Q/source-check.py',
 'diagnostics/simplex-core-architecture/results/MA-Q/publication.py',
 'diagnostics/simplex-core-architecture/results/MA-Q/publication.json',
]
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise SystemExit(msg)
closure=json.loads((E/'closure.json').read_text())
require(closure['all_passed'] is True,'Closure not PASS')
require(all(sha(p)==h for p,h in closure['sha256'].items()),'Closure hash drift')
require(not git('diff','--cached','--name-only'),'Preexisting staged change')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==set(NAMES)-{'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','diagnostics/simplex-core-architecture/results/MA-Q/publication.json'}|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope mismatch')
others=[n for n in NAMES if n!='diagnostics/simplex-core-architecture/results/MA-Q/publication.json']
obj={'all_passed':True,'checks':{'closure_pass_and_all_bindings':True,'no_prior_staged':True,'exact_untracked_scope':True},'exact_names':NAMES,'sha256':{str(R/n):sha(R/n) for n in others},'git_blobs':{n:git('hash-object','--',n) for n in others},'scope':'Fixed complete 23 names. Publication self blob is checked against working bytes in staged verification and postcommit, not self-hashed here.'}
with (E/'publication.json').open('x') as out:json.dump(obj,out,indent=2);out.write('\n')
subprocess.run(['git','add','--',*NAMES],cwd=R,check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Staged names mismatch')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Staged blob mismatch: '+n)
subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
print(json.dumps({'closure':True,'exact_staged_names_blobs':len(NAMES),'listed_sha256':len(others),'staged_diff_clean':True}))
