"""Exclusive offline adapter derivation, with reversible source edit ledger."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
source=R/'diagnostics/direct-bg-dynamic-upper/reproduce/dynamic-bg-reviewed.jl';original=source.read_text()
renames=[('DynamicBGFactor','BlockBGFactor'),('BGSlotUpper','BGBlockUpper'),('_dynamic_bg','_block_bg'),('_dbg_','_bbg_'),('dynamic BG','block BG')]
s=original
for a,b in renames:s=s.replace(a,b)
edits=[]
def edit(a,b):
 global s
 if s.count(a)!=1:raise RuntimeError('Nonunique replacement: '+a[:80])
 edits.append(dict(before=a,after=b));s=s.replace(a,b,1)
def chunk(a,z,b):
 start=s.index(a);end=s.index(z,start);edit(s[start:end],b+'\n')
edit('# Diagnostic Task2 candidate, UNEXECUTED. Dense Float64 direct BG only.\n# Slot primitives are the accepted Task1 candidate. No old method is overwritten.', '# Diagnostic Task2 block candidate, UNEXECUTED. Dense Float64 direct BG only.\n# Frozen Task1 block primitives; explicit private methods, no production overwrite.')
edit('factorize=_factorize_basis) where {R}', 'factorize=_factorize_basis,build=_bgu_build,limit::Integer=typemax(Int32)) where {R}')
edit('    ordinary=factorize(B,backend,policy)', '''    _bgu_limit(Base.Checked.checked_add(size(B,1),1),limit)
    B isa SparseMatrixCSC && !(B isa SparseMatrixCSC{Float64,Int}) &&
        throw(ArgumentError("block BG requires Int CSC indices"))
    ordinary=factorize(B,backend,policy)''')
edit('upper=_bg_slots(spdiagm(0=>ones(n)),collect(1:n))','upper=build(spdiagm(0=>ones(n)),collect(1:n))')
edit('upper=_bg_slots(parts.upper,parts.columns)','upper=build(parts.upper,parts.columns)')
edit('f.upper.live_count','f.upper.live')
chunk('# Cold diagnostic metadata only;', 'function _bbg_dimensions', '''# Cold diagnostic metadata only. No full scan is called by a solve.
function _block_bg_growth(f::BlockBGFactor)
    value=0.0;U=f.upper
    for cid in U.column_order
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);v=U.values[s]
            for p in a:a+Int(U.count[b])-1;value=max(value,abs(v[p]));end
            b=Int(U.next[b])
        end
    end
    return value
end
function _block_bg_finite(f::BlockBGFactor)
    U=f.upper
    for cid in U.column_order
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);v=U.values[s]
            for p in a:a+Int(U.count[b])-1;isfinite(v[p]) || return false;end
            b=Int(U.next[b])
        end
    end
    return true
end
# Reject private new scratch before dimensions/backend. No slab-owner scan.
function _bbg_destination(f,destination)
    (Base.mightalias(destination,f.work) || Base.mightalias(destination,f.upper.scratch_value)) &&
        throw(ArgumentError("destination must not alias factorization work storage"))
    return nothing
end''')
chunk('function _bbg_columns(f)', 'function _bbg_forward!', '''function _bbg_columns(f)
    c=f.row_cache;U=f.upper
    if c.upper_dirty
        first=c.upper_dirty_from
        resize!(c.active_upper,searchsortedfirst(c.active_upper,first)-1)
        for j in first:U.n
            cid=Int(U.column_order[j]);b=Int(U.column_head[cid]);t=Int(U.column_tail[cid])
            count=t==0 ? 0 : Int(U.count[t])
            tail=count==0 ? nothing : _bgu_tuple(U,Int32((t-1)*32+count))
            identity=b!=0 && b==t && count==1 && U.row_position[Int(tail[2])]==j && tail[1]==1.0
            identity || push!(c.active_upper,j)
            if !identity && c.upper_prefix_safe &&
                    (t==0 || U.row_position[Int(tail[2])]!=j || iszero(tail[1]))
                c.upper_prefix_safe=false
            end
        end
        c.upper_dirty=false;c.upper_dirty_from=U.n+1
    end
    return c.active_upper
end
# Descend block prefixes in logical-row order for Hessenberg/missing-diagonal lookup.
@inline function _bbg_entry(U,row,col)
    b=Int(U.column_tail[Int(U.column_order[col])])
    while b!=0
        s=Int(U.slab[b]);a=Int(U.start[b]);rows=U.row_ids[s]
        for k in Int(U.count[b]):-1:1
            logical=Int(U.row_position[Int(rows[a+k-1])])
            logical>row && continue
            return logical==row ? Int32((b-1)*32+k) : Int32(0)
        end
        b=Int(U.prev[b])
    end
    return Int32(0)
end
@inline function _bbg_value(U,row,col)
    h=_bbg_entry(U,row,col);return h==0 ? 0.0 : _bgu_tuple(U,h)[1]
end
@inline function _bbg_tail_diagonal(U,j)
    b=Int(U.column_tail[Int(U.column_order[j])])
    return b!=0 && U.row_ids[Int(U.slab[b])][Int(U.start[b])+Int(U.count[b])-1]==U.row_order[j]
end
@inline function _bbg_diagonal(U,j)
    b=Int(U.column_tail[Int(U.column_order[j])])
    if b!=0
        s=Int(U.slab[b]);p=Int(U.start[b])+Int(U.count[b])-1
        U.row_ids[s][p]==U.row_order[j] && return U.values[s][p]
    end
    return _bbg_value(U,j,j)
end
function _bbg_backsolve!(f,columns)
    U=f.upper;w=f.work
    for j in Iterators.reverse(columns)
        rid=Int(U.row_order[j]);value=w[rid]/_bbg_diagonal(U,j);w[rid]=value
        cid=Int(U.column_order[j]);tail=Int(U.column_tail[cid]);fast=_bbg_tail_diagonal(U,j)
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);values=U.values[s];rows=U.row_ids[s]
            count=Int(U.count[b])-(fast && b==tail ? 1 : 0)
            if fast
                for p in a:a+count-1;w[Int(rows[p])]-=values[p]*value;end
            else
                for p in a:a+count-1
                    row=Int(rows[p]);row==rid && continue;w[row]-=values[p]*value
                end
            end
            b=Int(U.next[b])
        end
    end
    return w
end
function _bbg_transpose_upper!(f,columns,first::Int=1)
    U=f.upper;w=f.work
    for k in first:length(columns)
        j=columns[k];rid=Int(U.row_order[j]);value=w[rid]
        cid=Int(U.column_order[j]);tail=Int(U.column_tail[cid]);fast=_bbg_tail_diagonal(U,j)
        b=Int(U.column_head[cid])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);values=U.values[s];rows=U.row_ids[s]
            count=Int(U.count[b])-(fast && b==tail ? 1 : 0)
            if fast
                for p in a:a+count-1;value-=values[p]*w[Int(rows[p])];end
            else
                for p in a:a+count-1
                    row=Int(rows[p]);row==rid && continue;value-=values[p]*w[row]
                end
            end
            b=Int(U.next[b])
        end
        w[rid]=value/_bbg_diagonal(U,j)
    end
    return w
end''')
# Two distinct methods retain original alias-check ordering.
a='    destination===f.work && throw(ArgumentError("destination must not alias factorization work storage"))'
if s.count(a)!=2:raise RuntimeError('Expected two destination gates')
edits.append(dict(before=a,after='    _bbg_destination(f,destination)',count=2));s=s.replace(a,'    _bbg_destination(f,destination)')
edit('U=f.upper;position=U.column_position[pivot]','U=f.upper;position=Int(U.column_position[pivot])')
chunk('    for j in 1:n\n        value=direction[U.column_order[j]];', '    return position\nend\nfunction _bbg_replace_column!', '''    for j in 1:n
        value=direction[U.column_order[j]];b=Int(U.column_head[Int(U.column_order[j])])
        while b!=0
            s=Int(U.slab[b]);a=Int(U.start[b]);values=U.values[s];rows=U.row_ids[s]
            for p in a:a+Int(U.count[b])-1
                f.spike[Int(U.row_position[Int(rows[p])])]+=values[p]*value
            end
            b=Int(U.next[b])
        end
    end''')
chunk('function _bbg_replace_column!', 'function _block_bg_replace!', '''# Remove whole column blocks without merging/repacking the old column.
function _bbg_clear_column!(U,cid::Int)
    b=Int(U.column_head[cid])
    while b!=0
        following=Int(U.next[b]);count=Int(U.count[b])
        for k in 1:count
            h=Int32((b-1)*32+k);v,r,p=_bgu_tuple(U,h);rid=Int(r)
            rank=Int(p)<U.gap_first[rid] ? Int(p) : Int(p)-Int(U.gap_length[rid])
            _bgu_gap!(U,rid,rank)
            g=Int(U.gap_first[rid]);l=Int(U.gap_length[rid]);U.rows[rid][g+l]=0
            U.gap_length[rid]=Int32(l+1);U.live-=1;_bgu_clear!(U,b,k)
        end
        _bgu_unlink_block!(U,b);b=following
    end
    return nothing
end
function _bbg_replace_column!(f,position,allocate,limit)
    U=f.upper;cid=Int(U.column_order[position]);_bbg_clear_column!(U,cid)
    for row in 1:U.n
        value=f.spike[row];iszero(value) && continue
        _track_upper_value!(f,value);rid=Int(U.row_order[row]);rank,_=_bgu_row_search(U,rid,cid)
        tail=Int(U.column_tail[cid]);pred=tail==0 ? Int32(0) : Int32((tail-1)*32+Int(U.count[tail]))
        _bgu_insert_at!(U,rid,cid,value,rank,pred,allocate,limit)
    end
    for j in position:U.n-1
        moved=U.column_order[j+1];U.column_order[j]=moved;U.column_position[Int(moved)]=Int32(j)
    end
    U.column_order[U.n]=Int32(cid);U.column_position[cid]=Int32(U.n)
    return nothing
end
function _bbg_last_pure(U,first)
    iszero(_bbg_value(U,first,first)) || return first-1
    lower=_bbg_value(U,first+1,first)
    _pivot_magnitude(lower)>zero(lower) || return first-1
    first==U.n-1 && return first
    blocker=U.n;rid=Int(U.row_order[first])
    for rank in 1:_bgu_degree(U,rid)
        h=_bgu_row_handle(U,rid,rank);col=Int(U.column_position[_bgu_cid(U,h)])
        if first<col<blocker && !iszero(_bgu_tuple(U,h)[1]);blocker=col;end
    end
    for j in first+1:U.n-1
        j==blocker && return j-1
        lower=_bbg_value(U,j+1,j)
        _pivot_magnitude(lower)>zero(lower) || return j-1
    end
    return U.n-1
end
# Monotone stable-column merge. Source membership does not change, but handles
# can move on every edit: reload the next source and target from row buffers.
function _bbg_eliminate_row!(f,j,m,visit=nothing;allocate=_bgu_allocate,limit::Integer=typemax(Int32))
    U=f.upper;source=Int(U.row_order[j]);target=Int(U.row_order[j+1]);i=1;k=1
    while i<=_bgu_degree(U,source)
        h=_bgu_row_handle(U,source,i);cid=_bgu_cid(U,h)
        if U.column_position[cid]>j
            isnothing(visit) || visit(cid)
            while k<=_bgu_degree(U,target) && _bgu_cid(U,_bgu_row_handle(U,target,k))<cid;k+=1;end
            t=k<=_bgu_degree(U,target) ? _bgu_row_handle(U,target,k) : Int32(0)
            present=t!=0 && _bgu_cid(U,t)==cid
            old=present ? _bgu_tuple(U,t)[1] : 0.0
            value=_track_upper_value!(f,old-m*_bgu_tuple(U,h)[1])
            if present
                if iszero(value)
                    _bgu_delete!(U,target,k,t)
                else
                    b,offset=_bgu_decode(t);U.values[Int(U.slab[b])][Int(U.start[b])+offset-1]=value;k+=1
                end
            elseif !iszero(value)
                _bgu_insert_at!(U,target,cid,value,k,h,allocate,limit);k+=1
            end
        end
        i+=1
    end
    return nothing
end
function _bbg_delete_handle!(U,h::Int32)
    v,r,p=_bgu_tuple(U,h);rid=Int(r)
    rank=Int(p)<U.gap_first[rid] ? Int(p) : Int(p)-Int(U.gap_length[rid])
    _bgu_delete!(U,rid,rank,h);return nothing
end''')
edit('function _block_bg_replace!(f,direction,pivot_row,zero_tolerance)','function _block_bg_replace!(f,direction,pivot_row,zero_tolerance;allocate=_bgu_allocate,limit::Integer=typemax(Int32))')
edit('_bbg_begin_update!(f,position);_bbg_replace_column!(f,position)','_bbg_begin_update!(f,position);_bbg_replace_column!(f,position,allocate,limit)')
edit('_bg_rotate_rows!(U,j,last_pure+1)','_bgu_rotate_rows!(U,j,last_pure+1)')
edit('_bg_swap_rows!(U,j)','_bgu_swap_rows!(U,j)')
edit('old=slot==0 ? 0.0 : U.value[slot];multiplier=old/pivot','old=slot==0 ? 0.0 : _bgu_tuple(U,slot)[1];multiplier=old/pivot')
edit('slot==0 || _bg_unlink!(U,slot)','slot==0 || _bbg_delete_handle!(U,slot)')
edit('iszero(multiplier) || _bbg_eliminate_row!(f,j,multiplier)','iszero(multiplier) || _bbg_eliminate_row!(f,j,multiplier;allocate,limit)')
chunk('function copy_basis_factorization(f::BlockBGFactor)', 'function _block_bg_refactor_with_exporter!', '''function _block_bg_copy_with(f::BlockBGFactor,copier)
    # All allocations first; shared-prefix bookkeeping changes only on success.
    upper=copier(f.upper);shared=length(f.updates)
    candidate=BlockBGFactor(_copy_backend(f.base),upper,copy(f.updates),similar(f.work),similar(f.spike),
        BartelsGolubUpdate{Float64}[],shared,_copy_triangular_row_cache(f))
    f.shared_update_count=shared;return candidate
end
copy_basis_factorization(f::BlockBGFactor)=_block_bg_copy_with(f,_bgu_copy)''')
edit('function _block_bg_refactor_with_exporter!(f::BlockBGFactor,B::AbstractMatrix{Float64},exporter)','function _block_bg_refactor_with_exporter!(f::BlockBGFactor,B::AbstractMatrix{Float64},exporter;build=_bgu_build)')
edit('exporter;normalize=f.base.normalize_requested)','exporter;normalize=f.base.normalize_requested,build)')
# Exact reverse of every declared edit and rename proves provenance, not semantics.
inv=s
for e in reversed(edits):
 count=e.get('count',1)
 if inv.count(e['after'])!=count:raise RuntimeError('Inverse mismatch: '+e['after'][:80])
 inv=inv.replace(e['after'],e['before'])
for a,b in reversed(renames):inv=inv.replace(b,a)
if inv!=original:raise RuntimeError('Whole inverse differs')
with (C/'block-bg.jl').open('x') as f:f.write(s)
record=dict(scope='Exact textual inverse, not a numerical or Julia parse proof',reference=str(source),reference_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(s.encode()).hexdigest(),renames=renames,edits=edits,whole_inverse=True,self_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (E/'adapter-inverse.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('UNEXECUTED adapter written; whole-source inverse exact;',len(edits),'edits')
