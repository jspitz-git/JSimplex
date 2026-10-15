"""Fresh exact-stage reviewer checks. Read-only except exclusive new reviewer report.
No Julia, seal, launcher, auditor, historical checker, or numerical oracle execution.
"""
from pathlib import Path
import json, hashlib, sys, os, time, subprocess
RUN=Path(__file__).resolve().parent;D=RUN.parents[1];R=D.parents[3];P=D.parent/'NATIVE-PIVOT-PREPARATION';Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';F=D.parent/'NATIVE-PIVOT-OBSERVER-FIX'
sys.path.insert(0,str(D))
import control, guard
checks={}; cache={}; byte_count=0;started=time.monotonic()
def rd(p):return json.loads(Path(p).read_text())
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def sha(p):
 global byte_count
 p=path(p)
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b);byte_count+=len(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def check(n,b):
 checks[n]=bool(b)
 if not b:raise ValueError(n)
def bindings(n,p):
 z=rd(p);check(n,all(sha(k)==v for k,v in z['sha256'].items()));return z
sp=RUN/'sealed.json';sealed=rd(sp);cfg=rd(RUN/'config.json');pins=rd(D/'preparation-pins.json')
check('unique_absolute_sealed_files',len(sealed['files'])==len(set(sealed['files']))==962 and all(Path(p).is_absolute() for p in sealed['files']))
check('exact_inventory_membership',set(sealed['files'])==set(sealed['inventory']))
check('all_962_fresh_hashes_and_resolved_paths',all(sha(p)==z['sha256'] and str(Path(p).resolve(strict=True))==z['resolved'] for p,z in sealed['inventory'].items()))
check('phase_root_command_binding',sealed['phase']=='green2' and sealed['config']==cfg==control.config('green2')==rd(D/'config-preview.json'))
check('sole_candidate_tree_empty_inputs',sealed['trees']==[cfg['stage']] and sealed['inputs']==[])
check('only_seal_config_host_before_review',{p.name for p in RUN.iterdir()}=={'sealed.json','config.json','host.json','admission-checks.py'})
check('no_output_reservation_admission',all(not (RUN/n).exists() for n in ['output','reservation.json','launch-pins.json','invocation.json','admission.json']))
check('881_preparation_and_required_membership',len(pins['sha256'])==881 and set(pins['sha256'])==set(rd(D/'required-paths.json')['paths']))
check('all_preparation_hashes',all(sha(k)==v for k,v in pins['sha256'].items()))
review=bindings('accepted_review_882_hashes',D/'review-final.json')
control.verify_review(review,D/'preparation-pins.json',list(pins['sha256'])+[str(D/'preparation-pins.json')],'offline preparation')
check('accepted_review_scope_membership',len(review['sha256'])==882)
for n in ['source-check.json','reviewer-checks.json','reviewer-final-bindings.json','publication-review.json','closure.json','closure-supplement.json','publication-final.json']:
 z=bindings('bindings_'+n,D/n)
 if 'all_passed' in z:check('accepted_'+n,z['all_passed'] is True)
 if 'checks' in z:check('checks_'+n,all(z['checks'].values()))
check('106_recorded_checks',len(rd(D/'reviewer-checks.json')['checks'])==106)
check('publication_scope',rd(D/'publication-review.json')['accepted'] is True and rd(D/'publication-review.json')['findings']==[] and rd(D/'publication-review.json')['scope']=='exact diff-context publication')
extra,groups=control.predecessor('green2');check('distinct_red_failedgreen_observer_bindings',len(groups)==212)
check('old_red_still_passed_green_still_failed',rd(Q/'runs/red/audit.json')['all_passed'] is True and rd(Q/'runs/green/audit.json')['all_passed'] is False)
staged=control.validate_stage(cfg)
check('exact_75_stage_files',len(staged)==75 and not any(p.is_symlink() for p in Path(cfg['stage']).rglob('*')))
expected=set(pins['sha256'])|{str(D/'preparation-pins.json'),str(D/'review-final.json'),str(RUN/'host.json'),str(RUN/'config.json'),str(control.STATUS),str(control.ROAD)}|{str(p) for p in staged+extra}
check('exact_seal_file_union',set(sealed['files'])==expected)
manifest=rd(P/'overlay-manifest.json')
for arm,count in [('candidate',75),('reference',73)]:check(arm+'_source_identity',len(manifest[arm])==count and all(sha(e['source'])==e['sha256'] for e in manifest[arm]))
inv=rd(P/'inverse.json');check('seven_files_28_edits',len(inv['original'])==7 and len(inv['edits'])==28)
check('original_candidate_inverse_hashes',all(sha(k)==v for t in ['original','candidate'] for k,v in inv[t].items()))
for original in inv['original']:
 rel=str(Path(original).relative_to(R));s=(P/'candidate'/rel).read_text()
 for e in reversed(inv['edits']):
  if e['file']==rel:
   check('unique_inverse_'+str(inv['edits'].index(e)),s.count(e['after'])==1);s=s.replace(e['after'],e['before'])
 check('whole_source_inverse_'+rel,s==Path(original).read_text())
sm=rd(D/'source-map.json')
for n,p in sm['byte_identical'].items():check('identical_'+n,(D/n).read_bytes()==Path(p).read_bytes())
driver=(D/'test-driver.jl').read_text()
reverse=driver.replace('include(joinpath(@__DIR__,"regression-reviewed.jl"))\n','').replace('root=RecordedTests.Capture("root")\n    regression=RecordedTests.Capture("regression")\n    helper_calls=Ref(0)','root=RecordedTests.Capture("root")')
insert='''        raw["regression_counts_before"]=copy(NP.counts)
        Test.@with_testset regression begin
            DenseTokenRegression.run((format,v)->begin
                helper_calls[]+=1
                NP.dense_tokens(format,v)
            end,NP.scalar,NP.token)
        end
        raw["regression_counts_after"]=copy(NP.counts)
'''
check('unique_driver_addition',reverse.count(insert)==1)
reverse=reverse.replace(insert,'').replace('if phase=="green2"','if phase=="red"\n            include(joinpath(@__DIR__,"..","NATIVE-PIVOT-QUALIFICATION","red-contract.jl"))\n        elseif phase=="green"').replace('\n        raw["regression_tests"]=RecordedTests.dictionary(regression)\n        raw["regression_helper_calls"]=helper_calls[]','').replace('failed(root)==0 && failed(regression)==0 ? 0 : 1','failed(root)==0 ? 0 : 1')
check('whole_driver_inverse',reverse==(F/'test-driver-fixed.jl').read_text())
check('top_level_regression_include',driver.index('include(joinpath(@__DIR__,"regression-reviewed.jl"))')<driver.index('function main()'))
budget=rd(D/'budget.json');reg=rd(D/'regression-budget.json')
check('original9groups_6858_assertions',len(budget['test_groups'])==9 and sum(budget['test_groups'].values())==budget['green_assertions']==6858)
check('original792_entries_324_equations',sum(budget['main'].values())+sum(budget['neighbors'].values())==792 and reg['original_equations']==324 and "len(equations)==324" in (D/'oracle.py').read_text())
check('119_separate_regression_16_helpers_zero_production',reg['assertions']==1+12*9+4*2+2==119 and reg['helper_calls']==12+4==16 and reg['selected_production_calls']==0 and reg['total_assertions']==6977 and budget['public_solves']==reg['public_solves']==0)
runtime=bindings('679_runtime_source_env_hashes',Q/'runtime-pins.json')
check('runtime_membership',len(runtime['sha256'])==679 and set(runtime['sha256'])<=set(sealed['files']))
check('wrapper_chain_and_binary_pinned',all(n in sealed['inventory'] for n in [control.WRAPPER,'/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/julia.sh','/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia','/bin/bash','/usr/bin/python3',str(Path(sys.executable).resolve())]))
check('loaded_stdlib_source_paths_pinned',all(p in sealed['inventory'] for p in rd(D/'loaded-paths.json').values()))
control.validate_environment();check('current_environment',True)
h=control.full_host(groups+sealed['groups'])
check('all212_groups_and_sessions_no_julia',len(h['groups'])==212 and set(h['groups'])==set(groups)==set(sealed['groups']) and h['matches']==[])
check('fresh_refs_boot',all(h[k]==sealed[k]==rd(RUN/'host.json')[k] for k in ['head','master','boot_id']) and h['head']=='3feb815bf8a1507d5feecafaf038315b645a4243' and h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194')
check('source_head_ancestor',subprocess.run(['git','merge-base','--is-ancestor',control.HEAD,'HEAD'],cwd=R).returncode==0)
check('tracked_index_clean',not control.git('diff','--name-only') and not control.git('diff','--cached','--name-only'))
mem=guard.memory();check('fresh_memory',not guard.pressure(mem))
check('inclusive60_inner52',cfg['seconds']==60 and control.guard_command(cfg,RUN/'launch-pins.json',100)[6:10]==['--seconds','52','--deadline','152'])
check('pidfd_available',hasattr(os,'pidfd_open') and hasattr(__import__('signal'),'pidfd_send_signal'))
identity=guard.process_identity(os.getpid());check('current_reviewer_identity',identity['start_ticks']>0 and bool(identity['command']) and identity['boot_id']==sealed['boot_id'])
record=dict(all_passed=all(checks.values()),checks=checks,sealed_sha256=sha(sp),sealed_files=len(sealed['files']),stage_files=len(staged),unique_files_hashed=len(cache),bytes_hashed=byte_count,elapsed_seconds=time.monotonic()-started,host=h,memory=mem,reviewer_identity=identity,sha256=cache,scope='Fresh independent read-only exact-stage admission evidence; no Julia or old auditor/checker execution')
with (RUN/'admission-checks.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:record[k] for k in ['all_passed','sealed_sha256','sealed_files','stage_files','unique_files_hashed','bytes_hashed','elapsed_seconds','memory']}));print('checks',len(checks))
