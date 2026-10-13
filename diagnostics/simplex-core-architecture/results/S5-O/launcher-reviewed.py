"""New exclusive S5-O admission/actual manifests and at most two focused attempts."""
from common_reviewed import *
import subprocess,sys
mode,label=sys.argv[1:];assert label in ('admission','green-1','master-1')
B.mkdir(parents=True,exist_ok=True)
ADMISSION=B/'admission-reviewed-pins.json'
pins=ADMISSION if label=='admission' else B/(label+'-pins.json');s=read(H/'schema.json')
PRE_REQUIRED=[ADMISSION,H/'prelaunch-final-review.md',H/'driver.jl',H/'launcher-reviewed.py',H/'common_reviewed.py',H/'common.py',H/'audit.py',H/'postcheck.py',H/'schema.json',H/'expected.toml',H/'insertions.toml']
GREEN_REQUIRED=[H/'green-review.md',H/'green-1-audit.json',H/'green-1-postcheck.json',B/'green-1/pins.json',B/'green-1/process.json',B/'green-1/raw/report.toml',B/'green-1/raw/case.toml']
target=MAIN if label=='master-1' else R
if mode=='freeze':
 assert not absent()['matches']
 old=read(H.parent/'S5-N/evidence.json')['sha256']
 for p,v in old.items():
  expected=s['candidate_sha256'] if mode=='freeze' and label!='admission' and p==str(R/REL) else v
  assert sha(p)==expected,p
 files=set(map(Path,old))|{p for p in H.iterdir() if p.is_file()}
 files|={p for p in (H.parent/'S5-N').rglob('*') if p.is_file()}
 files|={G,W,W.parents[3]/'.superpowers/basis-chain-cost/julia.sh'}
 files|={target/p for p in ('Project.toml','Manifest.toml','LocalPreferences.toml','.vscode/settings.json')}
 files.add(B/'admission-pins.json')
 files.add(Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl'))
 files.add(R/'diagnostics/simplex-core-architecture/S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-PREPARATION-REVIEW.md')
 if label=='admission':assert sha(R/REL)==s['prefix_sha256']
 else:
  accepted('prelaunch-acceptance.json',PRE_REQUIRED);assert sha(target/REL)==s['candidate_sha256']
  pre=read(ADMISSION)
  assert all(sha(p)==(s['candidate_sha256'] if p==str(R/REL) else v['sha256']) for p,v in pre['inventory'].items())
  files.add(ADMISSION)
  if label=='master-1':
   accepted('green-acceptance.json',GREEN_REQUIRED);assert read(H/'green-1-audit.json')['all_passed'] is True
   relative={str(p.relative_to(R)):sha(p) for tree in ('src','test') for p in (R/tree).rglob('*') if p.is_file()}
   assert {str(p.relative_to(MAIN)) for tree in ('src','test') for p in (MAIN/tree).rglob('*') if p.is_file()}==set(relative)
   assert all(sha(MAIN/p)==v for p,v in relative.items())
   dump(H/'master-source-comparison.json',{'all_passed':True,'sha256':relative,'green_audit_sha256':sha(H/'green-1-audit.json')})
   files.add(H/'master-source-comparison.json')
 cmd=[sys.executable,str(G),'freeze',str(pins)]
 for tree in sorted({R/'src',R/'test',target/'src',target/'test'}):cmd+=['--tree',str(tree)]
 for p in sorted(files):cmd+=['--file',str(p)]
 for n in ('big.mps','largo.mps','AnyMOD.mps'):cmd+=['--forbidden','/home/jspitz/mps/'+n]
 subprocess.run(cmd,check=True)
elif mode=='run':
 assert label!='admission';accepted('prelaunch-acceptance.json',PRE_REQUIRED)
 if label=='master-1':accepted('green-acceptance.json',GREEN_REQUIRED)
 accepted(label+'-launch-binding.json',[pins,H/'prelaunch-acceptance.json',H/'prelaunch-final-review.md',H/'launcher-reviewed.py']+([H/'green-acceptance.json',H/'green-review.md'] if label=='master-1' else []))
 assert not (B/label).exists() and not absent()['matches']
 if label=='master-1':
  p=read(B/'green-1/process.json');assert not absent([p['runner']['pgid'],p['child']['pgid']])['matches']
 raise SystemExit(subprocess.call([sys.executable,str(G),'run',str(pins),str(B/label),'--seconds','120','--',*command(label)],cwd=R))
else:raise ValueError(mode)
