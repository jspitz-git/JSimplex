"""New independent saved-result checks; no author helpers or Julia execute."""
from pathlib import Path
import json,hashlib,subprocess,tomllib,time,math
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION';RUN=D/'runs/red300';OUT=RUN/'output';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
checks={};detail={}
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(n,v):checks[n]=bool(v)
def git(*a,root=R):return subprocess.check_output(['git',*a],cwd=root).decode().strip()
def inventory(j):
 paths=set(j['files'])
 for root in j['trees']:
  p=Path(root)
  if p.is_symlink():return False
  for q in p.rglob('*'):
   if q.is_symlink():return False
   if q.is_file():paths.add(str(q))
 return paths==set(j['inventory']) and all(v=={'resolved':str(Path(p).resolve(strict=True)),'sha256':sha(p)} for p,v in j['inventory'].items())
s=rd(RUN/'sealed.json');lp=rd(RUN/'launch-pins.json');a=rd(RUN/'admission.json');au=rd(RUN/'audit.json');cfg=rd(RUN/'config.json');inv=rd(RUN/'invocation.json');res=rd(RUN/'reservation.json');p=rd(OUT/'process.json');cur=rd(OUT/'current.json');sup=inv['supervisor'];post=rd(RUN/'posthost.json');pre=rd(RUN/'prehost.json');host=rd(RUN/'host.json')
ck('seal_all_inventory',inventory(s));ck('launch_all_inventory',inventory(lp))
ck('launch_membership',set(lp['files'])==set(s['files'])|{str(RUN/'sealed.json'),str(RUN/'admission.json'),str(RUN/'prehost.json')} and lp['trees']==s['trees'] and lp['inputs']==[])
ck('seal_launch_inventory_agree',all(lp['inventory'].get(n)==v for n,v in s['inventory'].items()))
ck('output_pins_match',rd(OUT/'pins.json')==lp)
ck('admission_schema_exact_bindings',a['accepted'] is True and a['findings']==[] and a['scope']=='direct adapter exact-stage admission' and a['phase']=='red300' and a['pins_sha256']==sha(RUN/'sealed.json') and set(a['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and all(sha(n)==h for n,h in {**a['sha256'],**a['evidence_sha256']}.items()))
ck('config_seal',s['config']==cfg and cfg['phase']=='red300' and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1)
ck('commands',p['command']==cur['command']==inv['command']==cfg['command'] and p['cwd']==cur['cwd']==str(R))
ck('pins_invocation',p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(RUN/'launch-pins.json') and p['pins_unchanged'] is True)
ck('reservation',res==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=300) and inv['reservation_sha256']==sha(RUN/'reservation.json') and inv['review_sha256']==sha(RUN/'admission.json'))
expectedguard=[inv['python'],'-B',str(D/'guard.py'),'run',str(RUN/'launch-pins.json'),str(OUT),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','1','--',*cfg['command']]
ck('guard292_absolute_command',inv['guard_command']==expectedguard and Path(inv['python']).resolve()==Path('/usr/bin/python3').resolve())
ck('process_identity_linkage',cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'])
ck('process_boot_start_command',all(q['boot_id']==s['boot_id'] and type(q['start_ticks']) is int and q['start_ticks']>0 and q['pid']==q['pgid']==q['sid'] and q['command'] for q in [p['runner'],p['child']]))
ck('both_groups_sessions_covered',all(p[role][key] in post['groups'] for role in ['runner','child'] for key in ['pgid','sid']) and set(s['groups'])<=set(pre['groups'])<=set(post['groups']) and len(post['groups'])==224)
ck('saved_host_closure',all(h['matches']==[] for h in [host,pre,post]) and all(all(h[k]==s[k] for k in ['head','master','boot_id']) for h in [host,pre,post]))
ck('expected_exit_no_timeout',p['returncode']==1 and p['reason']=='exit1' and 'error' not in p and sup['returncode']==0 and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup)
ck('elapsed_bounds',all(type(v) in (int,float) and math.isfinite(v) and 0<v<=300 for v in [inv['elapsed_seconds'],sup['elapsed_seconds']]) and 0<p['elapsed_including_launch']<292)
resources=[json.loads(x) for x in (OUT/'resources.jsonl').read_text().splitlines()]
ck('all_resources_terminal',len(resources)==5 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
ck('sample_chronology',all(0<x['elapsed']<p['elapsed_including_launch'] for x in resources) and [x['elapsed'] for x in resources]==sorted(x['elapsed'] for x in resources))
ck('rss_observed',p['child_maxrss_kib']==431660)
raw=tomllib.loads((OUT/'raw.toml').read_text());root=raw['tests'];leaf=root['children'][0];loaded=rd(D/'loaded-paths.json');loaded['JSimplex']=str(Path(cfg['stage'])/'src/JSimplex.jl')
ck('raw_exact_schema',set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'} and raw['phase']=='red300' and raw['complete'] is True and raw['fatal']=='' and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1 and raw['loaded']==loaded)
nodekeys={'name','pass','fail','error','broken','failures','children'}
ck('raw_exact_tree',set(root)==set(leaf)==nodekeys and root['name']=='root' and root['failures']==[] and len(root['children'])==1 and all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','error','broken']) and leaf['name']=='Missing direct policy contract (seven expected failures)' and leaf['children']==[] and all(type(leaf[k]) is int and leaf[k]==v for k,v in [('pass',0),('fail',7),('error',0),('broken',0)]) and len(leaf['failures'])==7)
red=str(R/'diagnostics/direct-lu-policy-adapters/reproduce/red.jl');expected=[]
for manager in ['ForrestTomlinFactorization','SuhlSuhlFactorization','BartelsGolubFactorization']:
 for backend in ['native','markowitz']:
  expected.append(f'Test Failed at {red}:8\n  Expression: applicable(JSimplex._direct_lu_factor, Factor, B, Val(R), JSimplex._NATIVE_PIVOT_DEFAULT)\n   Evaluated: applicable(JSimplex._direct_lu_factor, JSimplex.{manager}, sparse(Int64[], Int64[], Float64[], 0, 0), Val{{:{backend}}}(), JSimplex._NATIVE_PIVOT_DEFAULT)')
expected.append(f'Test Failed at {red}:10\n  Expression: :pivot_policy in fieldnames(JSimplex.DirectLowerBackend)\n   Evaluated: pivot_policy in (:lower, :row_order, :scaling, :divide_scaling, :diagonal, :normalize_requested, :fallback, :work)')
ck('all7_exact_failure_identities',leaf['failures']==expected)
log=(OUT/'run.log').read_text();ck('failure_log_exact_records',log.count('TEST FAILURE:')==7 and log.split('TEST FAILURE: ')[1:]==[x+'\n' for x in expected])
ck('single_warning_no_error',log.count('WARNING:')==1 and 'Detected access to binding `Main.run_direct_lu_policy_red`' in log and all(x not in log for x in ['ERROR:','FATAL DRIVER:','BROKEN TEST:','GROUP/COUNT MISMATCH','LoadError']))
ck('launcher_log_process_matches',json.loads((RUN/'launcher.log').read_text())==p)
ck('output_exact_membership',{q.name for q in OUT.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(q.is_file() and not q.is_symlink() for q in OUT.iterdir()))
expected_audit=set(str(q) for q in RUN.rglob('*') if q.is_file() and q.name!='audit.json')
ck('saved_audit_binding_membership',set(au['sha256'])==expected_audit and all(sha(n)==h for n,h in au['sha256'].items()))
ck('saved_audit_matches_independent_result',au['all_passed'] is True and au['pure_timeout'] is False and au['error']=='' and au['phase']=='red300' and au['result']['assertions']==7 and au['result']['groups']==[[leaf['name'],0,7,0,0]])
base=rd(D/'baseline.json')
for label,rootdir in [('diagnostic',R),('production',W)]:
 ck(label+'_baseline',set(git('ls-files','src','test','.github','Project.toml',root=rootdir).splitlines())==set(base[label]) and all(sha(rootdir/n)==h for n,h in base[label].items()))
ck('refs_and_remote',git('rev-parse','HEAD')==s['head']=='1c10d172dcd8d914041f74be2f6d5fd7f6a84d87' and git('rev-parse','master')==git('rev-parse','HEAD',root=W)==s['master']=='26e2291745999f485a74f643298ca997d65c7205' and git('ls-remote','origin','refs/heads/master')==s['master']+'\trefs/heads/master')
ck('no_tracked_edits',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
groups=set(post['groups']);matches=[];unreadable=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  f=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe=''
  try:exe=str((q/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(q.name))
  except FileNotFoundError:pass
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(q.name),pgid=int(f[2]),sid=int(f[3]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh224_groups_sessions_clear',not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id'])
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};ck('fresh_resources',mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2)
detail=dict(seal_count=len(s['inventory']),launch_count=len(lp['inventory']),audit_file_count=len(au['sha256']),elapsed_seconds=inv['elapsed_seconds'],child_guard_elapsed_seconds=p['elapsed_including_launch'],child_maxrss_kib=p['child_maxrss_kib'],resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources+[p['terminal_memory']]),max_swap_kib=max(x['swap_used_kib'] for x in resources+[p['terminal_memory']]),host=dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
v=dict(all_passed=all(checks.values()),checks=checks,details=detail,scope='Independent saved RED300 review, no Julia or frozen helper/auditor rerun')
with (E/'result-review-checks.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],details={k:v for k,v in detail.items() if k!='host'})))
