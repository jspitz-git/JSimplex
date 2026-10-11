using LinearAlgebra, SparseArrays, SHA
scratch_capacity(f) = sum(length(getfield(v,:ref).mem) for v in (f.work,f.auxiliary,f.prepared_partial,f.prepared_direction))
function factor_hash(f)
    context=SHA.SHA2_256_CTX()
    b=f.base
    for data in (b.lower.colptr,b.lower.rowval,b.lower.nzval,b.upper.colptr,b.upper.rowval,
                 b.upper.nzval,b.rows,b.columns,b.positions,b.scaling,b.upper_rowptr,b.upper_columns)
        SHA.update!(context,reinterpret(UInt8,data))
    end
    SHA.update!(context,UInt8[b.divide_scaling,b.finite_upper])
    bytes2hex(SHA.digest!(context))
end
function same_size_sample(matrices,backend)
    f=JS.HuangfuHallFactorization(first(matrices),Val(backend))
    original=(f.work,f.auxiliary,f.prepared_partial,f.prepared_direction)
    GC.gc(true)
    timing=@timed begin
        for B in matrices
            JS.refactorize!(f,B)
        end
    end
    rhs=ones(size(last(matrices),1))
    forward=JS.forward_solve(f,rhs);transposed=JS.transpose_solve(f,rhs)
    @assert last(matrices)*forward ≈ rhs
    @assert transpose(last(matrices))*transposed ≈ rhs
    @assert all(a===b for (a,b) in zip(original,(f.work,f.auxiliary,f.prepared_partial,f.prepared_direction)))
    Dict("seconds"=>timing.time,"compile_seconds"=>timing.compile_time,"bytes"=>timing.bytes,
         "allocations"=>Base.gc_alloc_count(timing.gcstats),"gc_seconds"=>timing.gctime,
         "scratch_capacity_elements"=>scratch_capacity(f),"factor_hash"=>factor_hash(f),
         "forward_hash"=>bytes2hex(sha256(reinterpret(UInt8,forward))),
         "transpose_hash"=>bytes2hex(sha256(reinterpret(UInt8,transposed))))
end
function shape_sample(matrices,backend)
    f=JS.HuangfuHallFactorization(first(matrices),Val(backend))
    rows=Dict[]
    for B in matrices[2:end]
        GC.gc(true)
        timing=@timed JS.refactorize!(f,B)
        rhs=ones(size(B,1));solution=JS.forward_solve(f,rhs)
        transposed=JS.transpose_solve(f,rhs)
        @assert B*solution ≈ rhs
        @assert transpose(B)*transposed ≈ rhs
        push!(rows,Dict("dimension"=>size(B,1),"seconds"=>timing.time,
            "compile_seconds"=>timing.compile_time,"bytes"=>timing.bytes,
            "allocations"=>Base.gc_alloc_count(timing.gcstats),"gc_seconds"=>timing.gctime,
            "scratch_capacity_elements"=>scratch_capacity(f),"factor_hash"=>factor_hash(f),
            "forward_hash"=>bytes2hex(sha256(reinterpret(UInt8,solution))),
            "transpose_hash"=>bytes2hex(sha256(reinterpret(UInt8,transposed)))))
    end
    rows
end
