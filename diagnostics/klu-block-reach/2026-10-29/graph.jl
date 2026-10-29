# Pure structural dependencies; exact-zero edges only. Not a numerical skip admission.
struct BlockCSR
    ptr::Vector{Int}
    target::Vector{Int}
    nonzero::Vector{UInt8}
end
function reverse_graph(g::BlockCSR)
    n=length(g.ptr)-1;c=zeros(Int,n)
    for t in g.target;c[t]+=1;end
    p=Vector{Int}(undef,n+1);p[1]=1
    for i in 1:n;p[i+1]=p[i]+c[i];end
    next=copy(p);t=similar(g.target);z=similar(g.nonzero)
    for i in 1:n,k in g.ptr[i]:(g.ptr[i+1]-1)
        a=g.target[k];j=next[a];t[j]=i;z[j]=g.nonzero[k];next[a]+=1
    end
    BlockCSR(p,t,z)
end
function reach(g::BlockCSR,seeds)
    n=length(g.ptr)-1;seen=falses(n);queue=Int[];visits=0
    for s in seeds
        if !seen[s];seen[s]=true;push!(queue,s);end
    end
    head=1
    while head<=length(queue)
        a=queue[head];head+=1
        for k in g.ptr[a]:(g.ptr[a+1]-1)
            visits+=1
            if g.nonzero[k]!=0
                b=g.target[k]
                if !seen[b];seen[b]=true;push!(queue,b);end
            end
        end
    end
    seen,visits
end
function measure_reach(g,rg,dims,lustored,seeds,transposed)
    seen,visits=reach(transposed ? rg : g,seeds)
    lu=sum((lustored[i]-dims[i] for i in eachindex(dims) if seen[i]);init=0)
    stored=sum((lustored[i] for i in eachindex(dims) if seen[i]);init=0)
    fcols=sum((g.ptr[i+1]-g.ptr[i] for i in eachindex(dims) if seen[i]);init=0)
    Dict("seed_blocks"=>length(unique(seeds)),"active_blocks"=>count(seen),
        "active_rows"=>sum(dims[seen]),"active_LU_stored"=>stored,"active_LU_visits"=>lu,
        "active_F_column_visits"=>fcols,"active_dependency_visits"=>visits,
        "block_solve_coefficient_visits"=>lu+fcols,
        "edge_aware_coefficient_visits"=>lu+visits)
end
function classify_change(rowblock,targetblock,rows,old,new)
    own=0;above=0;below=0;scale=0
    for k in eachindex(rows)
        isequal(old[k],new[k]) && continue
        b=rowblock[rows[k]]
        if b==targetblock;own+=1;elseif b<targetblock;above+=1;else;below+=1;end
        abs(old[k])!=abs(new[k]) && (scale+=1)
    end
    Dict("diagonal_block_changed_entries"=>own,"above_block_changed_entries"=>above,
        "below_block_changed_entries"=>below,"potential_changed_row_sum_scales"=>scale,
        "preserves_old_upper_partition"=>below==0,
        "couplings_only_fixed_maps_scales"=>below==0 && own==0)
end
function graph_tests()
    # All 3-vertex upper-block DAGs, all seed subsets, independent Floyd closure.
    for edges in 0:7
        targets=Int[];flags=UInt8[];ptr=Int[1];R=Matrix{Bool}(I,3,3);bit=0
        for j in 1:3
            for i in 1:(j-1)
                if ((edges>>bit)&1)==1;push!(targets,i);push!(flags,1);R[j,i]=true;end
                bit+=1
            end
            push!(ptr,length(targets)+1)
        end
        for k in 1:3,i in 1:3,j in 1:3;R[i,j]|=R[i,k]&&R[k,j];end
        g=BlockCSR(ptr,targets,flags);rg=reverse_graph(g)
        for bits in 0:7
            seed=findall(i->((bits>>(i-1))&1)==1,1:3)
            @test first(reach(g,seed))==[any(s->R[s,j],seed) for j in 1:3]
            @test first(reach(rg,seed))==[any(s->R[j,s],seed) for j in 1:3]
        end
    end
    # Explicit zero coupling and duplicate edges must not create false reach.
    g=BlockCSR([1,1,4,5],[1,1,1,2],UInt8[0,1,1,0])
    @test first(reach(g,[3]))==Bool[0,0,1]
    @test first(reach(g,[2]))==Bool[1,1,0]
    a=classify_change([1,2,3],2,[1],[1.],[2.]);@test a["couplings_only_fixed_maps_scales"]
    a=classify_change([1,2,3],2,[2],[1.],[2.]);@test a["preserves_old_upper_partition"] && !a["couplings_only_fixed_maps_scales"]
    a=classify_change([1,2,3],2,[3],[0.],[1.]);@test !a["preserves_old_upper_partition"]
end
