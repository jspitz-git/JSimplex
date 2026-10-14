from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/PRESOLVE-ZERO-COEFFICIENT')
def write(n,s):
 with (D/n).open('x') as f:f.write(s)
write('green.jl','''using JSimplex,SparseArrays,Test,TOML,Statistics
const D=@__DIR__;const ROOT=normpath(joinpath(D,"../../../.."));const OUT=ARGS[1]
const OVERLAY=joinpath(ROOT,".superpowers/presolve-zero-coefficient/candidate")
realpath(pathof(JSimplex))==realpath(joinpath(OVERLAY,"src/JSimplex.jl")) || error("wrong source")
include(joinpath(D,"test-support.jl"))
Base.include(JSimplex,joinpath(D,"reference-functions.jl"))
Base.include(JSimplex,joinpath(D,"probe-original.jl"))
Base.include(JSimplex,joinpath(D,"probe-candidate.jl"))
function main()
 suite=@testset "Zero coefficient candidate regression" begin
  include(joinpath(D,"new-tests.jl"))
  for name in ("aggregation_zero_old_matrix_allocation_tests.jl","aggregation_zero_matrix_update_allocation_tests.jl","aggregation_defaults_allocation_tests.jl","aggregation_cancelled_matrix_allocation_tests.jl","aggregation_equal_matrix_denominator_allocation_tests.jl")
   include(joinpath(ROOT,"test",name))
  end
  p=zero_fixture(4)
  JSimplex.zero_conversion_count[]=0
  a=JSimplex.zero_conversion_probe(p);old_count=JSimplex.zero_conversion_count[]
  JSimplex.zero_conversion_count[]=0
  b=JSimplex.zero_candidate_probe(p);new_count=JSimplex.zero_conversion_count[]
  @test identical(a,b)
  @test old_count==4
  @test new_count==0
 end
 save_record(OUT,"tests.toml",Dict("passed"=>true,"summary"=>sprint(show,suite)))
 cases=[("positive",zero_fixture(128)),("negative_multiplier",zero_fixture(128;multiplier=-2.0)),("negative_term",zero_fixture(128;term=-3.0)),("both_negative",zero_fixture(128;multiplier=-2.0,term=-3.0)),("small",zero_fixture(1)),("stored_negative_zero",zero_fixture(128;old=-0.0,explicit=true)),("nonzero_control",zero_fixture(128;old=2.0)),("zero_multiplier_control",zero_fixture(128;multiplier=0.0))]
 dense=LinearProblem(sparse([2.0 3.0 1.0 2.0;4.0 1.0 2.0 3.0;2.0 2.0 3.0 1.0;6.0 1.0 1.0 4.0]),[0.0,2.0,1.0,1.0];row_lower=[4.0,nothing,nothing,nothing],row_upper=[4.0,20.0,20.0,20.0],column_lower=fill(nothing,4),column_upper=fill(nothing,4))
 push!(cases,("dense_control",dense));summaries=Dict{String,Any}()
 for (name,p) in cases
  records=paired_case(OUT,name,p,JSimplex.zero_reference_aggregate,JSimplex.aggregate_sparse_equalities)
  summaries[name]=summarize(records)
 end
 for name in ("afiro","adlittle","kb2")
  p=read_mps(joinpath(ROOT,"test/fixtures/solver/netlib",name*".mps");native_reader=true)
  records=paired_case(OUT,"full_"*name,p,JSimplex.zero_reference_presolve,JSimplex.presolve_problem)
  summaries["full_"*name]=summarize(records)
 end
 save_record(OUT,"raw.toml",Dict("all_passed"=>true,"loaded_path"=>pathof(JSimplex),"summaries"=>summaries,"cost_accepted"=>all(x["bytes_nonincrease"] && x["events_nonincrease"] for x in values(summaries)),"scope"=>"Correctness pass is separate from cost acceptance; no numerical retry."))
end
function summarize(records)
 refs=[r["metrics"]["reference"] for r in records];cands=[r["metrics"]["candidate"] for r in records]
 Dict("reference_bytes"=>median([r["bytes"] for r in refs]),"candidate_bytes"=>median([r["bytes"] for r in cands]),"reference_events"=>median([r["events"] for r in refs]),"candidate_events"=>median([r["events"] for r in cands]),"time_ratios"=>[c["seconds"]/r["seconds"] for (r,c) in zip(refs,cands)],"bytes_nonincrease"=>median([r["bytes"] for r in cands])<=median([r["bytes"] for r in refs]),"events_nonincrease"=>median([r["events"] for r in cands])<=median([r["events"] for r in refs]))
end
main()
''')
write('green-scope.md','''# Missing-zero Float64 candidate qualification

The independently accepted expected RED ran once: one exact missing-zero conversion,
correct -6 coefficient/upper12 and unchanged source, expected exit1 preserved.
Now qualify the separate ordinary candidate overlay. Actual src/test/environment/master
remain unchanged. Candidate changes only two fragments in presolve_aggregation.jl:
Float64 dictionary get with nothing sentinel, one original CSC read on miss, scalar
iszero(stored)&&!iszero(multiplier) skips conversion, and nothing joins old exact-zero
negation. All other types keep original get-do conversion. Dictionary hits always
use their staged Rational value; zero multipliers still require actual exact value.
Product calculation/representability/staging/fill caps/order/postsolve unchanged.

No BigInt mutation, new scratch/cache/vector/matrix/scan/solve. Frequency: each matrix
update attempted by sparse aggregation; existing O(m+nnz) and staged-storage costs
remain. Add scalar check on missing Float64 coefficients, remove an exact conversion
on eligible zero. Check union/sentinel overhead in sparse+dense/nonzero controls.

ONE green process, guard114/inclusive120 seconds, existing resource constraints,
no LP solve and no large external model. Candidate is actual loaded module source.
Reference aggregate/dispatcher/presolve are exact source copies with only scoped
function/call renames, no method overwrite. Both sides share unchanged helpers/types.
New 88 correctness/ownership assertions plus five exact existing focused files cover
four scalar types, tiny values/reduced ambient precision, staged hits/cancellation,
signed zero/zero multiplier/nonzero controls and rejection. Separate forwarded-work
probe: reference4 exact zero conversions, candidate0, full results equal.

Nine synthetic aggregation cases (four signed sparse targets, small target, explicit
negative-zero target, nonzero and zero-multiplier controls, fully populated4x4 control)
plus three Netlib complete presolves afiro/adlittle/kb2. Each3warm+8measured pairs,
alternating order, explicit GC outside each dispatch. Entire aggregate/full-presolve
call including all internal scratch/setup timed; input construction/read and full
result/input-owner comparisons outside. Record every time/byte/event/GC/compile field.
Measured compile/recompile must be zero; full results and unchanged inputs required.
For EACH case median bytes AND median events must not increase; no noise waiver.
At least signed sparse targets must reduce both before performance acceptance.
Timing is descriptive paired distribution; no speedup from counts alone. Do not
promote if cost gate fails. Large-model qualification is separate and conditional
on this stage; no hidden rerun, full-suite success or general precision claim.

Reviewer must bind green-config required+config, manifest and candidate inverse,
reference inverse and exact overlay/source relationship. No Julia in review.
''')
write('freeze-green.py','# New one-shot green preparation; original freeze executions preserved.\n'+(D/'freeze-stage.py').read_text())
