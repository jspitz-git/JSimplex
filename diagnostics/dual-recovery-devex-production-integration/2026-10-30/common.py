"""Definitions for one ordinary actual-master verification; never Julia on import."""
from pathlib import Path
import hashlib,json,os,subprocess,math
D=Path(__file__).resolve().parent;W=D.parents[2];M=Path('/home/jspitz/JSimplex.jl');R=W/'.superpowers/dual-recovery-devex-production-integration/master-1';P=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30'
def require(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def fresh(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def git(root,*a):return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split();return dict(pid=int(pid),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def owners():
 a=[]
 if (R/'attempt.json').exists():a.append(('launcher',read(R/'attempt.json')['runner']))
 for n in ('current.json','process.json'):
  if (R/'guard'/n).exists():
   q=read(R/'guard'/n);a.extend((k,q[k]) for k in ('runner','child') if k in q)
 return a
def groups(boot,include_launcher=True):
 before=read(D/'before.json')['host'];g=set(before['checked_groups']) if before['boot_id']==boot else set()
 for role,a in owners():
  if a['boot_id']==boot and (include_launcher or role!='launcher'):g.update((a['pgid'],a['sid']))
 return g
def host():
 state=read(D/'integration.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();g=groups(boot);excluded=[];me=identity(os.getpid())
 for role,a in owners():
  if role=='launcher' and all(a[k]==me[k] for k in ('pid','pgid','sid','start_ticks','boot_id','command')):g.difference_update((a['pgid'],a['sid']));excluded.append(a)
 conflict=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=identity(p.name)
   if (p/'comm').read_text().lower().strip().startswith('julia') or a['pgid'] in g or a['sid'] in g:conflict.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 require(not conflict,'Julia/group/session present '+str(conflict))
 m={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree']);require(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'memory pressure')
 refs=dict(diagnostic_head=git(W,'rev-parse','HEAD'),master=git(M,'rev-parse','HEAD'),master_branch=git(W,'rev-parse','master'),origin_master=git(W,'rev-parse','origin/master'))
 require(refs==dict(diagnostic_head=state['diagnostic_head'],master=state['production_commit'],master_branch=state['production_commit'],origin_master=state['remote_master_before']),'local integration/remote refs changed')
 require(git(M,'branch','--show-current')=='master' and not git(M,'diff','--cached','--name-only'),'master/index')
 require(git(M,'status','--porcelain','-uall')==read(D/'before.json')['master_status'],'user worktree state changed')
 require(all(sha(n)==v for n,v in state['user_hashes'].items()),'user file changed')
 require(not git(W,'diff','HEAD','--name-only') and not git(W,'diff','--cached','--name-only') and not git(W,'diff',state['production_commit'],'HEAD','--','src','test','Project.toml','.github'),'diagnostic production tree/index changed')
 return dict(boot_id=boot,checked_groups=sorted(g),conflicts=[],still_active_current_launcher=excluded,memory=memory,refs=refs,scope='full stored and actual owner groups AND sessions; own active launcher explicitly deferred')
def paths():
 c=read(D/'contract.json');s=set(str(p) for p in D.rglob('*') if p.is_file());s.update(str(M/n) for n in git(M,'ls-files','src').splitlines());s.update(str(M/'test'/n) for n in c['ordered_test_files']);s.update(str(M/'test'/n) for n in ('runtests.jl','support/devex_refinement_reference.jl','support/devex_legacy_rebuild_reference.jl'));s.update(c['known_fixtures']);s.update(str(p) for p in budget_paths());s.update(str(M/n) for n in ('Project.toml','Manifest.toml','LocalPreferences.toml','.vscode/settings.json'));s.update(str(W/n) for n in read(P/'publication.json')['expected_names']);s.add(str(Path(os.sys.executable).absolute()));j=Path(c['command'][0]);runtime=j.parents[1];s.update(str(p) for p in (j,runtime/'lib/libjulia.so.1.13.0',runtime/'lib/julia/sys.so',runtime/'lib/julia/libjulia-internal.so.1.13.0',runtime/'share/julia/base/timing.jl'));return sorted(s)
def verify_pins(pins):
 require(pins['trees']==[] and len(pins['files'])==len(set(pins['files'])) and set(pins['files'])==set(pins['inventory']),'pin membership')
 for n,v in pins['inventory'].items():require(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'],'pin changed '+n)
 return True
def admit(path,seal,pins):
 a=read(path);c=read(D/'contract.json');require(a['accepted'] is True and a['scope']=='numerical_admission' and a['phase']=='production-master' and a['head']==c['diagnostic_head']==seal['head'] and a['production_commit']==c['production_commit']==seal['production_commit'],'specific numerical admission')
 require(a['command']==c['command']==seal['command'] and a['seal_sha256']==sha(R/'seal.json') and a['pins_sha256']==sha(R/'pins.json')==seal['pins_sha256'],'admission command/seal/pins');require(a['checks'] and all(v is True for v in a['checks'].values()),'review checks');require(sha(a['review_report'])==a['review_report_sha256'],'review report');require(set(pins['inventory'])<=set(a['bindings']) and a['bindings'].get(str(R/'seal.json'))==sha(R/'seal.json') and a['bindings'].get(str(R/'pins.json'))==sha(R/'pins.json'),'complete specific admission bindings');require(all(sha(n)==v for n,v in a['bindings'].items()),'review binding changed');return a
def unused():require(not any((R/n).exists() for n in ('attempt.json','guard','completion.json','audit.json','closed.json')),'verification attempt consumed')
def guard_command(started):
 c=read(D/'contract.json');return [str(Path(os.sys.executable).absolute()),'-B',str(D/'guard/guard_reviewed.py'),'run',str(R/'pins.json'),str(R/'guard'),'--expected-exit','0','--seconds',str(c['remaining_seconds']-12),'--deadline',str(started+c['remaining_seconds']-12),'--',*c['command']]

def budget_paths():
 return [W/'diagnostics'/folder/'2026-10-30'/rel/'completion.json' for folder,rel in (('dual-recovery-devex-task4-red','red'),('dual-recovery-devex-task4-green','green'),('dual-recovery-devex-green2-result','green2'),('dual-recovery-devex-reference-cost-result','reference-cost'),('dual-recovery-devex-candidate-cost-result','candidate-cost'))]
def prior_time():
 records=[read(p) for p in budget_paths()];durations=[r['elapsed_inclusive_seconds'] for r in records]
 require(all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in durations),'prior duration types')
 require([r['supervisor_accepted'] for r in records]==[True,False,True,True,True],'failed prior time dropped')
 require(sum(durations)==1108.3747013349202==records[-1]['total_inclusive_seconds'],'previous total reset')
 return sum(durations)
