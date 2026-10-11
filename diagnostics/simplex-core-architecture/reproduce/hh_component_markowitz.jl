using JSimplex, LinearAlgebra, SparseArrays, SHA, TOML, Statistics
const JS = JSimplex

function matrix_fixture(n, dense, offset=1)
    # Exactly representable coefficients; construction is outside measured scopes.
    B = spdiagm(0 => fill(Float64(n + 2), n))
    for j in 1:n, i in 1:n
        if i != j && (dense || mod(i-j,n) == offset || mod(j-i,n) == offset)
            B[i,j] = Float64(mod(3i+5j,7)-3)/16
        end
    end
    B
end
function base_hash(b)
    c = SHA.SHA2_256_CTX()
    for v in (b.lower.colptr,b.lower.rowval,b.lower.nzval,b.upper.colptr,
              b.upper.rowval,b.upper.nzval,b.rows,b.columns,b.positions,b.scaling,
              b.upper_rowptr,b.upper_columns)
        SHA.update!(c,reinterpret(UInt8,v))
    end
    SHA.update!(c,UInt8[b.divide_scaling,b.finite_upper])
    bytes2hex(SHA.digest!(c))
end
function check_solves(f,B)
    rhs = [Float64(mod(i,5)-2) for i in axes(B,1)]
    x = JS.forward_solve(f,rhs)
    y = JS.transpose_solve(f,rhs)
    @assert norm(B*x-rhs,Inf) <= 1e-11
    @assert norm(transpose(B)*y-rhs,Inf) <= 1e-11
    nothing
end
function graph(f, old_checkpoint=nothing)
    saved = JS.copy_basis_factorization(f)
    @assert saved.base === f.base
    @assert saved.refactor_workspace === nothing
    @assert all(getfield(saved,k) !== getfield(f,k) for k in
                (:work,:auxiliary,:prepared_partial,:prepared_direction))
    @assert !Base.mightalias(f.base.lower.nzval,f.extract_workspace.values)
    @assert !Base.mightalias(f.base.upper.nzval,f.extract_workspace.values)
    F=f.refactor_workspace
    workspace=isnothing(F) ? nothing : F.workspace
    spare=isnothing(F) ? nothing : F.spare
    Dict{String,Any}("live_plus_old_checkpoint_julia_bytes" => Base.summarysize((f,old_checkpoint)),
         "backend_workspace_julia_bytes" => Base.summarysize(workspace),
         "backend_spare_julia_bytes" => Base.summarysize(spare),
         "backend_workspace_rows" => isnothing(workspace) ? 0 : length(workspace.rows),
         "backend_workspace_columns" => isnothing(workspace) ? 0 : length(workspace.columns),
         "backend_core_elements" => isnothing(F) ? 0 : length(F.core.factors),
         "backend_spare_core_elements" => isnothing(spare) ? 0 : length(spare.core.factors),
         "backend_pooled_vectors" => isnothing(F) ? 0 : length(F.lower_pool)+length(F.upper_pool),
         "live_julia_bytes" => Base.summarysize(f),
         "checkpoint_julia_bytes" => Base.summarysize(saved),
         "combined_deduplicated_julia_bytes" => Base.summarysize((f,saved)),
         "base_julia_bytes" => Base.summarysize(f.base),
         "backend_julia_bytes" => Base.summarysize(f.refactor_workspace),
         "extraction_scratch_julia_bytes" => Base.summarysize(f.extract_workspace),
         "solve_scratch_julia_bytes" => Base.summarysize((f.work,f.auxiliary,f.prepared_partial,f.prepared_direction,f.unit_workspace)),
         "lower_nnz" => nnz(f.base.lower), "upper_nnz" => nnz(f.base.upper))
end
function backend_batch(B, count)
    f = JS.HuangfuHallFactorization(B,Val(:markowitz))
    F = f.refactor_workspace
    GC.gc(true)
    t = @timed for k in 1:count
        F = JS._hh_refactor_backend(F,B,Val(:markowitz))
    end
    # Validate the last backend independently of the old immutable base.
    rhs=ones(size(B,1));x=similar(rhs);y=similar(rhs)
    JS._backend_forward_solve!(x,F,rhs)
    JS._backend_transpose_solve!(y,F,rhs)
    @assert norm(B*x-rhs,Inf) <= 1e-11
    @assert norm(transpose(B)*y-rhs,Inf) <= 1e-11
    t
end
function extraction_batch(B, count)
    f = JS.HuangfuHallFactorization(B,Val(:markowitz))
    lastbase = f.base
    expected = base_hash(lastbase)
    GC.gc(true)
    t = @timed for k in 1:count
        lastbase = JS._hh_extract_base(f.refactor_workspace,f.work,f.auxiliary,f.extract_workspace)
    end
    @assert base_hash(lastbase) == expected
    @assert !Base.mightalias(lastbase.lower.nzval,f.extract_workspace.values)
    t
end
function whole_batch(B, count)
    f = JS.HuangfuHallFactorization(B,Val(:markowitz))
    saved = JS.copy_basis_factorization(f)
    before = base_hash(saved.base)
    GC.gc(true)
    t = @timed for k in 1:count
        JS.refactorize!(f,B)
    end
    @assert base_hash(saved.base) == before == base_hash(f.base)
    check_solves(f,B); check_solves(saved,B)
    t
end
function lifecycle()
    initial = matrix_fixture(256,false)
    f = JS.HuangfuHallFactorization(initial,Val(:markowitz))
    saved = JS.copy_basis_factorization(f)
    h = base_hash(saved.base)
    rows = Dict[]
    for (label,B) in (("changed_pattern",matrix_fixture(256,false,7)),
                      ("shrink",matrix_fixture(64,false)),
                      ("regrow",matrix_fixture(256,false)))
        JS.refactorize!(f,B)
        check_solves(f,B);check_solves(saved,initial)
        @assert base_hash(saved.base)==h
        row=graph(f,saved);row["case"]=label;row["dimension"]=size(B,1)
        push!(rows,row)
    end
    live = base_hash(f.base)
    failed = false
    try
        JS.refactorize!(f,spzeros(256,256))
    catch e
        e isa LinearAlgebra.SingularException || rethrow()
        failed = true
    end
    @assert failed && f.refactor_workspace === nothing
    @assert base_hash(f.base)==live && base_hash(saved.base)==h
    check_solves(f,initial);check_solves(saved,initial)
    rows
end
function storage_transitions()
    B0=matrix_fixture(256,false)
    f=JS.HuangfuHallFactorization(B0,Val(:markowitz))
    saved=JS.copy_basis_factorization(f);h=base_hash(saved.base)
    rows=Dict[]
    for (name,B) in (("dense256",matrix_fixture(256,true)),
                     ("small_first",matrix_fixture(64,false)),
                     ("small_second",matrix_fixture(64,false)),
                     ("empty_first",spzeros(0,0)),("empty_second",spzeros(0,0)),
                     ("small_after_empty",matrix_fixture(64,false)))
        JS.refactorize!(f,B)
        if size(B,1)>0;check_solves(f,B);else
            @assert isempty(JS.forward_solve(f,Float64[]))
            @assert isempty(JS.transpose_solve(f,Float64[]))
        end
        check_solves(saved,B0);@assert base_hash(saved.base)==h
        row=graph(f,saved);row["case"]=name;row["dimension"]=size(B,1)
        push!(rows,row)
    end
    rows
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    samples=Dict[];retention=Dict[]
    count=16
    regions=(("backend",backend_batch),("extraction",extraction_batch),("whole_refactor",whole_batch))
    report=Dict("source"=>dirname(pathof(JS)),"julia_version"=>string(VERSION),
        "scope"=>"HH/markowitz Float64 synthetic component attribution; no speedup comparison",
        "backend"=>"markowitz", "precision"=>"Float64",
        "sample_lifetime"=>"Fresh owner each sample; first inactive-slot allocation is included in 16 calls; warm compilation is not warmed owner storage.",
        "retention_limits"=>"Julia reachable object graph only; excludes hidden backing capacity/native BLAS memory. old_checkpoint field includes the old saved factor; fresh-checkpoint graph shares current base. Backend/workspace/spare sizes overlap; do not sum. Independent region timings must not be added; GC is included.",
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
        "calls_per_sample"=>count,"rounds"=>6,"samples"=>samples,"retention"=>retention)
    save()=open(io->TOML.print(io,report),output,"w")
    for n in (64,256),dense in (false,true)
        B=matrix_fixture(n,dense)
        label=(dense ? "dense" : "sparse")*"-"*string(n)
        digest=bytes2hex(sha256(vcat(reinterpret(UInt8,B.colptr),reinterpret(UInt8,B.rowval),reinterpret(UInt8,B.nzval))))
        for (_,run) in regions;run(B,count);end
        for round in 1:6, shift in 0:2
            region,run=regions[mod1(round+shift,3)]
            t=run(B,count)
            row=Dict("case"=>label,"matrix_sha256"=>digest,"region"=>region,"round"=>round,
                "seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,
                "bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats))
            push!(samples,row);save()
            @assert t.compile_time==0
        end
        f=JS.HuangfuHallFactorization(B,Val(:markowitz));check_solves(f,B)
        row=graph(f);row["case"]=label;row["dimension"]=n;row["state"]="fresh";push!(retention,row)
        for k in 1:4;JS.refactorize!(f,B);end
        check_solves(f,B)
        row=graph(f);row["case"]=label;row["dimension"]=n;row["state"]="cycled";push!(retention,row)
        save()
    end
    report["lifecycle"]=lifecycle()
    report["storage_transitions"]=storage_transitions()
    @assert length(samples)==72
    report["complete"]=true;save()
    println("HH Markowitz attribution passed: 72 samples; ownership, residual and failure checks passed")
end
Base.invokelatest(main,ARGS[1])
