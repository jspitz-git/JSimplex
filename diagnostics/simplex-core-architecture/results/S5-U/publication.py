"""Exclusive fail-fast staging and exact blob publication checks after PASS closure."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';H=D/'results/S5-U';M=Path('/home/jspitz/JSimplex.jl')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(*args):return subprocess.check_output(['git',*args],text=True)
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
closure=json.loads((H/'closure.json').read_text());assert closure['all_passed'] is True and all(x is True for x in closure['checks'].values())
assert all(sha(k)==v for k,v in closure['sha256'].items())
assert not run('diff','--cached','--name-only').strip()
paths=[H,D/'STATUS.md',D/'S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION.md',D/'S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-ownership-contract.md']
expected={str(p.relative_to(R)) for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file()}
subprocess.run(['git','add','--',*[str(p.relative_to(R)) for p in paths]],check=True)
check=subprocess.run(['git','diff','--cached','--check'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
with (H/'publication-diffcheck.txt').open('x') as f:f.write(check.stdout)
assert check.returncode==0,check.stdout
names=set(run('diff','--cached','--name-only').splitlines());assert names==expected
blobs={k:hashlib.sha256(subprocess.check_output(['git','show',':'+k])).hexdigest() for k in sorted(names)};assert all(sha(R/k)==v for k,v in blobs.items())
checks=dict(closure_PASS=True,closure_all_bindings_unchanged=True,exact_staged_names=True,exact_staged_blobs=True,authored_diffcheck=True,test_already_integrated=run('diff','master','--','src','test','.github','Project.toml')=='')
assert all(checks.values());dump(H/'publication-check.json',dict(checks=checks,all_passed=True,closure_sha256=sha(H/'closure.json'),staged_count_before_records=len(names)))
for p in (H/'publication-diffcheck.txt',H/'publication-check.json'):subprocess.run(['git','add','--',str(p.relative_to(R))],check=True)
names=set(run('diff','--cached','--name-only').splitlines());blobs={k:hashlib.sha256(subprocess.check_output(['git','show',':'+k])).hexdigest() for k in sorted(names)};assert all(sha(R/k)==v for k,v in blobs.items())
record=H/'staged-files.json';dump(record,dict(sha256=blobs,scope='Exact complete staged paths except this self record; self blob separately verified before commit.'))
subprocess.run(['git','add','--',str(record.relative_to(R))],check=True)
actual=set(run('diff','--cached','--name-only').splitlines());assert actual==names|{str(record.relative_to(R))}
assert all(hashlib.sha256(subprocess.check_output(['git','show',':'+k])).hexdigest()==sha(R/k) for k in actual)
subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps(dict(checks=checks,exact_complete_staged_files=len(actual))))
