"""One-use offline permanent-test preparation; never invokes Julia."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S4-AC';A=D.parent/'S4-AB'
def require(x,m):
 if not x:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,b):
 with p.open('xb') as f:f.write(b)
source=R/'src/markowitz_factorization.jl';test=R/'test/markowitz_workspace_reuse_allocation_tests.jl'
original=source.read_bytes();candidate=(A/'candidate-source.jl').read_bytes();prefix=test.read_bytes();suffix=(D/'test-append.jl').read_bytes()
expected=original.replace(b'    nonzeros = sum(length, rows)\n',b'    nonzeros = 0\n',1).replace(b'        length(rows[row]) == 1 && push!(singleton_rows,row)\n',b'        row_count = length(rows[row])\n        nonzeros += row_count\n        row_count == 1 && push!(singleton_rows,row)\n',1)
require(candidate==expected,'candidate differs from qualified source')
write(D/'original-test.jl',prefix);write(D/'candidate-test.jl',prefix+suffix);write(D/'candidate-source.jl',candidate)
checks={
 'exact_AB_source_candidate':candidate==(A/'candidate-source.jl').read_bytes(),
 'exact_two_part_source_delta':candidate==expected and candidate!=original,
 'whole_test_prefix_unchanged':(D/'candidate-test.jl').read_bytes()==prefix+suffix,
 'isolated_test_module':suffix.startswith(b'\nmodule MarkowitzInitialRowCountTests\n') and suffix.endswith(b'end # module MarkowitzInitialRowCountTests\n'),
 'six_assertions_times_four_cases':suffix.count(b'@test ')==6 and b'for n in (3,8), capacity in (n,64)' in suffix,
 'real_constructor_and_reset':suffix.count(b'JSimplex._construct_markowitz(')==1 and suffix.count(b'JSimplex._reset_markowitz_workspace!(')==1,
 'row_column_ownership_and_clear':all(x in suffix for x in (b'row_owners[i]',b'column_owners[i]',b'isempty(row.data)',b'isempty(column.data)')),
 'expected_failure_and_work':b'failure isa SingularException && failure.info == 1' in suffix and b'vcat(ones(Int,n),zeros(Int,capacity-n))' in suffix,
 'no_new_test_solves_or_timing':not any(x in suffix for x in (b'forward_solve',b'transpose_solve',b'@timed',b'@allocated')),
 'actual_source_test_unchanged':source.read_bytes()==original and test.read_bytes()==prefix,
 'production_test_CI_master_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),
 'accepted_AB_qualification':read(A/'result-review.json')['accepted'] is True and read(A/'closure.json')['all_passed'] is True,
}
paths=[source,test,R/'test/markowitz_tests.jl',R/'test/runtime_markowitz_cache_tests.jl',R/'test/runtests.jl',R/'Project.toml',R/'AGENTS.md',R/'docs/superpowers/specs/2026-10-11-simplex-core-architecture-design.md',R/'docs/superpowers/plans/2026-10-13-markowitz-row-count-integration.md',*[D/n for n in ('prepare.py','test-append.jl','candidate-test.jl','original-test.jl','candidate-source.jl','host.json','continuation-map.json','STATUS.md.before-S4-AC','roadmap.md.before-S4-AC')],*[A/n for n in ('candidate-source.jl','driver.jl','source-checks.json','launch-pins.json','result-review.md','result-review.json','audit.json','postcheck.json','closure.json','publication.json')]]
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths},original_test_bytes=len(prefix),append_lines=len(suffix.splitlines()),prospective_tests=24,prospective_expected_RED=dict(passed=20,failed=4,errors=0),scope='Offline text/source checks only. No Julia parser/runtime/TDD result. Original S4-AB and all previous evidence frozen.')
write(D/'preparation.json',(json.dumps(result,indent=2)+'\n').encode());require(result['all_passed'],'preparation checks failed');print(json.dumps({k:result[k] for k in ('all_passed','original_test_bytes','append_lines','prospective_tests')}))
