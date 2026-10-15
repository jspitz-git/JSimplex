"""Independent static admission checker: no prepared imports or executable scripts."""
import hashlib,json,os,pathlib,re,subprocess,time,tomllib
R=pathlib.Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/NATIVE-ACCURACY-PREPARATION'
Q=D.parent/'NATIVE-ACCURACY-QUALIFICATION'
SP=Q/'accuracy-sealed-pins.json'
checks={};detail={}
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def ck(k,v):checks[k]=bool(v)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def current_inventory(paths):return {p:dict(resolved=str(pathlib.Path(p).resolve(strict=True)),sha256=sha(p)) for p in paths}
s=read(SP);p=read(D/'preparation-pins-reviewed.json');review=read(D/'review-final.json');required=read(D/'required-paths-reviewed.json');hs=read(Q/'accuracy-seal-host.json');hp=read(D/'host.json')
ck('exact1189_sealed_unique_absolute',len(s['files'])==1189 and len(set(s['files']))==1189 and all(pathlib.Path(n).is_absolute() for n in s['files']))
ck('fixed_file_inventory_no_dynamic_trees',s['trees']==[] and set(s['inventory'])==set(s['files']))
actual=current_inventory(s['files']);ck('all1189_sealed_resolutions_and_hashes',actual==s['inventory'])
ck('all1184_preparation_resolutions_and_hashes',len(p['files'])==1184 and set(p['files'])==set(p['inventory']) and all(actual.get(n)==v for n,v in p['inventory'].items()))
extras={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'),str(D/'preparation-pins-reviewed.json'),str(D/'review-final.json'),str(Q/'accuracy-seal-host.json')}
ck('exact_seal_delta_five',set(s['files'])==set(p['files'])|extras)
ck('accepted_preparation_digest',review['accepted'] is True and review['findings']==[] and review['pins_sha256']==sha(D/'preparation-pins-reviewed.json'))
ck('exact66_preparation_bindings',len(required)==len(set(required))==66 and set(review['sha256'])==set(required) and all(sha(n)==h for n,h in review['sha256'].items()))
ck('required_manifest_pinned',str(D/'required-paths-reviewed.json') in s['files'])
baseline=read(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];ck('all514_production_baseline_hashes',len(baseline)==514 and all(sha(R/n)==h for n,h in baseline.items()))
predecessor=read(D/'predecessor-bindings.json')['sha256'];ck('predecessor_hashes',all(sha(n)==h for n,h in predecessor.items()))
ck('old_cost1_still_false',read(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
fix=read(D/'review-fix.json');ck('initial_finding_sources_preserved',len(fix['mappings'])==5 and all(sha(v['preserved'])==v['sha256'] for v in fix['mappings'].values()))
ck('initial_review_rejection_preserved',read(D/'review.json')['accepted'] is False)
refs={'head':git('rev-parse','HEAD'),'master':git('rev-parse','master'),'branch':git('branch','--show-current')}
ck('expected_actual_refs',refs==dict(head='1720f7460458d7418b5702099967ab773166caa7',master='6f68e24e8ddac42b948da8fcc2d636c010751194',branch='codex/simplex-core-architecture'))
ck('seal_refs_match_actual',all(s[k]==hs[k]==refs[k] for k in ('head','master')))
ck('no_tracked_changes',git('diff','--name-only')==git('diff','--cached','--name-only')=='')
ck('continuation_bytes_preserved',sha(Q/'STATUS.md.before-qualification')==sha(R/'diagnostics/simplex-core-architecture/STATUS.md') and sha(Q/'roadmap.md.before-qualification')==sha(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'))
boot=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
ck('same_live_boot',boot==s['boot_id']==hs['boot_id']==hp['boot_id'])
groups=sorted(set(hs['groups'])|set(hp['groups']))
ck('full206_historical_groups_and_sessions',len(groups)==206 and groups==hs['groups']==hp['groups'])
processes=[];matches=[];unreadable=[]
for proc in pathlib.Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text();z=st[st.rindex(')')+2:].split();comm=(proc/'comm').read_text().strip();exe=''
  try:exe=str((proc/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(proc.name))
  except (FileNotFoundError,ProcessLookupError):pass
  item=dict(pid=int(proc.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe,boot_id=boot)
  processes.append(item)
  if item['pgid'] in groups or item['sid'] in groups or comm.lower().startswith('julia') or pathlib.Path(exe).name.lower().startswith('julia'):matches.append(item)
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh_no_historical_groups_sessions_or_julia',matches==[])
ck('seal_no_prior_matches',hs['matches']==[])
mem={line.split(':')[0]:int(line.split()[1]) for line in pathlib.Path('/proc/meminfo').read_text().splitlines()}
resources=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
ck('fresh_RAM6GiB_swap1GiB',resources['available_kib']>=6*1024**2 and resources['swap_used_kib']<=1024**2)
env=read(D/'environment.json');ck('loading_environment_unchanged',env=={k:os.environ.get(k) for k in env})
ck('no_attempt_reserved_or_started',not any((Q/n).exists() for n in ('accuracy-run','accuracy-reservation.json','accuracy-invocation.json','accuracy-launch-pins.json','accuracy-launcher.log','accuracy-prehost.json')))
cfg=read(D/'config.json');wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(R),str(D/'driver.jl'),str(Q/'accuracy-run'),str(D/'inputs.toml')]
ck('literal45second_ordinary_command',cfg=={'accuracy':dict(seconds=45,expected_exit=0,project=str(R),output=str(Q/'accuracy-run'),command=command)})
ck('command_loading_files_pinned',all(n in s['files'] for n in (wrapper,'/bin/bash',str(D/'driver.jl'),str(D/'inputs.toml'),str(R/'Project.toml'),str(R/'Manifest.toml'),str(R/'LocalPreferences.toml'))))
data=read(D/'inputs.json');old=read(D.parent/'DIRECT-LU-COST-PREPARATION/inputs.json')
ck('TOML_JSON_exact_inverse',tomllib.loads((D/'inputs.toml').read_text())==data)
ck('exact_frozen_B4_step5_subset',data['fixtures']==[dict(name=f['name'],matrix=f['matrices'][4],rhs={k:f['steps'][4][k] for k in ('a','dse','unit')}) for f in old['fixtures']])
f=old['fixtures'][0];life=dict(matrix=f['matrices'][0],rhs={k:f['steps'][0][k] for k in ('a','unit')},singular={**f['matrices'][4],'nzval':['0000000000000000']*len(f['matrices'][4]['nzval'])})
ck('exact_B0_step1_and_zeroed_B4',data['lifecycle']==life)
schedule=[]
for fi,f in enumerate(data['fixtures']):
 for rnd in range(1,12):
  arms=['C','P','R'];off=(fi+rnd-1)%3
  for arm in arms[off:]+arms[:off]:schedule.append(dict(id=len(schedule)+1,fixture=f['name'],arm=arm,round=rnd,warm=rnd<=3))
ck('exact132_rotated_schedule',len(schedule)==132 and schedule==data['schedule'])
ck('output_payload_counts',sum(f['matrix']['n'] for f in data['fixtures'])*33*48==405504 and 132*4*48==25344)
src={n:(D/n).read_text() for n in ('driver.jl','control.py','guard.py','supervisor.py','launch.py','seal.py','analysis.py','evidence.py')}
driver=src['driver.jl'];ck('only_three_stdlib_imports',re.findall(r'^using (.+)$',driver,re.M)==['SparseArrays, LinearAlgebra, TOML'] and not re.search(r'^\s*(?:import|include\(|eval\()',driver,re.M))
ck('driver_exact_count_assertion','Dict("fresh"=>141,"refactor"=>9,"copy"=>3,"ftran"=>4245,"btran"=>2133,"snapshot"=>12)' in driver)
ck('private_controls_before_constructor','F=lu(B;control=ctrl,check=true)' in driver and 'ctrl[PIVOT]=arm===:P ? 1.0 : 0.1' in driver and 'ctrl[IR]=arm===:R ? 2.0 : 0.0' in driver)
ck('constant_namespace_corrected','const CAPI=SparseArrays.LibSuiteSparse' in driver and len(re.findall(r'CAPI\.UMFPACK_',driver))==8 and not re.search(r'API\.UMFPACK_',driver.replace('CAPI.','')))
ck('private_T_refactor_no_shallow_candidate','T,tc=newfactor(B0,arm,c)' in driver and driver.count('lu!(T,')==3 and 'lu!(S,' not in driver)
ck('native_solve_orientation','ldiv!(x,transpose(F),b)' in driver and 'ldiv!(x,F,b)' in driver and 'Base.mightalias(x,b)' in driver)
ck('preallocated_outputs_and_info','outputs=[[zeros(size(Bs[i],1)) for _ in 1:48] for i in fi];infos=[zeros(4,48) for _ in schedule]' in driver)
ck('raw_saved_before_final_assert','finally\n        raw["counts"]=countdict(c);save(output,"raw.toml",raw)' in driver)
ck('raw_cell_saved_before_compile_rejection',driver.index('save(output,"window-')<driver.index('Measured compilation contamination'))
ck('unchanged_exact_residual_bound','bound=Q(128*n,2**52)*max(Q(1),norm*max(map(abs,x)),max(map(abs,b)))' in src['analysis.py'])
ck('refinement_attempts_and_retained_corrections','0<=t<=a<=(2 if arm==\'R\' else 0)' in src['analysis.py'] and 'CAPI.UMFPACK_IR_ATTEMPTED+1' in driver)
ck('strategy_and_sympivot_captured','"strategy"=>F.info[STRATEGY]' in driver and "v['sym_pivot']==base[15]" in src['analysis.py'])
ck('guard_memory_thread_limits',all(t in src['guard.py'] for t in ('resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))',"JULIA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'","OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'","sample['available_kib'] < 6 * 1024**2","sample['swap_used_kib'] > 1024**2")))
ck('guard_39_and_supervisor45_no_timeout_acceptance',"'--seconds','39','--deadline',str(started+39)" in src['control.py'] and "not record['soft_timeout'] and not record['hard_timeout']" in src['supervisor.py'] and "record['elapsed_seconds']<=limit" in src['supervisor.py'])
ck('resident_HWM_and_reaped_terminal_peak',"'VmRSS:', 'VmHWM:', 'VmPeak:', 'VmSwap:'" in src['guard.py'] and 'resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss' in src['guard.py'] and "values['VmRSS']<=values['VmHWM']<=peak" in src['evidence.py'])
ck('exact_admission_binding_in_launcher',"required=sealed['files']+[str(sealed_path)]" in src['launch.py'] and "validate_review(rd(review_path),sealed_path,required)" in src['launch.py'])
ck('fresh_host_and_exclusive_reservation_in_launcher',"fresh=host(groups)" in src['launch.py'] and "phase+'-reservation.json'" in src['launch.py'] and "with Path(path).open('x')" in src['control.py'])
ck('postrun_group_and_session_identity_checks',"for field in ('pgid','sid')" in src['evidence.py'] and "post['matches']==[]" in src['evidence.py'])
ck('no_future_output_bindings',all(not n.startswith(str(Q)+'/') or n==str(Q/'accuracy-seal-host.json') for n in s['files']))
result=dict(all_passed=all(checks.values()),checks=checks,checked_at=time.time(),sealed_pins_sha256=sha(SP),verified_hashes=len(actual),refs=refs,host=dict(boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,scope='All process stat/comm and readable executable symlinks; inaccessible system executable symlinks remain a visibility limit.',processes=processes),resources=resources,command=command,sha256={str(pathlib.Path(__file__).resolve()):sha(__file__)},scope='Fresh independent stdlib-only Python static/data/hash/host admission check. No Julia query/parser/import/compile/run; no prepared script import or execution; no launch, seal, guard, old auditor or old tests run.')
with (Q/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],check_count=len(checks),failed=[k for k,v in checks.items() if not v],verified_hashes=len(actual),resources=resources,process_count=len(processes),live_matches=len(matches),sealed_pins_sha256=result['sealed_pins_sha256']),indent=2))
