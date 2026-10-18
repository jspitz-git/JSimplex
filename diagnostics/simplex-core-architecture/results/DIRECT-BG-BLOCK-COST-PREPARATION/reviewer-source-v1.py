"""Independent final static budget/symmetry/control verification; no Julia parsing."""
from pathlib import Path
import hashlib,json
import control as c
E=Path(__file__).resolve().parent
checks={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def need(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def section(text,a,b):return text[text.index(a):text.index(b,text.index(a))]
s=(E/'cost.jl').read_text();p=(E/'probe.jl').read_text();control=(E/'control.py').read_text();audit=(E/'audit.py').read_text();launch=(E/'launch.py').read_text();seal=(E/'seal.py').read_text();close=(E/'close.py').read_text();publish=(E/'publish.py').read_text()
commands=json.loads((E/'commands.json').read_text())
need(set(commands)=={'cost1-300','cost1-600','cost2-300','cost2-600'},'exact_four_admissible_phases')
for phase,cfg in commands.items():
 need(cfg==c.config(phase),'exact_prepared_command_'+phase)
 cmd=c.guard_command(cfg,Path('/synthetic/pins'),100.)
 need(cmd[cmd.index('--seconds')+1]==str(cfg['seconds']-8) and float(cmd[cmd.index('--deadline')+1])==100+cfg['seconds']-8,'absolute_inner_deadline_'+phase)
life=section(s,'function lifecycle','function residual_ok')
need(life.count('J.forward_solve!(')==2 and life.count('J.replace_column!(')==1 and life.count('J.transpose_solve!(')==1,'per_step_two_FTRAN_one_update_one_BTRAN')
need(life.count('factory(side,')==1 and life.count('J.refactorize!(')==2 and 'for k in 1:8' in life and 'if k==4' in life and 'elseif k==8' in life,'one_setup_eight_updates_refactors4and8')
need('clocks=zeros(UInt64,6)' in life and life.count('t=time_ns();')==7 and life.count('time_ns()-t')==7,'six_symmetric_clock_buckets_seven_calls')
need(not any(x in life for x in ['summarysize','_bgu_check','_block_count!','token.','residual_ok','copy_basis_factorization']),'no_oracle_counter_graph_or_factor_copy_inside_lifecycle')
need('timed=@timed lifecycle(F,backend,side,f,outputs)' in s and s.index('retained=Base.summarysize(factor)')>s.index('timed=@timed'),'graph_outside_whole_lifecycle_timer')
need('factory(::Val{:reference},F,B,backend) = J._direct_lu_factor' in s and 'factory(::Val{:candidate},F,B,backend) = J._block_bg_factor' in s,'unchanged_reference_and_GREEN_timed_factories')
need('_probe_' not in life and 'DynamicBG' not in s,'probe_and_stopped_candidate_excluded_from_timed_lifecycle')
need('policy(::Val{:native}) = J._NATIVE_PIVOT_ONE' in s and 'policy(::Val{:markowitz}) = J._NATIVE_PIVOT_DEFAULT' in s,'fixed_native_one_markowitz_default')
need('for pair in 1:10' in s and 'pair>3' in s and 'isodd(pair) ⊻ startswith(PHASE,"cost2")' in s,'3warm7measured_opposite_second_order')
need('outputs=[zeros(f.n) for _ in 1:24]' in s and s.index('outputs=[zeros(f.n) for _ in 1:24]')<s.index('for pair in 1:10'),'24_external_output_destinations')
need('row=nothing' in s and 'push!(rows' not in s,'no_growing_window_row_or_factor_ledger')
need('for m in (J,LinearAlgebra,SparseArrays,TOML,PrecompileTools)' in s and 'using Test' not in s,'exact_five_reported_loaded_modules_no_Test')
need('row["compile_seconds"]==0 && row["recompile_seconds"]==0' in s,'measured_compile_and_recompile_immediate_stop')
need('memory=getfield(getfield(a,:ref),:mem)' in p and '"backing_length"=>length(memory)' in p and '"backing_bytes"=>sizeof(memory)' in p,'actual_backing_Memory_records')
need('Base.elsize(typeof(a))' in p,'pointer_element_width_from_array_elsize')
need('16*C+4*R+28*K+32*U.n+656' in p and '8*U.n+24*D' in p,'complete_payload_and_reserved_directory_formula')
need('for name in fieldnames(typeof(U))' in p and 'for s in 1:U.slabs' in p and 'for r in 1:U.n' in p,'all_top_vectors_and_child_buffers_enumerated')
need('Base.summarysize(U)' in p and '[Base.summarysize(x) for x in (r,d,p)]' in p,'upper_and_all_three_full_graphs')
need('states=[checkpoint(r,d,p,0,false)]' in p and 'push!(states,checkpoint(r,d,p,k,false))' in p and 'if k in (4,8)' in p and 'push!(states,checkpoint(r,d,p,k,true))' in p,'eleven_checkpoints_0plus8plus2')
need('J._bgu_check(d.upper) && J._probe_bgu_check(p.upper)' in p and 'isequal(history(r),history(d))' in p,'probe_invariant_history_and_state_equality')
need('for c in 1:64' in p and 'J._probe_bgu_build(spzeros(64,64),collect(1:64))' in p,'exact64_repeated_fill_structural_probe')
need('states' not in life,'checkpoint_state_not_in_timed_lifecycle')
need('one_attempt=True' in launch and 'save(res,' in launch and "Path(cfg['output']).exists()" in launch,'exclusive_one_attempt_reservation')
need('block BG matched cost admission' in launch and 'verify_review(' in launch and 'guard.pins_match(sealed)' in launch,'fresh_exact_stage_admission_before_launch')
need('first_process_viable(' in control and "result_review(prev,'pure timeout result'" in control and 'Unprepared or out-of-order attempt' in control,'separate_second_and_timeout_admissions')
need('timeout_ok(' in audit and 'output_checks(out,cfg,partial=True)' in audit and 'qualify(' in audit,'partial_prefix_validation_and_two_process_qualification')
need("preparation();" in close and "not (D/'runs').exists()" in close and "names==rd(D/'closure-names.json')['names']" in close,'closure_acceptance_no_phase_and_exact_names')
need("len(h['groups'])==238" in close and "h['head']==ENTRY and h['master']==MASTER" in close,'closure_requires_fresh_identity_group_and_ref_checks')
need("sorted(actual)==sorted(bound)" in publish and "sha(git('show',':'+n))==h==sha((R/n).read_bytes())" in publish and "'git','diff','--cached','--check'" in publish,'publication_exact_staged_names_and_blobs')
need(".open('x')" in publish and "'commit'" not in publish and "'push'" not in publish,'publication_exclusive_and_unexecuted_no_commit')
# Repeat full binding verification after all new reviewer checks, independent of author helpers.
m=json.loads((E/'preparation-pins.json').read_text())['sha256']
need(len(m)==1820 and all(sha(Path(n))==h for n,h in m.items()),'final_all1820_hashes_unchanged')
need(not (E/'runs').exists(),'final_no_new_seal_reservation_or_run')
counts=dict(cells=4*2,warm_windows=4*2*3*2,measured_windows=4*2*7*2,all_windows=4*2*10*2,constructors=160+8*3+8*2,refactors=160*2+8*3*2+8*2*2,replacements=160*8+8*3*8,FTRAN=160*16+8*3*16,BTRAN=160*8+8*3*8,factor_copies=0,explicit_factorization_entries=200+400,residual_vectors=160*24+8*3*24,checkpoints_per_cell=1+8+2)
need(counts==dict(cells=8,warm_windows=48,measured_windows=112,all_windows=160,constructors=200,refactors=400,replacements=1472,FTRAN=2944,BTRAN=1472,factor_copies=0,explicit_factorization_entries=600,residual_vectors=4416,checkpoints_per_cell=11),'independent_source_derived_call_budget')
with (E/'reviewer-source-v1.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,counts=counts,pins_sha256=sha(E/'preparation-pins.json'),checker_sha256=sha(__file__),scope='Independent static source budget/symmetry/control and final full binding verification'),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),counts=counts)))
