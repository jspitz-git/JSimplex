from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
NAMES=[
 'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-ADMISSION-PREPARATION.md',
 'diagnostics/simplex-core-architecture/STATUS.md',
 'diagnostics/simplex-core-architecture/results/MA-S/STATUS.md.before-MA-S',
 'diagnostics/simplex-core-architecture/results/MA-S/STATUS.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-S/admission-review-final.json',
 'diagnostics/simplex-core-architecture/results/MA-S/admission-review-final.md',
 'diagnostics/simplex-core-architecture/results/MA-S/admission-review.json',
 'diagnostics/simplex-core-architecture/results/MA-S/admission-review.md',
 'diagnostics/simplex-core-architecture/results/MA-S/admission-reviewed.md',
 'diagnostics/simplex-core-architecture/results/MA-S/admission.md',
 'diagnostics/simplex-core-architecture/results/MA-S/audit.py',
 'diagnostics/simplex-core-architecture/results/MA-S/audit_reviewed.py',
 'diagnostics/simplex-core-architecture/results/MA-S/closure.json',
 'diagnostics/simplex-core-architecture/results/MA-S/closure.py',
 'diagnostics/simplex-core-architecture/results/MA-S/commands.json',
 'diagnostics/simplex-core-architecture/results/MA-S/complete-step.py',
 'diagnostics/simplex-core-architecture/results/MA-S/completion-check.json',
 'diagnostics/simplex-core-architecture/results/MA-S/completion-map.json',
 'diagnostics/simplex-core-architecture/results/MA-S/continuation-map.json',
 'diagnostics/simplex-core-architecture/results/MA-S/deferred-minor.md',
 'diagnostics/simplex-core-architecture/results/MA-S/driver.jl',
 'diagnostics/simplex-core-architecture/results/MA-S/guard.py',
 'diagnostics/simplex-core-architecture/results/MA-S/host.json',
 'diagnostics/simplex-core-architecture/results/MA-S/launcher-reviewed.py',
 'diagnostics/simplex-core-architecture/results/MA-S/launcher.py',
 'diagnostics/simplex-core-architecture/results/MA-S/ledger.md',
 'diagnostics/simplex-core-architecture/results/MA-S/ledger.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-S/offline-tests-reviewed.json',
 'diagnostics/simplex-core-architecture/results/MA-S/offline-tests-reviewed.py',
 'diagnostics/simplex-core-architecture/results/MA-S/offline-tests.json',
 'diagnostics/simplex-core-architecture/results/MA-S/offline-tests.py',
 'diagnostics/simplex-core-architecture/results/MA-S/pins-reviewed.json',
 'diagnostics/simplex-core-architecture/results/MA-S/pins.json',
 'diagnostics/simplex-core-architecture/results/MA-S/preparation-check.json',
 'diagnostics/simplex-core-architecture/results/MA-S/prepare-pins-reviewed.py',
 'diagnostics/simplex-core-architecture/results/MA-S/prepare-pins.py',
 'diagnostics/simplex-core-architecture/results/MA-S/publication.json',
 'diagnostics/simplex-core-architecture/results/MA-S/publication.py',
 'diagnostics/simplex-core-architecture/results/MA-S/report.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-S/required-paths-reviewed.json',
 'diagnostics/simplex-core-architecture/results/MA-S/required-paths.json',
 'diagnostics/simplex-core-architecture/results/MA-S/review-fix-check.json',
 'diagnostics/simplex-core-architecture/results/MA-S/review-fix-red.json',
 'diagnostics/simplex-core-architecture/results/MA-S/review-fix.py',
 'diagnostics/simplex-core-architecture/results/MA-S/roadmap.md.before-MA-S',
 'diagnostics/simplex-core-architecture/results/MA-S/roadmap.md.before-completion',
 'diagnostics/simplex-core-architecture/results/MA-S/source-check.json',
 'diagnostics/simplex-core-architecture/results/MA-S/source-check.py',
 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(ok,msg):
 if not ok:raise SystemExit(msg)
c=json.loads((E/'closure.json').read_text())
require(c['all_passed'] is True and all(sha(p)==s for p,s in c['sha256'].items()),'Closure drift/failure')
require(not git('diff','--cached','--name-only'),'Preexisting stage')
selfname='diagnostics/simplex-core-architecture/results/MA-S/publication.json'
tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(len(NAMES)==49 and len(set(NAMES))==49,'Expected49')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Unexpected untracked files')
others=[n for n in NAMES if n!=selfname]
obj=dict(all_passed=True,checks={'closure26_pass46bindings':True,'no_prior_stage':True,'exact_untracked_scope':True},exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in others},git_blobs={n:git('hash-object','--',n) for n in others},scope='Fixed49complete names. Publication self checked at stage/commit, no self hash. Preparation only, no launch.')
with (E/'publication.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Wrong staged names')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Wrong staged blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(others),diff_clean=True,closure_pass=True)))
