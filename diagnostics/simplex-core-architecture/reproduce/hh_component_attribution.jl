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
function graph(f)
    saved = JS.copy_basis_factorization(f)
    @assert saved.base === f.base
    @assert saved.refactor_workspace === nothing
    @assert saved.work !== f.work
    @assert !Base.mightalias(f.base.lower.nzval,f.extract_workspace.values)
    @assert !Base.mightalias(f.base.upper.nzval,f.extract_workspace.values)
    Dict{String,Any}("live_julia_bytes" => Base.summarysize(f),
         "checkpoint_julia_bytes" => Base.summarysize(saved),
         "combined_deduplicated_julia_bytes" => Base.summarysize((f,saved)),
         "base_julia_bytes" => Base.summarysize(f.base),
         "backend_julia_bytes" => Base.summarysize(f.refactor_workspace),
         "extraction_scratch_julia_bytes" => Base.summarysize(f.extract_workspace),
         "solve_scratch_julia_bytes" => Base.summarysize((f.work,f.auxiliary,f.prepared_partial,f.prepared_direction,f.unit_workspace)),
         "lower_nnz" => nnz(f.base.lower), "upper_nnz" => nnz(f.base.upper))
end
function backend_batch(B, count)
    f = JS.HuangfuHallFactorization(B)
    F = f.refactor_workspace
    GC.gc(true)
    t = @timed for k in 1:count
        F = JS._hh_refactor_backend(F,B,Val(:native))
    end
    # Validate the last backend independently of the old immutable base.
    @assert norm(B*(F\ones(size(B,1)))-ones(size(B,1)),Inf) <= 1e-11
    t
end
function extraction_batch(B, count)
    f = JS.HuangfuHallFactorization(B)
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
    f = JS.HuangfuHallFactorization(B)
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
    f = JS.HuangfuHallFactorization(initial)
    saved = JS.copy_basis_factorization(f)
    h = base_hash(saved.base)
    rows = Dict[]
    for (label,B) in (("changed_pattern",matrix_fixture(256,false,7)),
                      ("shrink",matrix_fixture(64,false)),
                      ("regrow",matrix_fixture(256,false)))
        JS.refactorize!(f,B)
        check_solves(f,B);check_solves(saved,initial)
        @assert base_hash(saved.base)==h
        row=graph(f);row["case"]=label;row["dimension"]=size(B,1)
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
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    samples=Dict[];retention=Dict[]
    count=16
    regions=(("backend",backend_batch),("extraction",extraction_batch),("whole_refactor",whole_batch))
    report=Dict("source"=>dirname(pathof(JS)),"julia_version"=>string(VERSION),
        "scope"=>"HH/native Float64 synthetic component attribution; no speedup comparison",
        "retention_limits"=>"Julia reachable object graph only; excludes external UMFPACK storage and hidden backing capacity. Region lifetimes differ; do not add independent timings or subtract GC to infer arithmetic time.",
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
        f=JS.HuangfuHallFactorization(B);check_solves(f,B)
        row=graph(f);row["case"]=label;row["dimension"]=n;push!(retention,row)
        save()
    end
    report["lifecycle"]=lifecycle()
    @assert length(samples)==72
    report["complete"]=true;save()
    println("HH native attribution passed: 72 samples; ownership, residual and failure checks passed")
end
Base.invokelatest(main,ARGS[1])
