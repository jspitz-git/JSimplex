"""One-shot textual/inverse validation only; not Julia parsing or test execution."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=(C/'block-upper.jl').read_text();t=(C/'block-upper-tests.jl').read_text();o=(C/'block-oracles.jl').read_text()
checks={}
expected=['empty_and_import','nonidentity_q','handle_backrefs','direct_cursor_and_malformed','gap_move_grow','split32_insert33','boundary_swap_rotate','deletion_merge_right','reserve_failure','checked_limits','explicit_zero_order','repeated_row_fills','fragmented_high_water','copy_independence']
checks['14_named_testsets']=re.findall(r'@testset "([^"]+)"',t)==expected
for token in ['mutable struct BGBlockUpper','_bgu_build(','_bgu_find(','_bgu_set!(','_bgu_swap_rows!(','_bgu_rotate_rows!(','_bgu_copy(','_bgu_insert_at!(']:checks['api_'+token]=token in s
checks['no_solver_methods']=not any(token in s for token in ['function forward_solve!','function transpose_solve!','function replace_column!','solve(problem','ccall('])
checks['no_oracle_calls_in_candidate']=not any(token in s for token in ['_bgu_check','_bgu_materialize','Set{','Dict{','@test'])
checks['no_push_resize_in_candidate']=not any(token in s for token in ['push!(','resize!('])
checks['no_retained_allocator']='allocate::' not in s.split('\nend',1)[0]
checks['build_no_generic_insertion']='_bgu_set!' not in s[s.index('function _bgu_build_with'):s.index('_bgu_build(A::')]
checks['bulk_import_not_double_zeroed']='U.rows[r]=allocate(Int32,d)' in s and 'U.values[1]=allocate(Float64,m)' in s
checks['reserve_only_gap_zeroed']='for p in rank:rank+gap-1;a[p]=0;end' in s
checks['reserve_suffix_repair_only']='for k in rank:d\n        p=k+gap;_bgu_back!' in s
checks['no_second_bin_scan']='b=Int(U.bins[32])' in s
checks['copy_clear_disabled']='length(U.values),allocate,false)' in s
checks['right_descriptor_assertion']='V.column_head[3]==right==V.column_tail[3]' in t
checks['middle_split']='vcat(collect(1:16),collect(18:33)),17' in t
checks['true_and_synthetic_limits']='maxblock+1,1' in t and '_bgu_descriptor_capacity(8,9,512)==16' in t
checks['failure_each_explicit_request']='for stop in 1:count[]' in o
checks['allocator_throw_declared']='struct BGUInjectedAllocationFailure <: Exception' in o
checks['all_reserved_capacity_accounted']='D includes unassigned directory spare cells' in (E/'MEMORY-WORK.md').read_text()
checks['budget_original_false_preserved']=json.loads((E/'budget.json').read_text())['all_passed'] is False
checks['budget_refactor_reset_pass']=json.loads((E/'budget-final.json').read_text())['all_passed'] is True
stage=json.loads((E/'overlay-reviewed.json').read_text());O=Path(stage['path'])
checks['final_overlay78_and_hashes']=len(stage['sha256'])==78 and {str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(stage['sha256']) and all(sha(O/n)==h for n,h in stage['sha256'].items())
root=(O/'src/JSimplex.jl').read_bytes();addition=b'\n'+stage['root_addition'].encode()+b'\nend\n'
checks['root_exact_inverse']=root.count(addition)==1 and hashlib.sha256(root.replace(addition,b'\nend\n')).hexdigest()==stage['root_before_sha256']
checks['test_candidate_stage_identity']=all((O/dst).read_bytes()==(C/src).read_bytes() for dst,src in [('src/block-upper.jl','block-upper.jl'),('test/block-oracles.jl','block-oracles.jl'),('test/block-upper-tests.jl','block-upper-tests.jl')])
checks['all_original_tracked_files_unchanged']=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0
checks['head_expected']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='9979d3e6ae00f50e33cd167887d745f76a29e26d'
checks['master_expected']=subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='26e2291745999f485a74f643298ca997d65c7205'
paths=sorted([p for p in C.iterdir() if p.is_file()]+[p for p in E.iterdir() if p.is_file() and p.name not in ('source-check.json',)]+[R/'docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md',R/'docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md'])
record=dict(all_passed=all(checks.values()),checks=checks,testsets=expected,static_assertion_sites=len(re.findall(r'@test(?:_throws)?\b',t))+len(re.findall(r'@test(?:_throws)?\b',o)),scope='Literal source checks, exact file inverses, graph algebra only. No Julia parsing/import/run; static assertion sites not execution/assertion count.',sha256={str(p):sha(p) for p in paths})
with (E/'source-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),bindings=len(paths),static_assertion_sites=record['static_assertion_sites'],failed=[k for k,v in checks.items() if not v]),indent=2))
if not record['all_passed']:raise SystemExit(1)
