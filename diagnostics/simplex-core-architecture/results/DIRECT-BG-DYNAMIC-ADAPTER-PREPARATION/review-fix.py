"""Single separate offline R1/R2 correction. Original candidate/tests/overlay frozen."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
 with p.open('x') as f:f.write(s)
s=(C/'dynamic-bg.jl').read_text()
old='''@inline function _dbg_value(U,row,col)
    s=_bg_lookup(U,U.row_order[row],U.column_order[col])
    return s==0 ? 0.0 : U.value[s]
end'''
new='''# Hessenberg pivots are at the column tail or its predecessor. Other
# internal storage queries descend in logical-row order, never rescan a row.
@inline function _dbg_entry(U,row,col)
    s=U.column_tail[U.column_order[col]]
    while s!=0 && U.row_position[U.row_id[s]]>row;s=U.column_prev[s];end
    return s!=0 && U.row_position[U.row_id[s]]==row ? s : 0
end
@inline function _dbg_value(U,row,col)
    s=_dbg_entry(U,row,col)
    return s==0 ? 0.0 : U.value[s]
end'''
need(s.count(old)==1,'R1 entry anchor');s=s.replace(old,new)
old='''function _dbg_last_pure(U,first)
    for j in first:U.n-1
        iszero(_dbg_value(U,first,j)) || return j-1
        lower=_dbg_value(U,j+1,j)
        _pivot_magnitude(lower)>zero(lower) || return j-1
    end
    return U.n-1
end'''
new='''function _dbg_last_pure(U,first)
    # Preserve the cheap immediate rejection before scanning the carried row.
    iszero(_dbg_value(U,first,first)) || return first-1
    lower=_dbg_value(U,first+1,first)
    _pivot_magnitude(lower)>zero(lower) || return first-1
    first==U.n-1 && return first
    # Only Float64 reads: find the first future nonzero in logical-column
    # order once. NaN/Inf are nonzero exactly as in the original predicate.
    blocker=U.n;s=U.row_head[U.row_order[first]]
    while s!=0
        col=U.column_position[U.column_id[s]]
        if first<col<blocker && !iszero(U.value[s]);blocker=col;end
        s=U.row_next[s]
    end
    for j in first+1:U.n-1
        j==blocker && return j-1
        lower=_dbg_value(U,j+1,j)
        _pivot_magnitude(lower)>zero(lower) || return j-1
    end
    return U.n-1
end'''
need(s.count(old)==1,'R1 pure anchor');s=s.replace(old,new)
s=s.replace('slot=_bg_lookup(U,U.row_order[j+1],U.column_order[j])','slot=_dbg_entry(U,j+1,j)')
write(C/'dynamic-bg-reviewed.jl',s)
t=(C/'dynamic-bg-tests.jl').read_text()
t=t.replace('for (M,q,a,j) in (','for (M,q,a,j,expected) in (')
t=t.replace('(sparse(reshape([1.],1,1)),[1],[2.],1),','(sparse(reshape([1.],1,1)),[1],[2.],1,Tuple{Int,Int,Bool,Float64}[]),')
t=t.replace('(spdiagm(0=>ones(3)),[3,1,2],[1.,2.,3.],3),','(spdiagm(0=>ones(3)),[3,1,2],[1.,2.,3.],3,[(1,2,true,0.0)]),')
t=t.replace('(sparse([1. 1. 0.;0. 1. 1.;0. 0. 1.]),[1,2,3],[1.,1.,1.],1),','(sparse([1. 1. 0.;0. 1. 1.;0. 0. 1.]),[1,2,3],[1.,1.,1.],1,[(1,1,false,1.0),(2,2,false,1.0)]),')
t=t.replace('(spdiagm(0=>ones(4)),[4,2,1,3],[1.,1.,1.,1.],4),','(spdiagm(0=>ones(4)),[4,2,1,3],[1.,1.,1.,1.],4,[(1,3,true,0.0)]),')
t=t.replace('(sparse([1. 0. 2.;0. 1. 0.;0. 0. 1.]),[1,2,3],[1.,0.,1.],1))','(sparse([1. 0. 2.;0. 1. 0.;0. 0. 1.]),[1,2,3],[1.,0.,1.],1,[(1,1,true,0.0),(2,2,false,0.5)]))')
old='''            @test typeof(er)==typeof(ed)
            if isnothing(er);pair_state(r,d);else;@test _check_bg_slots(d.upper);end'''
new='''            @test isnothing(er) && isnothing(ed)
            @test length(r.updates)==length(d.updates)==1
            @test history(r)==history(d)==[[(a,b,c,reinterpret(UInt64,m)) for (a,b,c,m) in expected]]
            pair_state(r,d)'''
need(t.count(old)==1,'R2 success anchor');t=t.replace(old,new)
old='''            @test typeof(er)==typeof(ed)
            @test isequal(history(r),history(d)) && _check_bg_slots(d.upper)'''
new='''            if nnz(M)==0
                @test er isa ZeroPivotException && ed isa ZeroPivotException
                @test er.info==ed.info==1
            else
                @test isnothing(er) && isnothing(ed)
                @test length(r.updates)==nr+1 && length(d.updates)==nd+1
                @test !d.row_cache.upper_prefix_safe
            end
            @test isequal(history(r),history(d)) && _check_bg_slots(d.upper)'''
need(t.count(old)==1,'R2 failure anchor');t=t.replace(old,new)
anchor='        # Seventeen imported slots, then four new row2 entries: a real fill growth.\n'
addition='''        # Finite inputs, overflow in elimination: max - 1*(-max) = +Inf.
        m=floatmax(Float64);M=sparse([1. 1. -m;0. 1. m;0. 0. 1.])
        @test all(isfinite,M.nzval)
        r,d=controlled_pair(M,[1,2,3])
        er=try J.replace_column!(r,[1.,0.,0.],1;zero_tolerance=0.0);nothing catch e;e end
        ed=try J.replace_column!(d,[1.,0.,0.],1;zero_tolerance=0.0);nothing catch e;e end
        @test isnothing(er) && isnothing(ed)
        @test J._upper_value(r.upper[2],2)==J._dbg_value(d.upper,2,2)==Inf
        @test !r.row_cache.upper_prefix_safe && !d.row_cache.upper_prefix_safe
        pair_state(r,d) # no solve of this nonfinite factor

        # Force distinct physical maps in a TEST-OWNED copied arena. Actual copy
        # preserves its IDs; this deliberate exact rebase exercises the independent
        # upper/history map handoff without changing production copy semantics.
        B=Matrix{Float64}(I,4,4);r,d=controlled_pair(sparse(B),collect(1:4))
        replace_pair!(r,d,B,1,ones(4))
        sr=J.copy_basis_factorization(r);sd=J.copy_basis_factorization(d)
        logical=_bg_selected_state(sd.upper)
        A=SparseMatrixCSC(logical.n,logical.n,copy(logical.colptr),copy(logical.rowval),
            collect(reinterpret(Float64,logical.bits)))
        sd.upper=J._bg_slots(A,copy(sd.upper.column_order))
        J._dbg_sync_rows!(sd);J._sync_triangular_rows!(sr)
        @test sd.upper.row_order!=sd.row_cache.order
        @test J._upper_order(sr.upper).order!=sr.row_cache.order
        solve_pair(sr,sd,B,ones(4));solve_pair(sr,sd,B,ones(4);transposed=true)
        j,a=DirectLUFixtures.replacement(B,1);replace_pair!(sr,sd,B,j,a)
'''
need(t.count(anchor)==1,'R2 witness anchor');t=t.replace(anchor,addition+anchor)
write(C/'dynamic-bg-tests-reviewed.jl',t)
# New separate overlay builder. It reads the same accepted Task1 source.
b=(C/'prepare-adapter.py').read_text().replace('/task2-stage\'','/task2-reviewed-stage\'')
b=b.replace("'dynamic-bg.jl':'src/dynamic-bg.jl'","'dynamic-bg-reviewed.jl':'src/dynamic-bg.jl'").replace("'dynamic-bg-tests.jl':'test/dynamic-bg-tests.jl'","'dynamic-bg-tests-reviewed.jl':'test/dynamic-bg-tests.jl'")
b=b.replace("E/'overlay.json'","E/'overlay-reviewed.json'").replace("E/'preparation-pins.json'","E/'preparation-pins-reviewed.json'")
write(C/'prepare-adapter-reviewed.py',b)
# Separate source binder for corrected artifact, with the old row-lookup symbol
# mapped to its same original reference; text inverse remains explicitly lexical.
b=(E/'bind-source-2.py').read_text().replace("C/'dynamic-bg.jl'","C/'dynamic-bg-reviewed.jl'")
b=b.replace("['_dbg_backsolve!','_dbg_diagonal','_dbg_value']","['_dbg_backsolve!','_dbg_diagonal','_dbg_value','_dbg_entry']")
b=b.replace('reference-excerpts.jl','reference-excerpts-reviewed.jl').replace('reference-to-candidate.patch','reference-to-candidate-reviewed.patch').replace('reference-bindings.json','reference-bindings-reviewed.json')
write(E/'bind-source-reviewed.py',b)
paths=[C/n for n in ['dynamic-bg.jl','dynamic-bg-reviewed.jl','dynamic-bg-tests.jl','dynamic-bg-tests-reviewed.jl','prepare-adapter-reviewed.py']]
write(E/'review-fix.json',json.dumps(dict(scope='ONE separate offline correction for R1/R2; no Julia',initial_review='independent-review-initial.md',checks=dict(original_row_scan_present='_bg_lookup(U,U.row_order[row],U.column_order[col])' in (C/'dynamic-bg.jl').read_text(),new_tail_lookup='_dbg_entry(U,j+1,j)' in s,first_guard_before_blocker=s.index('iszero(_dbg_value(U,first,first))')<s.index('blocker=U.n'),explicit_expected_success='history(r)==history(d)==[' in t,zero_pivot_index='er.info==ed.info==1' in t,finite_overflow='all(isfinite,M.nzval)' in t,independent_maps='sd.upper.row_order!=sd.row_cache.order' in t),sha256={str(p):sha(p) for p in paths}),indent=2)+'\n')
print('Separate R1/R2 candidate/test correction written; UNEXECUTED')
