# Experimental local row reconstruction; never installed into production code.
residual_path=joinpath(@__DIR__,"probe_phase_transfer_residuals.jl")
residual_source=read(residual_path,String)
marker="\nrecords=Dict{String,Any}[]"
@assert count(marker,residual_source)==1
Base.include_string(Main,first(split(residual_source,marker)),residual_path)

# Recompute a coordinate directly instead of adding a correction that cancels
# its old value. All products and sums remain in the problem's Float64 type.
function row_coordinate(coefficients,values,rhs,chosen)
    total=rhs
    compensation=0.0
    for k in eachindex(values)
        k==chosen && continue
        product=-coefficients[k]*values[k]
        product_error=fma(-coefficients[k],values[k],-product)
        next=total+product
        part=next-total
        compensation+=(total-(next-part))+(product-part)+product_error
        total=next
    end
    return (total+compensation)/coefficients[chosen]
end
function local_quality(B,x,rhs,policy)
    scratch=JSimplex.SolveQualityScratch(Float64,length(rhs))
    quality=JSimplex._compensated_solve_quality!(scratch,B,x,rhs,policy,false)
    @assert !isnothing(quality)
    return quality,scratch
end
function local_rows!(B,x,rhs,policy,cutoff;limit=8)
    trace=Dict{String,Any}[]
    for sweep in 1:limit
        quality,scratch=local_quality(B,x,rhs,policy)
        quality.reliable && break
        bad=findall(i->abs(scratch.residual[i])>policy.solve_tolerance*scratch.work_scale[i],eachindex(rhs))
        changes=Dict{String,Any}[]
        for i in bad
            columns,coefficients=findnz(B[i,:])
            isempty(columns) && continue
            values=x[columns]
            products=abs.(coefficients.*values)
            chosen=argmax(products)
            iszero(products[chosen]) && (chosen=argmax(abs.(coefficients)))
            j=columns[chosen]
            value=row_coordinate(coefficients,values,rhs[i],chosen)
            isfinite(value) && abs(value-x[j])<=cutoff || continue
            old=x[j]
            x[j]=value
            old==value || push!(changes,Dict("equation"=>i,"coordinate"=>j,"old"=>old,"new"=>value))
        end
        after,_=local_quality(B,x,rhs,policy)
        push!(trace,Dict("sweep"=>sweep,"bad_before"=>length(bad),"changes"=>changes,
            "reliable_after"=>after.reliable,"relative_error_after"=>after.relative_error))
        isempty(changes) && break
    end
    return trace
end
const LOCAL_SWEEP_LIMIT=Ref(8)
function complete_local_transfer!(ws)
    B=JSimplex._basis_matrix!(ws)
    rhs=JSimplex._basis_primal_rhs(ws)
    basic,magnitude=corrected_vector(ws,ws.primal[ws.basis.basic_indices],rhs)
    policy=ws.progress.numerical_policy
    local_rows!(B,basic,rhs,policy,policy.solve_tolerance*magnitude;limit=LOCAL_SWEEP_LIMIT[])
    quality,_=local_quality(B,basic,rhs,policy)
    quality.reliable || return false
    dual=copy(ws.scratch.rho)
    JSimplex._native_cleanup_solve!(dual,ws,B,ws.costs[ws.basis.basic_indices],
        ()->false;transposed=true) || return false
    install_basic!(ws,basic)
    install_dual!(ws,dual)
    JSimplex._pipeline_changed!(ws,ws.scratch.row_solution)
    JSimplex._pipeline_changed!(ws,ws.scratch.rho)
    JSimplex._invalidate_pricing_pool!(ws;basis=false)
    return JSimplex._legacy_primal_point_certified(ws) && JSimplex._recomputed_basis_reliable(ws)
end

records=Dict{String,Any}[]
metadata=Dict{String,Any}("scope"=>"Experimental local reconstruction at a saved phase boundary; no production integration",
    "before_sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),
    "residual_helper_sha256"=>bytes2hex(sha256(residual_source)),"records"=>records)
@testset "Local phase transfer row reconstruction" begin
    ws,_,_=mapped_workspace(load_transfer();carry=true)
    saved_nonbasic=copy(ws.primal[ws.basis.states.!=JSimplex.BASIC])
    rhs=JSimplex._basis_primal_rhs(ws)
    basic,magnitude=corrected_vector(ws,ws.primal[ws.basis.basic_indices],rhs)
    cutoff=ws.progress.numerical_policy.solve_tolerance*magnitude
    metadata["cutoff"]=cutoff
    metadata["local_trace"]=local_rows!(JSimplex._basis_matrix!(ws),basic,rhs,ws.progress.numerical_policy,cutoff)
    install_basic!(ws,basic)
    dual=copy(ws.scratch.rho)
    dual_ok=JSimplex._native_cleanup_solve!(dual,ws,JSimplex._basis_matrix!(ws),
        ws.costs[ws.basis.basic_indices],()->false;transposed=true)
    @test dual_ok
    install_dual!(ws,dual)
    @test isequal(saved_nonbasic,ws.primal[ws.basis.states.!=JSimplex.BASIC])
    push!(records,inspect_workspace(ws,"local row candidate"))
    serialize(output*"-candidate.bin",ws)
    @test JSimplex._recomputed_basis_reliable(ws)
    @test JSimplex._legacy_primal_point_certified(ws)
    @test JSimplex._original_primal_feasible(ws,ws.primal[1:size(ws.problem.A,2)])
    expected=copy(ws.primal)
    policy=ws.progress.numerical_policy
    # A tiny nonzero RHS must survive reconstruction of a coupled zero row.
    B=sparse([1.0 1.0;0.0 1.0]);rhs=[0.0,1e-66]
    x=[1e-30,1e-66]
    local_rows!(B,x,rhs,policy,1e-21)
    @test local_quality(B,x,rhs,policy)[1].reliable
    @test x==[-1e-66,1e-66]
    metadata["portable_positive_point"]=copy(x)
    # This selection rule can cycle; a bounded trial must remain rejectable.
    x=[0.0,1e-66]
    trace=local_rows!(B,x,rhs,policy,1e-21)
    @test length(trace)==8
    @test !local_quality(B,x,rhs,policy)[1].reliable
    metadata["portable_rejection_sweeps"]=length(trace)
    metadata["portable_rejection_trace"]=trace
    source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
    i=first(findfirst("function _remove_artificials!",source))
    j=first(findnext("\nfunction ",source,i+1))-1
    body=source[i:j]
    needle="    _phase_refactor!(fresh,original,stop)"
    replacement="    fresh.primal .= phase.primal[map.original_to_phase]\n"*needle*
        "\n    Main.complete_local_transfer!(fresh) || return false"
    @assert count(needle,body)==1
    body=replace(body,needle=>replacement)
    metadata["export_variant_sha256"]=bytes2hex(sha256(body))
    write(output*"-export-method.jl",body)
    Base.include_string(JSimplex,body,"diagnostic_local_row_export.jl")
    LOCAL_SWEEP_LIMIT[]=0
    data=load_transfer();primal_before=copy(data.original.primal);basis_before=copy(data.original.basis.basic_indices)
    accepted=Base.invokelatest(JSimplex.remove_artificials!,data.phase,data.mapping,data.original,data.policy,()->false)
    @test !accepted
    @test isequal(primal_before,data.original.primal) && basis_before==data.original.basis.basic_indices
    metadata["zero_sweep_export_accepted"]=accepted
    LOCAL_SWEEP_LIMIT[]=8
    data=load_transfer()
    accepted=Base.invokelatest(JSimplex.remove_artificials!,data.phase,data.mapping,data.original,data.policy,()->false)
    @test accepted
    @test isequal(expected,data.original.primal)
    @test JSimplex._recomputed_basis_reliable(data.original)
    @test JSimplex._legacy_primal_point_certified(data.original)
    @test JSimplex._original_primal_feasible(data.original,data.original.primal[1:size(data.original.problem.A,2)])
    metadata["complete_export_accepted"]=accepted
    metadata["export_pricing"]=string(JSimplex._effective_pricing(data.original,:primal))
    push!(records,inspect_workspace(data.original,"complete local export"))
    serialize(output*"-exported.bin",data.original)

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
metadata["replay_helper_sha256"]=bytes2hex(sha256(helper_source))
metadata["julia"]=string(VERSION)
metadata["julia_threads"]=Threads.nthreads()
metadata["blas_threads"]=BLAS.get_num_threads()
metadata["architecture"]=string(Sys.ARCH)
metadata["scalar_type"]="Float64"
metadata["maximum_sweeps"]=8
open(output*".toml","w") do io
    TOML.print(io,metadata)
end
