from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/MA-R'
NAMES=[
 'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PREPARATION.md',
 'diagnostics/simplex-core-architecture/STATUS.md',
 'diagnostics/simplex-core-architecture/results/MA-R/JULIA-LICENSE.md',
 'diagnostics/simplex-core-architecture/results/MA-R/MA-DENSELU-BIGFLOAT-PREPARATION.md.before-review-fix',
 'diagnostics/simplex-core-architecture/results/MA-R/STATUS.md.before-MA-R',
 'diagnostics/simplex-core-architecture/results/MA-R/STATUS.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-R/candidate.jl',
 'diagnostics/simplex-core-architecture/results/MA-R/closure.json',
 'diagnostics/simplex-core-architecture/results/MA-R/closure.py',
 'diagnostics/simplex-core-architecture/results/MA-R/complete-step.py',
 'diagnostics/simplex-core-architecture/results/MA-R/completion-check.json',
 'diagnostics/simplex-core-architecture/results/MA-R/completion-host.json',
 'diagnostics/simplex-core-architecture/results/MA-R/completion-map.json',
 'diagnostics/simplex-core-architecture/results/MA-R/continuation-map.json',
 'diagnostics/simplex-core-architecture/results/MA-R/environment/Manifest.toml',
 'diagnostics/simplex-core-architecture/results/MA-R/environment/Project.toml',
 'diagnostics/simplex-core-architecture/results/MA-R/fixtures.toml',
 'diagnostics/simplex-core-architecture/results/MA-R/fixtures.toml.before-review-fix',
 'diagnostics/simplex-core-architecture/results/MA-R/host.json',
 'diagnostics/simplex-core-architecture/results/MA-R/instrumented.jl',
 'diagnostics/simplex-core-architecture/results/MA-R/ledger.md',
 'diagnostics/simplex-core-architecture/results/MA-R/ledger.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-R/ledger.md.before-review-fix',
 'diagnostics/simplex-core-architecture/results/MA-R/plan.md',
 'diagnostics/simplex-core-architecture/results/MA-R/plan.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-R/plan.md.before-review-fix',
 'diagnostics/simplex-core-architecture/results/MA-R/prepare.py',
 'diagnostics/simplex-core-architecture/results/MA-R/publication.json',
 'diagnostics/simplex-core-architecture/results/MA-R/publication.py',
 'diagnostics/simplex-core-architecture/results/MA-R/reference.jl',
 'diagnostics/simplex-core-architecture/results/MA-R/report.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-R/review-amendment.json',
 'diagnostics/simplex-core-architecture/results/MA-R/review-amendment.md',
 'diagnostics/simplex-core-architecture/results/MA-R/review-final.json',
 'diagnostics/simplex-core-architecture/results/MA-R/review-final.md',
 'diagnostics/simplex-core-architecture/results/MA-R/review-fix-map.json',
 'diagnostics/simplex-core-architecture/results/MA-R/review-fix.json',
 'diagnostics/simplex-core-architecture/results/MA-R/review-fix.py',
 'diagnostics/simplex-core-architecture/results/MA-R/review.json',
 'diagnostics/simplex-core-architecture/results/MA-R/review.md',
 'diagnostics/simplex-core-architecture/results/MA-R/roadmap.md.before-MA-R',
 'diagnostics/simplex-core-architecture/results/MA-R/roadmap.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-R/source-check.json',
 'diagnostics/simplex-core-architecture/results/MA-R/source-check.py',
 'diagnostics/simplex-core-architecture/results/MA-R/source-map.json',
 'diagnostics/simplex-core-architecture/results/MA-R/tests.jl',
 'diagnostics/simplex-core-architecture/results/MA-R/tests.jl.before-review-fix',
 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def require(ok,msg):
 if not ok:raise SystemExit(msg)
closure=json.loads((E/'closure.json').read_text())
require(closure['all_passed'] is True,'Closure not PASS')
require(all(sha(p)==h for p,h in closure['sha256'].items()),'Closure drift')
require(not git('diff','--cached','--name-only'),'Preexisting staged change')
tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
selfname='diagnostics/simplex-core-architecture/results/MA-R/publication.json'
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope mismatch')
require(len(NAMES)==48 and len(set(NAMES))==48,'Expected48names')
warning='diagnostics/simplex-core-architecture/results/MA-R/instrumented.jl:34: new blank line at EOF.\n'
others=[n for n in NAMES if n!=selfname]
obj={'all_passed':True,'checks':{'closure19_PASS45bindings':True,'no_prior_staged':True,'exact_untracked_scope':True},'exact_names':NAMES,'sha256':{str(R/n):sha(R/n) for n in others},'git_blobs':{n:git('hash-object','--',n) for n in others},'preserved_whitespace':{'expected':warning,'reason':'Frozen exact inverse instrumentation ends in one blank line; retain reviewed bytes rather than rewrite accepted evidence. No other whitespace exception.','sha256':sha(E/'instrumented.jl')},'scope':'Fixed complete48names. Publication self blob is checked in staged and committed verification. Original default diff warning must match exactly; all other whitespace checks pass.'}
with (E/'publication.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Staged names mismatch')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Staged blob mismatch '+n)
diff=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
require(diff.stdout==warning and not diff.stderr and diff.returncode!=0,'Unexpected default whitespace diagnostics')
subprocess.run(['git','-c','core.whitespace=-blank-at-eof','diff','--cached','--check'],check=True)
print(json.dumps({'closure_pass':True,'exact_staged_names_blobs':len(NAMES),'listed_hashes':len(others),'only_preserved_instrumentation_EOF_warning':True,'default_diff_check_exit':diff.returncode,'other_whitespace_clean':True}))
