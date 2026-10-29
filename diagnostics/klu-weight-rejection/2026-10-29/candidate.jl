# Isolated shared full-base context, Float64/Int64 only; no production inclusion.
mutable struct BiContext{C}
    forward::C
    inverseQ::Vector{Int}
    rowptr::Vector{Int}
    positions::Vector{Int}
    columns::Vector{Int}
    weights::Vector{Int}
    valid::Bool
    paths::Vector{Int}
end
function reverse_index(c::NativeOnly)
    BiContext(c,Int[],Int[],Int[],Int[],Int[],true,zeros(Int,7))
end
function reverse_index(c::GraphContext)
    p=c.parts;n=length(c.rhs);nf=length(p.Fi);ptr=zeros(Int,n+1)
    for i in p.Fi;ptr[i+1]+=1;end
    for i in 1:n;ptr[i+1]+=ptr[i];end
    ptr .+= 1;next=copy(ptr);pos=Vector{Int}(undef,nf);cols=similar(pos)
    for j in 1:n,k in p.Fp[j]:p.Fp[j+1]-1
        i=p.Fi[k];at=next[i];pos[at]=k;cols[at]=j;next[i]+=1
    end
    weights=zeros(Int,length(c.weights))
    for j in 1:n
        weights[c.block[j]]+=p.Lp[j+1]-p.Lp[j]+p.Up[j+1]-p.Up[j]-1+ptr[j+1]-ptr[j]
    end
    BiContext(c,invperm(p.Q),ptr,pos,cols,weights,true,zeros(Int,7))
end
function markpath!(b,path)
    b.forward.last_path=path;b.paths[path]+=1;nothing
end
function bguards(dest,b,rhs)
    c=b.forward;n=length(c.rhs)
    length(dest)==length(rhs)==n||throw(DimensionMismatch())
    owners=c isa GraphContext ? (c.rhs,c.work,c.native.nzval,c.parts.Lx,c.parts.Ux,c.parts.Fx,c.parts.Rs) : (c.rhs,c.native.nzval)
    any(v->overlaps(dest,v)||overlaps(rhs,v),owners)&&throw(ArgumentError("arguments alias private factor/scratch"))
    nothing
end
function native_btran!(dest,b,rhs,path)
    copyto!(dest,rhs);KLU.solve!(transpose(b.forward.native),dest);markpath!(b,path);dest
end
function generic_btran!(dest,b,rhs)
    bguards(dest,b,rhs)
    # Dense/unknown RHS is never labeled unit. Save original input before output.
    copyto!(b.forward.rhs,rhs);native_btran!(dest,b,b.forward.rhs,3)
end
function enqueue_transpose!(b,node)
    c=b.forward;c.marks[node]==c.epoch&&return
    c.marks[node]=c.epoch;c.scheduled+=b.weights[node];c.used+=1;i=c.used
    @inbounds while i>1
        parent=i>>1;c.heap[parent]<=node&&break
        c.heap[i]=c.heap[parent];i=parent
    end
    @inbounds c.heap[i]=node
end
function pop_transpose!(c)
    @inbounds node=c.heap[1];v=c.heap[c.used];c.used-=1;i=1
    @inbounds while 2i<=c.used
        j=2i;j<c.used&&c.heap[j]>c.heap[j+1]&&(j+=1)
        c.heap[j]>=v&&break
        c.heap[i]=c.heap[j];i=j
    end
    c.used>0&&(@inbounds c.heap[i]=v);node
end
function transpose_block!(b,node,::Val{LOCAL}) where LOCAL
    c=b.forward;p=c.parts;w=c.work;lo=p.R[node];hi=p.R[node+1]-1
    @inbounds for j in lo:hi
        value=w[j]
        for k in p.Up[j]:p.Up[j+1]-2;value-=p.Ux[k]*w[p.Ui[k]];end
        value/=p.Ux[p.Up[j+1]-1];isfinite(value)||return false;w[j]=value
    end
    @inbounds for j in hi:-1:lo
        value=w[j]
        for k in p.Lp[j]+1:p.Lp[j+1]-1;value-=p.Lx[k]*w[p.Li[k]];end
        isfinite(value)||return false;w[j]=value
    end
    @inbounds for i in lo:hi,k in b.rowptr[i]:b.rowptr[i+1]-1
        fk=b.positions[k];j=b.columns[k];w[j]-=p.Fx[fk]*w[i]
        if LOCAL&&!iszero(p.Fx[fk]);enqueue_transpose!(b,c.block[j]);end
    end
    true
end
# Producer owns and constructs the complete unit RHS in this call. No forged support tag.
function unit_btran!(dest,b,rhs,row,::Val{MODE}) where MODE
    bguards(dest,b,rhs);overlaps(dest,rhs)&&throw(ArgumentError("unit producer buffers overlap"));checkbounds(rhs,row)
    fill!(rhs,0.0);rhs[row]=1.0;c=b.forward;c.last_blocks=0;c.last_weight=0
    (!b.valid||(c isa GraphContext&&!c.valid))&&return native_btran!(dest,b,rhs,6)
    (c isa NativeOnly||MODE==:native)&&return native_btran!(dest,b,rhs,2)
    p=c.parts;n=length(rhs);c.used=0;c.scheduled=0
    if c.epoch==typemax(UInt32);fill!(c.marks,0);c.epoch=1;else;c.epoch+=1;end
    if MODE==:full
        @inbounds for j in 1:n;c.work[j]=rhs[p.Q[j]];end
        for node in eachindex(c.weights)
            c.last_blocks+=1;c.last_weight+=b.weights[node]
            transpose_block!(b,node,Val(false))||return native_btran!(dest,b,rhs,5)
        end
        path=7
    else
        fill!(c.work,0.0);pos=b.inverseQ[row];c.work[pos]=1.0;enqueue_transpose!(b,c.block[pos])
        while c.used>0
            4c.scheduled>=3c.fullweight&&return native_btran!(dest,b,rhs,4)
            node=pop_transpose!(c);c.last_blocks+=1;c.last_weight+=b.weights[node]
            transpose_block!(b,node,Val(true))||return native_btran!(dest,b,rhs,5)
        end
        path=1
    end
    @inbounds for j in 1:n
        value=c.work[j]/p.Rs[j]
        isfinite(value)||return native_btran!(dest,b,rhs,5)
        dest[p.P[j]]=value
    end
    markpath!(b,path);dest
end
function replace_bbase!(b,B)
    size(B)==(length(b.forward.rhs),length(b.forward.rhs))||throw(DimensionMismatch())
    f=make_factor(B) # failure leaves previous native/cache state untouched
    b.valid=false;b.forward.native=f
    b.forward isa GraphContext&&(b.forward.valid=false)
    b
end
mutable struct WeightFactor{C}
    ctx::C
    updates::Vector{JSimplex.PackedEta{Float64}}
    generic_calls::Int
end
function JSimplex.transpose_solve!(dest::Vector{Float64},f::WeightFactor,rhs::Vector{Float64})
    f.generic_calls+=1;generic_btran!(dest,f.ctx,rhs)
end
# No global method overwrite; only this private new factor type gets methods.

function metadata_stage(p,n)
    nb=length(p.R)-1;block=zeros(Int,n);weight=zeros(Int,nb)
    @assert p.R[1]==1 && p.R[end]==n+1 && all(>(0),diff(p.R))
    @assert sort(p.P)==collect(1:n) && sort(p.Q)==collect(1:n)
    @assert all(isfinite,p.Lx) && all(isfinite,p.Ux) && all(isfinite,p.Fx) && all(v->isfinite(v)&&v>0,p.Rs)
    for b in 1:nb,j in p.R[b]:p.R[b+1]-1
        block[j]=b
        weight[b]+=p.Lp[j+1]-p.Lp[j]+p.Up[j+1]-p.Up[j]-1+p.Fp[j+1]-p.Fp[j]
    end
    @assert all(p.Li[p.Lp[j]]==j && p.Lx[p.Lp[j]]==1 for j in 1:n)
    @assert all(p.Ui[p.Up[j+1]-1]==j && p.Ux[p.Up[j+1]-1]!=0 for j in 1:n)
    @assert all(j<=p.Li[k] && block[j]==block[p.Li[k]] for j in 1:n for k in p.Lp[j]:p.Lp[j+1]-1)
    @assert all(p.Ui[k]<=j && block[j]==block[p.Ui[k]] for j in 1:n for k in p.Up[j]:p.Up[j+1]-1)
    @assert all(block[p.Fi[k]]<block[j] for j in 1:n for k in p.Fp[j]:p.Fp[j+1]-1)
    (rowpos=invperm(p.P),block=block,weights=weight,fullweight=sum(weight))
end
function graph_scratch(f,p,m,n)
    GraphContext(f,zeros(n),p,m.rowpos,m.block,m.weights,zeros(n),zeros(UInt32,length(m.weights)),zeros(Int,length(m.weights)),0,UInt32(0),0,m.fullweight,true,0,0,0)
end
function prepare_staged(B;minimum_dimension=4096)
    t1=@timed make_factor(B);f=t1.value;n=size(B,1)
    if n<minimum_dimension||f.nblocks<=1
        t4=@timed NativeOnly(f,zeros(n),0,0,0);t5=@timed reverse_index(t4.value)
        return t5.value,(factor=t1,scratch=t4,reverse=t5)
    end
    t2=@timed export_once(f);p=t2.value
    t3=@timed metadata_stage(p,n);m=t3.value
    t4=@timed graph_scratch(f,p,m,n)
    t5=@timed reverse_index(t4.value)
    t5.value,(factor=t1,extraction=t2,metadata=t3,scratch=t4,reverse=t5)
end
