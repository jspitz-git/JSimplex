from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S-2'
NAMES = ['diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-SECOND-ADMISSION.md', 'diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-S-2/STATUS.md.before-MA-S-2', 'diagnostics/simplex-core-architecture/results/MA-S-2/admission-review.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/admission-review.md', 'diagnostics/simplex-core-architecture/results/MA-S-2/admission.md', 'diagnostics/simplex-core-architecture/results/MA-S-2/audit.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/closure.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/closure.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/commands.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/entry.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/entry.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/freeze-check.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/freeze.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/guard.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/host.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/launcher.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/ledger.md', 'diagnostics/simplex-core-architecture/results/MA-S-2/offline-tests.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/offline-tests.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/pins.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/preparation-failure.txt', 'diagnostics/simplex-core-architecture/results/MA-S-2/prepare-2.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/prepare.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/publication.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/publication.py', 'diagnostics/simplex-core-architecture/results/MA-S-2/required-paths.json', 'diagnostics/simplex-core-architecture/results/MA-S-2/roadmap.md.before-MA-S-2', 'diagnostics/simplex-core-architecture/results/MA-S-2/source-check.json', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
c=json.loads((E/'closure.json').read_text())
require(c['all_passed'] is True and c['runtime_qualified'] is False and all(sha(p)==s for p,s in c['sha256'].items()),'Closure failure/drift')
require(not git('diff','--cached','--name-only'),'Prior stage')
selfname='diagnostics/simplex-core-architecture/results/MA-S-2/publication.json'
tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(len(NAMES)==31 and len(set(NAMES))==31,'Expected31')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope')
require(set(git('diff','--name-only','HEAD').splitlines())==tracked,'Tracked scope')
others=[n for n in NAMES if n!=selfname]
o=dict(all_passed=True,runtime_qualified=False,checks={'closure_pass':True,'no_prior_stage':True,'exact_untracked_scope':True,'exact_tracked_scope':True},exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in others},git_blobs={n:git('hash-object','--',n) for n in others},scope='Fixed31names/30listedhashes. Self checked at stage/commit. Preparation only.')
with (E/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Wrong staged names')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Wrong staged blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(others),diff_clean=True,offline_only=True)))
