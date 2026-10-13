"""Exact complete publication check before commit; no numerical execution."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F-repair';prefix=str(D.relative_to(R))+'/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
names=read(D/'publication-names.json');closure=read(D/'closure.json');inputs=[n for n in names if n!=prefix+'publication.json'];checks={}
checks['closure_PASS']=closure['all_passed'] is True and all(closure['checks'].values())
checks['closure_bindings']=all(sha(R/p)==v for p,v in closure['sha256'].items())
checks['explicit_unique_names']=names==sorted(set(names))
checks['exact_staged_inputs']=set(git('diff','--cached','--name-only').splitlines())==set(inputs)
blobs={p:git('hash-object','--',p) for p in inputs};checks['exact_staged_blobs']=all(git('rev-parse',':'+p)==v for p,v in blobs.items())
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
expected=''.join(w['diagnostics'] for w in read(D/'whitespace.json')['warnings'])
checks['only_preserved_whitespace']=sorted(r.stdout.splitlines())==sorted(expected.splitlines()) and not r.stderr and r.returncode in (0,2)
if not all(checks.values()):raise SystemExit(json.dumps(checks))
with (D/'publication.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,exact_names=names,sha256={p:sha(R/p) for p in inputs},staged_blobs=blobs,scope='Stage this publication next and verify ALL explicit names/blobs before failfast commit/push.'),f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));print('complete names',len(names))
