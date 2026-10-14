from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK'
NAMES = ['diagnostics/simplex-core-architecture/MA-DENSELU-FALLBACK-ALLOCATION-ANALYSIS.md', 'diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/STATUS.md.before-MA-S-FALLBACK', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/analysis.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/analyze.py', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/closure.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/closure.py', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/continuation.py', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/entry.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/entry.py', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/host.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/ledger.md', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/publication.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/publication.py', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/review.json', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/review.md', 'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK/roadmap.md.before-MA-S-FALLBACK', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
c=json.loads((D/'closure.json').read_text())
require(c['all_passed'] is True and c['no_new_numerics'] is True and all(sha(p)==s for p,s in c['sha256'].items()),'Closure failure/drift')
require(not git('diff','--cached','--name-only'),'Prior stage')
selfname=str((D/'publication.json').relative_to(R));tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(len(NAMES)==19 and len(set(NAMES))==19,'Fixed19')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope')
require(set(git('diff','--name-only','HEAD').splitlines())==tracked,'Tracked scope')
others=[n for n in NAMES if n!=selfname]
o=dict(all_passed=True,no_new_numerics=True,checks={'closure_pass':True,'no_prior_stage':True,'exact_untracked_scope':True,'exact_tracked_scope':True},exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in others},git_blobs={n:git('hash-object','--',n) for n in others},scope='Fixed19names/18listed hashes, self checked at stage/commit. Source/stored-evidence only.')
with (D/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Staged names')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Staged blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(others),diff_clean=True,no_new_numerics=True)))
