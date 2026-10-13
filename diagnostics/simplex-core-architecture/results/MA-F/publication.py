"""Exact explicit names/blobs verified before failfast diagnostic commit/push."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F';prefix=str(D.relative_to(R))+'/'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
names=read(D/'publication-names.json');closure=read(D/'closure.json');out=prefix+'publication.json';inputs=[n for n in names if n!=out]
checks={}
checks['closure_PASS']=closure['all_passed'] is True and all(closure['checks'].values())
checks['closure_bindings']=all(sha(R/p)==v for p,v in closure['sha256'].items())
checks['unique_explicit_names']=names==sorted(set(names))
checks['exact_staged_inputs']=set(git('diff','--cached','--name-only').splitlines())==set(inputs)
blobs={p:git('hash-object','--',p) for p in inputs}
checks['staged_blobs_match']=all(git('rev-parse',':'+p)==v for p,v in blobs.items())
checks['staged_whitespace_clean']=not subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True).stdout
if not all(checks.values()):raise SystemExit(json.dumps(checks))
with (D/'publication.json').open('x') as f:
 json.dump(dict(all_passed=True,checks=checks,exact_names=names,sha256={p:sha(R/p) for p in inputs},staged_blobs=blobs,scope='Explicit complete publication list. Publication file itself is staged next, then ALL listed names/blobs verified before commit.'),f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));print('complete names',len(names))
