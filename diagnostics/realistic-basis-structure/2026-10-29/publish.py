from pathlib import Path
import subprocess,json,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/realistic-basis-structure/2026-10-29';pre=str(D.relative_to(W))+'/'
def git(*args):return subprocess.check_output(['git',*args],cwd=W,text=True).strip()
paths=git('diff','--cached','--name-only').splitlines();exception=pre+'inputs.toml';strict=[p for p in paths if p!=exception]
r=subprocess.run(['git','diff','--cached','--check','--',*strict],cwd=W,capture_output=True,text=True);old=json.loads((D/'whitespace-check.json').read_text())
checks={'only_diagnostic_paths':all(p.startswith(pre)for p in paths),'no_binaries':all(not p.endswith('.bin')for p in paths),'strict_other_files':r.returncode==0,'only_preserved_input_EOF_blank':old['returncode']==2 and old['stdout'].count('new blank line at EOF.')==1 and exception+':'in old['stdout']and(D/'inputs.toml').read_bytes().endswith(b'\n\n'),'closure':json.loads((D/'closure.json').read_text())['accepted'],'master_unchanged':git('-C','/home/jspitz/JSimplex.jl','rev-parse','master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'}
if not all(checks.values()):raise RuntimeError((checks,r.stdout,r.stderr))
with(D/'publication-check.json').open('x')as f:json.dump({'accepted':True,'checks':checks,'frozen_input_sha256':hashlib.sha256((D/'inputs.toml').read_bytes()).hexdigest(),'note':'One cosmetic EOF blank in accepted launch input preserved to retain101pins; original default false whitespace check retained. All other authored files strictly clean. No input/raw/config rewrite.'},f,indent=2);f.write('\n')
subprocess.run(['git','add','--',pre],cwd=W,check=True);entries=[]
for line in git('ls-files','--stage','--',pre).splitlines():
 meta,path=line.split('\t');mode,blob,stage=meta.split();entries.append({'path':path,'blob':blob,'mode':mode,'stage':stage,'sha256':hashlib.sha256((W/path).read_bytes()).hexdigest()})
if any(e['stage']!='0'for e in entries):raise RuntimeError('unmerged')
selfpath=pre+'STAGED.json';names=sorted([e['path']for e in entries]+[selfpath])
with(D/'STAGED.json').open('x')as f:json.dump({'entries':entries,'exact_names':names,'self_note':'Ownblob separatelysealedbeforecommit; ownnameincluded. Binaryhistory/witnessesexcluded.'},f,indent=2);f.write('\n')
subprocess.run(['git','add','--',selfpath],cwd=W,check=True)
if git('diff','--cached','--name-only').splitlines()!=names:raise RuntimeError('nameschanged')
for e in entries:
 if git('rev-parse',':'+e['path'])!=e['blob']:raise RuntimeError('blobchanged')
seal={'exact_names':names,'blobs':{p:git('rev-parse',':'+p)for p in names},'master':git('-C','/home/jspitz/JSimplex.jl','rev-parse','master')};Path('/tmp/realistic-structure-precommit-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'accepted':True,'checks':checks,'exact_staged_files':len(names)}))
