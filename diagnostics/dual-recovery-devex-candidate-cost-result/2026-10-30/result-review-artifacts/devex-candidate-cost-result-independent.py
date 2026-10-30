from pathlib import Path
import ast,hashlib,json,math,os,re,statistics,struct,subprocess,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-candidate-cost-result/2026-10-30';P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';ROOT=W/'.superpowers/dual-recovery-devex-task4/cost-1';R=ROOT/'candidate-cost';F=ROOT/'reference-cost';T=Path('/tmp/devex-candidate-cost-run-20261030');H='14720147d8850525c0603921064dfe3ba83d3fcb';M='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
checks={};bindings={}
def ck(n,x):
 assert type(x) is bool,(n,type(x));checks[n]=x
 if not x:raise AssertionError(n)
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 v=h.hexdigest();bindings[str(p)]=v;return v
def txt(p):sha(p);return Path(p).read_text()
def read(p):return json.loads(txt(p))
def verify(n,a,count=None):
 if count is not None:ck(n+' count',len(a)==count)
 for p,h in a.items():ck(n+' '+p,sha(p)==h)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def exact(n,p,v):ck(n,read(p)==v)
def good_checks(n,a):ck(n,type(a) is dict and bool(a) and all(type(v) is bool and v for v in a.values()))
# Bind every submitted preparation/source and every result/publication file without executing code.
for folder in (P,D):
 for p in sorted(folder.rglob('*')):
  if p.is_file():sha(p)
for n in ('preflight.py','preflight.json','admission-check.py','postcheck.py','prelaunch-full-host.json','close-publish.py','write-report.py','write-report-2.py','prepare-report-fix.py'):sha(T/n)
for n in ('audit.py','common.py','cost_checks.py','binding_checks.py','launch.py','seal.py','close.py','close-publish.py'):ast.parse(txt(P/n))
ast.parse(txt(T/'close-publish.py'))
contract=read(P/'contract.json');ck('driver exact',sha(O/'cost.jl')==contract['driver_sha256']);ck('reference exact',sha(O/'tests/reference.jl')==contract['reference_sha256'])
post=read(D/'postcheck.json');good_checks('postcheck11',post['checks']);ck('postcheck count',len(post['checks'])==11)
for kind,count in [('portable',22),('external_exact_copies',102)]:
 ck(kind+' count',len(post[kind])==count)
 for s,v in post[kind].items():ck(kind+' '+s,sha(s)==sha(v['copy'])==v['sha256'])
ad=read('/tmp/devex-candidate-cost-numerical-admission.json');verify('candidate admission',ad['bindings'],964);good_checks('candidate admission4744',ad['checks']);ck('ad checks count',len(ad['checks'])==4744);ck('ad report',sha(ad['review_report'])==ad['review_report_sha256']);exact('copied admission',R/'numerical-admission.json',ad)
refad=read(F/'numerical-admission.json');verify('reference admission',refad['bindings'],801)
refreview=read(W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30/review-final.json');verify('reference result',refreview['bindings'],934);ck('reference scope',refreview['accepted'] is True and refreview['runtime_accepted'] is True and refreview['cost_qualified'] is False and refreview['production_admission'] is False)
refclosure=read(W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30/closure.json');verify('reference publication closure',refclosure['bindings'],114)
publications=[]
for folder in [O,*[W/('diagnostics/'+n+'/2026-10-30') for n in ('dual-recovery-devex-task4-red','dual-recovery-devex-task4-green','dual-recovery-devex-green-fixture-preparation','dual-recovery-devex-green2-admission','dual-recovery-devex-green2-result')],P]:
 pub=read(folder/'publication.json');ck('publication accepted '+str(folder),pub['accepted'] is True);publications.extend(pub['expected_names'])
ck('560 committed lineage names',len(set(publications))==560)
tracked={row.split('\t',1)[1]:row.split()[2] for row in git('ls-tree','-r',H).splitlines()}
for name in sorted(set(publications)):
 p=W/name;sha(p);b=p.read_bytes();ck('committed blob '+name,hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==tracked[name])
basepins=None;owners=[];records={};counts={}
for phase,pin_count,nraw,nclosed,naudit,nad in [('reference-cost',566,21,22,21,801),('candidate-cost',589,22,23,43,964)]:
 r=ROOT/phase;side=phase.split('-')[0];pins=read(r/'pins.json');seal=read(r/'seal.json');attempt=read(r/'attempt.json');audit=read(r/'audit.json');closed=read(r/'closed.json');done=read(r/'completion.json');proc=read(r/'guard/process.json');sup=read(r/'supervisor.json');admission=read(attempt['admission_path']);records[side]=dict(pins=pins,seal=seal,attempt=attempt,audit=audit,closed=closed,done=done,proc=proc,sup=sup)
 ck(phase+' runtime count',len([p for p in r.rglob('*') if p.is_file()])==nraw)
 ck(phase+' pin count',len(pins['inventory'])==pin_count);ck(phase+' inventory membership',len(pins['files'])==pin_count and set(pins['files'])==set(pins['inventory']) and pins['trees']==pins['inputs']==[])
 for p,v in pins['inventory'].items():ck(phase+' pin '+p,sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'])
 if basepins is None:basepins=set(pins['inventory'])
 else:ck('candidate exactly reference plus23',set(pins['inventory'])==basepins|{str(p) for p in F.rglob('*') if p.is_file()}|{records['reference']['attempt']['admission_path'],refad['review_report']})
 verify(phase+' audit bindings',audit['bindings'],naudit);verify(phase+' closed bindings',closed['bindings'],nclosed)
 ck(phase+' exact closed membership',set(closed['bindings'])=={str(p) for p in r.rglob('*') if p.is_file() and p.name!='closed.json'}|{attempt['admission_path'],admission['review_report']})
 expected={str(p) for p in r.rglob('*') if p.is_file() and p.name not in ('closed.json','audit.json')}|{attempt['admission_path'],admission['review_report']}
 if side=='candidate':expected|={str(p) for p in F.rglob('*') if p.is_file()}
 ck(phase+' exact audit membership',set(audit['bindings'])==expected)
 ck(phase+' outcomes',audit['accepted'] is True and audit['error'] is None and audit['test_summary']==dict(Pass=272,Total=272) and closed['accepted'] is True and audit['production_admission'] is False)
 ck(phase+' process',type(proc['returncode']) is int and proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['command']==seal['command']==contract['commands'][phase] and seal['environment']==contract['environments'][phase])
 ck(phase+' supervisor',sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0 and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')) and 'cleanup_error' not in sup)
 ck(phase+' pins seal',sha(r/'pins.json')==seal['pins_sha256']==proc['pins_sha256']);exact(phase+' guard pins',r/'guard/pins.json',pins)
 ck(phase+' attempt hashes',sha(r/'seal.json')==attempt['seal_sha256'] and sha(attempt['admission_path'])==attempt['admission_sha256'])
 ck(phase+' admission seal',admission['seal_sha256']==sha(r/'seal.json') and admission['pins_sha256']==sha(r/'pins.json') and admission['head']==seal['head'])
 ck(phase+' python',seal['guard_python'] in pins['inventory'] and str(Path(seal['guard_python']).resolve())==pins['inventory'][seal['guard_python']]['resolved'])
 invocation=read(r/'invocation.json');remaining=1800-seal['used_seconds'];command=[seal['guard_python'],'-B',str(P/'guard/guard_reviewed.py'),'run',str(r/'pins.json'),str(r/'guard'),'--expected-exit','0','--seconds',str(remaining-12),'--deadline',str(attempt['started_monotonic']+remaining-12),'--',*seal['command']]
 ck(phase+' invocation',invocation==dict(command=command,cwd=str(P),environment=seal['environment']))
 gate=read(r/'guard/gate.json');cur=read(r/'guard/current.json');permit=read(r/'guard/permit.json')
 ck(phase+' gate',gate['identity']==proc['child'] and gate['parent']==proc['runner'] and gate['parent_death_signal']==9 and gate['command']==seal['command'] and gate['current_sha256']==sha(r/'guard/current.json') and gate['permit_sha256']==sha(r/'guard/permit.json') and permit==dict(current_sha256=sha(r/'guard/current.json'),command=seal['command']) and cur['child']==proc['child'] and cur['runner']==proc['runner'] and cur['command']==seal['command'])
 owners.extend([attempt['runner'],proc['runner'],proc['child']])
 for owner in [attempt['runner'],proc['runner'],proc['child']]:ck(phase+' owner '+str(owner['pid']),owner['pid']==owner['pgid']==owner['sid'] and type(owner['start_ticks']) is int and owner['start_ticks']>0 and bool(owner['command']) and owner['boot_id']==closed['host']['boot_id'])
 log=txt(r/'guard/run.log');ck(phase+' ordinary272',len(re.findall(r'^TASK4_COST\s+\|\s+272\s+272\s+\S+\s*$',log,re.M))==1 and log.splitlines().count('TASK4_COST_COMPLETED '+side)==1 and not any(x in log.lower() for x in ('error during test','test failed at','segmentation fault','error:','world age')))
 samples=[json.loads(s) for s in txt(r/'guard/resources.jsonl').splitlines()];counts[side+'_resources']=len(samples);ck(phase+'37 resource samples',len(samples)==37)
 ck(phase+' resources',all(type(s['available_kib']) is int and type(s['swap_used_kib']) is int and s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in [*samples,proc['terminal_memory']]))
 if side=='candidate':ck('candidate min/swap',min(q['available_kib'] for q in samples)==22276368 and max(q['swap_used_kib'] for q in samples)==0)
# Independent bit, type, work and statistics reconstruction; no imported submitted code.
def bits(v,T):return struct.pack('>f' if T=='Float32' else '>d',v).hex()
def stats(v):
 m=statistics.median(v);return dict(median=m,minimum=min(v),maximum=max(v),MAD=statistics.median([abs(x-m) for x in v]),values=v)
def profile(n,s):ck(n,all(type(s[k]) in (int,float) and math.isfinite(s[k]) and s[k]>=0 for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds')) and all(type(s[k]) is int and s[k]>=0 for k in ('bytes','events')))
raw={}
for side,r in [('reference',F),('candidate',R)]:
 a=tomllib.loads(txt(r/'result.toml'));raw[side]=a;ck(side+'8 cases',a['side']==side and len(a['cases'])==8)
 for i,(T0,layout,bad) in enumerate((t,l,b) for t in ('Float32','Float64') for l in ('sparse','dense') for b in (False,True)):
  q=a['cases'][i];n=f'{side} case{i}';ck(n+'key/types',q['type']==T0 and q['layout']==layout and q['unreliable'] is bad and type(q['dimension']) is int and q['dimension']==64 and type(q['nnz']) is int and q['nnz']==(190 if layout=='sparse' else 4096))
  matrix=[bits(64. if row==col else ((-1 if (row+col)%2==0 else 1)*(1+(row+2*col)%5)/64 if layout=='dense' or abs(row-col)==1 else 0.),T0) for col in range(1,65) for row in range(1,65)]
  ck(n+'matrix bits',q['matrix_bits']==matrix);ck(n+'policy bits',q['policy_solve_tolerance_bits']==('38000000' if T0=='Float32' else '3d30000000000000'));ck(n+'schedule',len(q['warm'])==3 and len(q['samples'])==7)
  ck(n+'total work',all(type(q[k]) is int and q[k]==(10 if bad else 0) for k in ('solve_entries_total','stop_entries_total')))
  profile(n+'prep',q['preparation']);profile(n+'gc',q['post_warm_gc'])
  for j,w in enumerate(q['warm']):profile(n+'warm'+str(j),w)
  for j,s in enumerate(q['samples'],1):
   z=n+'sample'+str(j);profile(z,s);ck(z+'index',type(s['index']) is int and s['index']==j);ck(z+'zero counters',all(s[k]==0 for k in ('bytes','events','compile_seconds','recompile_seconds','gc_seconds')));ck(z+'bools',s['finite'] is True and s['reliable'] is (not bad) and s['owners_preserved'] is True)
   ck(z+'bits',s['point_bits']==[bits(.5 if bad else 1.,T0)]+[bits(0.,T0)]*63 and s['rhs_bits']==matrix[::64] and s['absolute_bits']==bits(32. if bad else 0.,T0) and s['relative_bits']==bits(1/3 if bad else 0.,T0));ck(z+'work',all(type(s[k]) is int and s[k]==int(bad) for k in ('solve_entries','stop_entries')))
 ck(side+'80API40B40stop8GC',sum(len(q['warm'])+len(q['samples']) for q in a['cases'])==80 and sum(q['solve_entries_total'] for q in a['cases'])==40 and sum(q['stop_entries_total'] for q in a['cases'])==40 and len(a['cases'])==8)
comparison=read(R/'comparison.json');recomputed=[]
for a,b in zip(raw['reference']['cases'],raw['candidate']['cases']):
 rs={k:stats([s[k] for s in a['samples']]) for k in ('seconds','bytes','events','gc_seconds')};cs={k:stats([s[k] for s in b['samples']]) for k in ('seconds','bytes','events','gc_seconds')};g=dict(bytes_nonincrease=cs['bytes']['median']<=rs['bytes']['median'],events_nonincrease=cs['events']['median']<=rs['events']['median'],retained_graph_nonincrease=b['retained_julia_bytes']<=a['retained_julia_bytes'])
 q=dict(type=a['type'],layout=a['layout'],unreliable=a['unreliable'],gates=g,reference=rs,candidate=cs,median_time_ratio=cs['seconds']['median']/rs['seconds']['median'],reference_retained_julia_bytes=a['retained_julia_bytes'],candidate_retained_julia_bytes=b['retained_julia_bytes'],reference_preparation=a['preparation'],candidate_preparation=b['preparation'],reference_post_warm_gc=a['post_warm_gc'],candidate_post_warm_gc=b['post_warm_gc'],reference_warm=a['warm'],candidate_warm=b['warm']);recomputed.append(q)
 ck('strict gates '+str(len(recomputed)),all(type(v) is bool and v for v in g.values()));ck('same graph '+str(len(recomputed)),a['retained_julia_bytes']==b['retained_julia_bytes']);ck('preparation nonincrease '+str(len(recomputed)),b['preparation']['bytes']<=a['preparation']['bytes'] and b['preparation']['events']==a['preparation']['events'])
ck('exact complete paired comparison JSON',comparison==dict(accepted=True,cases=recomputed,scope='strict paired output/work and medianbytes/events/graph gates; no percent waiver',limitation='Separate processes, not temporal interleaving; no universal/end-to-end speedup or native-memory claim'))
ck('mixed elapsed ratios',any(q['median_time_ratio']>1 for q in recomputed) and any(q['median_time_ratio']<1 for q in recomputed))
ck('RSS scope recorded',records['reference']['proc']['child_maxrss_kib']==744392 and records['candidate']['proc']['child_maxrss_kib']==752456 and '8064' in txt(D/'MEMORY-NOTE.md'))
# Complete host groups AND sessions, identity and immutable production evidence.
old=read(P/'host.json')['host'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(old['checked_groups']) if boot==old['boot_id'] else set()
for a in owners:
 if a['boot_id']==boot:groups.update((a['pgid'],a['sid']))
ck('full742 groups',len(groups)==742)
def identity(p):
 p=Path(p);s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split();return dict(pid=int(p.name),pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
conflicts=[];owner_now=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=identity(p);comm=(p/'comm').read_text().strip()
  if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh full host noJulia groups sessions',not conflicts)
for a in owners:
 try:now=identity('/proc/'+str(a['pid']))
 except (FileNotFoundError,ProcessLookupError):now=None
 owner_now.append(dict(original=a,current=now));ck('closed owner '+str(a['pid']),now is None or (now['boot_id'],now['start_ticks'])!=(a['boot_id'],a['start_ticks']))
for side,n in [('reference',739),('candidate',742)]:
 h=records[side]['closed']['host'];expected=set(old['checked_groups'])
 for a in owners[:3 if side=='reference' else 6]:expected.update((a['pgid'],a['sid']))
 ck(side+'full saved closure',len(h['checked_groups'])==n and set(h['checked_groups'])==expected and h['conflicts']==[] and h['still_active_current_launcher']==[] and h['boot_id']==boot)
 postflight=read((F if side=='reference' else R)/'postflight.json');expected.remove(records[side]['attempt']['runner']['pgid']);ck(side+'live launcher deferred',set(postflight['checked_groups'])==expected and postflight['still_active_current_launcher']==[records[side]['attempt']['runner']])
refs={k:git('rev-parse',k) for k in ('HEAD','master','origin/master')};ck('current refs',refs==dict(HEAD=H,master=M,**{'origin/master':M}));ck('tracked work/index clean',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'));ck('actual production unchanged',not git('diff','master','HEAD','--','src','test','Project.toml','Manifest.toml','.github'))
mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};ck('fresh resource guard',mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2)
# Preserve previous failed time and every actual inclusive duration.
prior=[]
for folder,sub,outcome in [('dual-recovery-devex-task4-red','red',True),('dual-recovery-devex-task4-green','green',False),('dual-recovery-devex-green2-result','green2',True)]:
 r=W/'diagnostics'/folder/'2026-10-30'/sub;q=read(r/'completion.json');ck('prior outcome '+sub,q['supervisor_accepted'] is outcome);prior.append(q['elapsed_inclusive_seconds'])
 if sub=='green':ck('failed GREEN remains',read(r/'supervisor.json')['accepted'] is False and not (r/'audit.json').exists())
ck('prior/candidate cumulative no reset',sum(prior)==1033.6005972509156 and sum(prior)+records['reference']['done']['elapsed_inclusive_seconds']==1070.9948121299385 and records['candidate']['done']['elapsed_inclusive_seconds']==37.37988920498174 and records['candidate']['done']['total_inclusive_seconds']==1108.3747013349202 and 1070.9948121299385+37.37988920498174==1108.3747013349202 and 1800-1108.3747013349202==post['remaining_seconds']==691.6252986650798)
# Original/ref and GREEN2 candidate project content, source-qualified legacy bodies.
green=O.parent.parent/'dual-recovery-devex-green-fixture-preparation/2026-10-30/prepared/overlays/candidate'
# Determine exact admitted GREEN2 project from bound fixture manifest, not a guessed new variant.
candidate_files=sorted(p for p in (O/'overlays/candidate').rglob('*') if p.is_file());reference_files=sorted(p for p in (O/'overlays/reference').rglob('*') if p.is_file());ck('74 each project',len(candidate_files)==len(reference_files)==74)
for p in candidate_files:sha(p)
for p in reference_files:sha(p)
refsrc=txt(O/'overlays/reference/src/simplex_recovery.jl');qualified=txt(O/'tests/reference.jl').split('function refine_basis_solve!',1)[1].rsplit('end # module',1)[0].replace('JS.','');public,private=qualified.split('\nfunction _refine_basis_solve!',1);ck('source qualified original public',('function refine_basis_solve!'+public).strip() in refsrc);ck('source qualified original private',('function _refine_basis_solve!'+private).strip() in refsrc)
# Report-writer failure is source-only; never execute original/corrected report writers.
fix=read(D/'report-writer-fix.json');verify('writer fix',fix['bindings']);good_checks('three writer checks',fix['checks']);ck('writer3 count',len(fix['checks'])==3)
a=txt(D/'write-report.py');b=txt(D/'write-report-2.py');lines=a.splitlines(keepends=True);expected=''.join(lines[:10]+[lines[10][:-1]+')\n']+lines[11:]);ck('one character exact repair',b==expected and len(b)==len(a)+1)
try:ast.parse(a);original_bad=False
except SyntaxError as e:original_bad=e.lineno==11 and 'never closed' in e.msg
ck('preserved original syntax failure',original_bad);ast.parse(b);ck('corrected AST valid',True);ck('successful saved writer log',read(D/'report-writer-2.log')['report_written'] is True);ck('writer failure explicit scope',fix['initial_execution_exit']==1 and 'new AST check' in fix['initial_error']['scope'] and 'subsequent source check' in txt(D/'REPORT-WRITER-NOTE.md'))
report=txt(D/'REPORT.md');ck('report boundaries',all(s in report for s in ('272/272','691.6252986650798','no end-to-end solver speedup claim','Production admission and master integration are not granted')))
ck('publication unexecuted',not (D/'closure.json').exists() and not (D/'publication.json').exists() and not (D/'close-publish.py').exists())
# Bind checker itself and save only NEW /tmp reviewer evidence.
sha(__file__)
result=dict(accepted=True,checks=checks,bindings=bindings,counts=dict(checks=len(checks),bindings=len(bindings),candidate_pins=589,reference_pins=566,committed_blobs=560,candidate_admission_bindings=964,reference_admission_bindings=801,reference_result_bindings=934,candidate_measured=56,reference_measured=56,groups=742,**counts),host=dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,owners=owner_now,refs=refs,memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])),comparison_recomputed=comparison,scope='candidate_cost_result_only')
with Path('/tmp/devex-candidate-cost-result-independent.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),counts=result['counts'])))
