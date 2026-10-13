from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');MAIN=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;B=R/'.superpowers/simplex-core-architecture/S5-O'
G=R/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py'
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
REL='test/adaptive_pricing_lifecycle_tests.jl'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def absent(extra=()):
 groups={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,*extra};matches=[]
 for q in Path('/proc').glob('[0-9]*'):
  try:
   s=(q/'stat').read_text();a=s[s.rindex(')')+2:].split()
   if int(a[2]) in groups or (q/'comm').read_text().strip()=='julia':matches.append({'pid':int(q.name),'pgid':int(a[2]),'start_ticks':int(a[19]),'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
  except FileNotFoundError:pass
 return {'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'matches':matches}
def command(label):
 target=R if label=='green-1' else MAIN
 return ['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(target),str(H/'driver.jl'),str(target),str(B/label/'raw')]
def accepted(name):
 a=read(H/name);assert a['accepted'] is True and a['unresolved_findings']==[]
 assert all(sha(p)==v for p,v in a['reviewed_sha256'].items())
 return a
