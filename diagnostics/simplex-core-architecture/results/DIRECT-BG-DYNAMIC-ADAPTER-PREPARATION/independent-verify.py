"""Fresh independent text/hash audit only. Never loads Julia or old scripts."""
from pathlib import Path
import hashlib,json,tempfile,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-ADAPTER-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def require(v,m):
 if not v:raise RuntimeError(m)
checks={}
initial=rd(E/'independent-review-initial-pins.json')
for n,h in initial.items():require(sha(R/n)==h,'initial drift '+n)
checks['initial_review_inputs_preserved']=len(initial)
o=rd(E/'overlay-reviewed.json');stage=Path(o['path']);source=Path(o['source'])
require(not any(p.is_symlink() for p in stage.rglob('*')),'stage symlink')
require(set(o['sha256'])=={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()},'stage membership')
for n,h in o['sha256'].items():require(sha(stage/n)==h,'stage hash '+n)
for n,h in o['baseline'].items():
 require(sha(source/n)==h,'baseline hash '+n)
 if n!='src/JSimplex.jl':require((source/n).read_bytes()==(stage/n).read_bytes(),'baseline change '+n)
root=(source/'src/JSimplex.jl').read_bytes();new=(stage/'src/JSimplex.jl').read_bytes()
require(new==root[:-5]+b'\ninclude("dynamic-bg.jl")\n\nend\n','root exact delta')
for n,d in o['new_files'].items():require((C/n).read_bytes()==(stage/d).read_bytes(),'candidate copy '+n)
checks['overlay_files']=len(o['sha256']);checks['baseline_files']=len(o['baseline']);checks['new_copies']=len(o['new_files'])
for name,groupkey in [('reference-bindings-reviewed.json','groups'),('actual-dispatch-bindings.json','records')]:
 b=rd(C/name)
 for p,h in b['sha256'].items():require(sha(Path(p))==h,'binding hash '+p)
 for g in b[groupkey]:
  lines=Path(g['source']).read_bytes().splitlines(keepends=True)
  piece=b''.join(lines[g['first']-1:g['last']])
  require(hashlib.sha256(piece).hexdigest()==g['excerpt_sha256'],'excerpt '+str(g))
 checks[name]=len(b[groupkey])
with tempfile.TemporaryDirectory(prefix='independent-bg-review-') as td:
 p=Path(td)/'text.jl';p.write_bytes((E/'reference-excerpts-reviewed.jl').read_bytes())
 for reverse,expected in [(False,C/'dynamic-bg-reviewed.jl'),(True,E/'reference-excerpts-reviewed.jl')]:
  proc=subprocess.run(['git','apply']+(['--reverse'] if reverse else [])+[str(E/'reference-to-candidate-reviewed.patch')],cwd=td,capture_output=True,text=True)
  require(proc.returncode==0,'text patch '+proc.stderr)
  require(p.read_bytes()==expected.read_bytes(),'text inverse bytes')
checks['independent_patch_forward_and_reverse']=True
paths=[C/n for n in ['dynamic-bg-reviewed.jl','dynamic-bg-tests-reviewed.jl','reference-bindings-reviewed.json','actual-dispatch-bindings.json','fixtures.jl','slot-oracles.jl','prepare-adapter-reviewed.py']]+[E/n for n in ['REPORT.md','overlay-reviewed.json','lookup-work-witness.json','independent-verify.py']]
result={'status':'PASS offline hash/text audit only','checks':checks,'sha256':{str(p.relative_to(R)):sha(p) for p in paths}}
with (E/'independent-verify.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
