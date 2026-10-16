# UNEXECUTED Task1 tests. Include inside the candidate module only in a future
# independently admitted test driver. No solver, backend or arithmetic kernels.
using Test
using SparseArrays

# Test-only O(n+C) checker; never included by slot-upper.jl or normal factory.
function _check_bg_slots(U::BGSlotUpper)::Bool
    n, C = U.n, U.capacity
    n >= 0 && C >= 0 && 0 <= U.live_count <= C || return false
    arrays = (U.value, U.row_id, U.column_id, U.row_prev, U.row_next,
              U.column_prev, U.column_next)
    all(a -> length(a) == C, arrays) || return false
    maps = (U.row_order, U.row_position, U.column_order, U.column_position,
            U.row_head, U.row_tail, U.column_head, U.column_tail)
    all(a -> length(a) == n, maps) || return false
    # No persistent buffer may alias another or the other index's metadata.
    all(i == j || arrays[i] !== arrays[j] for i in 1:7 for j in 1:7) || return false
    all(i == j || maps[i] !== maps[j] for i in 1:8 for j in 1:8) || return false
    all(a !== b for a in arrays for b in maps) || return false
    for j in 1:n
        r, c = U.row_order[j], U.column_order[j]
        1 <= r <= n && 1 <= c <= n || return false
        U.row_position[r] == j && U.column_position[c] == j || return false
    end
    rows, columns, free = falses(C), falses(C), falses(C)
    for rid in 1:n
        s, prev, cid = U.row_head[rid], 0, 0
        while s != 0
            1 <= s <= C && !rows[s] || return false
            U.row_id[s] == rid && cid < U.column_id[s] <= n || return false
            U.row_prev[s] == prev || return false
            rows[s] = true
            cid, prev, s = U.column_id[s], s, U.row_next[s]
        end
        U.row_tail[rid] == prev || return false
    end
    for cid in 1:n
        s, prev, pos = U.column_head[cid], 0, 0
        while s != 0
            1 <= s <= C && !columns[s] || return false
            rid = U.row_id[s]
            U.column_id[s] == cid && 1 <= rid <= n || return false
            pos < U.row_position[rid] <= n && U.column_prev[s] == prev || return false
            columns[s] = true
            pos, prev, s = U.row_position[rid], s, U.column_next[s]
        end
        U.column_tail[cid] == prev || return false
    end
    s = U.free_head
    while s != 0
        1 <= s <= C && !free[s] && !rows[s] && !columns[s] || return false
        U.row_id[s] == 0 && U.column_id[s] == 0 || return false
        U.row_prev[s] == 0 && U.row_next[s] == 0 && U.column_prev[s] == 0 || return false
        U.value[s] == 0.0 || return false
        free[s] = true
        s = U.column_next[s]
    end
    rows == columns && count(rows) == U.live_count || return false
    all(rows[s] != free[s] for s in 1:C) || return false
    return true
end

# Detached logical CSC tokens, preserving explicit -0.0 and NaN payload bits.
function _bg_selected_state(U::BGSlotUpper)
    _check_bg_slots(U) || throw(ArgumentError("invalid slot arena"))
    ptr, rows, bits = Int[1], Int[], UInt64[]
    for cid in U.column_order
        s = U.column_head[cid]
        while s != 0
            push!(rows, U.row_position[U.row_id[s]])
            push!(bits, reinterpret(UInt64, U.value[s]))
            s = U.column_next[s]
        end
        push!(ptr, length(rows) + 1)
    end
    return (n=U.n, colptr=ptr, rowval=rows, bits=bits)
end

_bg_test_matrix() = SparseMatrixCSC(3, 3, [1,2,4,7], [1,1,2,1,2,3],
                                  [2.0,-0.0,3.0,1.0,4.0,5.0])
_bg_test_tokens(M) = (n=size(M,1), colptr=copy(M.colptr), rowval=copy(M.rowval),
                      bits=collect(reinterpret(UInt64, M.nzval)))
_bg_test_buffers(U) = (U.value,U.row_id,U.column_id,U.row_prev,U.row_next,
                       U.column_prev,U.column_next)
_bg_test_snapshot(U) = Tuple(getfield(U,k) isa AbstractArray ? copy(getfield(U,k)) :
                             getfield(U,k) for k in fieldnames(typeof(U)))

# Independent expected row permutation: sort source tokens only in tests.
function _bg_test_permuted(M, order)
    ptr, rows, bits = Int[1], Int[], UInt64[]
    for j in 1:size(M,2)
        tokens = [(findfirst(==(M.rowval[k]),order), reinterpret(UInt64,M.nzval[k]))
                  for k in M.colptr[j]:M.colptr[j+1]-1]
        sort!(tokens; by=first)
        append!(rows, first.(tokens)); append!(bits, last.(tokens))
        push!(ptr,length(rows)+1)
    end
    return (n=size(M,1),colptr=ptr,rowval=rows,bits=bits)
end

function _bg_test_row_ids(U,rid)
    ids = Int[]; s = U.row_head[rid]
    while s != 0
        push!(ids,U.column_id[s]); s = U.row_next[s]
    end
    return ids
end

# O(degree) test insertion-location search; not a proposed hot-path helper.
function _bg_test_insert!(U,rid,cid,value)
    rp=0; rn=U.row_head[rid]
    while rn != 0 && U.column_id[rn] < cid
        rp=rn; rn=U.row_next[rn]
    end
    cp=0; cn=U.column_head[cid]
    while cn != 0 && U.row_position[U.row_id[cn]] < U.row_position[rid]
        cp=cn; cn=U.column_next[cn]
    end
    return _bg_link!(U,rid,cid,value,rp,rn,cp,cn)
end

@testset "BG slots: import and stable q" begin
    for (M,q) in [(spzeros(0,0),Int[]), (spdiagm(0=>ones(3)),[1,2,3]),
                  (_bg_test_matrix(),[1,2,3]), (_bg_test_matrix(),[3,1,2])]
        before = _bg_test_tokens(M); oldq=copy(q)
        U = _bg_slots(M,q)
        @test _check_bg_slots(U)
        @test isequal(_bg_selected_state(U),before)
        @test U.column_order == q && U.column_position == invperm(q)
        @test U.row_order == U.row_position == collect(1:size(M,1))
        @test U.live_count == nnz(M)
        @test U.capacity == (size(M,1)==0 ? 0 : max(nnz(M),16))
        @test isequal(_bg_test_tokens(M),before) && q == oldq
        @test U.value !== M.nzval && U.row_id !== M.rowval && U.column_order !== q
        if size(M,1)>0
            M.nzval[1]=77.0; q[1]=0
            @test isequal(_bg_selected_state(U),before)
            @test U.column_order == oldq
        end
    end
    U=_bg_slots(_bg_test_matrix(),[3,1,2])
    @test _bg_test_row_ids(U,1) == [1,2,3]
    @test reinterpret(UInt64,U.value[_bg_lookup(U,1,1)]) == 0x8000000000000000
    @test _bg_lookup(U,3,3) == 0
    @test _bg_lookup(U,2,1) != 0
    for q in ([1,1,3],[0,2,3],[1,2,4],[1,2])
        @test_throws ArgumentError _bg_slots(_bg_test_matrix(),q)
    end
    @test_throws ArgumentError _bg_slots(spzeros(2,3),[1,2,3])
    # Corrupt already-constructed valid CSC inputs, so the rejection belongs
    # to our constructor and not an upstream SparseMatrixCSC constructor.
    for rows in ([1,1],[2,1],[1,3])
        M=SparseMatrixCSC(2,2,[1,3,3],[1,2],[1.,2.])
        copyto!(M.rowval,rows)
        @test_throws ArgumentError _bg_slots(M,[1,2])
    end
    M=SparseMatrixCSC(2,2,[1,2,3],[1,2],[Inf,reinterpret(Float64,0x7ff8000000000001)])
    @test isequal(_bg_selected_state(_bg_slots(M,[2,1])),_bg_test_tokens(M))
end

@testset "BG slots: unlink, exact zero, free reuse and local guards" begin
    U=_bg_slots(_bg_test_matrix(),[1,2,3])
    s=_bg_lookup(U,1,3); C=U.capacity
    _bg_unlink!(U,s)
    @test _check_bg_slots(U) && _bg_lookup(U,1,3)==0
    @test _bg_test_insert!(U,1,3,9.0)==s
    @test _check_bg_slots(U) && U.capacity==C && U.live_count==6
    for z in (0.0,-0.0)
        s=_bg_lookup(U,1,3); _bg_set_at!(U,s,z)
        @test _check_bg_slots(U) && _bg_lookup(U,1,3)==0
        @test _bg_test_insert!(U,1,3,4.0)==s
    end
    for k in 1:50
        s=_bg_lookup(U,1,3); _bg_unlink!(U,s)
        @test _bg_test_insert!(U,1,3,Float64(k))==s
        @test _check_bg_slots(U) && U.capacity==C
    end
    # Every boundary/singleton of both indexes, including nontrivial row maps.
    V=_bg_slots(spzeros(4,4),[3,1,4,2]); _bg_swap_rows!(V,2)
    for rid in (3,1,4,2), cid in (4,2,1,3)
        _bg_test_insert!(V,rid,cid,Float64(10rid+cid))
        @test _check_bg_slots(V)
    end
    for rid in (1,4,2,3), cid in (1,4,2,3)
        _bg_unlink!(V,_bg_lookup(V,rid,cid))
        @test _check_bg_slots(V)
    end
    @test V.live_count==0 && all(iszero,V.row_head) && all(iszero,V.column_tail)
    s=_bg_lookup(U,1,3)
    for x in (7.0,Inf,reinterpret(Float64,0x7ff8000000000001),nextfloat(0.0))
        _bg_set_at!(U,s,x)
        @test reinterpret(UInt64,U.value[s])==reinterpret(UInt64,x)
        @test _bg_lookup(U,1,3)==s && _check_bg_slots(U)
    end
    before=_bg_test_snapshot(U)
    @test_throws ArgumentError _bg_link!(U,1,3,1.0,0,0,0,0)
    @test_throws ArgumentError _bg_link!(U,0,1,1.0,0,0,0,0)
    @test_throws ArgumentError _bg_lookup(U,1,4)
    @test_throws ArgumentError _bg_unlink!(U,0)
    @test_throws ArgumentError _bg_set_at!(U,U.free_head,2.0)
    @test isequal(_bg_test_snapshot(U),before)
end

@testset "BG slots: capacity and allocation failure" begin
    @test _bg_capacity(0,1)==16
    @test _bg_capacity(16,17)==32
    @test _bg_capacity(24,25)==40
    @test _bg_capacity(24,100)==100
    @test_throws OverflowError _bg_capacity(typemax(Int)-1,typemax(Int))
    for U in (_bg_slots(spzeros(0,0),Int[]),_bg_slots(_bg_test_matrix(),[3,1,2]),
              _bg_slots(sparse(reshape(vcat(0.0,ones(24)),5,5)),collect(1:5)))
        C=U.capacity; old=_bg_test_buffers(U); state=_bg_selected_state(U)
        _bg_reserve!(U,C)
        @test all(a===b for (a,b) in zip(old,_bg_test_buffers(U)))
        _bg_reserve!(U,C+1)
        @test U.capacity==_bg_capacity(C,C+1) && _check_bg_slots(U)
        @test all(a!==b for (a,b) in zip(old,_bg_test_buffers(U)))
        @test isequal(_bg_selected_state(U),state)
        @test all(isequal(a,b[1:C]) for (a,b) in zip(old,_bg_test_buffers(U)))
    end
    # Success with deliberately dirty fresh buffers: every suffix field must
    # be initialized, independently of memory returned by the allocator.
    U=_bg_slots(_bg_test_matrix(),[3,1,2]); old=_bg_test_buffers(U)
    state=_bg_selected_state(U); C=U.capacity; calls=Ref(0)
    dirtyallocate=function (T,n)
        calls[]+=1
        return fill(T(77),n)
    end
    _bg_reserve_with!(U,C+1,dirtyallocate)
    @test calls[]==7 && U.capacity==32 && _check_bg_slots(U)
    @test all(isequal(a,b[1:C]) for (a,b) in zip(old,_bg_test_buffers(U)))
    @test all(a!==b for (a,b) in zip(old,_bg_test_buffers(U)))
    @test isequal(_bg_selected_state(U),state)
    for failat in 1:7
        U=_bg_slots(_bg_test_matrix(),[3,1,2]); before=_bg_test_snapshot(U)
        owners=_bg_test_buffers(U); calls=Ref(0)
        allocate=function (T,n)
            calls[]+=1
            calls[]==failat && throw(OutOfMemoryError())
            return Vector{T}(undef,n)
        end
        @test_throws OutOfMemoryError _bg_reserve_with!(U,U.capacity+1,allocate)
        @test calls[]==failat
        @test all(a===b for (a,b) in zip(owners,_bg_test_buffers(U)))
        @test isequal(_bg_test_snapshot(U),before) && _check_bg_slots(U)
    end
    U=_bg_slots(_bg_test_matrix(),[1,2,3]); before=_bg_test_snapshot(U)
    @test_throws ArgumentError _bg_reserve!(U,-1)
    @test_throws OverflowError _bg_reserve!(U,typemax(Int))
    @test isequal(_bg_test_snapshot(U),before)
    # Automatic fill growth must reuse holes before allocating.
    U=_bg_slots(spzeros(5,5),collect(1:5))
    for rid in 1:5, cid in 1:5
        _bg_test_insert!(U,rid,cid,1.0)
    end
    @test U.capacity==32 && U.live_count==25 && _check_bg_slots(U)
end

@testset "BG slots: swaps and rotations" begin
    for q in ([1,2,3],[3,1,2])
        M=_bg_test_matrix(); U=_bg_slots(M,q); original=_bg_selected_state(U)
        values=copy(U.value); rowids=copy(U.row_id); colids=copy(U.column_id)
        for j in (1,2,2,1)
            _bg_swap_rows!(U,j)
            @test _check_bg_slots(U)
            @test isequal(_bg_selected_state(U),_bg_test_permuted(M,U.row_order))
            @test all(issorted(_bg_test_row_ids(U,r)) for r in 1:3)
        end
        @test isequal(_bg_selected_state(U),original)
        _bg_rotate_rows!(U,1,3)
        @test U.row_order==[2,3,1] && _check_bg_slots(U)
        @test isequal(_bg_selected_state(U),_bg_test_permuted(M,[2,3,1]))
        for j in (2,1); _bg_swap_rows!(U,j); end
        @test isequal(_bg_selected_state(U),original)
        @test isequal(U.value,values) && U.row_id==rowids && U.column_id==colids
        before=_bg_test_snapshot(U); _bg_rotate_rows!(U,2,2)
        @test isequal(_bg_test_snapshot(U),before)
        @test_throws ArgumentError _bg_swap_rows!(U,0)
        @test_throws ArgumentError _bg_swap_rows!(U,3)
        @test_throws ArgumentError _bg_rotate_rows!(U,3,1)
        @test isequal(_bg_test_snapshot(U),before)
    end
    for M in (spzeros(4,4),spdiagm(0=>ones(4)),sparse(ones(4,4)))
        U=_bg_slots(M,[4,2,1,3]); _bg_rotate_rows!(U,2,4)
        @test _check_bg_slots(U)
        @test isequal(_bg_selected_state(U),_bg_test_permuted(M,[1,3,4,2]))
        _bg_swap_rows!(U,2)
        @test isequal(_bg_selected_state(U),_bg_test_permuted(M,[1,4,3,2]))
    end
end

@testset "BG slots: checker detects corrupt structures" begin
    original=_bg_slots(_bg_test_matrix(),[3,1,2])
    mutations=(U->(U.row_next[U.row_head[1]]=U.row_head[1]),
               U->(U.column_prev[U.column_head[1]]=U.column_head[1]),
               U->(U.row_id[U.column_head[1]]=3),
               U->(U.free_head=U.row_head[1]),
               U->(U.column_id[U.row_next[U.row_head[1]]]=U.column_id[U.row_head[1]]),
               U->(U.row_head[1]=0), U->(U.row_position[1]=2),
               U->(U.row_tail[1]=U.capacity+1),
               U->(U.column_next[U.free_head]=U.free_head),
               U->(U.row_prev[U.free_head]=1), U->(U.live_count+=1),
               U->(U.row_head=U.column_head))
    for corrupt! in mutations
        U=deepcopy(original); corrupt!(U)
        @test !_check_bg_slots(U)
    end
    @test _check_bg_slots(original)
end
