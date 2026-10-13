from pathlib import Path
import hashlib,json,time,sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');M=Path('/home/jspitz/JSimplex.jl');H=Path(__file__).resolve().parent;T=H.parent/'S5-T'
B=R/'.superpowers/simplex-core-architecture/S5-U';G=H/'guard.py';C=T/'candidate.jl';REL='test/simplex_precision_tests.jl'
EXPECTED='357a976f5fc984025452ee4b259f2fc1f140885212f5b40ff71e072ebfab3684';OLD='b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5'
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh')
PLAN=R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-test-integration.md'
GROUPS={23249,23257,49081,49084,52772,52774,53479,53481,60706,60708,63808,63815,64420,64422,71824,71826}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def root(stage):
 assert stage in ('green','master');return R if stage=='green' else M
def out(stage):return B/(stage+'-1')
def stage_files(stage):return H/stage

def absent(extra=()):
 matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split()
   if int(f[2]) in GROUPS|set(extra) or (p/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(p.name),pgid=int(f[2]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(GROUPS|set(extra)),matches=matches,time_ns=time.time_ns())
def command(stage):return ['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(root(stage)),str(H/'driver.jl'),str(root(stage)),str(out(stage)/'raw')]
def essentials():return [C,G,W,W.parents[3]/'.superpowers/basis-chain-cost/julia.sh',PLAN,H/'common_reviewed.py',H/'launcher-reviewed.py',H/'audit-reviewed.py',H/'driver.jl',H/'schema.json',H/'expected.toml',H/'insertions.toml',H/'expected-suffix.jl',H/'admission.md',H/'host-before.json',H/'source-preparation.json',H/'failure-tests.json',H/'failure_tests.py',H/'review_fix.py',H/'reviewed_failure_tests.py',H/'reviewed-failure-tests.json']
def required(stage=None):
 req=read(H/'required-reviewed-paths.json')['sha256'];assert req and set(map(str,essentials())).issubset(req)
 req=dict(req)
 if stage:
  root(stage);req[str(R/REL)]=EXPECTED
  if stage=='master':req[str(M/REL)]=EXPECTED
 return req

def inventory_ok(pins,stage=None):
 req=required(stage);inv=pins['inventory'];trees={str(p/d) for p in (R,M) for d in ('src','test')}
 return (set(req)|{str(H/'required-reviewed-paths.json')}).issubset(inv) and all(inv[k]['sha256']==v for k,v in req.items()) and all(sha(k)==v['sha256'] and str(Path(k).resolve(strict=True))==v['resolved'] for k,v in inv.items()) and set(pins['trees'])==trees and all({str(p) for p in Path(t).rglob('*') if p.is_file()}=={k for k in inv if Path(k).is_relative_to(t)} for t in trees)
def accepted():
 a=read(H/'admission-acceptance-reviewed.json');paths=[*essentials(),H/'required-reviewed-paths.json',H/'admission-reviewed-pins.json',H/'admission-accepted-review.md']
 assert a['accepted'] is True and a['unresolved_findings']==[] and set(map(str,paths)).issubset(a['sha256'])
 assert all(sha(k)==v for k,v in a['sha256'].items());return a

def current_refs():
 import subprocess
 return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,M)}
def stage_required(stage):
 paths={str(p) for p in (root(stage)/REL,H/'admission-acceptance-reviewed.json',H/'admission-accepted-review.md',H/'admission-reviewed-pins.json',H/'required-reviewed-paths.json',H/'common_reviewed.py',H/'launcher-reviewed.py',H/'audit-reviewed.py',H/'driver.jl',H/'expected.toml',H/'insertions.toml')}
 if stage=='master':paths|={str(H/'green'/n) for n in ('audit.json','postcheck.json','review.md','pins.json')}
 return paths
def stage_record_valid(a,stage,hashfn=sha,refs=None):
 refs=current_refs() if refs is None else refs
 return (a.get('accepted') is True and a.get('unresolved_findings')==[] and a.get('stage')==stage and a.get('root')==str(root(stage)) and a.get('refs')==refs and a.get('candidate_sha256')==EXPECTED and type(a.get('sha256')) is dict and stage_required(stage).issubset(a['sha256']) and a['sha256'].get(str(root(stage)/REL))==EXPECTED and all(hashfn(k)==v for k,v in a['sha256'].items()))
def stage_accepted(stage):
 a=read(stage_files(stage)/'stage-acceptance.json');assert stage_record_valid(a,stage)
 if stage=='master':
  audit=read(H/'green/audit.json');post=read(H/'green/postcheck.json');review=(H/'green/review.md').read_text()
  assert audit['all_passed'] is True and audit['checks'] and all(v is True for v in audit['checks'].values())
  assert post['all_passed'] is True and post['checks'] and all(v is True for v in post['checks'].values())
  assert {str(H/'green'/n) for n in ('audit.json','pins.json')}.issubset(post['sha256']) and all(sha(k)==v for k,v in post['sha256'].items())
  assert 'ACCEPTED' in review and 'Unresolved findings: []' in review
 return a
def launch_accepted(stage):
 stage_accepted(stage);h=stage_files(stage);p=h/'pins.json';inv=read(p)['inventory']
 required_extra={str(H/n) for n in ('admission-reviewed-pins.json','admission-accepted-review.md','admission-acceptance-reviewed.json')}|{str(h/'stage-acceptance.json')}
 assert required_extra.issubset(inv) and all(sha(k)==inv[k]['sha256'] for k in required_extra)
 b=read(h/'launch-binding.json');keys={str(p),str(H/'admission-acceptance-reviewed.json'),str(h/'stage-acceptance.json'),str(H/'launcher-reviewed.py'),str(H/'audit-reviewed.py')}
 assert b.get('accepted') is True and b.get('unresolved_findings')==[] and b.get('stage')==stage and b.get('command')==command(stage) and keys.issubset(b['sha256']) and all(sha(k)==v for k,v in b['sha256'].items())
 return b

def invocation_valid(stage,process,pin_hash):
 h=stage_files(stage);inv=read(h/'guard-invocation.json');res=read(h/'attempt-reserved.json');log=read(h/'guard-output.log');cmd=[sys.executable,str(G),'run',str(h/'pins.json'),str(out(stage)),'--seconds','120','--',*command(stage)]
 return (type(inv.get('returncode')) is int and inv['returncode']==0 and 'error' not in inv and inv.get('command')==cmd and res.get('command')==command(stage) and res.get('pins_sha256')==pin_hash and log==process and all(type(x) is int for x in (res.get('time_ns'),inv.get('started_ns'),inv.get('ended_ns'))) and res['time_ns']<=inv['started_ns']<=inv['ended_ns'] and inv['host']['boot_id']==process['runner']['boot_id'] and inv['host']['matches']==[])
