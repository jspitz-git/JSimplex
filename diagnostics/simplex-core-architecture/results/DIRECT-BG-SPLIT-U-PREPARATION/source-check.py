from pathlib import Path
import json,hashlib,re,subprocess
R=Path.cwd();Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce';O=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rename(s):return s.replace('BGBlockUpper','BGSplitUpper').replace('_bgu_','_sbu_').replace('BGUInjectedAllocationFailure','SBUInjectedAllocationFailure')
c=(N/'split-upper.jl').read_text();t=(N/'split-upper-tests.jl').read_text();o=(N/'split-oracles.jl').read_text();checks={}
removed=(Q/'original-reserve-renamed.jl.txt').read_text();new=(Q/'replacement-reserve.jl.txt').read_text()
checks['whole_candidate_inverse']=c.count(new)==1 and c.replace(new,removed)==rename((O/'block-upper.jl').read_text())
oldtests=rename((O/'block-upper-tests.jl').read_text()).replace('function _sbu_structural_tests()','function _sbu_inherited_structural_tests()').replace('Include block-upper.jl and block-oracles.jl','Include split-upper.jl and split-oracles.jl')
checks['inherited_tests_exact_prefix']=t.startswith(oldtests)
baseo=o.split('\n# Test-only free extent fixture,')[0]
a=baseo.index('    @assert sum(Int(U.capacity[b])');z=baseo.index('    livehandles=',a)
checks['oracle_inverse_except_partition_clear']=baseo[:a]+baseo[z:]==rename((O/'block-oracles.jl').read_text())
checks['target_before_search']=new.index('target=_sbu_target(required)')<new.index('b=_sbu_free_block(U,target)')
checks['reserve_before_unlink']=new.index('_sbu_reserve_descriptors!')<new.index('_sbu_take!(U,b)')
checks['checked_before_unlink']=all(new.index(x)<new.index('_sbu_take!(U,b)') for x in ['_sbu_handle(suffix,32,limit)','_sbu_limit(nextstart,limit)','split U partition'])
checks['exact_return_type']='function _sbu_reserve_block!(U::BGSplitUpper,required::Int,allocate,limit::Integer)::Int' in new
checks['single_suffix_no_coeff_copy']=all(x not in new for x in ['copyto!','_sbu_clear!','_sbu_write!','Vector{','zeros(']) and 'suffix=Base.Checked.checked_add(U.used,1)' in new
checks['free_prefix_and_suffix']='_sbu_free!(U,b);_sbu_free!(U,suffix)' in new
checks['tests_first_preserved']=all(sha(R/n)==want for n,want in {str(Q.relative_to(R)/'tests.before-author-budget.jl.txt'):json.loads((Q/'tests-first.json').read_text())['sha256'][str(N.relative_to(R)/'split-upper-tests.jl')],str(Q.relative_to(R)/'oracles.before-author-counters.jl.txt'):json.loads((Q/'tests-first.json').read_text())['sha256'][str(N.relative_to(R)/'split-oracles.jl')]}.items())
names=re.findall(r'@testset "([^"]+)"',t)
checks['testsets_14_inherited_11_new']=len(names)==25 and len(re.findall(r'@testset "([^"]+)"',oldtests))==14
checks['failure_coverage']=all(x in t for x in ['count[]==7','count[]==13','for stop in 2:8','U.rows[1]!==oldrow','_sbu_test_handles(U)==handles','@test_throws OverflowError'])
checks['exact_monotone_budget']=all(x in t for x in ['totals[:payload]==5048','totals[:requests]==52','totals[:descriptor_copied]==224','totals[:relocated]==31','totals[:cleared]==31'])
checks['counter_all_boundaries']='observe();totals[:requests]+=1' in o and 'typemax(Int32));observe()' in o and 'isbitstype(T) ? sizeof(T) : sizeof(Ptr{Cvoid})' in o
checks['geometry_model_pass']=json.loads((Q/'geometry-model.json').read_text())['all_passed'] is True
checks['no_adapter_or_driver']=sorted(p.name for p in N.iterdir())==['source-bindings.json','split-oracles.jl','split-upper-tests.jl','split-upper.jl']
checks['tracked_unchanged']=not subprocess.check_output(['git','diff','--name-only'],text=True).strip() and not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip()
files=[R/'AGENTS.md',R/'docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md',R/'docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md',*[O/n for n in ['block-upper.jl','block-oracles.jl','block-upper-tests.jl']],*sorted(N.iterdir()),*[Q/n for n in ['REPORT.md','MEMORY-WORK.md','host.json','tests-first.json','author-counter-fix.json','author-budget-fix.json','oracles.before-author-counters.jl.txt','tests.before-author-budget.jl.txt','prepare.py','original-reserve-renamed.jl.txt','replacement-reserve.jl.txt','geometry-model.py','geometry-model.json','source-check.py']]]
result={'scope':'Task1 source checks, NOT Julia parse/runtime tests','all_passed':all(checks.values()),'checks':checks,'testsets_unexecuted':names,'sha256':{str(p.relative_to(R)):sha(p) for p in files}}
with (Q/'source-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':checks,'hashes':len(files)}))
if not result['all_passed']:raise SystemExit(1)
