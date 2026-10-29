# Isolated Float64/Int64 fixed-base experiment; never included by production.
mutable struct NativeOnly
    native::KLU.KLUFactorization{Float64,Int}
    rhs::Vector{Float64}
    last_path::Int
    last_blocks::Int
    last_weight::Int
end
mutable struct GraphContext{P}
    native::KLU.KLUFactorization{Float64,Int}
    rhs::Vector{Float64}
    parts::P
    rowpos::Vector{Int}
    block::Vector{Int}
    weights::Vector{Int}
    work::Vector{Float64}
    marks::Vector{UInt32}
    heap::Vector{Int}
    used::Int
    epoch::UInt32
    scheduled::Int
    fullweight::Int
    valid::Bool
    last_path::Int
    last_blocks::Int
    last_weight::Int
end
function prepare(B; minimum_dimension=4096)
    f=make_factor(B);n=size(B,1)
    if n<minimum_dimension || f.nblocks<=1
        return NativeOnly(f,zeros(n),0,0,0)
    end
    p=export_once(f);nb=length(p.R)-1;block=zeros(Int,n);weight=zeros(Int,nb)
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
    GraphContext(f,zeros(n),p,invperm(p.P),block,weight,zeros(n),zeros(UInt32,nb),zeros(Int,nb),0,UInt32(0),0,sum(weight),true,0,0,0)
end
# Pointer intervals also reject partial unsafe_wrap overlaps; all owners held alive.
function overlaps(a::Vector{Float64},b::Vector{Float64})
    isempty(a) || isempty(b) ? false : GC.@preserve a b begin
        pa=UInt(pointer(a));pb=UInt(pointer(b));na=UInt(sizeof(a));nb=UInt(sizeof(b))
        pa<=pb ? pb-pa<na : pa-pb<nb
    end
end
function guards(dest,c,A,e)
    n=length(c.rhs);size(A,1)==n && length(dest)==n || throw(DimensionMismatch())
    1<=e<=size(A,2)+n || throw(BoundsError(A,e))
    any(v->overlaps(dest,v),(c.rhs,A.nzval,c.native.nzval)) && throw(ArgumentError("destination aliases private/source storage"))
    overlaps(A.nzval,c.rhs) && throw(ArgumentError("source aliases RHS"))
    nothing
end
function guards(dest,c::GraphContext,A,e)
    n=length(c.rhs);size(A,1)==n && length(dest)==n || throw(DimensionMismatch())
    1<=e<=size(A,2)+n || throw(BoundsError(A,e))
    p=c.parts
    any(v->overlaps(dest,v),(c.rhs,A.nzval,c.native.nzval,c.work,p.Lx,p.Ux,p.Fx,p.Rs)) && throw(ArgumentError("destination aliases private/source storage"))
    (overlaps(A.nzval,c.rhs)||overlaps(A.nzval,c.work)) && throw(ArgumentError("source aliases scratch"))
    nothing
end
function rhs!(c,A,e)
    fill!(c.rhs,0.)
    if e<=size(A,2)
        for k in nzrange(A,e);c.rhs[A.rowval[k]]=A.nzval[k];end
    else
        c.rhs[e-size(A,2)]=-1.
    end
end
function native!(dest,c,path)
    c.last_path=path;copyto!(dest,c.rhs);KLU.solve!(c.native,dest);dest
end
function column_ftran!(dest,c::NativeOnly,A,e,::Val)
    guards(dest,c,A,e);rhs!(c,A,e);c.last_blocks=0;c.last_weight=0;native!(dest,c,2)
end
function enqueue!(c,b)
    c.marks[b]==c.epoch && return
    c.marks[b]=c.epoch;c.scheduled+=c.weights[b];c.used+=1;i=c.used
    @inbounds while i>1
        parent=i>>1;c.heap[parent]>=b && break
        c.heap[i]=c.heap[parent];i=parent
    end
    @inbounds c.heap[i]=b
end
function popblock!(c)
    @inbounds b=c.heap[1];v=c.heap[c.used];c.used-=1;i=1
    @inbounds while 2i<=c.used
        j=2i;j<c.used && c.heap[j]<c.heap[j+1] && (j+=1)
        c.heap[j]<=v && break
        c.heap[i]=c.heap[j];i=j
    end
    c.used>0 && (@inbounds c.heap[i]=v);b
end
# Match exported CSC order in both controls. Reach propagation is fused with F.
function solveblock!(c,b,::Val{LOCAL}) where LOCAL
    p=c.parts;w=c.work;lo=p.R[b];hi=p.R[b+1]-1
    @inbounds for j in lo:hi
        v=w[j];isfinite(v) || return false
        for k in p.Lp[j]+1:p.Lp[j+1]-1;w[p.Li[k]]-=p.Lx[k]*v;end
    end
    @inbounds for j in hi:-1:lo
        v=w[j]/p.Ux[p.Up[j+1]-1];isfinite(v) || return false;w[j]=v
        for k in p.Up[j]:p.Up[j+1]-2;w[p.Ui[k]]-=p.Ux[k]*v;end
    end
    @inbounds for j in lo:hi,k in p.Fp[j]:p.Fp[j+1]-1
        w[p.Fi[k]]-=p.Fx[k]*w[j]
        if LOCAL && !iszero(p.Fx[k]);enqueue!(c,c.block[p.Fi[k]]);end
    end
    true
end
function column_ftran!(dest,c::GraphContext,A,e,mode::Val{MODE}) where MODE
    guards(dest,c,A,e);rhs!(c,A,e);c.last_blocks=0;c.last_weight=0
    !c.valid && return native!(dest,c,6)
    n=length(dest);p=c.parts
    countstored=e<=size(A,2) ? A.colptr[e+1]-A.colptr[e] : 1
    MODE==:local && 2countstored>=n && return native!(dest,c,3)
    c.used=0;c.scheduled=0
    if c.epoch==typemax(UInt32);fill!(c.marks,0);c.epoch=1;else;c.epoch+=1;end
    if MODE==:full
        @inbounds for j in 1:n;c.work[j]=c.rhs[p.P[j]]/p.Rs[j];end
        for b in length(c.weights):-1:1
            c.last_blocks+=1;c.last_weight+=c.weights[b]
            solveblock!(c,b,Val(false)) || return native!(dest,c,5)
        end
        c.last_path=7
    else
        fill!(c.work,0.)
        if e<=size(A,2)
            for k in nzrange(A,e)
                v=A.nzval[k];(!isfinite(v)||(iszero(v)&&signbit(v))) && return native!(dest,c,5)
                if !iszero(v)
                    pos=c.rowpos[A.rowval[k]];z=v/p.Rs[pos];isfinite(z)||return native!(dest,c,5)
                    c.work[pos]=z;enqueue!(c,c.block[pos])
                end
            end
        else
            pos=c.rowpos[e-size(A,2)];z=-1.0 / p.Rs[pos];isfinite(z)||return native!(dest,c,5)
            c.work[pos]=z;enqueue!(c,c.block[pos])
        end
        while c.used>0
            4c.scheduled>=3c.fullweight && return native!(dest,c,4)
            b=popblock!(c);c.last_blocks+=1;c.last_weight+=c.weights[b]
            solveblock!(c,b,Val(true)) || return native!(dest,c,5)
        end
        c.last_path=1
    end
    @inbounds for j in 1:n;dest[p.Q[j]]=c.work[j];end
    dest
end
function replace_native!(c::GraphContext,B)
    size(B)==(length(c.rhs),length(c.rhs))||throw(DimensionMismatch())
    f=make_factor(B) # failure preserves all previous state
    c.valid=false;c.native=f;c
end
function dense_ftran!(dest,c,rhs)
    length(rhs)==length(c.rhs)==length(dest)||throw(DimensionMismatch())
    private = c isa GraphContext ? (c.rhs,c.native.nzval,c.work,c.parts.Lx,c.parts.Ux,c.parts.Fx,c.parts.Rs) : (c.rhs,c.native.nzval)
    any(v->overlaps(dest,v),private) && throw(ArgumentError("destination aliases private storage"))
    overlaps(rhs,c.rhs)&&throw(ArgumentError("input aliases private RHS"))
    copyto!(c.rhs,rhs);native!(dest,c,3)
end
