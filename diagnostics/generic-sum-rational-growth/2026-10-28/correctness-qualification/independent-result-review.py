from pathlib import Path
import json,hashlib,re,os,subprocess,datetime
K=Path(__file__).resolve().parent;D=K.parent;M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):
 with (K/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
pins=read(K/'pins.json');need(len(pins['inventory'])==1311,'pin count')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership')
for prior in ['pins.json','pins-reviewed.json','pins-ready.json']:
 need(all(pins['inventory'].get(n)==v for n,v in read(D/prior)['inventory'].items()),'prior inventory '+prior)
for prior in ['admission.json','admission-reviewed.json','admission-ready.json','decoder-root-cause-review.json']:
 for n,v in read(D/prior)['bindings'].items():need(sha(n)==v,'prior binding '+n)
for section in read(K/'protected-before.json').values():
 for n,v in section.items():need(sha(n)==v,'protected '+n)
for name in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((K/'guard'/name).read_bytes()==(D/'guard'/name).read_bytes(),'guard copy')
for name in ['common.py','launch.py','environment.json','protected-before.json']:need((K/name).read_bytes()==(D/name).read_bytes(),'unchanged launcher '+name)
for record in [read(K/'admission.json'),read(K/'audit.json'),read(D/'cost-qualification-review.json')]:
 need(record['accepted'] is True,'accepted admission/audit/static review')
 for n,v in record['bindings'].items():need(sha(n)==v,'accepted binding '+n)
con=read(K/'contract.json');p=read(K/'output/process.json');sup=read(K/'supervisor.json');done=read(K/'completed.json');audit=read(K/'audit.json');inv=read(K/'invocation.json');res=read(K/'reservation.json');log=(K/'output/run.log').read_text()
need(p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] is True,'process success')
need(sup['accepted'] is True and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and not sup['abnormal_cleanup_attempted'] and 'cleanup_error' not in sup,'supervisor success')
need(done['accepted'] is True and done['pins_unchanged'] is True and done['elapsed_shared_seconds']<=900 and sup['elapsed_seconds']<=900,'shared deadline')
need(p['command']==con['command']==inv['Julia_command'] and p['pins_sha256']==sha(K/'pins.json')==res['pins_sha256'],'command/pin linkage')
need(res['admission_sha256']==sha(K/'admission.json') and res['guard_deadline']==res['started_monotonic']+892 and res['outer_deadline']==res['started_monotonic']+900,'admission/deadline linkage')
need(inv['common_started']==res['started_monotonic'] and inv['guard_deadline']==res['guard_deadline'] and inv['outer_deadline']==res['outer_deadline'],'invocation deadline')
need(sup['guard_identity']['command']==' '.join(inv['command'])+' ','exact guard command')
gate=read(K/'output/gate.json');cur=read(K/'output/current.json');permit=read(K/'output/permit.json')
need(p['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and p['child']==cur['child']==gate['identity'],'identities')
need(gate['command']==cur['command']==permit['command']==con['command'] and gate['parent_death_signal']==9,'gate command/signal')
need(gate['current_sha256']==sha(K/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(K/'output/permit.json') and sha(K/'output/pins.json')==sha(K/'pins.json'),'gate/copied hashes')
need(not re.search(r'^ERROR:',log,re.M) and 'Test Failed at ' not in log and 'Error During Test' not in log,'ordinary no errors/failures')
need(re.findall(r'^Test Summary:.*?\|\s*(.*?)$',log,re.M)==['Pass  Total     Time'],'summary schema')
need(re.search(r'^SRG corrected exact-decoder qualification\s*\|\s*28227\s+28227\s+[^\n]+$',log,re.M),'exact ordinary total')
need(log.count('SRG_CORRECTNESS_COMPLETE')==1,'success marker')
contexts=[f'BF{bits}_{mode}' for bits in [64,128,256] for mode in ['Nearest','Down','Up','ToZero','FromZero']]+['Float32','Float64','Rational{BigInt}','Rational{Int64}']
need(re.findall(r'^CONTEXT (.*)$',log,re.M)==contexts,'all 19 ordered contexts')
need(con['expected_assertions']==28227 and con['measured_windows']==0 and not (K/'output/results.toml').exists(),'correctness only')
need(audit['assertions']==28227 and audit['measured_windows']==0 and audit['original_comparison_remains_failed'] is True and audit['auditor_not_in_original_launch_manifest'] is True,'honest supplemental audit')
resources=[json.loads(line) for line in (K/'output/resources.jsonl').read_text().splitlines()]
need(bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resource samples')
need(p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
for name in ['host-after.json','audit-host.json']:need(len(read(K/name)['groups'])==653 and read(K/name)['no_Julia'] is True,'recorded closure')
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in OVERRIDES),'environment override')
need({k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(K/'environment.json')['inherited'],'environment drift')
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(all(git(M,'rev-parse',v)=='ce5d4a74019e0dc2e656d08161641c498b159e7b' for v in ['HEAD','master','origin/master']),'master refs')
need(git(R,'rev-parse','HEAD')=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic HEAD')
need(not git(M,'diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
old=read(K/'host-seed.json');parentgroups=set(old['groups']);newgroups={p[k][v] for k in ['runner','child'] for v in ['pgid','sid']};groups=parentgroups|newgroups
need(len(parentgroups)==651 and len(groups)==653 and groups==parentgroups|newgroups,'all historical and failed-run groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==old['boot_id'],'boot changed')
allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed identity allowance')
permitted=read(allowance)['identities'];processes=[];collisions=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v];comm=(proc/'comm').read_text().strip()
  ident=dict(pid=int(proc.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd,boot_id=boot)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]),'live Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in permitted,'historical group/session collision');collisions.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-result-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,verified_unrelated_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report="""# Independent qualification result: accepted

The actual ordinary Test run passed all 28,227 expected assertions across the exact 19 ordered contexts. Its process exited0; the guard and supervisor accepted it without timeout or abnormal cleanup. Inclusive elapsed time was71.526421053 seconds within900. No measurement windows or results.toml were produced, so no cost measurements were repeated.

The admitted source is unchanged. The passing assertions include all original whole-function parity, input-value/owner, finite/zero/exception, rounding/precision and state/storage/priority checks. For each of90 stored512 recovery probes, the old ambient decoder matches its independently derived rounded rational and differs from the original exact target, while conversion scoped only to the result's stored precision equals that unchanged target and restores ambient precision/rounding. This supports the decoder-only diagnosis; it does not modify or relabel the original failed comparison.

All1,311 pins and previous inventories, launch admission and supplemental-auditor bindings were freshly verified. Raw command/guard/session identities, startup gate signal/hash links, copied pins, exact root Test totals and marker, every resource sample, terminal memory and deadline records agree. Current independent closure checked all653 historical identifiers as both groups and sessions, boot/start-ticks/commands, the fixed unrelated-process allowance, no Julia, protected files/indexes, refs and environment.

No unnecessary production work or retained memory was introduced: this was an unchanged-candidate correctness run with extra decoder validation only. No Julia or previous auditor was rerun by this independent result review. The original cost comparison still records111,259 passes and90 decoder failures and remains frozen. This accepted qualification permits the separately accepted canonical qualified auditor to evaluate those preserved raw costs; it does not itself accept performance claims or production integration.
"""
with (K/'RESULT-REVIEW.md').open('x') as f:f.write(report)
paths=[K/n for n in ['audit.json','audit.py','admission.json','contract.json','pins.json','driver.jl','extra-corrected.jl','oracle-correction.json','output/process.json','output/run.log','output/resources.jsonl','output/gate.json','output/current.json','output/permit.json','output/pins.json','supervisor.json','completed.json','reservation.json','invocation.json','host-after.json','audit-host.json','independent-result-review.py','independent-result-host.json','RESULT-REVIEW.md']]+[D/n for n in ['cost-qualification-review.json','decoder-root-cause-review.json','output/process.json','output/run.log','output/results.toml']]
put('result-review.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in paths},assertions=28227,contexts=19,measured_windows=0,elapsed_shared_seconds=done['elapsed_shared_seconds'],original_comparison_passed=False,cost_results_accepted=False,Julia_executed=False))
print(json.dumps(dict(accepted=True,findings=0,assertions=28227,contexts=19,measured_windows=0,elapsed_shared_seconds=done['elapsed_shared_seconds'],fresh_groups_and_sessions=653)))
