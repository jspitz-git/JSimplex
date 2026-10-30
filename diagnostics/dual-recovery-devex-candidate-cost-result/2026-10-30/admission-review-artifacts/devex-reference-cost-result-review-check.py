from pathlib import Path
import hashlib,json,tomllib,struct,math,statistics,subprocess,shlex,os
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30';P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/cost-1/reference-cost';O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
bindings={};checks={}
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 bindings[str(p.absolute())]=h.hexdigest();return h.hexdigest()
def read(p):sha(p);return Path(p).read_text()
def j(p):return json.loads(read(p))
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise AssertionError(k)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
post=j(D/'postcheck.json');pins=j(R/'pins.json');seal=j(R/'seal.json');attempt=j(R/'attempt.json');ad=j(attempt['admission_path']);audit=j(R/'audit.json');closed=j(R/'closed.json');proc=j(R/'guard/process.json');sup=j(R/'supervisor.json');done=j(R/'completion.json');contract=j(P/'contract.json')
for folder in (D,P):
 for p in folder.rglob('*'):
  if p.is_file():sha(p)
for p in (O/'cost.jl',O/'tests/reference.jl',Path(__file__)):sha(p)
ck('postcheck accepted and checks',post['accepted'] is True and all(v is True for v in post['checks'].values()))
ck('566 inventory exact membership',len(pins['inventory'])==566 and set(pins['inventory'])==set(pins['files']) and len(pins['files'])==566 and pins['trees']==pins['inputs']==[])
for p,v in pins['inventory'].items():ck('pin '+p,sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'])
publication_names=set()
for folder in ('dual-recovery-devex-task4','dual-recovery-devex-task4-red','dual-recovery-devex-task4-green','dual-recovery-devex-green-fixture-preparation','dual-recovery-devex-green2-admission','dual-recovery-devex-green2-result','dual-recovery-devex-cost-admission'):
 pub=j(W/'diagnostics'/folder/'2026-10-30/publication.json');ck('published '+folder,pub['accepted'] is True)
 publication_names.update(pub['expected_names'])
ck('560 publication names',len(publication_names)==560)
for name in sorted(publication_names):
 p=W/name;ck('committed blob '+name,not p.is_symlink() and git('hash-object',str(p))==git('rev-parse','HEAD:'+name))
ck('pins consist publication plus six runtime',set(pins['inventory'])=={str(W/n) for n in publication_names}|{seal['guard_python'],*pins['inventory'].keys()-{str(W/n) for n in publication_names}} and len(set(pins['inventory'])-{str(W/n) for n in publication_names})==6)
ck('admission 4664 true checks 801bindings',ad['accepted'] is True and ad['scope']=='numerical_admission' and ad['phase']=='reference-cost' and len(ad['checks'])==4664 and all(v is True for v in ad['checks'].values()) and len(ad['bindings'])==801)
for p,h in ad['bindings'].items():ck('admission binding '+p,sha(p)==h)
ck('admission covers pins seal',set(pins['inventory'])<=set(ad['bindings']) and ad['seal_sha256']==sha(R/'seal.json')==attempt['seal_sha256'] and ad['pins_sha256']==sha(R/'pins.json')==seal['pins_sha256'] and sha(attempt['admission_path'])==attempt['admission_sha256'] and sha(ad['review_report'])==ad['review_report_sha256'])
ck('admission runtime copies',sha(R/'numerical-admission.json')==sha(attempt['admission_path']) and sha(R/'ADMISSION-REVIEW.md')==sha(ad['review_report']))
files={str(p) for p in R.rglob('*') if p.is_file()};external={attempt['admission_path'],ad['review_report']}
ck('21 raw runtime files',len(files)==21)
for label,q,exclude in [('audit',audit,{'audit.json','closed.json'}),('closed',closed,{'closed.json'})]:
 expected={p for p in files if Path(p).name not in exclude}|external
 ck(label+' exact members',set(q['bindings'])==expected)
 ck(label+' accepted',q['accepted'] is True and q['phase']=='reference-cost')
 for p,h in q['bindings'].items():ck(label+' binding '+p,sha(p)==h)
ck('canonical272',audit['test_summary']=={'Pass':272,'Total':272} and audit['error'] is None and audit['production_admission'] is False)
for key,count in [('portable',21),('external_exact_copies',80)]:
 ck(key+' count',len(post[key])==count)
 for p,q in post[key].items():ck(key+' '+p,sha(p)==sha(q['copy'])==q['sha256'])
ck('portable exact members',set(post['portable'])==files and {str(p) for p in (D/'reference-cost').rglob('*') if p.is_file()}=={v['copy'] for v in post['portable'].values()})
ck('candidate absent',not (R.parent/'candidate-cost').exists())
cmd=contract['commands']['reference-cost'];env=contract['environments']['reference-cost']
ck('driver/reference frozen',sha(O/'cost.jl')==contract['driver_sha256'] and sha(O/'tests/reference.jl')==contract['reference_sha256'])
ck('command/env',seal['command']==ad['command']==proc['command']==cmd and seal['environment']==env and seal['expected_exit']==0)
ck('original cost schedule',contract['cost']==j(O/'contract.json')['cost'])
ck('guard pins',j(R/'guard/pins.json')==pins and proc['pins_sha256']==sha(R/'pins.json') and proc['pins_unchanged'] is True)
ck('successful exit',proc['returncode']==sup['returncode']==0 and proc['reason']=='exit0' and sup['accepted'] is True and all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')) and 'cleanup_error' not in sup)
used=1033.6005972509156;elapsed=37.39421487902291
ck('inclusive time',done['limit_seconds']==1800 and done['supervisor_accepted'] is True and done['elapsed_inclusive_seconds']==elapsed and done['total_inclusive_seconds']==used+elapsed==1070.9948121299385 and 1800-used-elapsed==729.0051878700615 and 0<sup['elapsed_seconds']<=elapsed and seal['used_seconds']==used and seal['remaining_seconds']==attempt['remaining_seconds']==1800-used)
prior=[]
for folder,stage,acc in [('dual-recovery-devex-task4-red','red',True),('dual-recovery-devex-task4-green','green',False),('dual-recovery-devex-green2-result','green2',True)]:
 p=W/'diagnostics'/folder/'2026-10-30'/stage/'completion.json';q=j(p);prior.append(q['elapsed_inclusive_seconds']);ck('prior outcome '+stage,q['supervisor_accepted'] is acc)
ck('prior all time',sum(prior)==used)
expected_guard=[seal['guard_python'],'-B',str(P/'guard/guard_reviewed.py'),'run',str(R/'pins.json'),str(R/'guard'),'--expected-exit','0','--seconds',str(1800-used-12),'--deadline',str(attempt['started_monotonic']+1800-used-12),'--',*cmd]
# Preserve the launch expression's exact floating point association.
expected_guard[11]=str(attempt['started_monotonic']+(1800-used)-12)
ck('exact invocation',j(R/'invocation.json')=={'command':expected_guard,'cwd':str(P),'environment':env})
gate=j(R/'guard/gate.json');current=j(R/'guard/current.json');permit=j(R/'guard/permit.json')
ck('gate/permit bindings',gate['identity']==proc['child']==current['child'] and gate['parent']==proc['runner']==current['runner'] and gate['parent_death_signal']==9 and gate['command']==current['command']==cmd and gate['current_sha256']==sha(R/'guard/current.json') and gate['permit_sha256']==sha(R/'guard/permit.json') and permit=={'current_sha256':sha(R/'guard/current.json'),'command':cmd})
ck('supervisor guard identities',sup['guard_initial_identity']==sup['guard_identity']==proc['runner'])
owners=[attempt['runner'],proc['runner'],proc['child']];boot=read('/proc/sys/kernel/random/boot_id').strip();groups=set(j(P/'host.json')['host']['checked_groups'])
ck('baseline736',len(groups)==736)
for name,q,argv in zip(('launcher','guard','child'),owners,(['python3','-B','launch.py','reference-cost',attempt['admission_path']],expected_guard,proc['gate_command'])):
 ck(name+' identity',q['boot_id']==boot and type(q['start_ticks']) is int and q['start_ticks']>0 and q['pid']==q['pgid']==q['sid'] and shlex.split(q['command'])==argv)
 groups.update((q['pgid'],q['sid']))
ck('postcheck owner identities',post['closed_owner_identities']==owners)
ck('739 closed historical groups sessions',len(groups)==739 and set(closed['host']['checked_groups'])==set(post['host']['checked_groups'])==groups and closed['host']['conflicts']==[] and closed['host']['still_active_current_launcher']==[])
for name,count,exclude in [('prelaunch-host.json',736,[]),('postflight.json',738,[attempt['runner']])]:
 q=j(R/name);ck(name+' host',len(q['checked_groups'])==count and q['conflicts']==[] and q['still_active_current_launcher']==exclude and q['refs']['HEAD']==seal['head']==ad['head'])
conflicts=[];observed=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text();s=a[a.rfind(')')+2:].split();q={'pid':int(p.name),'pgid':int(s[2]),'sid':int(s[3]),'start_ticks':int(s[19]),'boot_id':boot,'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),'comm':(p/'comm').read_text().strip()}
  if q['pgid'] in groups or q['sid'] in groups or q['comm'].lower().startswith('julia'):conflicts.append(q)
  if q['pid'] in {v['pid'] for v in owners}:observed.append(q)
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh full739 groups AND sessions noJulia',not conflicts)
mem={a.split(':')[0]:int(a.split()[1]) for a in Path('/proc/meminfo').read_text().splitlines()};memory={'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']}
resources=[json.loads(s) for s in read(R/'guard/resources.jsonl').splitlines()]
ck('37 samples',len(resources)==37)
for i,q in enumerate([*resources,proc['terminal_memory'],memory]):ck('resources '+str(i),type(q['available_kib']) is int and type(q['swap_used_kib']) is int and q['available_kib']>=6*1024**2 and 0<=q['swap_used_kib']<=1024**2)
refs={k:git('rev-parse',k) for k in ('HEAD','master','origin/master')}
ck('fresh refs',refs['HEAD']==seal['head']==ad['head']=='d618023b27a42170438c26995c50a036af01c2b4' and refs['master']==refs['origin/master']=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
ck('tracked tree index and production unchanged',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only') and not git('diff','master','HEAD','--','src','test','Project.toml','.github'))
log=read(R/'guard/run.log');lines=log.splitlines();ck('ordinary summary and completion',len([s for s in lines if s.startswith('TASK4_COST ') and '|' in s])==1 and any(s.split('|')[1].split()[:2]==['272','272'] for s in lines if s.startswith('TASK4_COST ') and '|' in s) and lines.count('TASK4_COST_COMPLETED reference')==1 and not any(x in log.lower() for x in ('error:','test failed at','error during test','segmentation fault','world age','undefvarerror')))
r=tomllib.loads(read(R/'result.toml'));ck('side eight cases',r['side']=='reference' and len(r['cases'])==8)
def bits(x,T):return struct.pack('>f' if T=='Float32' else '>d',x).hex()
def stats(q,label,measured=False):
 ck(label+' typed stats',all(type(q[k]) in (int,float) and math.isfinite(q[k]) and q[k]>=0 for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds')) and all(type(q[k]) is int and q[k]>=0 for k in ('bytes','events')))
 if measured:ck(label+' all zero',all(q[k]==0 for k in ('bytes','events','compile_seconds','recompile_seconds','gc_seconds')))
summaries=[];solve=stop=0
for qi,(T,layout,bad) in enumerate((T,l,b) for T in ('Float32','Float64') for l in ('sparse','dense') for b in (False,True)):
 q=r['cases'][qi];label=str(qi);ck(label+' case key',(q['type'],q['layout'],q['unreliable'])==(T,layout,bad) and type(q['unreliable']) is bool and q['dimension']==64 and q['nnz']==(190 if layout=='sparse' else 4096))
 matrix=[bits(64 if i==j else ((-1 if (i+j)%2==0 else 1)*(1+(i+2*j)%5))/64 if layout=='dense' or abs(i-j)==1 else 0,T) for j in range(1,65) for i in range(1,65)]
 ck(label+' matrix policy',q['matrix_bits']==matrix and q['policy_solve_tolerance_bits']==('38000000' if T=='Float32' else '3d30000000000000'))
 ck(label+' schedule work',len(q['warm'])==3 and len(q['samples'])==7 and type(q['retained_julia_bytes']) is int and q['retained_julia_bytes']>=0 and q['solve_entries_total']==q['stop_entries_total']==(10 if bad else 0))
 stats(q['preparation'],label+' prep');stats(q['post_warm_gc'],label+' gc')
 for i,w in enumerate(q['warm']):stats(w,label+' warm'+str(i))
 solve+=q['solve_entries_total'];stop+=q['stop_entries_total']
 for i,s in enumerate(q['samples'],1):
  x=label+' sample'+str(i);stats(s,x,True)
  ck(x+' numerical owners work',type(s['index']) is int and s['index']==i and s['finite'] is True and s['reliable'] is (not bad) and s['owners_preserved'] is True and s['point_bits']==[bits(.5 if bad else 1,T)]+[bits(0,T)]*63 and s['rhs_bits']==matrix[::64] and s['absolute_bits']==bits(32 if bad else 0,T) and s['relative_bits']==bits(1/3 if bad else 0,T) and type(s['solve_entries']) is int and type(s['stop_entries']) is int and s['solve_entries']==s['stop_entries']==int(bad))
 vals=[s['seconds'] for s in q['samples']];med=statistics.median(vals);summaries.append({'type':T,'layout':layout,'unreliable':bad,'median_seconds':med,'range_seconds':[min(vals),max(vals)],'MAD_seconds':statistics.median(abs(v-med) for v in vals),'retained_julia_bytes':q['retained_julia_bytes'],'preparation':q['preparation'],'post_warm_gc':q['post_warm_gc']})
ck('80API 40BTRAN 40stop 8GC 56measurements',sum(len(q['warm'])+len(q['samples']) for q in r['cases'])==80 and solve==stop==40 and len(r['cases'])==8 and sum(len(q['samples']) for q in r['cases'])==56)
result={'accepted':all(checks.values()),'scope':'reference_cost_result_only','checks':checks,'bindings':bindings,'counts':{'checks':len(checks),'bindings':len(bindings),'pins':566,'committed_publication_blobs':560,'admission_bindings':801,'runtime_files':21,'audit_bindings':len(audit['bindings']),'closed_bindings':len(closed['bindings']),'external_copies':80,'resource_samples':len(resources),'groups_and_sessions':len(groups)},'host':{'boot_id':boot,'checked_groups':sorted(groups),'conflicts':conflicts,'owner_pids_observed':observed,'memory':memory,'refs':refs},'owners':owners,'case_summaries':summaries,'elapsed_inclusive_seconds':elapsed,'total_inclusive_seconds':used+elapsed,'remaining_seconds':1800-used-elapsed}
Path('/tmp/devex-reference-cost-result-review-check-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'accepted':result['accepted'],'counts':result['counts'],'memory':memory,'refs':refs},indent=2))
