# Localize phase-boundary residual rejection and test bounded native correction.
# Reuse only the replay helpers; do not run its test or replace export methods.
helper_path=joinpath(@__DIR__,"replay_phase_transfer.jl")
helper_source=read(helper_path,String)
marker="\nrecords=Dict{String,Any}[]"
@assert count(marker,helper_source)==1
Base.include_string(Main,first(split(helper_source,marker)),helper_path)
using SparseArrays
function native_quality(ws,x,rhs;transposed=false)
    B=JSimplex._basis_matrix!(ws)
    scratch=JSimplex.SolveQualityScratch(Float64,length(rhs))
    quality=JSimplex._compensated_solve_quality!(scratch,B,x,rhs,
        ws.progress.numerical_policy,transposed)
    @assert !isnothing(quality)
    return quality,scratch
end
function residual_report(ws,x,rhs;transposed=false)
    quality,scratch=native_quality(ws,x,rhs;transposed)
    ratios=[iszero(s) ? 0.0 : abs(r)/s for (r,s) in zip(scratch.residual,scratch.work_scale)]
    indices=sort!(unique(vcat(sortperm(ratios;rev=true)[1:10],
        sortperm(abs.(scratch.residual);rev=true)[1:10])))
    B=JSimplex._basis_matrix!(ws)
    rows=Dict{String,Any}[]
    for i in indices
        sources,coefficients=findnz(transposed ? B[:,i] : B[i,:])
        terms=[Dict("source"=>j,"coefficient"=>a,"value"=>x[j],"product"=>a*x[j])
            for (j,a) in zip(sources,coefficients) if !iszero(a*x[j])]
        sort!(terms;by=t->abs(t["product"]),rev=true)
        push!(rows,Dict("equation"=>i,"rhs"=>rhs[i],"residual"=>scratch.residual[i],
            "scale"=>scratch.work_scale[i],"ratio"=>ratios[i],
            "nonzero_products"=>length(terms),"largest_terms"=>first(terms,min(10,length(terms)))))
    end
    return Dict("absolute_error"=>quality.absolute_error,"relative_error"=>quality.relative_error,
        "reliable"=>quality.reliable,"finite"=>quality.finite,
        "rows_above_tolerance"=>count(>(ws.progress.numerical_policy.solve_tolerance),ratios),
        "bad_equations"=>findall(>(ws.progress.numerical_policy.solve_tolerance),ratios),
        "bad_homogeneous_equations"=>count(i->iszero(rhs[i]) && ratios[i]>ws.progress.numerical_policy.solve_tolerance,eachindex(rhs)),
        "largest_bad_absolute_residual"=>maximum((abs(scratch.residual[i]) for i in eachindex(ratios)
            if ratios[i]>ws.progress.numerical_policy.solve_tolerance);init=0.0),"selected_rows"=>rows)
end
function corrected_vector(ws,x,rhs;transposed=false)
    quality,scratch=native_quality(ws,x,rhs;transposed)
    correction=similar(x)
    if transposed
        JSimplex.transpose_solve!(correction,ws.factorization,scratch.residual)
    else
        JSimplex._ordinary_forward_solve!(correction,ws.factorization,scratch.residual)
    end
    @assert all(isfinite,correction)
    return x+correction,maximum(abs,correction;init=0.0)
end
function install_basic!(ws,basic)
    ws.primal[ws.basis.basic_indices].=basic
    ws.scratch.row_solution.=basic
end
function install_dual!(ws,dual)
    ws.scratch.rho.=dual
    JSimplex._recompute_reduced_costs!(ws.reduced_costs,ws,dual)
end
function inspect_workspace(ws,label)
    result=point_report(ws,label)
    result["primal_residual"]=residual_report(ws,ws.primal[ws.basis.basic_indices],JSimplex._basis_primal_rhs(ws))
    result["dual_residual"]=residual_report(ws,ws.scratch.rho,ws.costs[ws.basis.basic_indices];transposed=true)
    return result
end
records=Dict{String,Any}[]
metadata=Dict{String,Any}("scope"=>"Local native residual diagnosis; no production change or outer-driver continuation",
    "before_sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),
    "helper_sha256"=>bytes2hex(sha256(helper_source)),"records"=>records)
@testset "Phase transfer native residual diagnosis" begin
    baseline,mapped,candidate=mapped_workspace(load_transfer();carry=true)
    @test JSimplex._legacy_primal_point_certified(baseline)
    @test !JSimplex._recomputed_basis_reliable(baseline)
    metadata["solve_tolerance"]=baseline.progress.numerical_policy.solve_tolerance
    metadata["primal_tolerance"]=baseline.options.primal_tolerance
    metadata["iteration"]=baseline.iterations
    push!(records,inspect_workspace(baseline,"mapped reconstruction"))
    for (label,primal,dual) in (("primal correction",true,false),("dual correction",false,true),
                              ("both corrections",true,true))
        ws,_,_=mapped_workspace(load_transfer();carry=true)
        nonbasic=ws.basis.states.!=JSimplex.BASIC
        saved=copy(ws.primal[nonbasic])
        basic_correction=dual_correction=0.0
        if primal
            basic,basic_correction=corrected_vector(ws,ws.primal[ws.basis.basic_indices],JSimplex._basis_primal_rhs(ws))
            install_basic!(ws,basic)
        end
        if dual
            prices,dual_correction=corrected_vector(ws,copy(ws.scratch.rho),ws.costs[ws.basis.basic_indices];transposed=true)
            install_dual!(ws,prices)
        end
        @test isequal(saved,ws.primal[nonbasic])
        row=inspect_workspace(ws,label)
        row["maximum_primal_correction"]=basic_correction
        row["maximum_dual_correction"]=dual_correction
        push!(records,row)
    end
    ws,_,_=mapped_workspace(load_transfer();carry=true)
    cleanup_details=Dict{String,Any}[]
    for transposed in (false,true)
        rhs=transposed ? ws.costs[ws.basis.basic_indices] : JSimplex._basis_primal_rhs(ws)
        original=transposed ? copy(ws.scratch.rho) : ws.primal[ws.basis.basic_indices]
        trial,magnitude=corrected_vector(ws,original,rhs;transposed)
        before_cleanup=copy(trial)
        B=JSimplex._basis_matrix!(ws)
        cutoff=ws.progress.numerical_policy.solve_tolerance*magnitude
        changed=JSimplex._clean_homogeneous_terms!(trial,B,rhs,transposed,zeros(Int,length(rhs)),
            ws.progress.numerical_policy;cutoff)
        detail=residual_report(ws,trial,rhs;transposed)
        detail["transposed"]=transposed
        detail["cutoff"]=cutoff
        detail["changed"]=changed
        detail["cleared_indices"]=findall(before_cleanup.!=trial)
        protected=Dict{String,Any}[]
        for j in detail["cleared_indices"]
            equations,coefficients=findnz(transposed ? B[j,:] : B[:,j])
            affected=[i for (i,a) in zip(equations,coefficients) if !iszero(a) && !iszero(rhs[i])]
            isempty(affected) || push!(protected,Dict("index"=>j,"before"=>before_cleanup[j],
                "after"=>trial[j],"inhomogeneous_equations"=>affected))
        end
        detail["cleared_with_inhomogeneous_support"]=protected
        push!(cleanup_details,detail)
        transposed ? install_dual!(ws,trial) : install_basic!(ws,trial)
    end
    row=inspect_workspace(ws,"unaccepted cleanup proposal")
    row["cleanup_details"]=cleanup_details
    push!(records,row)
    ws,_,_=mapped_workspace(load_transfer();carry=true)
    saved=copy(ws.primal)
    saved_dual=copy(ws.scratch.rho);saved_prices=copy(ws.reduced_costs)
    accepted=JSimplex._try_native_cleanup_recompute!(ws,()->false)
    row=inspect_workspace(ws,"existing native cleanup")
    row["cleanup_returned_success"]=accepted
    if !accepted
        @test isequal(ws.primal,saved)
        @test isequal(ws.scratch.rho,saved_dual)
        @test isequal(ws.reduced_costs,saved_prices)
    end
    row["maximum_primal_change"]=maximum(abs.(ws.primal.-saved);init=0.0)
    @test isequal(saved[ws.basis.states.!=JSimplex.BASIC],ws.primal[ws.basis.states.!=JSimplex.BASIC])
    push!(records,row)
    serialize(output*"-cleanup.bin",ws)
end
h=SHA.SHA2_256_CTX()
root=dirname(dirname(pathof(JSimplex)))
files=["Project.toml"]
for (dir,_,names) in walkdir(joinpath(root,"src")), file in names
    endswith(file,".jl") && push!(files,relpath(joinpath(dir,file),root))
end
for file in sort(files)
    SHA.update!(h,codeunits(file*"\0"))
    SHA.update!(h,read(joinpath(root,file)))
end
metadata["production_sha256"]=bytes2hex(SHA.digest!(h))
metadata["julia"]=string(VERSION)
metadata["julia_threads"]=Threads.nthreads()
metadata["blas_threads"]=BLAS.get_num_threads()
metadata["architecture"]=string(Sys.ARCH)
metadata["scalar_type"]=string(eltype(load_transfer().phase.primal))
open(output*".toml","w") do io
    TOML.print(io,metadata)
end
