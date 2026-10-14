from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S'
NAMES = ['diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-QUALIFICATION.md', 'diagnostics/simplex-core-architecture/STATUS.md', 'diagnostics/simplex-core-architecture/results/MA-S/STATUS.md.before-MA-S-execution', 'diagnostics/simplex-core-architecture/results/MA-S/audit-1.json', 'diagnostics/simplex-core-architecture/results/MA-S/execution-closure.json', 'diagnostics/simplex-core-architecture/results/MA-S/execution-closure.py', 'diagnostics/simplex-core-architecture/results/MA-S/execution-continuation-map.json', 'diagnostics/simplex-core-architecture/results/MA-S/execution-entry.json', 'diagnostics/simplex-core-architecture/results/MA-S/execution-entry.py', 'diagnostics/simplex-core-architecture/results/MA-S/execution-ledger.md', 'diagnostics/simplex-core-architecture/results/MA-S/execution-postcheck.json', 'diagnostics/simplex-core-architecture/results/MA-S/execution-postcheck.py', 'diagnostics/simplex-core-architecture/results/MA-S/execution-publication.json', 'diagnostics/simplex-core-architecture/results/MA-S/execution-publication.py', 'diagnostics/simplex-core-architecture/results/MA-S/invocation-1.json', 'diagnostics/simplex-core-architecture/results/MA-S/launch-context.json', 'diagnostics/simplex-core-architecture/results/MA-S/launcher-1.log', 'diagnostics/simplex-core-architecture/results/MA-S/numerical-review.json', 'diagnostics/simplex-core-architecture/results/MA-S/numerical-review.md', 'diagnostics/simplex-core-architecture/results/MA-S/posthost-1.json', 'diagnostics/simplex-core-architecture/results/MA-S/prelaunch-1.json', 'diagnostics/simplex-core-architecture/results/MA-S/reservation-1.json', 'diagnostics/simplex-core-architecture/results/MA-S/result-review.json', 'diagnostics/simplex-core-architecture/results/MA-S/result-review.md', 'diagnostics/simplex-core-architecture/results/MA-S/roadmap.md.before-MA-S-execution', 'diagnostics/simplex-core-architecture/results/MA-S/run-1/current.json', 'diagnostics/simplex-core-architecture/results/MA-S/run-1/pins.json', 'diagnostics/simplex-core-architecture/results/MA-S/run-1/process.json', 'diagnostics/simplex-core-architecture/results/MA-S/run-1/raw.toml', 'diagnostics/simplex-core-architecture/results/MA-S/run-1/resources.jsonl', 'diagnostics/simplex-core-architecture/results/MA-S/run-1/run.log', 'diagnostics/simplex-core-architecture/results/MA-S/sequence-execution.log', 'diagnostics/simplex-core-architecture/results/MA-S/sequence-reservation.json', 'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(v,m):
 if not v:raise SystemExit(m)
c=json.loads((E/'execution-closure.json').read_text())
require(c['all_passed'] is True and c['qualification_accepted'] is False and all(sha(p)==s for p,s in c['sha256'].items()),'Closure failed/drift')
require(not git('diff','--cached','--name-only'),'Prior stage')
selfname='diagnostics/simplex-core-architecture/results/MA-S/execution-publication.json'
tracked={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
require(len(NAMES)==34 and len(set(NAMES))==34,'Expected34')
require(set(git('ls-files','--others','--exclude-standard').splitlines())==(set(NAMES)-tracked-{selfname})|{'Manifest.toml','LocalPreferences.toml'},'Untracked scope')
require(set(git('diff','--name-only','HEAD').splitlines())==tracked,'Tracked scope')
others=[n for n in NAMES if n!=selfname]
o=dict(all_passed=True,qualification_accepted=False,checks={'closure_pass':True,'no_prior_stage':True,'exact_untracked_scope':True,'exact_tracked_scope':True},exact_names=NAMES,sha256={str(R/n):sha(R/n) for n in others},git_blobs={n:git('hash-object','--',n) for n in others},scope='Fixed34names;33listedhashes. Self staged/committed blob verified externally. Diagnostic failed qualification only.')
with (E/'execution-publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*NAMES],check=True)
require(set(git('diff','--cached','--name-only').splitlines())==set(NAMES),'Stage names')
for n in NAMES:require(git('rev-parse',':'+n)==git('hash-object','--',n),'Stage blob '+n)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(exact_staged_names_blobs=len(NAMES),listed_hashes=len(others),diff_clean=True,diagnostic_closure_pass=True,numerical_qualification=False)))
