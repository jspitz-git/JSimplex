from pathlib import Path
import subprocess,json,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/triangular-structural-options/2026-10-29';B=W/'diagnostics/bg-local-rotation/2026-10-29';prefixes=[str(p.relative_to(W))+'/'for p in [D,B]]
def git(*args):return subprocess.check_output(['git',*args],cwd=W,text=True).strip()
exceptions=[str((B/n).relative_to(W))for n in ['replay-core.jl','replay-core-2.jl']]
paths=git('diff','--cached','--name-only').splitlines();strict=[p for p in paths if p not in exceptions]
r=subprocess.run(['git','diff','--cached','--check','--',*strict],cwd=W,text=True,capture_output=True)
old=json.loads((D/'whitespace-initial.json').read_text());checks={'strict_other_files':r.returncode==0,'only_two_frozen_EOF_blanklines':old['returncode']==2 and old['stdout'].count('new blank line at EOF.')==2 and all(p+':'in old['stdout']for p in exceptions)and all((W/p).read_bytes().endswith(b'\n\n')for p in exceptions),'only_new_diagnostic_paths':all(any(p.startswith(pre)for pre in prefixes)for p in paths),'closure_pass':json.loads((D/'closure.json').read_text())['accepted'],'master_unchanged':git('-C','/home/jspitz/JSimplex.jl','rev-parse','master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'}
if not all(checks.values()):raise RuntimeError((checks,r.stdout,r.stderr))
with(D/'publication-check.json').open('x')as f:json.dump({'accepted':True,'checks':checks,'exceptions':{p:hashlib.sha256((W/p).read_bytes()).hexdigest()for p in exceptions},'reason':'Only two cosmetic EOF blank lines in preserved sealed replay cores; source/raw/pin fidelity retained. All other authored files strictly clean. Initial false default check preserved. No configuration mutation or source rewriting.'},f,indent=2);f.write('\n')
subprocess.run(['git','add','--',*prefixes],cwd=W,check=True)
entries=[]
for line in git('ls-files','--stage','--',*prefixes).splitlines():
 meta,path=line.split('\t');mode,blob,stage=meta.split();entries.append({'path':path,'mode':mode,'blob':blob,'stage':stage,'sha256':hashlib.sha256((W/path).read_bytes()).hexdigest()})
if any(x['stage']!='0'for x in entries):raise RuntimeError('stagedconflict')
selfpath=str((D/'STAGED.json').relative_to(W));names=sorted([x['path']for x in entries]+[selfpath])
with(D/'STAGED.json').open('x')as f:json.dump({'entries':entries,'exact_names':names,'self_note':'Ownblob separately sealed beforecommit; exactnames includes this file.'},f,indent=2);f.write('\n')
subprocess.run(['git','add','--',selfpath],cwd=W,check=True)
if git('diff','--cached','--name-only').splitlines()!=names:raise RuntimeError('exactnameschanged')
for e in entries:
 if git('rev-parse',':'+e['path'])!=e['blob']:raise RuntimeError('blobchanged')
seal={'exact_names':names,'blobs':{p:git('rev-parse',':'+p)for p in names},'master':git('-C','/home/jspitz/JSimplex.jl','rev-parse','master')}
Path('/tmp/triangular-options-precommit-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'accepted':True,'checks':checks,'exact_staged_files':len(names)}))
