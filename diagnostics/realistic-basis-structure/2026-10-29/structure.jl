# Read-only structural analysis. Matching and SCC are never part of hot timing.
# All graph edges are EXACT nonzeros. Matching is structural, not pivot selection.
function structural_blocks(B::SparseMatrixCSC; edge_budget=50_000_000)
    n = size(B,1)
    size(B,2) == n || error("structural analysis requires a square matrix")
    colmatch = zeros(Int,n); rowmatch = zeros(Int,n)
    visits = 0
    # Protect available diagonal matches before a greedy free-row pass.
    for j in 1:n
        for k in nzrange(B,j)
            visits += 1
            if B.rowval[k] == j && !iszero(B.nzval[k])
                colmatch[j] = j; rowmatch[j] = j; break
            end
        end
    end
    for j in 1:n
        colmatch[j] != 0 && continue
        for k in nzrange(B,j)
            visits += 1
            i = B.rowval[k]
            if !iszero(B.nzval[k]) && rowmatch[i] == 0
                colmatch[j] = i; rowmatch[i] = j; break
            end
        end
    end
    rowseen = zeros(Int,n); colseen = zeros(Int,n); parent = zeros(Int,n)
    queue = Vector{Int}(undef,n); stamp = 0
    for root in 1:n
        colmatch[root] != 0 && continue
        stamp += 1; head = 1; tail = 1; queue[1] = root; colseen[root] = stamp
        free = 0
        while head <= tail && free == 0
            j = queue[head]; head += 1
            for k in nzrange(B,j)
                visits += 1
                visits <= edge_budget || error("structural matching edge budget exceeded")
                i = B.rowval[k]
                (iszero(B.nzval[k]) || rowseen[i] == stamp) && continue
                rowseen[i] = stamp; parent[i] = j
                if rowmatch[i] == 0
                    free = i; break
                end
                next = rowmatch[i]
                if colseen[next] != stamp
                    colseen[next] = stamp; tail += 1; queue[tail] = next
                end
            end
        end
        free != 0 || error("structurally singular basis/spike")
        i = free
        while i != 0
            j = parent[i]; previous = colmatch[j]
            colmatch[j] = i; rowmatch[i] = j; i = previous
        end
    end
    visits <= edge_budget || error("structural matching edge budget exceeded")
    @test sort(colmatch) == collect(1:n)
    @test all(j -> !iszero(B[colmatch[j],j]),1:n)
    # CSR of the matched square graph: original row r becomes rowmatch[r].
    counts = zeros(Int,n); nonzeros = 0
    for j in 1:n, k in nzrange(B,j)
        iszero(B.nzval[k]) && continue
        counts[rowmatch[B.rowval[k]]] += 1; nonzeros += 1
    end
    ptr = Vector{Int}(undef,n+1); ptr[1] = 1
    for i in 1:n; ptr[i+1] = ptr[i] + counts[i]; end
    next = copy(ptr); edges = Vector{Int}(undef,nonzeros)
    for j in 1:n, k in nzrange(B,j)
        iszero(B.nzval[k]) && continue
        i = rowmatch[B.rowval[k]]; edges[next[i]] = j; next[i] += 1
    end
    # Iterative Kosaraju; no recursion proportional to matrix dimension.
    seen = falses(n); finish = Int[]; stack = Int[]; cursors = Int[]
    sizehint!(finish,n); sizehint!(stack,n); sizehint!(cursors,n)
    for root in 1:n
        seen[root] && continue
        seen[root] = true; push!(stack,root); push!(cursors,ptr[root])
        while !isempty(stack)
            node = stack[end]; cursor = cursors[end]
            if cursor < ptr[node+1]
                other = edges[cursor]; cursors[end] += 1
                if !seen[other]
                    seen[other] = true; push!(stack,other); push!(cursors,ptr[other])
                end
            else
                push!(finish,pop!(stack)); pop!(cursors)
            end
        end
    end
    labels = zeros(Int,n); sizes = Int[]; members = Int[]; starts = Int[1]
    for root in Iterators.reverse(finish)
        labels[root] != 0 && continue
        id = length(sizes)+1; count = 0; labels[root] = id; push!(stack,root)
        while !isempty(stack)
            j = pop!(stack); count += 1; push!(members,j)
            for k in nzrange(B,j)
                iszero(B.nzval[k]) && continue
                i = rowmatch[B.rowval[k]]
                if labels[i] == 0
                    labels[i] = id; push!(stack,i)
                end
            end
        end
        push!(sizes,count); push!(starts,length(members)+1)
    end
    off = 0; biggest_nnz = 0; biggest = argmax(sizes)
    depth = ones(Int,length(sizes))
    for block in eachindex(sizes), p in starts[block]:(starts[block+1]-1)
        i = members[p]
        for k in ptr[i]:(ptr[i+1]-1)
            j = edges[k]
            labels[i] <= labels[j] || error("condensation is not topologically ordered")
            if labels[i] != labels[j]
                off += 1; depth[labels[j]] = max(depth[labels[j]],depth[labels[i]]+1)
            elseif block == biggest
                biggest_nnz += 1
            end
        end
    end
    histogram = Dict{String,Int}()
    for s in sizes; key = string(s); histogram[key] = get(histogram,key,0)+1; end
    summary = Dict{String,Any}("dimension"=>n,"nnz"=>nonzeros,"blocks"=>length(sizes),
        "singletons"=>count(==(1),sizes),"largest_block"=>maximum(sizes),
        "largest_block_nnz"=>biggest_nnz,"coupling_nnz"=>off,"condensation_depth"=>maximum(depth),
        "block_sizes_histogram"=>histogram,"matching_edge_visits"=>visits,
        "permutation_triangularizable"=>all(==(1),sizes))
    return (summary=summary,colmatch=colmatch,labels=labels)
end

const WITNESS_BYTES = Ref(0)
function write_witness(path,B,result)
    expected_bytes = 24 + 8*(3*size(B,1)+2*nnz(B)+1)
    if WITNESS_BYTES[] + expected_bytes > 512*1024^2
        return Dict("omitted"=>"512MiB witness budget", "projected_bytes"=>expected_bytes)
    end
    ispath(path) && error("witness already exists")
    open(path,"w") do io
        write(io,codeunits("JSTRUC01")); write(io,Int64(size(B,1)),Int64(nnz(B)))
        write(io,B.colptr); write(io,B.rowval); write(io,B.nzval)
        write(io,result.colmatch); write(io,result.labels)
    end
    WITNESS_BYTES[] += filesize(path)
    Dict("path"=>path,"sha256"=>bytes2hex(open(sha256,path)),"bytes"=>filesize(path))
end

# Independent small-matrix structural matching oracle, exhaustive permutations.
function brute_matching(B)
    n = size(B,1); used = falses(n)
    function walk(j)
        j > n && return true
        for i in 1:n
            if !used[i] && !iszero(B[i,j])
                used[i] = true
                walk(j+1) && return true
                used[i] = false
            end
        end
        false
    end
    walk(1)
end
function graph_sanity()
    for bits in 0:511
        B = sparse([Float64((bits >> ((j-1)*3+i-1)) & 1) for i in 1:3, j in 1:3])
        if brute_matching(B)
            r = structural_blocks(B)
            # Independent Floyd closure verifies strong-component equivalence.
            inv = invperm(r.colmatch); reach = Matrix{Bool}(I,3,3)
            for j in 1:3, k in nzrange(B,j); reach[inv[B.rowval[k]],j] = true; end
            for k in 1:3, i in 1:3, j in 1:3; reach[i,j] |= reach[i,k] && reach[k,j]; end
            @test all(i -> all(j -> (r.labels[i]==r.labels[j]) == (reach[i,j]&&reach[j,i]),1:3),1:3)
        else
            @test_throws ErrorException structural_blocks(B)
        end
    end
    @test structural_blocks(sparse(Matrix{Float64}(I,4,4))).summary["largest_block"] == 1
    @test structural_blocks(sparse(ones(4,4))).summary["largest_block"] == 4
    cycle = spdiagm(0=>ones(10),1=>ones(9)); cycle[10,1]=1.
    @test structural_blocks(cycle).summary["largest_block"] == 10
    @test structural_blocks(spdiagm(0=>ones(10_000))).summary["blocks"] == 10_000
end
