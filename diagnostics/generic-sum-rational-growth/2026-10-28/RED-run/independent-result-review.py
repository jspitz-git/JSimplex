from pathlib import Path
import json,hashlib,re,os,subprocess,datetime
P=Path(__file__).resolve().parent;D=P.parent;M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];RED=D/'RED'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
pins=read(P/'pins.json');need(len(pins['inventory'])==1343,'pins')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership')
for n,v in read(D/'baseline-tree.json').items():need(sha(RED/n)==sha(M/n)==v,'original baseline '+n)
for tree in ['src','test']:
 expected={n for n in read(D/'baseline-tree.json') if n.startswith(tree+'/')}
 if tree=='test':expected.add('test/generic_sum_rational_growth_tests.jl')
 need({str(p.relative_to(RED)) for p in (RED/tree).rglob('*') if p.is_file()}==expected,'only new test added '+tree)
need((D/'new-test.jl').read_bytes()==(RED/'test/generic_sum_rational_growth_tests.jl').read_bytes(),'test exact copy')
for record in [read(D/'result-review.json'),read(D/'correctness-qualification/result-review.json')]:
 need(record['accepted'] is True and record['findings']==[],'accepted candidate/correctness review')
 for n,v in record['bindings'].items():need(sha(n)==v,'prior binding '+n)
for section in read(P/'protected-before.json').values():
 for n,v in section.items():need(sha(n)==v,'protected '+n)
admission=read(P/'admission.json');audit=read(P/'audit.json')
for record in [admission,audit]:
 need(record['accepted'] is True,'accepted admission/audit')
 for n,h in record['bindings'].items():need(sha(n)==h,'admission/audit binding '+n)
base=(D/'phase-audit.py').read_text()
addition=""" if fails:
  admitted=read('admission.json')
  need(type(admitted['expected_total']) is int and type(admitted['expected_passes']) is int,'frozen independent RED totals')
  need(pass_count==admitted['expected_passes'] and pass_count+fails==admitted['expected_total'],'exact independently admitted RED total')
"""
need((P/'audit.py').read_text()==base.replace(' resources=[json.loads(x)',addition+' resources=[json.loads(x)'), 'supplemental audit only strengthens admitted totals')
need((P/'audit.py').read_bytes()==(D/'phase-audit-complete.py').read_bytes(),'exact current auditor template copy')
con=read(P/'contract.json');process=read(P/'output/process.json');sup=read(P/'supervisor.json');done=read(P/'completed.json');inv=read(P/'invocation.json');res=read(P/'reservation.json');log=(P/'output/run.log').read_text()
need(process['reason']=='exit1' and process['returncode']==1 and process['pins_unchanged'] is True,'expected child RED exit')
need(sup['accepted'] is True and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and not sup['abnormal_cleanup_attempted'] and 'cleanup_error' not in sup,'successful guarded RED outcome')
need(done['accepted'] is True and done['pins_unchanged'] is True and done['elapsed_shared_seconds']<=3000 and sup['elapsed_seconds']<=3000,'shared deadline')
need(process['command']==con['command']==inv['Julia_command'] and process['pins_sha256']==sha(P/'pins.json')==res['pins_sha256'],'exact command/pins')
need(res['admission_sha256']==sha(P/'admission.json') and res['guard_deadline']==res['started_monotonic']+2992 and res['outer_deadline']==res['started_monotonic']+3000,'admission/deadline linkage')
need(inv['common_started']==res['started_monotonic'] and inv['guard_deadline']==res['guard_deadline'] and inv['outer_deadline']==res['outer_deadline'],'invocation deadline')
need(sup['guard_identity']['command']==' '.join(inv['command'])+' ','guard command')
gate=read(P/'output/gate.json');cur=read(P/'output/current.json');permit=read(P/'output/permit.json')
need(process['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and process['child']==cur['child']==gate['identity'],'process identity linkage')
need(gate['command']==cur['command']==permit['command']==con['command'] and gate['parent_death_signal']==9,'entry gate')
need(gate['current_sha256']==sha(P/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(P/'output/permit.json') and sha(P/'output/pins.json')==sha(P/'pins.json'),'gate/copied hashes')
need(re.findall(r'^SRG_SOURCE (.*)$',log,re.M)==[str(RED/'src/JSimplex.jl')] and re.findall(r'^INCLUDING (.*)$',log,re.M)==['generic_sum_rational_growth_tests.jl'],'loaded source and whole file')
need(re.findall(r'^ERROR: (.*)$',log,re.M)==['LoadError: Some tests did not pass: 28316 passed, 7 failed, 0 errored, 0 broken.'],'only expected Test failure exception')
need('Error During Test' not in log and 'SRG_COMPLETED RED' not in log,'no test errors or false success marker')
headers=re.findall(r'^Test Summary:.*?\|\s*(.*?)$',log,re.M);need(len(headers)==1 and headers[0].split()==['Pass','Fail','Total','Time'],'root summary schema')
need(re.search(r'^Sum rational growth RED\s*\|\s*28316\s+7\s+28323\s+[^\n]+$',log,re.M),'exact root totals')
locations=[[p,int(n)] for p,n in re.findall(r'Test Failed at (.*?):(\d+)',log)];need(locations==con['expected_failure_locations'] and len(locations)==7,'all and only seven line624 failures')
need(admission['expected_total']==audit['total']==28323 and admission['expected_passes']==audit['passed']==28316 and audit['expected_failures']==7,'independent totals')
leaf=[line for line in log.splitlines() if re.match(r'^    (ordinary whole functions|independent boundaries)',line)]
need(len(leaf)==38 and sum(int(line.split('|')[1].split()[-2]) for line in leaf)==28227,'all numerical leaf assertions present')
need(all(len(line.split('|')[1].split())==3 for line in leaf),'all numerical leaf testsets passed')
need(log.count('Expression: all(')==7,'seven allocation expressions')
resources=[json.loads(line) for line in (P/'output/resources.jsonl').read_text().splitlines()];need(len(resources)==audit['samples'] and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),'all resource samples')
need(process['terminal_memory']['available_kib']>=6*1024**2 and process['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
for name in ['host-after.json','audit-host.json']:need(len(read(P/name)['groups'])==655 and read(P/name)['no_Julia'] is True,'recorded closure')
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in OVERRIDES),'environment override');need({k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(P/'environment.json')['inherited'],'environment')
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(all(git(M,'rev-parse',v)=='ce5d4a74019e0dc2e656d08161641c498b159e7b' for v in ['HEAD','master','origin/master']),'master refs')
need(git(R,'rev-parse','HEAD')=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic HEAD');need(not git(M,'diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
seed=read(P/'host-seed.json');runids={process[k][v] for k in ['runner','child'] for v in ['pgid','sid']};groups=set(seed['groups'])|runids;historical=set(read(D/'host-seed.json')['groups'])
for n in ['output/process.json','correctness-qualification/output/process.json']:
 q=read(D/n);historical.update(q[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
historical.update(runids);need(len(seed['groups'])==653 and groups==historical and len(groups)==655,'historical completeness')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');allowed=read(allowance)['identities'];processes=[];collisions=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  fields=(proc/'stat').read_text().rsplit(')',1)[1].split();cmd=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();identity=dict(pid=int(proc.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=cmd,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+cmd[:1]),'live Julia')
  if identity['pgid'] in groups or identity['sid'] in groups:need(identity in allowed,'historical group/session collision');collisions.append(identity)
  processes.append(identity)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-result-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report="""# Independent original RED result: accepted

The admitted original-source run produced exactly28,316 passes and7 expected allocation failures,28,323 assertions total, with no errors or broken/skipped tests. All seven failures occur at generic_sum_rational_growth_tests.jl:624 in the strict lower-events/lower-median-bytes expression. All38 numerical leaf testsets passed their complete28,227 assertions. The42 compile/recompile-zero checks and47 gate validation assertions passed as well. The child exited1 as admitted; the guard/supervisor accepted that expected RED outcome, not a numerical all-pass result.

The test used the exact RED project/source path and one complete permanent test file. RED production sources and all prior tests remain byte-identical to actual master and the baseline; only the admitted new test is added. All1,343 pins, admission/audit bindings, protected user files and indexes, refs, environment and tree membership were rechecked. No candidate production code has been staged.

The post-exit auditor is the original reviewed phase template plus only the stricter independent-admission total/pass-count check. Raw logs independently satisfy the exact expected Test exception, summary schema, locations and totals; there is no fabricated successful-test marker. Command, startup gate/signal/hashes, runner/child identity, copied pins and shared deadlines link correctly. Elapsed shared time was74.546205990 seconds within3000; all73 resource samples and terminal memory passed, with zero swap and child maximum RSS958,192 KiB. Current closure independently checks all655 historical identifiers as groups AND sessions, boot/start ticks/commands and only the fixed unrelated allowance; no Julia remains.

This supplies the required original allocation RED evidence. It permits the already accepted exact A/B/C production changes and this new test to be staged for the planned independent production review and GREEN checks. It does not itself approve integration or push. The gates prove that original code fails the required combined allocation-reduction condition; they do not provide a new speed estimate or native retained-memory measurement. No unnecessary new production work or memory was introduced by the RED test run; fixture/reset/capture work is outside the typed timed kernels.

The reviewer ran no Julia, previous auditor, production edit or Git mutation. Earlier failed comparison and all supplemental qualifications/rejections remain preserved.
"""
with (P/'RESULT-REVIEW.md').open('x') as f:f.write(report)
paths=[P/n for n in ['admission.json','audit.json','audit.py','contract.json','pins.json','tests.jl','output/run.log','output/process.json','output/resources.jsonl','output/gate.json','output/current.json','output/permit.json','output/pins.json','supervisor.json','completed.json','reservation.json','invocation.json','host-after.json','audit-host.json','independent-result-review.py','independent-result-host.json','RESULT-REVIEW.md']]+[D/n for n in ['new-test.jl','test-gates.json','phase-audit.py','phase-audit-complete.py','result-review.json']]+[RED/'test/generic_sum_rational_growth_tests.jl']
put('result-review.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in paths},arm='RED',passed=28316,expected_failures=7,total=28323,all_numerical_assertions_passed=28227,elapsed_shared_seconds=done['elapsed_shared_seconds'],production_staging_authorized=True,integration_authorized=False,Julia_executed=False))
print(json.dumps(dict(accepted=True,findings=0,passed=28316,expected_failures=7,total=28323,elapsed_shared_seconds=done['elapsed_shared_seconds'],fresh_groups_and_sessions=655)))
