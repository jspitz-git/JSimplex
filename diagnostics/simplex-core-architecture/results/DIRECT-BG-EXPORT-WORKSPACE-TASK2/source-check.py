from pathlib import Path
import hashlib,json,re,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
C=R/'diagnostics/direct-bg-export-workspace/reproduce';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-TASK2';E1=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-TASK1')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def put(name,data):
 with (E/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
old=json.loads((C/'source-manifest.json').read_text());stage=Path(old['stage']);original=old['original_readtime_sha256'];checks={}
checks['all679_original_stage_runtime_pins']=len(original)==679 and all(sha(p)==h for p,h in original.items())
final=json.loads((E1/'final-review.json').read_text());checks['Task1_accepted']=final['accepted'] and not any(final[k] for k in ('critical','important','minor'))
checks['Task1_eight_files_frozen']=all(sha(C/name)==final['readtime_sha256'][str(C/name)] for name in ('workspace.jl','export.jl','import.jl','workspace-tests.jl','import-tests.jl','work-memory-ledger.md','source-inverse.json','source-manifest.json'))
f=(C/'factor.jl').read_text();t=(C/'lifecycle-tests.jl').read_text();ledger=(C/'composition-ledger.md').read_text();ref=(stage/'src/direct-factor.jl').read_text()
checks['tests_written_first']=json.loads((E/'tests-first.json').read_text())['factor_file_absent']
checks['one_inner_publication']=f.count('f.inner=candidate')==1
checks['private_order']=f.index('candidate=_bgx_build')<f.index('check_inner(f.inner,candidate)')<f.index('f.inner=candidate')<f.index('finally\n        f.busy=false')
checks['busy_before_try']=f.index('f.busy && throw')<f.index('f.busy=true')<f.index('candidate=_bgx_build')
checks['drop_and_rethrow']='catch\n        _bgx_drop!(f)\n        rethrow()' in f
checks['single_factorize_export_import']=f.count('ordinary=factorize(B,backend,policy)')==1 and f.count('parts=export_parts(ordinary,owner;allocate)')==1 and f.count('upper,D=import_upper(parts.upper,normalize;allocate)')==1
checks['no_discarded_reference_factory']='_direct_lu_factor(' not in f
checks['copy_no_scratch']='BGExportFactor(copy_basis_factorization(f.inner),nothing,false)' in f
checks['exact_backend_construction']=all(s in f and s in ref for s in ('DirectLowerBackend{R,F}(spzeros(0,0),Int[],Float64[],false,nothing,','DirectLowerBackend{R,F}(parts.lower,parts.rows,parts.scaling,parts.divide_scaling,','D,normalize,policy,nothing,zeros(length(parts.rows)))'))
checks['no_inner_reimplementation']=not any(s in f for s in ('for name in fieldnames','_upper_backsolve!','_backend_forward_solve!','mul!','ldiv!','_begin_upper_update!'))
forwardings={'forward_solve!':'forward_solve!(out,f.inner,rhs)','transpose_solve!':'transpose_solve!(out,f.inner,rhs)','_ordinary_forward_solve!':'_ordinary_forward_solve!(out,f.inner,rhs)','forward_solve':'forward_solve(f.inner,rhs)','transpose_solve':'transpose_solve(f.inner,rhs)','_unit_transpose_rhs':'_unit_transpose_rhs(f.inner,rhs,row)','_copy_prepared_spike!':'_copy_prepared_spike!(f.inner,direction)','_direct_mode':'_direct_mode(f.inner)','_backend_dimension':'_backend_dimension(f.inner.base)','_factor_storage_count':'_factor_storage_count(f.inner)','_factor_growth_measure':'_factor_growth_measure(f.inner)','_factor_growth_reference':'_factor_growth_reference(f.inner)','_finite_updated_factor':'_finite_updated_factor(f.inner)'}
checks['all13_direct_forwardings']=all(v in f for v in forwardings.values())
checks['update_original_tolerance']='zero_tolerance::Real=_positive_tolerance(Float64,1//10^12)' in f and 'replace_column!(f.inner,direction,row;zero_tolerance)' in f
checks['scope_guards']=all(s in f for s in ('policy===_NATIVE_PIVOT_ONE','policy===_NATIVE_PIVOT_DEFAULT','SparseMatrixCSC{Float64,Int}'))
checks['all4_required_test_entries']=all('function run_'+s+'()' in t for s in ('repeated_shape_lifecycle','private_publish_failure_matrix','copy_refactor_diverge','dimension_fallback_transition'))
checks['all7_fixtures_both_modes_policies']='for fixture in export_fixtures(), (R,p) in ARMS, normalize in (false,true)' in t
checks['eight_updates_refactors4_8']='for t in 1:8' in t and 'if t in (4,8)' in t
checks['enter_dse_update_original']='X.replace_column!(f,entering,j)' in t and t.index('X.forward_solve!(aux,f,dse)')<t.index('X.replace_column!(f,entering,j)')
checks['all_failure_seams']=all(s in t for s in ('factorize=(args...)->throw(sentinel)','export_parts=malformed','import_upper=(args...;kwargs...)->throw(sentinel)','make_inner=(args...)->throw(sentinel)','check_inner=(args...)->throw(sentinel)','for k in 1:a.calls','for k in 1:5','recursive='))
checks['exact_preservation']=all(s in t for s in ('samegraph(old,before)','samegraph(saved.inner,copybefore)','snapshot(B)==input','validation_error[]=err','rethrow()'))
checks['real_and_synthetic_poison']='active=graph(f.inner)' in t and 'Explicit synthetic cache injection' in t
checks['full_graph_not_sparse_dense_iteration']='if v isa Array || v isa BitArray' in t and 'IdDict' in t and 'isdefined(v,i)' in t
checks['fallback_once']='calls[]==1 && exports[]==1' in t
checks['no_autorun']=t.rstrip().endswith('end\nend')
checks['work_memory_limits_explicit']=all(s in ledger for s in ('A_old+A_new','policy charge','2984','M_R<=25','failed-copy','15 fields','No runtime allocation'))
checks['no_tracked_edits']=not subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R,text=True).strip()
newnames=('factor.jl','lifecycle-tests.jl','composition-ledger.md')
paths=set(original)|{str(p) for p in C.iterdir() if p.is_file()}|{str(E1/n) for n in ('FINAL.md','final-review.md','final-review.json','closure.json','publication.json')}|{str(R/'docs/superpowers'/d/'2026-10-18-direct-bg-export-workspace.md') for d in ('plans','specs')}|{str(E/n) for n in ('host.json','tests-first.json','source-check.py')}
# Original fixture/oracle text remains a dependency, not an automatically executed entry.
paths.add(str(R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl'))
manifest={'scope':'OFFLINE Task2 only; not a launch manifest','stage':str(stage),'original_readtime_sha256':original,'candidate_task1_frozen':{str(C/n):sha(C/n) for n in ('workspace.jl','export.jl','import.jl','workspace-tests.jl','import-tests.jl','work-memory-ledger.md','source-inverse.json','source-manifest.json')},'candidate_task2':{str(C/n):sha(C/n) for n in newnames},'root_additions':old['root_additions']+[str(C/'factor.jl')],'root_rule':old['root_rule'],'test_order':[str(C/n) for n in ('workspace-tests.jl','import-tests.jl','lifecycle-tests.jl')],'test_entry':'BGExportLifecycleTests.run_lifecycle_tests() only; Task1 entries not run','all_tests':'UNEXECUTED; no parser/Julia/compile','forwarding_inventory':forwardings}
with (C/'overlay-manifest.json').open('x') as out:json.dump(manifest,out,indent=2);out.write('\n')
paths.add(str(C/'overlay-manifest.json'))
result=dict(all_passed=all(checks.values()),checks=checks,readtime_sha256={p:sha(p) for p in sorted(paths)},static_test_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',t)),scope='Source/inverse/provenance checks; NOT Julia syntax, dispatch or numerical proof')
put('source-check.json',result);print(json.dumps({'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'hashes':len(paths),'assertion_sites':result['static_test_assertion_sites']}));raise SystemExit(0 if result['all_passed'] else 1)
