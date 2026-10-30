import hashlib,json,pathlib,re,subprocess
W=pathlib.Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1/red';D=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30'
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def git(*args):return subprocess.check_output(['git','-C',str(W),*args]).decode().strip()
checks={};bindings={};details={}
def ck(name,condition):checks[name]=bool(condition)
def bind(p):bindings[str(p)]=sha(p)
seal=read(R/'seal.json');pins=read(R/'pins.json');ad=read(R/'numerical-admission.json');audit=read(R/'audit.json');post=read(D/'postcheck.json');extra=read(D/'admission-extra-copies.json');proc=read(R/'guard/process.json');sup=read(R/'supervisor.json');done=read(R/'completion.json');gate=read(R/'guard/gate.json');permit=read(R/'guard/permit.json');current=read(R/'guard/current.json');attempt=read(R/'attempt.json');inv=read(R/'invocation.json');pre=read(R/'prelaunch-host.json');flight=read(R/'postflight.json')
for p in list(R.rglob('*'))+list(D.rglob('*')):
 if p.is_file():bind(p)
for p in [W/'AGENTS.md',W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md']:bind(p)
ck('admitted_head_and_master',git('rev-parse','HEAD')==seal['head']=='68240e80279b1339fd24c002b91664559acfb1dd' and git('rev-parse','master')==git('rev-parse','origin/master')==seal['master']=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
ck('actual_src_test_project_ci_unchanged',not git('diff','master','--','src','test','Project.toml','.github') and not git('diff','--cached'))
ck('217_actual_hashes_and_resolutions',len(pins['inventory'])==len(pins['files'])==217 and set(pins['files'])==set(pins['inventory']) and all(sha(p)==v['sha256'] and str(pathlib.Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()))
for p in pins['inventory']:bind(p)
ck('289_admission_bindings_unchanged',len(ad['bindings'])==289 and all(sha(p)==v for p,v in ad['bindings'].items()))
for p in ad['bindings']:bind(p)
ck('all_audit_bindings_unchanged',all(sha(p)==v for p,v in audit['bindings'].items()))
ck('19_portable_runtime_exact_copies',len(post['portable'])==19 and all(sha(p)==sha(v['copy'])==v['sha256'] for p,v in post['portable'].items()) and {str(p) for p in R.rglob('*') if p.is_file()}==set(post['portable']))
ck('admission_report_json_and_tmpcheck_exact_copies',len(post['external_exact_copies'])==2 and len(extra)==1 and all(sha(p)==sha(v['copy'])==v['sha256'] for p,v in (post['external_exact_copies']|extra).items()))
ck('admission_28_checks_accepted_exact_SHA',ad['accepted'] and len(ad['checks'])==28 and all(ad['checks'].values()) and sha(R/'numerical-admission.json')==attempt['admission_sha256']=='72d02dc05998312c3e7488d62202e1474c2181da4f272b0fba760233c9fa7419')
ck('seal_pins_report_bindings',sha(R/'seal.json')==ad['seal_sha256']==attempt['seal_sha256']=='7ba238fb9655a035754f3c43d445137712a6250fdc5486d8639db87b2d03d5c7' and sha(R/'pins.json')==seal['pins_sha256']==ad['pins_sha256']==proc['pins_sha256']==sha(R/'guard/pins.json') and sha(ad['review_report'])==ad['review_report_sha256'])
ck('guard_child_command_environment',proc['command']==seal['command']==ad['command']==gate['command']==permit['command'] and inv['environment']==seal['environment'] and inv['command'][inv['command'].index('--')+1:]==seal['command'])
ck('expected_exit1_only',proc['returncode']==1 and proc['reason']=='exit1' and seal['expected_exit']==1 and proc['pins_unchanged'] is True)
ck('entry_identity_and_permit',gate['identity']==proc['child'] and gate['parent']==proc['runner'] and gate['parent_death_signal']==9 and gate['permit_sha256']==sha(R/'guard/permit.json') and gate['current_sha256']==permit['current_sha256']==sha(R/'guard/current.json'))
ck('supervisor_normal_completion',sup['accepted'] is True and sup['returncode']==0 and done['supervisor_accepted'] is True and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted']) and sup['guard_identity']==sup['guard_initial_identity']==proc['runner'])
ck('inclusive_budget_1800',seal['used_seconds']==0 and seal['previous']==[] and done['elapsed_inclusive_seconds']==done['total_inclusive_seconds']==post['elapsed_inclusive_seconds']==33.35953255696222 and done['limit_seconds']==seal['shared_total_seconds']==1800 and 1800-done['total_inclusive_seconds']==post['remaining_guarded_seconds']==1766.6404674430378 and proc['elapsed_including_launch']<=sup['elapsed_seconds']<=done['elapsed_inclusive_seconds'])
log=(R/'guard/run.log').read_text();warnings=[s for s in log.splitlines() if s.startswith('WARNING:')]
ck('ordinary_summary_exact_7_1_0_0',re.findall(r'^TASK4_RED\s+\|\s+(\d+)\s+(\d+)\s+(\d+)\s+',log,re.M)==[('7','1','8')] and '7 passed, 1 failed, 0 errored, 0 broken.' in log and log.count('Test Failed at')==1 and str(P/'red.jl')+':22' in log and 'Expression: recovery_ready === true' in log and 'Evaluated: false === true' in log)
ck('no_substitute_runtime_error',not any(s in log.lower() for s in ['world age','undefvarerror','error during test','syntax:','segmentation fault','could not load']))
ck('all_four_import_warnings_preserved',warnings==post['warning_lines'] and len(warnings)==4 and all(x in '\n'.join(warnings) for x in ['StyledStrings.@styled_str','StyledStrings.styled','OpenSpecFun_jll.libopenspecfun','Bzip2_jll.libbzip2']))
ck('canonical_audit_and_postcheck',audit['accepted'] and audit['test_summary']=={'Pass':7,'Fail':1,'Total':8} and audit['production_admission'] is False and post['accepted'] and len(post['checks'])==9 and all(post['checks'].values()))
samples=[json.loads(s) for s in (R/'guard/resources.jsonl').read_text().splitlines()]
ck('resource_readings',len(samples)==33 and min(s['available_kib'] for s in samples)==22675264 and max(s['swap_used_kib'] for s in samples)==0 and proc['child_maxrss_kib']==702444 and proc['terminal_memory']=={'available_kib':23166160,'swap_used_kib':0} and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples))
ids=set(pre['checked_groups'])|{406098,406119,406120}
ck('recorded_host_closure',len(pre['checked_groups'])==727 and len(ids)==730 and set(post['checked_groups'])==ids and set(flight['checked_groups'])==ids-{406098} and pre['conflicts']==flight['conflicts']==post['conflicts']==[] and pre['refs']==flight['refs']=={'HEAD':seal['head'],'master':seal['master'],'origin/master':seal['master']})
boot=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip();conflicts=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  stat=(p/'stat').read_text();fields=stat[stat.rindex(')')+2:].split();pgid,sid=int(fields[2]),int(fields[3]);comm=(p/'comm').read_text().strip();exe=(p/'exe').resolve().name
  if pgid in ids or sid in ids or comm.lower().startswith('julia') or exe.lower().startswith('julia'):conflicts.append({'pid':int(p.name),'pgid':pgid,'sid':sid,'comm':comm})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
ck('fresh_all730_groups_AND_sessions_absent_no_Julia',boot==pre['boot_id']==post['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb' and not conflicts)
ref=P/'overlays/reference/src';files=list(ref.rglob('*.jl'))
ck('all71_reference_sources_exact_master',len(files)==71 and all(p.read_bytes()==subprocess.check_output(['git','-C',str(W),'show','master:src/'+str(p.relative_to(ref))]) for p in files))
ck('eight_assertions_real_original_boundary',len(re.findall(r'^\s*@test ',(P/'red.jl').read_text(),re.M))==8 and '_rebuild_recovery_weights_result!' not in '\n'.join(p.read_text() for p in files) and 'Base.invokelatest(task4_red)' in (P/'red.jl').read_text() and 'realpath(pathof(JSimplex))' in (P/'red.jl').read_text())
ck('singular_attempt_no_other_phases',sorted(p.name for p in R.parent.iterdir())==['red'])
details={'checked_groups_count':len(ids),'boot_id':boot,'conflicts':conflicts,'warnings':warnings,'resource_samples':len(samples),'minimum_available_kib':min(s['available_kib'] for s in samples),'maximum_swap_kib':max(s['swap_used_kib'] for s in samples),'child_maxrss_kib':proc['child_maxrss_kib'],'elapsed_inclusive_seconds':done['elapsed_inclusive_seconds'],'remaining_seconds':1800-done['total_inclusive_seconds']}
ck('all_readonly_inputs_still_immutable',all(sha(p)==v for p,v in bindings.items()))
result={'accepted':all(checks.values()),'checks':checks,'bindings':bindings,'details':details}
pathlib.Path('/tmp/devex-task4-red-result-independent-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'accepted':result['accepted'],'checks':checks,'bindings_count':len(bindings),'details':details},indent=2))
