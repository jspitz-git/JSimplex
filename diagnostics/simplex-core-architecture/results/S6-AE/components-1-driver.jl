using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const INPUT=joinpath(ROOT,"diagnostics/simplex-core-architecture/results/S6-AE/inputs.toml")
const DATA=TOML.parsefile(INPUT)
const RECORDS=Dict{String,Any}[]
rat(s)=begin p=split(s,"/");parse(BigInt,p[1])//(length(p)==1 ? big(1) : parse(BigInt,p[2])) end
readfloat(s)=begin q=rat(s);x=Float64(q);@assert Rational{BigInt}(x)==q;x end
exact(x)=string(Rational{BigInt}(x))
exact_values(x)=exact.(vec(x))
bits(x)=string.(reinterpret(UInt64,vec(x));base=16,pad=16)
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
B=sparse(reduce(vcat,permutedims.(map(row->readfloat.(row),DATA["B"]))))
unit=readfloat.(DATA["unit_rhs"]);dup=readfloat.(DATA["duplicate_rhs"])
crhs=readfloat.(DATA["correction_rhs"]);declared=readfloat.(DATA["declared_rho"])
expected_rho=readfloat.(DATA["exact_rho"]);expected_dir=readfloat.(DATA["direction"])
expected_corr=readfloat.(DATA["correction"])
const BASELINE=(copy(B.colptr),copy(B.rowval),copy(B.nzval),copy(unit),copy(dup),copy(crhs),copy(declared))
const GLOBALS=(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
@assert GLOBALS==(256,RoundNearest,RoundNearest,false)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
@assert !ispath(only(ARGS))
function prepared_count(f)
    f isa JS.AbstractTriangularBasisFactorization || return 0
    c=f.row_cache.prepared
    isnothing(c) ? 0 : count(e->!isnothing(e.destination),c.entries)
end
function run_case(manager,mode)
    options=SolverOptions(Float64;algorithm=:dual,simplex_strategy=:legacy,basis_update=manager,pricing=:dantzig,verbose=false)
    policy=JS.NumericalPolicy(Float64)
    @assert !policy.hypersparse && !policy.pivot_validation && !policy.solve_refinement && !policy.recovery
    @assert policy.max_refinements==3 && policy.max_pivot_candidates==8 && policy.max_recovery_rounds==2
    rec=Dict{String,Any}("manager"=>string(manager),"mode"=>mode,"options"=>fields(options),"policy"=>fields(policy),
        "initial_factorizations"=>0,"refactors"=>0,"unit_btran"=>0,"prepared_ftran"=>0,"correction_btran"=>0,"quality_entries"=>0,"explicit_invalidations"=>0,"error"=>"none")
    push!(RECORDS,rec)
    try
        rec["initial_factorizations"]+=1
        factor=JS._basis_factorization(mode=="fresh" ? B : spdiagm(0=>fill(-1.0,4)),options)
        if mode=="refactor"
            rec["refactors"]+=1;JS.refactorize!(factor,B)
        end
        rec["factor_type"]=string(typeof(factor));rec["backend_type"]=string(typeof(factor.base))
        rec["updates_before"]=length(factor.updates);rec["prepared_before"]=prepared_count(factor)
        rho=zeros(4);direction=zeros(4);correction=zeros(4)
        unit_arg=JS._unit_transpose_rhs(factor,unit,2)
        rec["unit_rhs_type"]=string(typeof(unit_arg))
        rec["unit_btran"]+=1;JS.transpose_solve!(rho,factor,unit_arg)
        rec["rho"]=exact_values(rho);rec["rho_bits"]=bits(rho)
        rec["prepared_ftran"]+=1;JS.forward_solve!(direction,factor,dup)
        rec["direction"]=exact_values(direction);rec["direction_bits"]=bits(direction)
        rec["prepared_after_ftran"]=prepared_count(factor)
        rec["correction_btran"]+=1;JS.transpose_solve!(correction,factor,crhs)
        rec["correction"]=exact_values(correction);rec["correction_bits"]=bits(correction)
        rec["prepared_after_correction"]=prepared_count(factor)
        rec["explicit_invalidations"]+=1;JS._invalidate_prepared_destination!(factor,direction)
        rec["prepared_after_invalidation"]=prepared_count(factor)
        rec["updates_after"]=length(factor.updates)
        scratch=JS.SolveQualityScratch(Float64,4)
        rec["quality_entries"]+=1
        quality=JS._compensated_solve_quality!(scratch,B,declared,unit,policy,true)
        rec["quality_isnothing"]=isnothing(quality)
        if !isnothing(quality)
            rec["quality_finite"]=quality.finite;rec["quality_reliable"]=quality.reliable
            rec["quality_absolute"]=exact(quality.absolute_error);rec["quality_relative"]=exact(quality.relative_error)
            rec["quality_residual"]=exact_values(scratch.residual);rec["quality_residual_bits"]=bits(scratch.residual)
        end
        rec["input_preserved"]=(B.colptr,B.rowval,B.nzval,unit,dup,crhs,declared)==BASELINE
        @testset "$manager $mode" begin
            @test rho==expected_rho
            @test direction==expected_dir
            @test correction==expected_corr
            @test !isnothing(quality) && quality.finite
            @test !isnothing(quality) && scratch.residual==crhs
            @test rec["input_preserved"]
            @test rec["updates_before"]==rec["updates_after"]==0
            @test rec["prepared_before"]==rec["prepared_after_invalidation"]==0
            @test rec["prepared_after_ftran"]==rec["prepared_after_correction"]==(manager==:pfi ? 0 : 1)
        end
    catch exception
        rec["error"]=sprint(showerror,exception);rethrow()
    end
end
try
    @testset "New dyadic dual factor components" begin
        for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),mode in ("fresh","refactor")
            run_case(manager,mode)
        end
        @test (precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())==GLOBALS
    end
finally
    open(only(ARGS),"w") do io
        TOML.print(io,Dict("source"=>pathof(JS),"input_sha256"=>bytes2hex(sha256(read(INPUT))),"input"=>DATA,
            "matrix_colptr"=>B.colptr,"matrix_rowval"=>B.rowval,"matrix_values"=>exact_values(B.nzval),"matrix_bits"=>bits(B.nzval),
            "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
            "global_precision"=>GLOBALS[1],"global_rounding"=>string(GLOBALS[2]),
            "globals_preserved"=>(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())==GLOBALS,
            "records"=>RECORDS,"scope"=>"Eight new component cases only; no workspace, public solver, adapter, factor copy/update, observer or certificate. Entry counts include attempts; no internal arithmetic/hidden trajectory claim."))
    end
end
