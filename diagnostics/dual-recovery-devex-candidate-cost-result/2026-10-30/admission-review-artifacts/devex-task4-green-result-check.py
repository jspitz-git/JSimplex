"""Independent failed-GREEN result check. Reads evidence only; writes /tmp outputs.
Never imports or executes repository scripts or Julia; Git calls are read-only.
"""
from pathlib import Path
import hashlib,json,re,subprocess,tomllib,math,traceback
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
D=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
R=W/'.superpowers/dual-recovery-devex-task4/qualification-1/green'
RED=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30'
OUT=Path('/tmp/devex-task4-green-result-checks.json')
bindings={};checks={}
def raw(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b
def txt(p):return raw(p).decode()
def read(p):return json.loads(raw(p))
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 bindings[str(p)]=h.hexdigest();return h.hexdigest()
def check(n,b):
 checks[n]=bool(b)
 if not b:raise AssertionError(n)
def git(*args):return subprocess.check_output(['git','-C',str(W),*args])
post=read(D/'postcheck.json');cause=read(D/'cause-check.json');ad=read(D/'devex-task4-green-admission.json')
pins=read(R/'pins.json');seal=read(R/'seal.json');proc=read(R/'guard/process.json');sup=read(R/'supervisor.json');done=read(R/'completion.json');attempt=read(R/'attempt.json');contract=read(P/'contract.json')
for p in D.rglob('*'):
 if p.is_file():sha(p)
for p in [W/'AGENTS.md',W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md',W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md']:
 txt(p)
check('admission_40_checks_371_bindings',len(ad['checks'])==40 and all(v is True for v in ad['checks'].values()) and len(ad['bindings'])==371)
check('all_371_admission_bindings',all(sha(n)==h for n,h in ad['bindings'].items()))
check('217_exact_unique_pin_inventory',len(pins['inventory'])==len(pins['files'])==217 and set(pins['files'])==set(pins['inventory']))
check('all_217_pin_hashes_and_resolutions',all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()))
check('sealed_pin_and_guard_copies',sha(R/'pins.json')==seal['pins_sha256']==ad['pins_sha256']==proc['pins_sha256']=='f84d570ee1980faf9d317f88d2b36935f8111c681a20f868cc535c77250fc0e2' and raw(R/'pins.json')==raw(R/'guard/pins.json'))
check('seal_and_admission_report_binding',sha(R/'seal.json')==ad['seal_sha256']==attempt['seal_sha256']=='24c962ca1e0c50ff57f25c50a8c641611aea524464b871dd117ad13bb78b3f48' and sha(attempt['admission_path'])==attempt['admission_sha256']==sha(D/'devex-task4-green-admission.json') and sha(ad['review_report'])==ad['review_report_sha256'])
check('nineteen_runtime_files_exact_inventory',len(post['portable'])==19 and set(post['portable'])=={str(p) for p in R.rglob('*') if p.is_file()})
check('nineteen_runtime_portable_copies',all(sha(n)==sha(v['copy'])==v['sha256'] for n,v in post['portable'].items()))
check('twelve_external_exact_copies',len(post['external_exact_copies'])==12 and all(sha(n)==sha(v['copy'])==v['sha256'] for n,v in post['external_exact_copies'].items()))
check('cause_check_all_twelve_bindings',len(cause['bindings'])==12 and all(sha(n)==h for n,h in cause['bindings'].items()))
check('supplemental_checks_scoped',len(post['checks'])==9 and len(cause['checks'])==12 and all(v is True for v in post['checks'].values()) and all(v is True for v in cause['checks'].values()) and post['canonical_audit_accepted'] is False and 'source/raw diagnosis only' in cause['scope'])
refs={n:git('rev-parse',n).decode().strip() for n in ['HEAD','master','origin/master']}
check('current_refs_exact',refs['HEAD']==seal['head']==ad['head']=='31415cc1eccc2d6c332ff14863e509f0d805c909' and refs['master']==refs['origin/master']=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' and git('branch','--show-current').decode().strip()=='codex/native-quality-finite')
check('tracked_tree_and_index_unchanged',not git('diff','HEAD','--name-only').strip() and not git('diff','--cached','--name-only').strip())
check('production_test_project_ci_unchanged_from_master',not git('diff','master','--','src','test','Project.toml','.github').strip())
ref=P/'overlays/reference/src';cand=P/'overlays/candidate/src'
names={str(x.relative_to(ref)) for x in ref.rglob('*.jl')}
check('71_original_sources_match_reference_and_master',len(names)==71 and names=={str(x.relative_to(cand)) for x in cand.rglob('*.jl')} and all(raw(ref/n)==raw(W/'src'/n)==git('show','master:src/'+n) for n in names))
changed={n for n in names if raw(ref/n)!=raw(cand/n)}
check('candidate_only_three_canonical_substitutions',changed=={'simplex_recovery.jl','simplex_numerics.jl','simplex_pivot.jl'} and all(raw(cand/n)==raw(W/'diagnostics/dual-recovery-devex-task3/2026-10-30'/source) for n,source in [('simplex_recovery.jl','simplex_recovery-reviewed.jl'),('simplex_numerics.jl','simplex_numerics.jl'),('simplex_pivot.jl','simplex_pivot.jl')]))
for side in ['reference','candidate']:
 check(side+'_three_environment_copies_unchanged',all(raw(P/'overlays'/side/n)==raw(W/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']))
regressions=read(P/'staging.json')['regressions']
check('all_seven_regressions_unchanged',len(regressions)==7 and all(raw(P/'tests'/n)==raw(W/'test'/n)==git('show','master:test/'+n) for n in regressions))
log=txt(R/'guard/run.log');driver=txt(P/'green.jl');endpoint=txt(P/'endpoint.jl');stage=txt(P/'stage.py');prep=txt(P/'ADMISSION-PREPARATION.md');test=txt(P/'tests/simplex_numerics_tests.jl')
header=next(s for s in log.splitlines() if s.startswith('Test Summary:'));line=next(s for s in log.splitlines() if s.startswith('TASK4_GREEN') and '|' in s)
keys=re.findall(r'Pass|Fail|Error|Broken|Total|Time',header.split('|')[1]);vals=line.split('|')[1].split();summary={k:int(v) for k,v in zip(keys,vals) if k!='Time'}
for n in ['Pass','Fail','Error','Broken']:summary.setdefault(n,0)
check('ordinary_summary_5772_0_1_0_5773',summary=={'Pass':5772,'Fail':0,'Error':1,'Broken':0,'Total':5773} and '5772 passed, 0 failed, 1 errored, 0 broken' in log)
missing=P/'tests/fixtures/solver/netlib/adlittle.mps';original=W/'test/fixtures/solver/netlib/adlittle.mps'
check('sole_missing_file_error',log.count('Error During Test at')==1 and 'Numerical strategy propagation: Error During Test' in log and f'opening file "{missing}": No such file or directory' in log and ':129 [inlined]' in log)
check('fixture_original_exact_and_staged_absent',not missing.exists() and original.stat().st_size==16500 and sha(original)=='fec81e24fa91bc545d97239b108b43e6034f37b4bf2455a3f8c179726b44d44c')
check('omitted_dependency_explicit_source_cause','read_mps(joinpath(@__DIR__,"fixtures","solver","netlib","adlittle.mps"))' in test and 'adlittle' not in stage and str(missing) not in pins['inventory'] and 'wide-bound129.mps' in stage and 'No other model file is admitted.' in prep)
check('two_original_checks_after_failing_read',test.index('problem = read_mps')<test.index('@test result.status == OPTIMAL')<test.index('@test !isempty(observed) && all(==(7),observed)'))
check('twelve_ordered_markers_no_green_completion',re.findall(r'^TASK4_INCLUDED (.+)$',log,re.M)==contract['green_includes'] and len(contract['green_includes'])==12 and 'TASK4_GREEN_COMPLETED' not in log)
check('ordinary_driver_candidate_and_unmodified_includes','using JSimplex,Test' in driver and '"overlays","candidate","src","JSimplex.jl"' in driver and re.findall(r'^    include\("(.+)"\)',driver,re.M)==contract['green_includes'])
records=tomllib.loads(txt(R/'result.toml'))['cases']
check('two_endpoint_cases_46_pass',len(records)==2 and {q['type'] for q in records}=={'Float32','Float64'} and re.search(r'^\s+TASK4_POST_FALLBACK\s+\|\s+46\s+46\s+',log,re.M) is not None and len(re.findall(r'^    @test(?:_|\s)',endpoint,re.M))==23)
check('endpoint_certificates_work_and_trajectory',all(q['point']==q['witness']==[1,0] and all(q[k] is True for k in ['original_primal_certified','original_optimality_certified','invalid_witness_rejected','invalid_row_rejected','trajectory_changed']) and all(q[k]==1 for k in ['iterations','factorizations','attempted_weight_rows','avoided_weight_rows']) and (q['core_and_weight_ftran'],q['core_and_weight_btran'],q['final_ftran'],q['final_btran'])==(1,3,2,4) for q in records))
check('endpoint_nonnegative_stats_not_benchmark',all(all(type(s[k]) in [int,float] and math.isfinite(s[k]) and s[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds']) for q in records for s in [q[k] for k in ['preparation','whole_fallback','component_preparation','component_revalidation','component_reset']]))
check('process_natural_failure_preserved',proc['reason']=='exit1' and proc['returncode']==sup['returncode']==1 and proc['pins_unchanged'] is True and sup['accepted'] is False and done['supervisor_accepted'] is False and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and all(sup[k] is True for k in ['abnormal_cleanup_attempted','child_cleanup_attempted']))
launch=txt(P/'launch-reviewed.py');audit=txt(P/'audit_reviewed.py');txt(P/'common.py')
check('audit_absent_and_launcher_rejects_before_call',not (R/'audit.json').exists() and not (D/'green/audit.json').exists() and launch.index("C.require(result.get('accepted') is True and used+elapsed<=1800")<launch.index('audit.audit_phase(phase)'))
check('exact_admitted_command_environment',ad['command']==seal['command']==proc['command'] and read(R/'invocation.json')['environment']==seal['environment'] and '--expected-exit' in read(R/'invocation.json')['command'] and seal['expected_exit']==0)
red_audit_path=R.parent/'red/audit.json';red_audit=read(red_audit_path)
check('original_red_audit_and_bindings_unchanged',red_audit['accepted'] is True and sha(red_audit_path)==seal['previous'][0]['audit_sha256']=='3a4082f2a5f37e3f71d70188a9caae08675f5a1dd3a4d94846f26d68251a1b60' and all(sha(n)==h for n,h in red_audit['bindings'].items()))
red_log=txt(R.parent/'red/guard/run.log');warn=lambda s:[x for x in s.splitlines() if x.startswith('WARNING:')]
check('four_red_warnings_preserved',len(warn(log))==4 and warn(log)==warn(red_log)==post['warnings'])
check('shared_arithmetic_exact_not_exhausted',seal['used_seconds']==33.35953255696222 and done['elapsed_inclusive_seconds']==494.6009602919803 and done['total_inclusive_seconds']==seal['used_seconds']+done['elapsed_inclusive_seconds']==527.9604928489425 and 1800-done['total_inclusive_seconds']==post['remaining_seconds']==1272.0395071510575)
check('only_red_green_no_retry_or_cost',sorted(p.name for p in R.parent.iterdir() if p.is_dir())==['green','red'])
samples=[json.loads(x) for x in txt(R/'guard/resources.jsonl').splitlines()]
check('494_resource_samples_within_limits',len(samples)==494 and min(x['available_kib'] for x in samples)==20915012 and max(x['swap_used_kib'] for x in samples)==0 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in [*samples,proc['terminal_memory'],post['host']['memory']]) and proc['child_maxrss_kib']==2129068)
old=read(RED/'postcheck.json');groups=set(old['checked_groups']);identities=[attempt['runner'],proc['runner'],proc['child']]
check('three_exact_recorded_identities',[(a['pid'],a['start_ticks']) for a in identities]==[(410682,32720389),(410703,32720412),(410704,32720428)] and all(a['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb' for a in identities) and identities==post['closed_owner_identities'])
for a in identities:groups.update([a['pgid'],a['sid']])
check('733_full_historical_group_session_set',len(groups)==733 and groups==set(post['checked_groups'])==set(post['host']['checked_groups']) and post['host']['conflicts']==[])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();conflicts=[];races=0;inspected=0
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();inspected+=1
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia'):
   conflicts.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),comm=comm))
 except (FileNotFoundError,ProcessLookupError):races+=1
check('fresh_full_733_group_session_no_julia_closure',boot==post['host']['boot_id'] and not conflicts)
mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()}
host=dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,inspected_processes=inspected,vanished_proc_races=races,refs=refs,memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
check('fresh_host_resource_headroom',host['memory']['available_kib']>=6*1024**2 and host['memory']['swap_used_kib']<=1024**2)
report=txt(D/'REPORT.md')
check('report_failure_and_limits_explicit',all(s in report for s in ['GREEN NOT ACCEPTED','5772 PASS / 0 FAIL / 1 ERROR / 0 BROKEN','canonical auditor was NOT run','Preparation and admission overlooked it','cost phases are unexecuted','No actual production code changed','No observer-neutrality','Prepare a separately named offline continuation']))
sha(__file__)
result=dict(accepted=True,scope='independent read-only evidence check for failed GREEN diagnosis and closure only',runtime_accepted=False,candidate_accepted=False,canonical_audit_run=False,production_accepted=False,checks=checks,bindings=bindings,counts=dict(checks=len(checks),bindings=len(bindings),runtime_pins=217,admission_bindings=371,runtime_portable_copies=19,external_exact_copies=12,closure_groups_and_sessions=733,resource_samples=494),host=host,ordinary_summary=summary,endpoint_cases=records,budget=dict(green_seconds=done['elapsed_inclusive_seconds'],red_plus_green_seconds=done['total_inclusive_seconds'],unspent_seconds=1800-done['total_inclusive_seconds']),limitations=['No Julia or frozen script imported/executed; no signals, repo mutation, retry, cost or production/master acceptance','Review accepts diagnostic failure decision only; canonical auditor NOT RUN','Fresh closure is full group/session scan, not PID-only proof','Endpoint is bounded positive evidence; two public-solve assertions not reached','No speedup, default allocation neutrality, hidden native memory, full-suite or original-model solver correctness inferred'])
with OUT.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,runtime_accepted=False,candidate_accepted=False,counts=result['counts'],host=host['memory'],proc_races=races)))
