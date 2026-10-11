using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Serialization
const JS=JSimplex
const TYPES=(Float16,Float32,BigFloat,Rational{BigInt},Rational{Int64})
function fixture(::Type{T},n,dense,shift=false) where T
    B=spdiagm(0=>ones(T,n));v=one(T)/T(16)
    if dense
        for j in 1:n,i in 1:n;B[i,j]+=v;end
    else
        for i in 1:2:n-1;B[i,i+1]=v;B[i+1,i]=v;end
        if shift;n>2 && (B[1,3]=v);end
    end
    B
end
function fingerprint(x)
    io=IOBuffer();serialize(io,x);bytes2hex(sha256(take!(io)))
end
function state(b)
    deepcopy((b.lower,b.upper,b.rows,b.columns,b.positions,b.scaling,
        b.upper_rowptr,b.upper_columns,b.divide_scaling,b.finite_upper))
end
function residual(B,x,rhs)
    T=eltype(B);error=norm(B*x-rhs,Inf)
    @assert T<:Rational ? iszero(error) : error<=T(16)*eps(T)*max(one(T),norm(rhs,Inf))
end
function check(f,B)
    T=eltype(B);rhs=T[mod(i,5)-2 for i in axes(B,1)]
    residual(B,JS.forward_solve(f,rhs),rhs)
    residual(transpose(B),JS.transpose_solve(f,rhs),rhs)
end
function graph(f)
    saved=JS.copy_basis_factorization(f)
    @assert saved.base===f.base && saved.refactor_workspace===nothing
    @assert all(getfield(saved,k)!==getfield(f,k) for k in (:work,:auxiliary,:prepared_partial,:prepared_direction))
    @assert !Base.mightalias(f.base.lower.nzval,f.extract_workspace.values)
    @assert !Base.mightalias(f.base.upper.nzval,f.extract_workspace.values)
    Dict("live_julia_bytes"=>Base.summarysize(f),"base_julia_bytes"=>Base.summarysize(f.base),
      "backend_julia_bytes"=>Base.summarysize(f.refactor_workspace),
      "extraction_scratch_julia_bytes"=>Base.summarysize(f.extract_workspace),
      "solve_scratch_julia_bytes"=>Base.summarysize((f.work,f.auxiliary,f.prepared_partial,f.prepared_direction,f.unit_workspace)),
      "checkpoint_julia_bytes"=>Base.summarysize(saved),
      "combined_deduplicated_julia_bytes"=>Base.summarysize((f,saved)),
      "lower_nnz"=>nnz(f.base.lower),"upper_nnz"=>nnz(f.base.upper))
end
function backend_batch(B,backend,count)
    f=JS.HuangfuHallFactorization(B,backend);F=f.refactor_workspace
    GC.gc(true)
    t=@timed for i in 1:count;F=JS._hh_refactor_backend(F,B,backend);end
    rhs=ones(eltype(B),size(B,1))
    if backend===Val(:markowitz)
        x=similar(rhs);y=similar(rhs)
        JS._backend_forward_solve!(x,F,rhs);JS._backend_transpose_solve!(y,F,rhs)
    else
        x=F\rhs;y=transpose(F)\rhs
    end
    residual(B,x,rhs);residual(transpose(B),y,rhs);t
end
function extraction_batch(B,backend,count)
    f=JS.HuangfuHallFactorization(B,backend);expected=state(f.base);b=f.base
    GC.gc(true)
    t=@timed for i in 1:count;b=JS._hh_extract_base(f.refactor_workspace,f.work,f.auxiliary,f.extract_workspace);end
    @assert isequal(state(b),expected)
    @assert !Base.mightalias(b.lower.nzval,f.extract_workspace.values)
    t
end
function whole_batch(B,backend,count)
    f=JS.HuangfuHallFactorization(B,backend);saved=JS.copy_basis_factorization(f);expected=state(saved.base)
    GC.gc(true)
    t=@timed for i in 1:count;JS.refactorize!(f,B);end
    @assert isequal(state(saved.base),expected) && isequal(state(f.base),expected)
    check(f,B);check(saved,B);t
end
function lifecycle(::Type{T},backend) where T
    B0=fixture(T,32,false);f=JS.HuangfuHallFactorization(B0,backend)
    saved=JS.copy_basis_factorization(f);expected=state(saved.base);rows=Dict[]
    for (label,B) in (("changed_pattern",fixture(T,32,false,true)),("shrink",fixture(T,8,false)),
         ("dense_regrow",fixture(T,32,true)),("empty",spzeros(T,0,0)),("restore",B0))
        JS.refactorize!(f,B)
        if isempty(B)
            @assert isempty(JS.forward_solve(f,T[])) && isempty(JS.transpose_solve(f,T[]))
        else;check(f,B);end
        check(saved,B0);@assert isequal(state(saved.base),expected)
        push!(rows,Dict("transition"=>label,"dimension"=>size(B,1),"graph"=>graph(f)))
    end
    live=state(f.base);failed=false
    try;JS.refactorize!(f,spzeros(T,32,32))
    catch e;e isa SingularException || rethrow();failed=true;end
    @assert failed && f.refactor_workspace===nothing
    @assert isequal(state(f.base),live) && isequal(state(saved.base),expected)
    check(f,B0);check(saved,B0)
    Dict("transitions"=>rows,"failed_refactor_preserved"=>true)
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    @assert precision(BigFloat)==256
    samples=Dict[];retention=Dict[];lifecycles=Dict[];cases=Dict[]
    report=Dict("source"=>dirname(pathof(JS)),"source_hh_sha256"=>bytes2hex(sha256(read(joinpath(dirname(pathof(JS)),"huangfu_hall_factorization.jl")))),
        "julia_version"=>string(VERSION),"bigfloat_precision"=>precision(BigFloat),"julia_threads"=>Threads.nthreads(),
        "blas_threads"=>BLAS.get_num_threads(),"calls_per_sample"=>4,"rounds"=>3,"samples"=>samples,"cases"=>cases,
        "retention"=>retention,"lifecycle"=>lifecycles,"scope"=>"HH small scalar component attribution only; fresh owner per sample, GC included, not speedup comparison")
    save()=open(io->TOML.print(io,report),output,"w")
    regions=(("backend",backend_batch),("extraction",extraction_batch),("whole_refactor",whole_batch))
    for T in TYPES,backend_name in (:native,:markowitz)
        backend=Val(backend_name)
        for n in (8,32),dense in (false,true)
            label=string(T)*"/"*string(backend_name)*"/"*(dense ? "dense" : "sparse")*string(n)
            B=fixture(T,n,dense);f=JS.HuangfuHallFactorization(B,backend);check(f,B)
            push!(cases,Dict("case"=>label,"precision"=>string(T),"backend"=>string(backend_name),"dimension"=>n,
                "input_nnz"=>nnz(B),"matrix_sha256"=>fingerprint(B),"actual_factor_type"=>string(typeof(f.refactor_workspace))))
            for (_,run) in regions;run(B,backend,4);end
            for round in 1:3,shift in 0:2
                region,run=regions[mod1(round+shift,3)];t=run(B,backend,4)
                push!(samples,Dict("case"=>label,"round"=>round,"region"=>region,"seconds"=>t.time,
                   "compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats)))
                save();@assert t.compile_time==0
            end
            push!(retention,Dict("case"=>label,"state"=>"fresh","graph"=>graph(f)))
            for i in 1:4;JS.refactorize!(f,B);end
            check(f,B);push!(retention,Dict("case"=>label,"state"=>"cycled","graph"=>graph(f)))
            save();println("Completed ",label);flush(stdout)
        end
        row=lifecycle(T,backend);row["precision"]=string(T);row["backend"]=string(backend_name)
        push!(lifecycles,row);save()
    end
    @assert length(samples)==360 && length(cases)==40 && length(lifecycles)==10
    report["complete"]=true;save();println("Scalar attribution accepted: 360 samples, 40 cases, 10 lifecycles")
end
Base.invokelatest(main,ARGS[1])
