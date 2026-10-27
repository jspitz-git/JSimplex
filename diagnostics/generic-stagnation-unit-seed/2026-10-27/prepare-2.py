from pathlib import Path
import json,hashlib,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27')
st=(D/'baseline/src/simplex_stalling.jl').read_text();pr=(D/'baseline/src/primal_simplex.jl').read_text()
def region(s,a,b):
 if s.count(a)!=1 or s.count(b)!=1:raise RuntimeError('unique region')
 return s[s.index(a):s.index(b)]
metrics=region(st,'function _workspace_stagnation_values(ws,state::WorkspaceStagnation{BigFloat,BigFloat},algorithm)','function _reset_workspace_stagnation!')
newmetrics=metrics.replace('function _workspace_stagnation_values(ws,state::WorkspaceStagnation{BigFloat,BigFloat},algorithm)','function _workspace_stagnation_values(ws::SimplexWorkspace{BigFloat},state::WorkspaceStagnation{BigFloat,BigFloat},algorithm)').replace('objective, primal, dual = zero(S),zero(S),zero(S)','objective, primal, dual = zero(S),zero(S),zero(S)\n    comparison_zero = primal').replace(' : abs(price)',' : _primal_direction_magnitude(price)').replace(': zero(S)',': comparison_zero').replace('max(zero(S),lower,upper)','max(comparison_zero,lower,upper)')
unit=region(pr,'function _primal_unit_basis(workspace::SimplexWorkspace{T}) where {T}','function _primal_initialize_steepest!')
bfunit=unit.replace('function _primal_unit_basis(workspace::SimplexWorkspace{T}) where {T}','function _primal_unit_basis(workspace::SimplexWorkspace{BigFloat})').replace('abs(A.nzval[start]) == one(T)','_primal_direction_magnitude(A.nzval[start]) == Clong(1)')
ratunit=unit.replace('function _primal_unit_basis(workspace::SimplexWorkspace{T}) where {T}','function _primal_unit_basis(workspace::SimplexWorkspace{Rational{BigInt}})').replace('abs(A.nzval[start]) == one(T) || return false','value = A.nzval[start]\n            (value == 1 || value == -1) || return false')
init=region(pr,'function _primal_initialize_steepest!(workspace::SimplexWorkspace{T}) where {T}','function _primal_updated_weight(weight::T, alpha::T, beta::T,')
newinit=init.replace('function _primal_initialize_steepest!(workspace::SimplexWorkspace{T}) where {T}','function _primal_initialize_steepest!(workspace::SimplexWorkspace{BigFloat})\n    T = BigFloat').replace('    for index in (column_count + 1):(column_count + row_count)','    row_cacheable = false\n    row_ready = false\n    for index in (column_count + 1):(column_count + row_count)').replace('        scratch.steepest_valid[index] = _primal_cacheable_weight(row_weight)','        if !row_ready\n            row_cacheable = _primal_cacheable_weight(row_weight)\n            row_ready = true\n        end\n        scratch.steepest_valid[index] = row_cacheable')
changes=[dict(variant='A',file='src/simplex_stalling.jl',old=metrics,new=metrics+'\n'+newmetrics),dict(variant='B',file='src/primal_simplex.jl',old=unit,new=unit+'\n'+bfunit+'\n'+ratunit),dict(variant='C',file='src/primal_simplex.jl',old=init,new=init+'\n'+newinit)]
parts=[region(st,'_stagnation_price_step(price,pivot)','function StagnationMonitor{T}'),unit,init]
header='''using JSimplex,SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,WorkspaceStagnation,StagnationMonitor,VariableState,
 BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_is_fixed,bound_value,_primal_direction_magnitude,
 _finite_workspace,_with_recovery_precision,observe_progress!,reset_stagnation!,
 _simplex_event!,_primal_direction_weight,_primal_cacheable_weight
'''
base='\n'.join(parts)
for arm,enabled in [('Reference',[]),('A',['A']),('B',['B']),('C',['C']),('BC',['B','C'])]:
 body=base
 for ch in changes:
  if ch['variant'] in enabled:
   if body.count(ch['old'])!=1:raise RuntimeError('one clone region')
   body=body.replace(ch['old'],ch['new'])
 with (D/(arm+'.jl')).open('x') as f:f.write('module SSU'+arm+'\n'+header+body+'\nend\n')
with (D/'changes.json').open('x') as f:json.dump(changes,f,indent=2);f.write('\n')
with (D/'source-clones.json').open('x') as f:json.dump(dict(clones={n:hashlib.sha256((D/(n+'.jl')).read_bytes()).hexdigest() for n in ['Reference','A','B','C','BC']},regions=parts),f,indent=2);f.write('\n')
shutil.copyfile(__file__,D/'prepare-2.py');print('5 exact private namespaces/3 production substitutions prepared; noJulia')
