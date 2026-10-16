from pathlib import Path
import json,hashlib,subprocess,ast
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-RED';D=E.parent/'DIRECT-BG-DYNAMIC-DRIVER-PREPARATION';run=D/'runs/red300'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
v=rd(run/'result-review.json');assert v['accepted'] is True and v['findings']==[] and v['scope']=='dynamic BG RED result' and v['phase']=='red300'
paths={str(p) for p in run.rglob('*') if p.is_file() and p.name!='result-review.json'};assert set(v['sha256'])==paths
for n,h in v['sha256'].items():assert sha(n)==h
for n,h in v['evidence_sha256'].items():assert sha(n)==h
post=rd(E/'postcheck.json');assert post['all_passed'] is True and len(post['checks'])==13 and all(post['checks'].values())
for n,h in post['sha256'].items():assert sha(n)==h
S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={S:E/'STATUS.md.before-RED',ROAD:E/'roadmap.md.before-RED'}
for n,p in mapping.items():assert n.read_bytes()==p.read_bytes()
assert S.read_text().count('## Exact next action\n\n')==1
assert '### Historical prior continuation (superseded)' in S.read_text().split('## Exact next action\n\n')[1]
count=0
for record in [D/'closure.json',D/'publication.json']:
 j=rd(record)
 for n,h in j['sha256'].items():
  path=Path(n) if Path(n).is_absolute() else R/n;old=mapping.get(path,path);assert sha(old)==h;count+=path in mapping
 for n,h in j.get('git_blobs',{}).items():
  path=Path(n) if Path(n).is_absolute() else R/n;old=mapping.get(path,path);assert git('hash-object','--',str(old))==h;count+=path in mapping
assert count==6
for n in ['close.py','publish.py']:ast.parse((E/n).read_text())
assert {p.name for p in (D/'runs').iterdir()}=={'red300'}
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
head='d7d090d86b1f1ed2d7b68a079437a0136f73a9f6';master='26e2291745999f485a74f643298ca997d65c7205';remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
assert git('rev-parse','HEAD')==head and git('rev-parse','master')==master
assert head+'\trefs/heads/codex/simplex-core-architecture' in remote and master+'\trefs/heads/master' in remote
assert all(not p.is_symlink() and p.is_file() for p in E.iterdir())
proof=dict(all_passed=True,run_files=18,result_primary_bindings=17,postcheck_gates=13,continuation_mappings=6,head=head,master=master,remote=remote,closure_scripts_executed=False,scope='Independent offline result/closure/publication preconditions')
with (E/'independent-closure-proof.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print(json.dumps(proof,indent=2))
