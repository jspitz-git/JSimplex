"""New read-only result verifier. Does not import or execute any old checker."""
from pathlib import Path
import hashlib,json,math,os,re,subprocess,tomllib,traceback,time
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
D=W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30'
P=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30'
F=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30'
R=W/'.superpowers/dual-recovery-devex-task4/green2-1'
HEAD='4f5e6b9966830955637cfb7bba288b9339c9a494'
MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
checks={};bindings={};facts={}
def raw(p):
 p=Path(p);data=p.read_bytes();bindings[str(p)]=hashlib.sha256(data).hexdigest();return data
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 bindings[str(p)]=h.hexdigest();return h.hexdigest()
def read(p):return json.loads(raw(p))
def check(name,v):
 if name in checks:raise ValueError('duplicate check '+name)
 checks[name]=bool(v)
def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(W),*a],text=True).strip()
def nonnegative(x):return type(x) in (int,float) and math.isfinite(x) and x>=0
def memcheck(q):return all(type(q[k]) is int for k in ['available_kib','swap_used_kib']) and q['available_kib']>=6291456 and 0<=q['swap_used_kib']<=1048576
try:
 raw(W/'AGENTS.md');raw(D/'REPORT.md');raw(D/'postcheck.py')
 for n in ['ADMISSION-PREPARATION.md','REVIEW-FINAL.md','seal.py','common.py','launch-reviewed.py','audit_reviewed.py','binding_checks.py','fixture_check.py','guard/entry_gate.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py']:raw(P/n)
 post=read(D/'postcheck.json');seal=read(R/'seal.json');pins=read(R/'pins.json');attempt=read(R/'attempt.json');audit=read(R/'audit.json');proc=read(R/'guard/process.json');sup=read(R/'supervisor.json');done=read(R/'completion.json');contract=read(P/'contract.json')
 ad=read(attempt['admission_path'])
 check('postcheck_10_all_true',post['accepted'] is True and len(post['checks'])==10 and all(v is True for v in post['checks'].values()))
 check('admission_3088_all_true',ad['accepted'] is True and ad['scope']=='numerical_admission' and len(ad['checks'])==3088 and all(v is True for v in ad['checks'].values()))
 check('admission_scope_and_once',ad['maximum_new_attempts']==1 and ad['numerical_result_accepted'] is False and ad['cost_qualified'] is False and ad['production_admission'] is False)
 check('admission_635_bindings',len(ad['bindings'])==635)
 for n,h in ad['bindings'].items():check('admission_hash:'+n,sha(n)==h)
 check('admission_report',sha(ad['review_report'])==ad['review_report_sha256'])
 check('admission_attempt_hash',sha(attempt['admission_path'])==attempt['admission_sha256']=='68b35c3c04a40b79f94fb04e85e9d3983d1b7439ae82f0af6b4906046f60231f')
 check('seal_hash',sha(R/'seal.json')==ad['seal_sha256']==attempt['seal_sha256']=='da0d0f2653da383f633825fff75a971c259d42932de835c2d97a5ee59c400daf')
 check('pins_hash',sha(R/'pins.json')==ad['pins_sha256']==seal['pins_sha256']==proc['pins_sha256']=='4deb0e97c0a3acdca21c9fb8dbf5b4c4095873d462c95469ad93c19e7b786582')
 check('all_inventory_in_admission',set(pins['inventory'])<=set(ad['bindings']))
 check('pin_membership',len(pins['inventory'])==459 and len(pins['files'])==459 and set(pins['files'])==set(pins['inventory']) and pins['trees']==[])
 for n,v in pins['inventory'].items():
  check('pin_sha:'+n,sha(n)==v['sha256']);check('pin_resolved:'+n,str(Path(n).resolve(strict=True))==v['resolved'])
 required=set();published=set()
 for suffix in ['dual-recovery-devex-task4','dual-recovery-devex-task4-red','dual-recovery-devex-task4-green','dual-recovery-devex-green-fixture-preparation','dual-recovery-devex-green2-admission']:
  pub=read(W/'diagnostics'/suffix/'2026-10-30/publication.json');check('publication_accepted:'+suffix,pub['accepted'] is True)
  published.update(pub['expected_names'])
 required.update(str(W/n) for n in published)
 runtime=Path(seal['command'][0]).parents[1]
 required.update(map(str,[Path(seal['guard_python']),Path(seal['command'][0]),runtime/'lib/libjulia.so.1.13.0',runtime/'lib/julia/sys.so',runtime/'lib/julia/libjulia-internal.so.1.13.0',runtime/'share/julia/base/timing.jl']))
 check('459_exact_required_inventory',required==set(pins['inventory']) and len(published)==453)
 tree={}
 for line in git('ls-tree','-r','HEAD').splitlines():
  meta,n=line.split('\t',1);tree[n]=meta.split()[2]
 for n in sorted(published):
  p=W/n;data=raw(p);blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  check('publication_blob:'+n,p.is_file() and not p.is_symlink() and tree.get(n)==blob)
 check('guard_pin_copy',read(R/'guard/pins.json')==pins)
 check('runtime_portable_exact_set',set(post['portable'])=={str(p) for p in R.rglob('*') if p.is_file()} and len(post['portable'])==20)
 for label,m in [('portable',post['portable']),('external',post['external_exact_copies'])]:
  for n,v in m.items():check(label+':'+n,sha(n)==sha(v['copy'])==v['sha256'])
 check('all_tmp_admission_bindings_mapped',all(n in post['external_exact_copies'] for n in ad['bindings'] if Path(n).is_relative_to('/tmp')))
 for n,h in audit['bindings'].items():check('audit_binding:'+n,sha(n)==h)
 check('canonical_audit_accepted',audit['accepted'] is True and audit['phase']=='green2' and audit['error'] is None and audit['test_summary']=={'Pass':5774,'Total':5774} and audit['production_admission'] is False)
 check('seal_contract_command',seal['command']==contract['command']==proc['command']==ad['command'] and seal['environment']==contract['environment'] and seal['expected_exit']==0 and seal['phase']=='green2')
 check('interpreter',seal['guard_python']=='/usr/bin/python3' and seal['guard_python'] in pins['inventory'])
 check('attempt_identity_scope',attempt['phase']=='green2' and nonnegative(attempt['started_monotonic']) and attempt['remaining_seconds']==seal['remaining_seconds']==ad['remaining_inclusive_seconds']==1800-seal['used_seconds'])
 command=[seal['guard_python'],'-B',str(P/'guard/guard_reviewed.py'),'run',str(R/'pins.json'),str(R/'guard'),'--expected-exit','0','--seconds',str(1800-seal['used_seconds']-12),'--deadline',str(attempt['started_monotonic']+1800-seal['used_seconds']-12),'--',*seal['command']]
 # Preserve the canonical operation ordering for the floating-point deadline.
 command[command.index('--deadline')+1]=str(attempt['started_monotonic']+(1800-seal['used_seconds'])-12)
 invocation=read(R/'invocation.json')
 check('exact_guard_invocation',invocation=={'command':command,'cwd':str(P),'environment':seal['environment']})
 check('process_exit',type(proc['returncode']) is int and proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and proc['cwd']==str(P))
 check('supervisor_success',sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted']) and 'cleanup_error' not in sup)
 redbase=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30';oldbase=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
 red=read(redbase/'red/audit.json');red_done=read(redbase/'red/completion.json');old_done=read(oldbase/'green/completion.json');old_sup=read(oldbase/'green/supervisor.json')
 check('red_accepted_7_1',red['accepted'] is True and red['test_summary']=={'Pass':7,'Fail':1,'Total':8})
 check('old_green_remains_rejected',old_sup['accepted'] is False and old_sup['returncode']==1 and old_done['supervisor_accepted'] is False and not (oldbase/'green/audit.json').exists())
 check('time_no_reset',seal['used_seconds']==red_done['elapsed_inclusive_seconds']+old_done['elapsed_inclusive_seconds']==old_done['total_inclusive_seconds']==527.9604928489425)
 check('time_inclusive_total',done['supervisor_accepted'] is True and done['limit_seconds']==seal['shared_total_seconds']==1800 and done['elapsed_inclusive_seconds']==505.6401044019731 and done['total_inclusive_seconds']==seal['used_seconds']+done['elapsed_inclusive_seconds']==1033.6005972509156 and 1800-done['total_inclusive_seconds']==post['remaining_seconds']==766.3994027490844)
 check('supervisor_time',0<sup['elapsed_seconds']<=done['elapsed_inclusive_seconds'] and 0<proc['elapsed_including_launch']<=done['elapsed_inclusive_seconds'])
 check('prior_fact_hashes',seal['previous']==contract['previous'] and seal['previous'][0]['completion_sha256']==sha(redbase/'red/completion.json') and seal['previous'][0]['audit_sha256']==sha(redbase/'red/audit.json') and seal['previous'][1]['completion_sha256']==sha(oldbase/'green/completion.json') and seal['previous'][1]['supervisor_sha256']==sha(oldbase/'green/supervisor.json'))
 owners=[attempt['runner'],proc['runner'],proc['child']];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 check('exact_owner_ids',[(a['pid'],a['pgid'],a['sid'],a['start_ticks']) for a in owners]==[(422629,422629,422629,33166992),(422652,422652,422652,33167037),(422687,422687,422687,33167058)] and all(a['boot_id']==boot=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb' and a['command'] for a in owners) and post['closed_owner_identities']==owners)
 check('owner_commands',owners[0]['command']=='python3 -B launch-reviewed.py /tmp/devex-green2-numerical-admission.json ' and owners[1]['command']==' '.join(command)+' ' and owners[2]['command']==' '.join(proc['gate_command'])+' ' and sup['guard_identity']==owners[1])
 gate=read(R/'guard/gate.json');current=read(R/'guard/current.json');permit=read(R/'guard/permit.json')
 check('gate_identity',gate['identity']==owners[2] and gate['parent']==owners[1] and gate['parent_death_signal']==9 and gate['command']==seal['command'])
 check('gate_hash_chain',gate['current_sha256']==sha(R/'guard/current.json') and gate['permit_sha256']==sha(R/'guard/permit.json') and permit=={'current_sha256':sha(R/'guard/current.json'),'command':seal['command']} and current['child']==owners[2] and current['runner']==owners[1] and current['command']==seal['command'])
 initial=read(P/'host.json')['host'];prior_groups=set(initial['checked_groups']);groups=prior_groups|{a[k] for a in owners for k in ['pgid','sid']}
 check('complete_group_set',len(prior_groups)==733 and len(groups)==736 and initial['boot_id']==boot and set(post['checked_groups'])==set(post['host']['checked_groups'])==groups)
 pf=read(R/'postflight.json');pre=read(R/'prelaunch-host.json')
 check('canonical_postflight_live_launcher_explicit',pf['still_active_current_launcher']==[owners[0]] and set(pf['checked_groups'])==prior_groups|{owners[1]['pgid'],owners[2]['pgid']} and pf['conflicts']==[])
 check('postexit_no_deferred_launcher',post['host']['still_active_current_launcher']==[] and post['host']['conflicts']==[])
 for label,h in [('saved_prelaunch',pre),('canonical_postflight',pf),('saved_postexit',post['host'])]:
  check(label+'_refs_memory',h['refs']=={'HEAD':HEAD,'master':MASTER,'origin/master':MASTER} and h['conflicts']==[] and memcheck(h['memory']) and h['boot_id']==boot)
 conflicts=[];scanned=0
 for p in Path('/proc').glob('[0-9]*'):
  try:
   text=(p/'stat').read_text();fields=text[text.rfind(')')+2:].split();pgid,sid=int(fields[2]),int(fields[3]);comm=(p/'comm').read_text().strip();scanned+=1
   if pgid in groups or sid in groups or comm.lower().startswith('julia'):
    conflicts.append({'pid':int(p.name),'pgid':pgid,'sid':sid,'start_ticks':int(fields[19]),'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),'comm':comm})
  except (FileNotFoundError,ProcessLookupError):pass
 check('fresh_full_736_groups_sessions_no_julia',not conflicts and scanned>1)
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory={'available_kib':mem['MemAvailable'],'swap_used_kib':mem['SwapTotal']-mem['SwapFree']}
 check('fresh_resources',memcheck(memory));refs={k:git('rev-parse',k) for k in ['HEAD','master','origin/master']}
 check('fresh_refs',refs=={'HEAD':HEAD,'master':MASTER,'origin/master':MASTER} and git('branch','--show-current')=='codex/native-quality-finite' and seal['head']==ad['head']==HEAD)
 check('tracked_tree_and_index_unchanged',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'))
 check('production_tests_environment_CI_unchanged',not git('diff','master','HEAD','--','src','test','Project.toml','Manifest.toml','LocalPreferences.toml','.github'))
 facts['fresh_host']={'timestamp':time.time(),'boot_id':boot,'checked_groups':sorted(groups),'processes_inspected':scanned,'conflicts':conflicts,'refs':refs,'memory':memory,'owners':owners}
 log=raw(R/'guard/run.log').decode();lines=log.splitlines()
 check('ordinary_summary',len(re.findall(r'^TASK4_GREEN\s*\|\s*5774\s+5774\s+7m54\.1s$',log,re.M))==1 and lines.count('Test Summary: | Pass  Total     Time')==1 and not any(s in log.lower() for s in ['world age','error during test','undefvarerror','syntax:','segmentation fault','error:','test failed at']))
 check('ordered_12_includes',re.findall(r'^TASK4_INCLUDED (.+)$',log,re.M)==contract['green_includes'] and len(contract['green_includes'])==12)
 check('completion_and_no_fabricated_child_row',lines.count('TASK4_GREEN_COMPLETED')==1 and 'TASK4_POST_FALLBACK' not in log and lines[-1]=='TASK4_GREEN_COMPLETED')
 warnings=[s for s in lines if s.startswith('WARNING:')]
 for label,path in [('red',redbase/'red/guard/run.log'),('oldgreen',oldbase/'green/guard/run.log')]:
  check(label+'_same_warnings',[s for s in raw(path).decode().splitlines() if s.startswith('WARNING:')]==warnings and len(warnings)==4)
 fm=read(P/'fixture-manifest.json');prepared=F/'prepared';ep=raw(prepared/'endpoint.jl').decode()
 check('unchanged_46_endpoint_assertions',len(re.findall(r'^\s*@test(?:_throws)?\b',ep,re.M))==23 and 'for T in (Float32,Float64)' in ep and contract['endpoint_assertions']==46)
 check('prepared_91_files',len([p for p in prepared.rglob('*') if p.is_file()])==91)
 check('fixture_graph_counts',seal['fixture_audit']['program_count']==15 and seal['fixture_audit']['include_edges']==14 and seal['fixture_audit']['fixture_count']==2 and len(fm['programs'])==15)
 for rel,h in {**fm['programs'],**fm['fixtures']}.items():check('fixture_graph_hash:'+rel,sha(prepared/rel)==h)
 check('fixture_inputs_exact',pins['inputs']==contract['fixture_inputs']==sorted(str(prepared/n) for n in fm['fixtures']) and contract['fixture_hashes']=={str(prepared/n):h for n,h in fm['fixtures'].items()})
 cases=tomllib.loads(raw(R/'result.toml').decode())['cases'];check('two_endpoint_types',len(cases)==2 and {q['type'] for q in cases}=={'Float32','Float64'})
 counts={'iterations':1,'factorizations':1,'attempted_weight_rows':1,'avoided_weight_rows':1,'core_and_weight_ftran':1,'core_and_weight_btran':3,'final_ftran':2,'final_btran':4}
 for q in cases:
  tag=q['type'];check(tag+'_work_counts',all(type(q[k]) is int and q[k]==v for k,v in counts.items()))
  check(tag+'_original_certificates_and_rejections',all(q[k] is True for k in ['original_primal_certified','original_optimality_certified','invalid_witness_rejected','invalid_row_rejected','trajectory_changed']))
  check(tag+'_exact_point_witness',all(type(q[k]) is list and q[k]==[1,0] and all(type(v) in (int,float) and math.isfinite(v) for v in q[k]) for k in ['point','witness']))
  check(tag+'_retained_graph_type',type(q['retained_julia_bytes']) is int and q['retained_julia_bytes']>=0)
  for k in ['preparation','whole_fallback','component_preparation','component_revalidation','component_reset']:
   v=q[k];check(tag+'_stats_'+k,all(nonnegative(v[x]) for x in ['seconds','gc_seconds','compile_seconds','recompile_seconds']) and all(type(v[x]) is int and v[x]>=0 for x in ['bytes','events']))
 facts['endpoint_records']=cases
 samples=[json.loads(s) for s in raw(R/'guard/resources.jsonl').decode().splitlines()]
 check('505_resource_samples',len(samples)==505 and all(memcheck(s) for s in samples) and memcheck(proc['terminal_memory']))
 check('recorded_resource_extrema',min(s['available_kib'] for s in samples)==post['min_available_kib']==20992408 and max(s['swap_used_kib'] for s in samples)==post['max_swap_used_kib']==0 and proc['child_maxrss_kib']==2034964)
 facts.update(runtime_files=len(post['portable']),external_copies=len(post['external_exact_copies']),pins=len(pins['inventory']),publication_blobs=len(published),admission_bindings=len(ad['bindings']),audit_bindings=len(audit['bindings']),elapsed_inclusive_seconds=done['elapsed_inclusive_seconds'],total_inclusive_seconds=done['total_inclusive_seconds'],remaining_seconds=1800-done['total_inclusive_seconds'])
except Exception:
 checks['checker_exception']=False;facts['exception']=traceback.format_exc()
sha(__file__)
result={'accepted':all(checks.values()),'scope':'green2_result_only','runtime_accepted':all(checks.values()),'production_admission':False,'cost_qualified':False,'checks':checks,'bindings':bindings,'facts':facts}
out=Path('/tmp/devex-green2-result-review-check-result.json')
with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'accepted':result['accepted'],'checks':len(checks),'bindings':len(bindings),'failed':[k for k,v in checks.items() if not v],'exception':facts.get('exception'),'facts':{k:v for k,v in facts.items() if k not in ['fresh_host','endpoint_records']}}))
