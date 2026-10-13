from pathlib import Path
import hashlib,json,re,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent;B=R/'.superpowers/simplex-core-architecture/S5-S';O=B/'qualification-1'
C=H.parent/'S5-R/candidate-reviewed.jl';EXPECTED='d03fcc9c0d2f70a16437ea2412e56c807babccb99f6df25aec82894b67d51950'
G=R/'diagnostics/simplex-core-architecture/reproduce/guarded_run.py'
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
PLAN=R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-qualification.md'
GROUPS={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def absent(extra=()):
 matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split()
   if int(f[2]) in GROUPS|set(extra) or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(f[2]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(GROUPS|set(extra)),matches=matches,time_ns=time.time_ns())
def command():return ['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(R),str(C),str(O/'report.toml')]
def essentials():return [C,G,W,W.parents[3]/'.superpowers/basis-chain-cost/julia.sh',PLAN,H/'common.py',H/'launcher.py',H/'audit.py',H/'schema.json',H/'required-paths.json',H/'admission.md',H/'host-before.json',H/'command.json']
def required():
 req=read(H/'required-paths.json')['sha256'];assert req and {str(p) for p in essentials() if p!=H/'required-paths.json'}.issubset(req)
 return req
def inventory_ok(pins):
 req=required();inv=pins['inventory']
 return (set(req)|{str(H/'required-paths.json')}).issubset(inv) and all(inv[p]['sha256']==v for p,v in req.items()) and all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in inv.items()) and set(pins['trees'])=={str(R/'src'),str(R/'test')} and all({str(p) for p in Path(t).rglob('*') if p.is_file()}=={p for p in inv if Path(p).is_relative_to(t)} for t in pins['trees'])
def accepted():
 a=read(H/'prelaunch-acceptance.json');required_paths=[*essentials(),H/'prelaunch-review.md',H/'admission-pins.json']
 assert a['accepted'] is True and a['unresolved_findings']==[] and set(map(str,required_paths)).issubset(a['reviewed_sha256'])
 assert all(sha(p)==v for p,v in a['reviewed_sha256'].items())
 return a
