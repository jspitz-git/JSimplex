using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const INPUT=joinpath(ROOT,"diagnostics/simplex-core-architecture/results/S6-Q/trace-1-report.toml")
const TRACE=TOML.parsefile(INPUT)
const BEFORE=TRACE["events"][10]
const AFTER=TRACE["events"][11]
const RECORDS=Dict{String,Any}[]
rat(s)=begin
    fields=split(s,"//")
    parse(BigInt,fields[1])//(length(fields)==1 ? BigInt(1) : parse(BigInt,fields[2]))
end
str(x::Real)=isfinite(x) ? string(Rational{BigInt}(x)) : repr(x)
strings(x)=str.(vec(x))
function readfloat(s)
    q=rat(s);x=Float64(q)
    Rational{BigInt}(x)==q || error("input conversion is not exact")
    x
end
B=SparseMatrixCSC(2,2,copy(BEFORE["matrix_colptr"]),copy(BEFORE["matrix_rowval"]),readfloat.(BEFORE["matrix_nzval"]))
@assert BEFORE["basis_indices"]==[1,2] && BEFORE["basis_states"]==["BASIC","BASIC","AT_LOWER","AT_UPPER"]
@assert isempty(BEFORE["updates"]) && isempty(AFTER["updates"])
@assert all(==(1//1),rat.(BEFORE["column_scaling"])) # Fixed unit-column-scaling replay only.
# With no structural nonbasic variables, each nonbasic -I slack contributes
# its selected original bound to recompute!'s primal RHS. Do not use scratch RHS.
rhs=[readfloat(BEFORE["lower"][3]["exact"]),readfloat(BEFORE["upper"][4]["exact"])]
dual_rhs=readfloat.(BEFORE["costs"][BEFORE["basis_indices"]])
@assert rhs==[-2.0^20,2.0^20] && dual_rhs==[0.0,-1.0]
opts=SolverOptions(Float64)
options=Dict(string(k)=>repr(getfield(opts,k)) for k in fieldnames(typeof(opts)))
@assert options==TRACE["options"]==BEFORE["options"]
@assert TRACE["policy"]["hypersparse"]=="false" && TRACE["policy"]["solve_refinement"]=="false"
@assert string(VERSION)==TRACE["julia_version"] && string(Sys.ARCH)==TRACE["arch"]
@assert Threads.nthreads()==BLAS.get_num_threads()==TRACE["julia_threads"]==TRACE["blas_threads"]==1
const INITIAL_PRECISION=precision(BigFloat)
const INITIAL_ROUNDING=rounding(BigFloat)
@assert INITIAL_PRECISION==256 && INITIAL_ROUNDING==RoundNearest
@assert !ispath(only(ARGS))
const INPUT_HASH=bytes2hex(sha256(read(INPUT)))
const ORIGINAL_B=copy(B)
const ORIGINAL_RHS=copy(rhs)
const ORIGINAL_DUAL_RHS=copy(dual_rhs)
function run_case(mode)
    initial=nothing
    factor=if mode=="fresh"
        JSimplex._basis_factorization(B,opts)
    else
        # Production initially factors the -I slack basis. Copy marks it shared,
        # gives the candidate no spare; refactor then performs a fresh lu(B).
        initial=JSimplex._basis_factorization(spdiagm(0=>fill(-1.0,2)),opts)
        candidate=JSimplex.copy_basis_factorization(initial)
        @assert candidate.base.shared && isnothing(candidate.base.spare)
        JSimplex.refactorize!(candidate,B)
        candidate
    end
    @assert factor isa JSimplex.PFIFactorization{Float64,JSimplex.UMFPACKBackend}
    @assert isempty(factor.updates)
    f=factor.base.factorization
    control_before=copy(getfield(f,:control))
    x=zeros(2);dual=zeros(2)
    JSimplex._ordinary_forward_solve!(x,factor,rhs)
    JSimplex.transpose_solve!(dual,factor,dual_rhs)
    # Supported SparseArrays properties. Extract only AFTER both recorded solves.
    # No runtime pointers are serialized; these arrays own their storage.
    L,U,p,q,Rs=getproperty(f,Symbol(":"))
    rec=Dict{String,Any}("mode"=>mode,"ftran_calls"=>1,"btran_calls"=>1,
        "initial_factorizations"=>1,"explicit_refactors"=>mode=="fresh" ? 0 : 1,
        "copy_calls"=>mode=="fresh" ? 0 : 1,"factor_type"=>string(typeof(factor)),
        "primal"=>strings(x),"dual"=>strings(dual),"matrix"=>strings(Matrix(B)),
        "rhs"=>strings(rhs),"dual_rhs"=>strings(dual_rhs),
        "L"=>strings(Matrix(L)),"U"=>strings(Matrix(U)),"p"=>p,"q"=>q,"Rs"=>strings(Rs),
        "control_before"=>strings(control_before),"control_after"=>strings(getfield(f,:control)),
        "umfpack_refinement_steps"=>getfield(f,:control)[SparseArrays.UMFPACK.JL_UMFPACK_IRSTEP],
        "umfpack_scaling_mode"=>getfield(f,:control)[SparseArrays.UMFPACK.JL_UMFPACK_SCALE],
        "update_count"=>length(factor.updates),"source_unchanged"=>B==ORIGINAL_B && rhs==ORIGINAL_RHS && dual_rhs==ORIGINAL_DUAL_RHS,
        "primal_matches_trace"=>strings(x)==AFTER["scratch_row_solution"],
        "dual_matches_recorded_scratch"=>strings(dual)==AFTER["scratch_rho"],
        "initial_copy_base_preserved"=>isnothing(initial) || (initial.base.factorization !== f && initial.base.dimension==2 && isempty(initial.updates)))
    push!(RECORDS,rec)
    @testset "$mode component endpoint" begin
        @test rec["primal_matches_trace"]
        @test rec["dual_matches_recorded_scratch"]
        @test rec["source_unchanged"]
        @test rec["control_before"]==rec["control_after"]
        @test rec["initial_copy_base_preserved"]
        @test rec["update_count"]==0
    end
end
try
    @testset "Bounded handoff factor replay" begin
        for mode in ("fresh","copy_refactor")
            run_case(mode)
        end
    end
finally
    open(only(ARGS),"w") do io
        TOML.print(io,Dict("source"=>pathof(JSimplex),"input_sha256"=>INPUT_HASH,
            "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),
            "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
            "options"=>options,"source_policy"=>TRACE["policy"],
            "global_precision"=>INITIAL_PRECISION,"global_rounding"=>string(INITIAL_ROUNDING),
            "globals_preserved"=>precision(BigFloat)==INITIAL_PRECISION && rounding(BigFloat)==INITIAL_ROUNDING,
            "records"=>RECORDS,
            "scope"=>"Two component lifecycle cases; four basis solves total, no workspace or full solver. Factors newly constructed, not captured opaque runtime factors. Scratch dual match is not a certificate."))
    end
end
