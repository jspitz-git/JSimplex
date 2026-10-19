from pathlib import Path
import subprocess,hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3]
N=['REPORT.md','helpers.jl','host-entry.json','independent-review.json','independent-review.md','inputs.json','original-block.txt','panel-tests.jl','prepare.py','progress.md.before-p011-repair','replacement.txt','source-before.json','source-check.json','source-check.py','stage-supplement.json','progress.md.after-p011-repair','closure.py','publication.py','closure.json','publication-final.py','publication.json']
def call(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(v,s):
 if not v:raise RuntimeError(s)
closure=json.loads((D/'closure.json').read_text());require(closure['all_passed'] and all(closure['checks'].values()),'closure')
require(all(sha(D/p)==s for p,s in closure['bindings'].items()),'closure bindings')
require(call('diff','--name-only')=='' and call('diff','--cached','--name-only')=='','existing tracked/index changes')
require(call('rev-parse','HEAD')=='f179c815dfdd0db969b485a0685fe4d247225fb0','head')
require(call('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205','master')
require(sorted(p.name for p in D.iterdir())==sorted(set(N)-{'publication.json'}),'exact file roster')
paths=[str((D/n).relative_to(R)) for n in N]
with (D/'publication.json').open('x') as f:json.dump({'scope':'diagnostic offline preparation only','exact_names':paths,'listed_blobs':{p:call('hash-object',p) for p in paths if not p.endswith('/publication.json')},'closure_passed':True,'publication_draft':'publication.py preserved UNEXECUTED; final writer permits only the exact byte-preserved helper EOF separator warning','expected_whitespace_warning':'helpers.jl:60: new blank line at EOF.'},f,indent=2);f.write('\n')
call('add','--',*paths)
require(sorted(call('diff','--cached','--name-only').splitlines())==sorted(paths),'exact staged names')
diff=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
expected_warning=str((D/'helpers.jl').relative_to(R))+':60: new blank line at EOF.\n'
require(diff.returncode in (0,2) and diff.stderr=='' and diff.stdout in ('',expected_warning),'only preserved helper separator whitespace allowed')
require(sha(D/'helpers.jl')=='24164ea279f5eeaaf5a9860ffb11a813ac98e1d8ed8d950c957cd4d2be6c5f6f','exact reviewed helper separator')
print(json.dumps({'authored_whitespace_clean':True,'preserved_verbatim_warning':diff.stdout.strip()}))
expected={p:call('hash-object',p) for p in paths}
require(all(call('rev-parse',':'+p)==blob for p,blob in expected.items()),'staged blobs')
Path('/tmp/p011-expected-blobs.json').write_text(json.dumps(expected,indent=2)+'\n')
print(json.dumps({'all_passed':True,'exact_staged_names_and_blobs':len(expected),'listed_blobs':len(expected)-1}))
