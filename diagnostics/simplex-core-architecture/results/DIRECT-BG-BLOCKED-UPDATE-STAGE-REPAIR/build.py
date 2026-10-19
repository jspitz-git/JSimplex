"""Offline ordinary stage builder: complete committed master sources + unchanged ordinary adapters/env."""
from pathlib import Path
import sys,json,subprocess,hashlib,difflib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR');sys.path.insert(0,str(H));import control as c
from contract import contract
MASTER=c.rd(D/'entry.json')['master'];old=Path(c.rd(H/'stages.json')['red']['path']);stage=old.with_name('task2-master-stage')
def blob(n):return subprocess.check_output(['git','show',MASTER+':'+n],cwd=R)
def digest(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
c.require(c.git('rev-parse','master')==MASTER,'Master drift');c.require(MASTER+'\trefs/heads/master' in c.git('ls-remote','origin','refs/heads/master'),'Remote drift')
c.require(not stage.exists(),'Separate fresh destination required')
paths=c.git('ls-tree','-r','--name-only',MASTER,'src','Project.toml').splitlines();sources={};differences={}
for n in paths:
 b=blob(n);sources[n]=dict(sha256=digest(b),git_blob=c.git('rev-parse',MASTER+':'+n));put(stage/n,b)
 if (R/n).read_bytes()!=b:
  differences[n]=dict(old_sha256=c.sha(R/n),master_sha256=digest(b))
  put(D/'diffs'/Path(n).with_suffix('.diff'),''.join(difflib.unified_diff((R/n).read_text().splitlines(True),b.decode().splitlines(True),fromfile='diagnostic/'+n,tofile=MASTER+'/'+n)).encode())
for n in ['Manifest.toml','LocalPreferences.toml']:
 put(stage/n,(old/n).read_bytes())
c.require((stage/'Project.toml').read_bytes()==(old/'Project.toml').read_bytes(),'Dependency project changed: separate environment design required')
ordinary=R/'diagnostics/direct-lu-policy-adapters/reproduce'
for n in ['factor-export.jl','direct-factor.jl']:put(stage/'src'/n,(ordinary/n).read_bytes())
root=stage/'src/JSimplex.jl';before=root.read_bytes();insertion=c.rd(c.C/'overlay-manifest.json')['root_insertion'].encode();offset=before.rfind(b'\nend')
c.require(offset>=0 and before.count(b'\nend')==1,'Unexpected root shape');root.write_bytes(before[:offset]+insertion+before[offset:])
c.require(root.read_bytes().replace(insertion,b'',1)==blob('src/JSimplex.jl'),'Root inverse')
files={str(p.relative_to(stage)):c.sha(p) for p in sorted(stage.rglob('*')) if p.is_file()}
c.save(D/'stage.json',dict(scope=__doc__,master=MASTER,stage=str(stage),failed_stage=str(old),master_files=sources,root_insertion=insertion.decode(),ordinary={n:c.sha(ordinary/n) for n in ['factor-export.jl','direct-factor.jl']},environment={n:c.sha(stage/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']},sha256={str(stage/n):h for n,h in files.items()},stage_files=files,baseline_changes=differences,runtime_acceptance=False,launch_admitted=False))
checks=contract(stage);c.save(D/'structural-green.json',dict(all_passed=all(checks.values()),checks=checks,scope='Offline source contract GREEN, not the Julia RED/GREEN tests',sha256={str(stage/n):c.sha(stage/n) for n in ['src/factorization.jl','src/triangular_factorization.jl','src/direct-factor.jl','src/JSimplex.jl']}));c.require(all(checks.values()),'Source contract failed')
print('Prepared',len(files),'stage files;',len(differences),'baseline changes; source contracts',len(checks),'PASS')
