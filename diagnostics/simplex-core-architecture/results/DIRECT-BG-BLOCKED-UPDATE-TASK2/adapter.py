from pathlib import Path
import re,json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def put(n,s):
 with (C/n).open('x') as f:f.write(s)
source=(R/'src/triangular_factorization.jl').read_text();start=source.index('    run_start = 0',source.index('function replace_column!(factor::BartelsGolubFactorization'))
end=source.index('    push!(factor.updates, BartelsGolubUpdate{T}(steps))',start)
original=source[start:end];scalar=original.replace('position','r').replace('{T}','{Float64}').replace('zero(T)','zero(Float64)')
symbols=sorted(set(re.findall(r'\b_[A-Za-z_]+!?',scalar))|{'BartelsGolubStep'},key=len,reverse=True)
for name in symbols:scalar=re.sub(r'(?<![\w.])'+re.escape(name)+r'(?![\w!])','J.'+name,scalar)
injections=[('        if last_pure > column_index\n','            _emit(probe,:pure,column_index,last_pure)\n'),('        if swapped\n','            # swap is observed below before mutating live rows\n')]
# Only two optional cold events; no replacement arithmetic or original tests.
scalar=scalar.replace('        if last_pure > column_index\n','        if last_pure > column_index\n            _emit(probe,:pure,column_index,last_pure)\n',1)
anchor='        if swapped\n';scalar=scalar.replace(anchor,'        _emit(probe,:scalar_pivot,column_index,J._upper_value(column,column_index),\n              J._upper_value(column,column_index+1),swapped)\n'+anchor,1)
header=r'''# UNEXECUTED experimental Task2 adapter; no production method overwrite.
module BGBlockedAdapter
import ..JSimplex, ..BGBlockedPanel
using LinearAlgebra, SparseArrays
const J=JSimplex
const K=BGBlockedPanel
const Workspace=K.BGPanelWorkspace{K.BGNoCounts}
mutable struct BGPanelFactor{I}
    inner::I
    workspace::Union{Nothing,Workspace}
    busy::Bool
end
@inline _emit(::Nothing,args...)=nothing
@inline _emit(p,args...)=p(args...)
@inline function _idle(f)
    f.busy && throw(ArgumentError("BG blocked workspace is busy"))
    nothing
end
function _input(B::AbstractMatrix{Float64},::Val{R},policy) where R
    ((R===:native && policy===J._NATIVE_PIVOT_ONE) ||
     (R===:markowitz && policy===J._NATIVE_PIVOT_DEFAULT)) || throw(ArgumentError("unsupported BG policy"))
    B isa SparseMatrixCSC && !(B isa SparseMatrixCSC{Float64,Int}) && throw(ArgumentError("Int CSC required"))
end
function _bgb_factor(B::AbstractMatrix{Float64},backend::Val,policy)
    _input(B,backend,policy)
    BGPanelFactor(J._direct_lu_factor(J.BartelsGolubFactorization,B,backend,policy),nothing,false)
end
function _failed!(f)
    f.workspace=nothing
    J._invalidate_sparse_upper!(f.inner,1)
    f.inner.row_columns_ready=false
    f.inner.row_cache.upper_prefix_candidate=false
    f.inner.row_cache.upper_prefix_safe=false
    nothing
end
function _workspace!(f)
    n=length(f.inner.upper);ws=f.workspace
    if ws===nothing || size(ws.values,1)!=n
        ws=K.BGPanelWorkspace(n);f.workspace=ws
    end
    ws
end
# Exact original suffix with namespace/Float64/r substitutions and cold events.
function _bgb_scalar_suffix!(factor,r,steps,probe=nothing)
    n=length(factor.upper);columns_by_row=factor.row_columns
'''
tail=r'''    nothing
end
function _bgb_eliminate!(f,r,steps,probe,blocked)
    inner=f.inner;n=length(inner.upper)
    while r<n
        # Preserve original pure-run optimization instead of crossing its boundary.
        if !blocked || J._last_pure_bartels_golub_swap(inner.upper,r)>r
            _emit(probe,:scalar_suffix,r)
            _bgb_scalar_suffix!(inner,r,steps,probe)
            break
        end
        _emit(probe,:eligibility,r)
        d=K._bgb_eligibility(inner,r)
        if !d.accepted
            d.finite || (inner.row_cache.upper_prefix_candidate=false)
            _emit(probe,:panel_reject,d)
            _emit(probe,:scalar_suffix,r)
            _bgb_scalar_suffix!(inner,r,steps,probe)
            break
        end
        ws=_workspace!(f)
        _emit(probe,:panel_begin,r,d.count)
        K._bgb_gather!(ws,inner,r,d.count)
        pivot_probe=probe===nothing ? nothing : (k,a,z,s)->_emit(probe,:panel_pivot,k,a,z,s)
        d=K._bgb_apply!(ws,r,d.count,n-r+1,pivot_probe)
        if d.accepted;d=K._bgb_commit!(inner,ws,d);end
        if !d.accepted
            d.finite || (inner.row_cache.upper_prefix_candidate=false)
            _emit(probe,:panel_reject,d)
            _emit(probe,:scalar_suffix,r)
            _bgb_scalar_suffix!(inner,r,steps,probe)
            break
        end
        for k in 1:d.count
            step=ws.steps[k]
            (step.swapped || !iszero(step.multiplier)) && push!(steps,step)
        end
        _emit(probe,:panel_commit,d)
        r+=d.count
    end
    nothing
end
function _bgb_replace!(f::BGPanelFactor,direction::Vector{Float64},row::Integer;
        zero_tolerance::Real=J._positive_tolerance(Float64,1//10^12),probe=nothing,blocked=true)
    _idle(f);f.busy=true
    try
        inner=f.inner
        r=J._prepare_spike!(inner,direction,row,zero_tolerance)
        J._begin_upper_update!(inner,r)
        J._ensure_bartels_golub_incidence!(inner)
        J._replace_bartels_golub_incidence_column!(inner,r)
        J._rotate_columns!(inner,r)
        fill!(inner.spike,0.0)
        steps=J._take_bartels_golub_steps!(inner)
        _emit(probe,:begin,inner)
        _bgb_eliminate!(f,r,steps,probe,blocked)
        push!(inner.updates,J.BartelsGolubUpdate{Float64}(steps))
        _emit(probe,:finish,inner,steps)
        J._finish_upper_update!(inner)
        f
    catch
        _failed!(f);rethrow()
    finally
        f.busy=false
    end
end
# Cold microtest entry accepts post-rotation H, not a public basis replacement.
function _bgb_test_eliminate!(f::BGPanelFactor,r;probe=nothing)
    _idle(f);f.busy=true
    try
        inner=f.inner;J._begin_upper_update!(inner,r)
        J._ensure_bartels_golub_incidence!(inner);fill!(inner.spike,0.0)
        steps=J._take_bartels_golub_steps!(inner);_emit(probe,:begin,inner)
        _bgb_eliminate!(f,r,steps,probe,true)
        push!(inner.updates,J.BartelsGolubUpdate{Float64}(steps))
        _emit(probe,:finish,inner,steps);J._finish_upper_update!(inner);f
    catch
        _failed!(f);rethrow()
    finally
        f.busy=false
    end
end
# Ordinary reference, same preamble/end; no panel, no persistent wrapper scratch.
function _bgb_reference_replace!(inner,direction,row;probe=nothing)
    f=BGPanelFactor(inner,nothing,false)
    _bgb_replace!(f,direction,row;probe,blocked=false)
    inner
end
function J.refactorize!(f::BGPanelFactor,B::AbstractMatrix{Float64})
    _idle(f);f.busy=true
    try
        _input(B,Val(J._direct_requested_backend(f.inner.base)),f.inner.base.pivot_policy)
        oldn=length(f.inner.upper)
        J.refactorize!(f.inner,B)
        n=length(f.inner.upper)
        if n!=oldn || !(64<=n<=4096);f.workspace=nothing;end
        f
    catch
        _failed!(f);rethrow()
    finally
        f.busy=false
    end
end
function J.copy_basis_factorization(f::BGPanelFactor)
    _idle(f)
    BGPanelFactor(J.copy_basis_factorization(f.inner),nothing,false)
end
# Fixed concrete surface: no extra solve, conversion, input copy or scan.
function J.forward_solve!(out::Vector{Float64},f::BGPanelFactor,rhs::Vector{Float64})
    _idle(f);J.forward_solve!(out,f.inner,rhs)
end
function J.transpose_solve!(out::Vector{Float64},f::BGPanelFactor,rhs::Union{Vector{Float64},J._UnitTransposeRHS{Float64}})
    _idle(f);J.transpose_solve!(out,f.inner,rhs)
end
function J._ordinary_forward_solve!(out::Vector{Float64},f::BGPanelFactor,rhs::Vector{Float64})
    _idle(f);J._ordinary_forward_solve!(out,f.inner,rhs)
end
J.forward_solve(f::BGPanelFactor,rhs::Vector{Float64})=(_idle(f);J.forward_solve(f.inner,rhs))
J.transpose_solve(f::BGPanelFactor,rhs::Vector{Float64})=(_idle(f);J.transpose_solve(f.inner,rhs))
J._unit_transpose_rhs(f::BGPanelFactor,rhs::Vector{Float64},row::Int)=J._unit_transpose_rhs(f.inner,rhs,row)
J.replace_column!(f::BGPanelFactor,direction::Vector{Float64},row::Integer;zero_tolerance::Real=J._positive_tolerance(Float64,1//10^12))=_bgb_replace!(f,direction,row;zero_tolerance)
J._direct_mode(f::BGPanelFactor)=J._direct_mode(f.inner)
J._backend_dimension(f::BGPanelFactor)=J._backend_dimension(f.inner.base)
J._factor_storage_count(f::BGPanelFactor)=J._factor_storage_count(f.inner)
J._factor_growth_measure(f::BGPanelFactor)=J._factor_growth_measure(f.inner)
J._factor_growth_reference(f::BGPanelFactor)=J._factor_growth_reference(f.inner)
J._finite_updated_factor(f::BGPanelFactor)=J._finite_updated_factor(f.inner)
end
'''
put('factor.jl',header+scalar+tail)
# Test-only kernel copy with three pre-allocation/mutation call sites. Default
# dispatch is unchanged; this copy never substitutes for frozen Task1 kernel.
panel=(C/'panel.jl').read_text();fault=panel.replace('module BGBlockedPanel\n','module BGBlockedPanelFault\n',1)
control='''const armed=Ref(:none)
const hits=Ref(0)
const sentinel=Ref{Any}(nothing)
arm!(point,error)=(armed[]=point;hits[]=0;sentinel[]=error;nothing)
disarm!()=(armed[]=:none;nothing)
function fault!(point)
    if armed[]===point;hits[]+=1;throw(sentinel[]);end
    nothing
end
'''
fault=fault.replace('const J = JSimplex\n','const J = JSimplex\n'+control,1)
hooks=[('    ws.start=r;ws.count=b;ws.width=w;ws.owner=inner.upper\n','    fault!(:gather)\n'),('        sizehint!(inner.row_columns[r+i-1],need)\n','        fault!(:reserve)\n'),('            bump!(c,Val(18))\n','            fault!(:writeback)\n')]
for a,b in hooks:
 if fault.count(a)!=1:raise ValueError(a)
 fault=fault.replace(a,a+b,1)
put('panel-fault.jl',fault)
put('factor-fault.jl',(header+scalar+tail).replace('BGBlockedAdapter','BGBlockedAdapterFault').replace('BGBlockedPanel','BGBlockedPanelFault'))
put('adapter-source-map.json',json.dumps(dict(original_suffix=original,qualified_suffix=scalar,substitutions={'position':'r','T':'Float64','namespace_symbols':symbols},cold_events=['pure','scalar_pivot'],fault_hooks=hooks,fault_control=control,scope='Source inverse only; no Julia parse or execution; copied suffix is ordinary original arithmetic'),indent=2)+'\n')
for n in ['bg-task2-tests.py','bg-task2-adapter.py']:
 with (Q/n.removeprefix('bg-task2-')).open('xb') as out:out.write((Path('/tmp')/n).read_bytes())
print('Adapter and exact-inverse fault copies saved; Julia UNEXECUTED')
