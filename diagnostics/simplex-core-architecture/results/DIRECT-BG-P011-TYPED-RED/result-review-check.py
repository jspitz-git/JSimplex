"""Independent saved RED result review. No harness imports, Julia, or audit reruns."""
from pathlib import Path
import hashlib,json,math,os,re,subprocess,sys,time,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-TYPED-HARNESS';E=D.with_name('DIRECT-BG-P011-TYPED-RED');run=D/'runs/p011-red300';outer=D/'outers/p011-red300';phase='p011-red300'
HEAD='e2b2ad2ce70301693fe142f04e58b2252271393e';MASTER='26e2291745999f485a74f643298ca997d65c7205';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a,root=R):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
checks=[]
def check(v,label):
 checks.append(dict(name=label,passed=bool(v)))
 if not v:raise AssertionError(label)
def bound(d):return all(sha(Path(p) if Path(p).is_absolute() else R/p)==h for p,h in d.items())
def integer(v):return type(v) is int and 0<=v<=2**63-1
def bounded(v,limit=300):return type(v) in (int,float) and math.isfinite(v) and 0<=v<=limit
def inventory(files,trees):
 paths=set(map(Path,files))
 for t in map(Path,trees):
  check(t.is_dir() and not t.is_symlink(),'pinned tree '+str(t))
  for p in t.rglob('*'):
   check(not p.is_symlink(),'no pinned tree symlink '+str(p))
   if p.is_file():paths.add(p)
 return {str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)}
result=dict(scope='Independent exact P011 RED saved-result checks',phase=phase,started=time.time(),checks=checks,new_julia_execution=False,historical_scripts_rerun=False)
try:
 costs=('load.toml','panel-load.toml','tests-load.toml','probe-setup.toml','probe-cost.toml','tests-cost.toml')
 payload_names=set(costs)|{'probe.toml','unit-1.toml','raw.toml'}
 guard_names={'pins.json','current.json','process.json','resources.jsonl','run.log'}
 top={'admission.json','audit.json','config.json','host.json','invocation.json','launch-pins.json','launcher.log','outer-closure.json','posthost.json','prehost.json','reservation.json','sealed.json','output','payload'}
 check({p.name for p in run.iterdir()}==top,'exact run top-level membership')
 check({p.name for p in (run/'payload').iterdir()}==payload_names and {p.name for p in (run/'output').iterdir()}==guard_names,'exact nine payloads and five guard outputs')
 check(not run.is_symlink() and all(not p.is_symlink() for p in run.rglob('*')),'no result symlinks')
 check({p.name for p in outer.iterdir()}=={'outer-ready.json','release.json','outer-invocation.json','outer-outcome.json'} and all(p.is_file() and not p.is_symlink() for p in outer.iterdir()),'exact four outer records')
 files={str(p) for p in run.rglob('*') if p.is_file()};check(len(files)==26,'26 result input files')
 s=rd(run/'sealed.json');ad=rd(run/'admission.json');cfg=rd(run/'config.json');pins=rd(run/'launch-pins.json');aud=rd(run/'audit.json');cl=rd(run/'outer-closure.json');inv=rd(run/'invocation.json');sup=inv['supervisor'];p=rd(run/'output/process.json');cur=rd(run/'output/current.json');ready=rd(outer/'outer-ready.json');release=rd(outer/'release.json');oi=rd(outer/'outer-invocation.json');outcome=rd(outer/'outer-outcome.json')
 check(sha(run/'sealed.json')=='38d528ef4d7110a5616c94d71d99ce5a5e60b41d9b9f2b15616a10b677f7203c' and sha(run/'admission.json')=='4a239a9182765ec7c8af15857ed2702db5244d037e66f46f4ea057ad3201aa58','exact previously reviewed seal and admission preserved')
 check(ad['accepted'] is True and ad['findings']==[] and ad['scope']=='P011 typed exact-run admission' and ad['phase']==phase and ad['pins_sha256']==sha(run/'sealed.json'),'admission acceptance scope/phase/pins')
 check(set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')} and bound(ad['sha256']) and bound(ad['evidence_sha256']),'all 1902 admission and evidence bindings')
 prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');required=rd(D/'required-paths.json')['paths']
 check(len(prep['sha256'])==258 and set(prep['sha256'])==set(required) and bound(prep['sha256']),'current preparation membership/bytes')
 check(pr['accepted'] is True and pr['findings']==[] and pr['launch_admitted'] is False and pr['pins_sha256']==sha(D/'preparation-pins.json') and set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and bound(pr['sha256']) and bound(pr['evidence_sha256']),'preparation review exact bindings')
 runtime=rd(D/'runtime-inputs-complete.json')['inventory'];baseline=rd(D/'baseline.json');stage=rd(D/'stages.json')['red']
 check(len(runtime)==609 and inventory(list(runtime),[])==runtime,'609 current runtime resolved paths/bytes')
 for label,root,n in [('diagnostic',R,514),('production',W,516)]:
  check(len(baseline[label])==n and set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(baseline[label]) and all(sha(root/k)==v for k,v in baseline[label].items()),label+' baseline exact membership/bytes')
 check(len(stage['sha256'])==75 and {str(q.relative_to(stage['path'])) for q in Path(stage['path']).rglob('*') if q.is_file()}==set(stage['sha256']) and all(sha(Path(stage['path'])/k)==v for k,v in stage['sha256'].items()),'75 stage files exact membership/bytes')
 prepared=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256'])
 expected=prepared|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in baseline[label]}|{str(Path(stage['path'])/n) for n in stage['sha256']}|{str(run/'host.json'),str(run/'config.json'),str(outer/'outer-ready.json')}
 check(s['files']==sorted(expected) and len(expected)==1901 and s['inputs']==[],'1901 exact sealed subjects')
 trees=[stage['path'],str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')),str(D.with_name('DIRECT-BG-P011-TYPED-REPAIR'))]
 check(s['trees']==trees and inventory(s['files'],s['trees'])==s['inventory'],'full sealed inventory unchanged')
 extra={str(run/'sealed.json'),str(run/'admission.json'),str(run/'prehost.json'),str(outer/'release.json'),str(outer/'outer-invocation.json')}
 check(pins['files']==sorted(set(s['files'])|extra) and pins['trees']==trees and pins['inputs']==[] and inventory(pins['files'],pins['trees'])==pins['inventory'],'1906 launch files complete inventory unchanged')
 check(rd(run/'output/pins.json')==pins and all(pins['inventory'][k]==v for k,v in s['inventory'].items()),'guard/seal/launch inventory linkage')
 expectedcmd=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+stage['path'],str(D/'driver.jl'),str(run/'payload'),stage['path'],phase]
 check(cfg==dict(phase=phase,mode='red',seconds=300,expected_exit=1,stage=stage['path'],run=str(run),output=str(run/'output'),payload=str(run/'payload'),command=expectedcmd) and s['config']==cfg and s['phase']==phase,'exact admitted RED command/config')
 check(release==dict(phase=phase,sealed_sha256=sha(run/'sealed.json'),admission_sha256=sha(run/'admission.json'),outer_ready_sha256=sha(outer/'outer-ready.json'),one_attempt=True) and release['one_attempt'] is True,'exclusive one-attempt release linkage')
 identity=ready['identity'];check(ready['waiting_only'] is True and ready['phase']==phase and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py'),'outer ready source binding')
 check(oi==dict(identity=identity,phase=phase,seal_sha256=sha(run/'sealed.json'),review_sha256=sha(run/'admission.json'),release_sha256=sha(outer/'release.json'),launcher_sha256=sha(D/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'exact outer invocation')
 check(outcome['identity']==identity==s['outer_identity']==cl['outer_identity'] and outcome['launched'] is True and type(outcome['returncode']) is int and outcome['returncode']==0 and outcome['error']=='','outer execution succeeded')
 res=rd(run/'reservation.json');check(res==dict(one_attempt=True,phase=phase,command=expectedcmd,pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300) and res['one_attempt'] is True,'exclusive one-attempt reservation')
 check(inv['reservation_sha256']==sha(run/'reservation.json') and inv['review_sha256']==sha(run/'admission.json') and inv['pins_sha256']==cur['pins_sha256']==p['pins_sha256']==sha(run/'launch-pins.json'),'invocation/reservation/review/pin linkage')
 guardcmd=[inv['python'],'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(run/'output'),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','1','--',*expectedcmd]
 check(inv['guard_command']==guardcmd and Path(inv['python']).resolve()==Path(sys.executable).resolve() and inv['command']==cur['command']==p['command']==expectedcmd and p['cwd']==str(R),'exact guard command/deadline/cwd')
 check(p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'],'guard/current/process identity linkage')
 for role,i in [('outer',identity),('guard',p['runner']),('child',p['child'])]:
  check(set(i)=={'pid','pgid','sid','start_ticks','boot_id','command'} and all(type(i[k]) is int and i[k]>0 for k in ('pid','pgid','sid','start_ticks')) and i['pid']==i['pgid']==i['sid'] and i['boot_id']==s['boot_id'] and bool(i['command']),role+' exact process identity')
 check(p['runner']['command']==' '.join(guardcmd)+' ' and p['child']['command']==' '.join(expectedcmd)+' ','recorded actual guard/child commands')
 check(type(p['returncode']) is int and p['returncode']==1 and p['reason']=='exit1' and type(sup['returncode']) is int and sup['returncode']==0 and sup['accepted'] is True,'Julia exit1 and guard/supervisor success')
 check(all(sup.get(k) is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in sup and not {'error','remaining_group','remaining_session'}&set(p),'no timeout/termination/cleanup failure')
 check(bounded(inv['elapsed_seconds']) and bounded(sup['elapsed_seconds']) and bounded(p['elapsed_including_launch'],292) and p['pins_unchanged'] is True,'inclusive 300/292 limits and final pins')
 resources=[json.loads(line) for line in (run/'output/resources.jsonl').read_text().splitlines()];last=-1
 check(len(resources)==9,'nine recorded resource samples')
 for j,z in enumerate(resources):
  check({'available_kib','swap_used_kib','elapsed'}<=set(z)<={'available_kib','swap_used_kib','elapsed','child_memory'} and bounded(z['elapsed'],p['elapsed_including_launch']) and z['elapsed']>=last and ('child_memory' not in z or type(z['child_memory']) is list and all(type(v) is str for v in z['child_memory'])),f'resource sample {j} shape/time')
  last=z['elapsed']
 check(set(p['terminal_memory'])=={'available_kib','swap_used_kib'},'terminal memory schema')
 check(all(integer(z[k]) for z in resources+[p['terminal_memory']] for k in ('available_kib','swap_used_kib')) and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[p['terminal_memory']]),'all resource samples and terminal satisfy 6GiB/1GiB thresholds')
 check(integer(p['child_maxrss_kib']) and p['child_maxrss_kib']>0,'positive recorded child maxRSS')
 data={q.name:tomllib.loads(q.read_text()) for q in (run/'payload').iterdir()};raw=data['raw.toml'];unit=data['unit-1.toml'];probe=data['probe.toml']
 for n in costs:
  m=data[n];check(set(m)=={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'} and integer(m['bytes']) and integer(m['events']) and all(bounded(m[k]) for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds')),n+' complete typed metrics')
 check(set(probe)=={'bytes','events','consumed_bytes','consumed_events','warm','bytes_decision','events_decision','values_unchanged','owners_unchanged'},'probe exact fields')
 check(all(type(probe[k]) is int and probe[k]==0 for k in ('bytes','events','consumed_bytes','consumed_events')) and probe['values_unchanged'] is True and probe['owners_unchanged'] is True,'probe four integer zero counters and value/owner flags')
 for k in ('warm','bytes_decision','events_decision'):
  d=probe[k];check(d==dict(start=1,count=0,accepted=False,reason='dimensions',finite=True,counters=[0]*20) and type(d['start']) is int and type(d['count']) is int and d['accepted'] is False and d['finite'] is True and all(type(v) is int for v in d['counters']),k+' complete typed decision')
 check(set(unit)=={'index','name','complete','fatal','tests','records'} and type(unit['index']) is int and unit['index']==1 and unit['name']=='panel' and unit['complete'] is True and unit['fatal']=='','unit completion/schema')
 sites={f'P{i:03}':1 for i in range(1,95)}
 for i,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:sites[f'P{i:03}']=n
 for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
  for i in range(lo,hi+1):sites[f'P{i:03}']=n
 rec=unit['records'];check(set(rec)=={'active','failure_count','apis','events','failures','sites'} and rec['active']=='' and rec['apis']==rec['events']=={} and rec['sites']==sites and all(type(v) is int for v in rec['sites'].values()) and sum(sites.values())==11760,'all 94 exact assertion site counts')
 testsource=str(D.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')/'panel-tests.jl')
 detail='Test Failed at '+testsource+':103\n  Expression: $(Expr(:escape, :(#= '+testsource+':103 =# @allocated(K._bgb_eligibility(f, 1)) == 0)))'
 check(len(detail)==439 and Path(testsource).read_text().splitlines()[102].strip()=='@check "P011" (@allocated K._bgb_eligibility(f,1)) == 0','independent P011 rendering source line')
 check(type(rec['failure_count']) is int and rec['failure_count']==1 and rec['failures']==[dict(detail=detail,kind='fail',site='P011')],'sole exact P011 failure with no prescribed byte amount')
 root=unit['tests'];fields={'name','pass','fail','error','broken','children'}
 check(set(root)==fields and root['name']=='panel' and all(type(root[k]) is int and root[k]==0 for k in ('pass','fail','error','broken')) and len(root['children'])==4,'root empty and four structural groups')
 names=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses'];expectedrows=[[22,1,0,0],[11619,0,0,0],[74,0,0,0],[44,0,0,0]]
 for i,(node,name,row) in enumerate(zip(root['children'],names,expectedrows)):
  check(set(node)==fields and node['name']==name and node['children']==[] and all(type(node[k]) is int for k in ('pass','fail','error','broken')) and [node[k] for k in ('pass','fail','error','broken')]==row,f'group {i+1} exact schema/counts')
 loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(stage['path'])/'src/JSimplex.jl'))
 check(set(raw)=={'blas_threads','complete','fatal','phase','qualification','schema','test_source','threads','totals','loaded','probe','unit'} and raw['complete'] is True and raw['fatal']=='' and type(raw['schema']) is int and raw['schema']==1 and raw['phase']==phase and raw['qualification']=='p011_typed_structural','raw exact schema/completion/scope')
 check(raw['loaded']==loaded and raw['test_source']==testsource and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'loaded module/test paths and thread counts')
 check(raw['totals']==[11759,1,0,0] and all(type(v) is int for v in raw['totals']) and raw['probe']==probe and raw['unit']==unit,'exact aggregate and duplicate probe/unit records')
 log=(run/'output/run.log').read_text();launchlog=(run/'launcher.log').read_text();token='TEST FAILURE: P011 '+detail
 check(not re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError',log+'\n'+launchlog,re.I) and log.count(token)==1 and not re.search(r'Test Failed|Test Error|TEST FAILURE',log.replace(token,'',1)+'\n'+launchlog,re.I),'warnings before exact expected-failure removal and no other failures')
 check(log==token+'\n' and json.loads(launchlog)==p,'complete Julia/launcher log contents')
 check(aud['all_passed'] is True and aud['pure_timeout'] is False and aud['error']=='' and aud['phase']==phase and aud['process_elapsed_seconds']==inv['elapsed_seconds'],'saved admitted audit successful')
 check(set(aud['sha256'])==files-{str(run/'audit.json'),str(run/'outer-closure.json')} and bound(aud['sha256']),'exact 24 auditor bindings')
 check(aud['result']['totals']==raw['totals'] and aud['result']['probe']==probe and aud['result']['preparation']=={n:data[n] for n in costs} and aud['result']['expected_failure_sites']==['P011'],'saved audit agrees with independently parsed payload')
 closurepaths={str(outer/n) for n in ('outer-ready.json','release.json','outer-invocation.json','outer-outcome.json')}|{str(run/n) for n in ('sealed.json','admission.json','posthost.json','audit.json')}
 check(cl['all_passed'] is True and set(cl['sha256'])==closurepaths and bound(cl['sha256']),'exact eight external closure bindings')
 hosts=[rd(run/n) for n in ('host.json','prehost.json','posthost.json')]+[cl['host']]
 for i,h in enumerate(hosts):
  check(h['matches']==[] and h['unreadable_identity_pids']==[] and h['head']==s['head']==HEAD and h['master']==s['master']==MASTER and h['boot_id']==s['boot_id'] and set(h['remote'].splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},f'host evidence {i} clean identities/refs/boot')
 historical=set(rd(D/'historical-groups.json')['groups']);groups=historical|{i[k] for i in (identity,p['runner'],p['child']) for k in ('pgid','sid')}
 check(len(historical)==280 and set(s['groups'])==historical and set(hosts[0]['groups'])==set(hosts[1]['groups'])==historical and set(hosts[2]['groups'])==groups-{identity['pid']} and set(hosts[3]['groups'])==groups and len(groups)==283,'exact group AND session coverage through external closure')
 post=rd(E/'postcheck.json');postfiles=files|{str(q) for q in outer.iterdir()}|{str(E/n) for n in ('host-entry.json','entry-check.json','request.txt','outer.log','postcheck.py')}
 check(post['all_passed'] is True and len(post['checks'])==12 and all(v is True for v in post['checks'].values()) and set(post['sha256'])==postfiles and bound(post['sha256']),'author postcheck exact preserved 35 bindings and 12 positive checks')
 resource_summary=dict(samples=len(resources),min_available_kib=min(z['available_kib'] for z in resources),max_swap_used_kib=max(z['swap_used_kib'] for z in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'])
 check(post['totals']==raw['totals'] and post['failures']==rec['failures'] and post['probe']==probe and post['preparation']=={n:data[n] for n in costs} and post['resource_summary']==resource_summary and post['process_seconds']==p['elapsed_including_launch'] and post['supervisor_seconds']==sup['elapsed_seconds'],'author summary agrees with saved data')
 check(git('rev-parse','HEAD')==HEAD and git('rev-parse','master')==MASTER and git('rev-parse','HEAD',root=W)==MASTER,'fresh local diagnostic/master/production refs')
 remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');check(set(remote.splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'fresh remote refs')
 env=rd(D/'environment.json');check({k:os.environ.get(k) for k in env}==env,'current exact loading environment')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[];unreadableidentity=[]
 for q in Path('/proc').glob('[0-9]*'):
  try:
   f=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();argv0=(q/'cmdline').read_bytes().split(b'\0')[0].decode(errors='replace');exe=''
   try:exe=str((q/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(q.name))
   except FileNotFoundError:pass
   if int(f[2]) in groups or int(f[3]) in groups or any(Path(v).name.lower().startswith('julia') for v in (comm,argv0,exe)):matches.append(dict(pid=int(q.name),pgid=int(f[2]),sid=int(f[3]),comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadableidentity.append(int(q.name))
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
 host=dict(time=time.time(),boot_id=boot,head=HEAD,master=MASTER,remote=remote,groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadableidentity,memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
 result['host']=host
 check(boot==s['boot_id'] and matches==[] and unreadableidentity==[],'fresh independent 283 groups AND sessions absent and no visible Julia')
 check(host['memory']['available_kib']>=6*1024**2 and host['memory']['swap_used_kib']<=1024**2,'fresh memory above guard thresholds')
 check(not (D/'runs/p011-green300').exists() and not (D/'outers/p011-green300').exists(),'no GREEN run or outer')
 result.update(all_passed=True,findings=[],totals=raw['totals'],group_counts=expectedrows,probe=probe,failure=rec['failures'][0],costs={n:data[n] for n in costs},resource_summary=resource_summary,process_seconds=p['elapsed_including_launch'],supervisor_seconds=sup['elapsed_seconds'],invocation_seconds=inv['elapsed_seconds'],outer_seconds=outcome['elapsed_with_checks_seconds'],bindings={n:sha(n) for n in sorted(files)},sealed_files=len(s['files']),launch_files=len(pins['files']))
except Exception as error:result.update(all_passed=False,findings=[repr(error)])
result['finished']=time.time()
with (E/'result-review-check.corrected.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ('all_passed','findings','totals','resource_summary','process_seconds','supervisor_seconds') if k in result},indent=2));print('checks',len(checks))
if not result['all_passed']:sys.exit(1)
