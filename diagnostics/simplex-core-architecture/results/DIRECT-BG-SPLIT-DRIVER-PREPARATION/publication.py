from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION'
def need(v,m):
 if not v:raise RuntimeError(m)
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
names=json.loads((E/'publication-names.json').read_text())['names'];out=str((E/'publication.json').relative_to(R));prior=[k for k in names if k!=out]
c=json.loads((E/'closure.json').read_text());need(c['all_passed'],'closure')
need(all(hashlib.sha256((R/k).read_bytes()).hexdigest()==v for k,v in c['sha256'].items()),'closure bindings')
need(not git('diff','--cached','--name-only'),'index not empty')
need(all(not subprocess.run(['git','ls-files','--error-unmatch',k],capture_output=True).returncode==0 for k in names),'unexpected tracked publication path')
subprocess.run(['git','add','--',*prior],check=True)
need(set(git('diff','--cached','--name-only').splitlines())==set(prior),'stage exact names')
blobs={k:git('rev-parse',':'+k) for k in prior}
need(all(git('hash-object',k)==v for k,v in blobs.items()),'stage vs disk')
check=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
need(check.returncode==0,'diff check: '+check.stdout+check.stderr)
r=dict(all_passed=True,scope='Exact diagnostic-only publication before commit. No Julia or master change.',names=names,staged_blobs=blobs,closure_sha256=hashlib.sha256((E/'closure.json').read_bytes()).hexdigest(),checks=dict(closure_pass=True,closure_bindings=True,only_new_paths=True,exact_names=True,exact_blobs=True,diff_check=True),self_binding='publication.json intentionally not self-hashed; exact final index/disk and committed blobs independently checked immediately before/after commit')
with (E/'publication.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
subprocess.run(['git','add','--',out],check=True)
need(set(git('diff','--cached','--name-only').splitlines())==set(names),'final stage names')
need(all(git('rev-parse',':'+k)==git('hash-object',k) for k in names),'final stage all blobs')
print(json.dumps(dict(all_passed=True,exact_names=len(names),listed_blobs=len(blobs))))
