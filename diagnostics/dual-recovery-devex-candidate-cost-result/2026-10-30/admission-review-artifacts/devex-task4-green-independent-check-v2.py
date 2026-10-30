from pathlib import Path
import json,hashlib,subprocess,re,os
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1';G=R/'green';D=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30';T=Path('/tmp/dual-recovery-devex-task4-green-20261030')
HEAD='31415cc1eccc2d6c332ff14863e509f0d805c909';MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
bindings={};checks={}
def read(p):
 p=Path(p).absolute();b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def sha(p):return hashlib.sha256(read(p)).hexdigest()
def js(p):return json.loads(read(p))
def check(k,v):
 checks[k]=bool(v)
 if not v:raise AssertionError(k)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a])
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def publication(p,n):
 d=js(p/'publication.json'); names=d['expected_names'];check(str(p.name)+'_publication_count_'+str(n),d['accepted'] and len(names)==n)
 for name in names:
  b=read(W/name);h=blob(b);assert git('rev-parse','HEAD:'+name).decode().strip()==h,name
  if name in d['blobs_excluding_publication']:assert d['blobs_excluding_publication'][name]==h,name
 check(str(p.parent.name)+'_committed_blobs',True)
 return names
seal=js(G/'seal.json');pins=js(G/'pins.json');pre=js(T/'preflight.json');read(T/'preflight.py')
check('seal_sha',sha(G/'seal.json')=='24c962ca1e0c50ff57f25c50a8c641611aea524464b871dd117ad13bb78b3f48')
check('pins_sha',sha(G/'pins.json')==seal['pins_sha256']=='f84d570ee1980faf9d317f88d2b36935f8111c681a20f868cc535c77250fc0e2')
check('217_pins_and_unique_exact_inventory',len(pins['inventory'])==217 and len(pins['files'])==217 and set(pins['files'])==set(pins['inventory']) and not pins['trees'] and not pins['inputs'])
for p,v in pins['inventory'].items():assert str(Path(p).resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],p
check('all_217_hashes_and_resolved_targets',True)
publication(P,211);publication(D,33)
refs={x:git('rev-parse',x).decode().strip() for x in ('HEAD','master','origin/master')}
check('current_refs_branch',refs=={'HEAD':HEAD,'master':MASTER,'origin/master':MASTER} and git('branch','--show-current').decode().strip()=='codex/native-quality-finite')
check('clean_tracked_and_index',not git('diff','HEAD','--name-only').strip() and not git('diff','--cached','--name-only').strip())
check('production_test_project_ci_unchanged_from_master',not git('diff',MASTER,'--','src','test','Project.toml','.github').strip())
remote=dict((s.split()[1],s.split()[0]) for s in git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').decode().splitlines())
check('remote_refs',remote==pre['remote_refs']=={'refs/heads/master':MASTER,'refs/heads/codex/native-quality-finite':HEAD})
sources=sorted(x.relative_to(P/'overlays/reference/src') for x in (P/'overlays/reference/src').rglob('*') if x.is_file())
check('71_source_names',len(sources)==71 and sources==sorted(x.relative_to(P/'overlays/candidate/src') for x in (P/'overlays/candidate/src').rglob('*') if x.is_file()))
changed=[]
for name in sources:
 b=read(P/'overlays/reference/src'/name);assert b==git('show',MASTER+':src/'+str(name))==read(W/'src'/name),name
 if b!=read(P/'overlays/candidate/src'/name):changed.append(str(name))
check('only_3_candidate_substitutions',changed==['simplex_numerics.jl','simplex_pivot.jl','simplex_recovery.jl'])
for target,origin in [('simplex_numerics.jl','simplex_numerics.jl'),('simplex_pivot.jl','simplex_pivot.jl'),('simplex_recovery.jl','simplex_recovery-reviewed.jl')]:assert read(P/'overlays/candidate/src'/target)==read(W/'diagnostics/dual-recovery-devex-task3/2026-10-30'/origin)
check('canonical_task3_source',True)
for name in ['Project.toml','Manifest.toml','LocalPreferences.toml']:assert read(P/'overlays/reference'/name)==read(P/'overlays/candidate'/name)==read(W/name)
check('3_environment_original_copies',True)
c=js(P/'contract.json');entry=read(P/'green.jl').decode();includes=re.findall(r'^    include\("([^"]+)"\)',entry,re.M)
check('12_exact_ordered_includes',includes==c['green_includes'] and len(includes)==12 and re.findall(r'TASK4_INCLUDED ([^"]+)',entry)==includes)
for name in includes:read(P/name)
for name in includes[4:11]:assert read(P/name)==git('show',MASTER+':test/'+Path(name).name)
check('7_regressions_master_exact',True)
for target,source in [('refinement_outcome_tests.jl','dual-recovery-devex-task1/2026-10-30/refinement_outcome_tests-reviewed.jl'),('reference_comparison_tests.jl','dual-recovery-devex-task1/2026-10-30/reference_comparison_tests.jl'),('recovery_weight_tests.jl','dual-recovery-devex-task2/2026-10-30/recovery_weight_tests.jl'),('recovery_devex_fallback_tests.jl','dual-recovery-devex-task3/2026-10-30/recovery_devex_fallback_tests-reviewed.jl')]:assert read(P/'tests'/target)==read(W/'diagnostics'/source),target
check('4_canonical_test_modules',True)
endpoint=read(P/'endpoint.jl').decode();check('46_endpoint_assertions',len(re.findall(r'^    @test(?:_throws)?\b',endpoint,re.M))*2==46 and 'for T in (Float32,Float64)' in endpoint)
check('exact_command_phase_scope',seal['phase']=='green' and seal['head']==HEAD and seal['master']==MASTER and seal['expected_exit']==0 and seal['command']==[str(Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia')),'--startup-file=no','--history-file=no','--color=no','--compiled-modules=existing','--pkgimages=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--check-bounds=yes','--project='+str(P/'overlays/candidate'),str(P/'green.jl')])
check('python_interpreter_pin',seal['guard_python']=='/usr/bin/python3' and seal['guard_python'] in pins['inventory'])
check('environment_constraints',seal['environment']['TASK4_OUTPUT']==str(G/'result.toml') and seal['environment']['JULIA_LOAD_PATH']=='@:@stdlib' and all(seal['environment'][k]=='1' for k in ('JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','JULIA_IMAGE_THREADS','JULIA_NUM_PRECOMPILE_TASKS')) and seal['environment']['JULIA_PKG_OFFLINE']=='true' and seal['environment']['JULIA_PKG_PRECOMPILE_AUTO']=='0' and all(Path(x).is_dir() for x in seal['environment']['JULIA_DEPOT_PATH'].split(':')))
a=js(R/'red/audit.json');done=js(R/'red/completion.json')
for p,h in a['bindings'].items():assert sha(p)==h,p
check('red_audit_immutable',a['accepted'] is True and a['test_summary']['Pass']==7 and a['test_summary']['Fail']==1 and sha(R/'red/audit.json')==seal['previous'][0]['audit_sha256'])
raw=sorted(p.relative_to(R/'red') for p in (R/'red').rglob('*') if p.is_file())
for name in raw:assert read(R/'red'/name)==read(D/'red'/name),name
check('19_red_portable_raw_copies',len(raw)==19)
check('shared_budget_exact',seal['shared_total_seconds']==1800 and seal['used_seconds']==done['elapsed_inclusive_seconds']==33.35953255696222 and pre['remaining_seconds']==1800-seal['used_seconds']==1766.6404674430378 and seal['previous']==pre['previous'])
check('unattempted_green_no_later_phase',sorted(p.name for p in G.iterdir())==['pins.json','seal.json'] and not (R/'reference-cost').exists() and not (R/'candidate-cost').exists())
for task in ['task1','task2','task3']:
 p=W/('diagnostics/dual-recovery-devex-'+task+'/2026-10-30');read(p/'REVIEW-FINAL.md');d=js(p/'review-final.json');check(task+'_review_accepted',d['accepted'] is True)
read(D/'REVIEW-FINAL.md');d=js(D/'review-final.json');check('red_result_review_accepted',d['accepted'] is True)
for p in [W/'AGENTS.md',W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md',W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md']:read(p)
post=js(D/'postcheck.json');groups=set(post['checked_groups']);check('730_groups_in_external_preflight',len(groups)==730 and groups==set(pre['host']['checked_groups']) and groups-set(seal['preflight']['checked_groups'])=={406098})
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text();f=st[st.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):conflicts.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),comm=comm))
 except (FileNotFoundError,ProcessLookupError):pass
mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};host=dict(boot_id=boot,checked_group_session_ids=len(groups),conflicts=conflicts,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],refs=refs,remote_refs=remote)
check('fresh_host730_noJulia_resources',boot==pre['host']['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb' and not conflicts and host['available_kib']>=6*1024**2 and host['swap_used_kib']<=1024**2)
for p,h in list(bindings.items()):assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
check('all_read_inputs_unchanged_at_end',True)
read('/tmp/devex-task4-green-independent-check.py');read('/tmp/devex-task4-green-independent-check-v2.py')
out=dict(accepted=True,checks=checks,host=host,bindings=bindings,scope='New independent read-only offline checker; no frozen script imported or executed; no Julia',pin_count=217,prepared_committed_names=211,red_committed_names=33)
Path('/tmp/devex-task4-green-independent-checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),host=host,pins=217)))
