from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-R'
J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu');L=J/'share/julia/stdlib/v1.13/LinearAlgebra/src'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,s):
 with (E/n).open('x') as f:f.write(s)
def section(p,start,end):
 t=p.read_text();a=t.index(start);b=t.index(end,a);return t[a:b].rstrip()+'\n'
blocks=[]
def transform(label,p,start,end,replacements):
 original=section(p,start,end);candidate=original
 for old,new in replacements:
  if old not in candidate:raise ValueError('missing transform '+label+': '+old)
  candidate=candidate.replace(old,new)
 inverse=candidate
 for old,new in reversed(replacements):inverse=inverse.replace(new,old)
 if inverse!=original:raise ValueError('inverse '+label)
 blocks.append({'name':label,'source':str(p),'start_line':p.read_text()[:p.read_text().index(start)].count('\n')+1,'original':original,'candidate':candidate,'replacements':replacements,'original_sha256':sha(original.encode()),'candidate_sha256':sha(candidate.encode()),'inverse_exact':True})
 return candidate
f=R/'src/factorization.jl'
ref='''# UNEXECUTED; original backend methods, renamed only. No candidate auto-load.
module MADenseProbe
using LinearAlgebra
using Base: require_one_based_indexing, @lazy_str
import MutableArithmetics
import JSimplex
using LinearAlgebra: _ustrip
const MA = MutableArithmetics
const LA = LinearAlgebra
const DenseLUBackend = JSimplex.DenseLUBackend
const Float32LUBackend = JSimplex.Float32LUBackend
'''
ref+=transform('reference_forward',f,'function _backend_forward_solve!(destination::Vector, backend::Union{DenseLUBackend,Float32LUBackend}', 'function _backend_transpose_solve!(destination::Vector, backend::UMFPACKBackend',[('_backend_forward_solve!','reference_forward!')])
ref+='\n'+transform('reference_transpose',f,'function _backend_transpose_solve!(destination::Vector, backend::Union{DenseLUBackend,Float32LUBackend}', 'function _check_destination_dimension',[('_backend_transpose_solve!','reference_transpose!')])+'\nend # MADenseProbe\n'
write('reference.jl',ref)
head='''# UNEXECUTED. Include into MADenseProbe with Base.include after reference.jl.
# Stdlib-derived loops below: Julia MIT license in JULIA-LICENSE.md.
# No methods are added to Base, LinearAlgebra or JSimplex.
function _dense_ma_eligible(dest, backend, rhs)::Bool
    dest isa Vector{BigFloat} && rhs isa Vector{BigFloat} || return false
    backend isa DenseLUBackend{BigFloat,LU{BigFloat,Matrix{BigFloat},Vector{Int}}} || return false
    n = size(backend.factorization, 1)
    n >= 16 && size(backend.factorization, 2) == n && length(dest) == n && length(rhs) == n || return false
    return Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]
end
@inline _dense_ma_mul!(product::BigFloat, a::BigFloat, b::BigFloat) =
    MA.operate_to!(product, *, a, b)

function candidate_forward!(dest, backend, rhs)
    _dense_ma_eligible(dest, backend, rhs) || return reference_forward!(dest, backend, rhs)
    product = BigFloat()
    require_one_based_indexing(dest, rhs)
    _ma_lu_forward!(backend.factorization, copyto!(dest, rhs), product)
    return dest
end
function candidate_transpose!(dest, backend, rhs)
    _dense_ma_eligible(dest, backend, rhs) || return reference_transpose!(dest, backend, rhs)
    product = BigFloat()
    require_one_based_indexing(dest, rhs)
    _ma_lu_transpose!(transpose(backend.factorization), copyto!(dest, rhs), product)
    return dest
end

'''
cand=head
cand+=transform('pivot_rows',L/'lu.jl','_apply_ipiv_rows!(A::LU,','function _swap_rows!(B::AbstractMatrix',[('_apply_inverse_ipiv_rows!','_ma_inverse_ipiv_rows!'),('_apply_ipiv_rows!','_ma_apply_ipiv_rows!'),('_ipiv_rows!','_ma_ipiv_rows!'),('_swap_rows!','_ma_swap_rows!')])
cand+='\n'+transform('lu_forward',L/'lu.jl','function ldiv!(A::LU, B::AbstractVecOrMat)','ldiv!(transA::TransposeFactorization',[
 ('function ldiv!(A::LU, B::AbstractVecOrMat)','function _ma_lu_forward!(A::LU, B::AbstractVecOrMat, product::BigFloat)'),
 ('_apply_ipiv_rows!(A, B)','_ma_apply_ma_ipiv_rows!(A, B)'),
 ('ldiv!(UpperTriangular(A.factors), ldiv!(UnitLowerTriangular(A.factors), B))','_ma_triangular!(UpperTriangular(A.factors), _ma_triangular!(UnitLowerTriangular(A.factors), B, product), product)')])
# pivot renames are recorded literally; chained replacement creates _ma_apply_ma_ipiv_rows!.
cand+='\n'+transform('lu_transpose',L/'lu.jl','function ldiv!(transA::TransposeFactorization','ldiv!(adjA::AdjointFactorization',[
 ('function ldiv!(transA::TransposeFactorization{<:Any,<:LU}, B::AbstractVecOrMat)','function _ma_lu_transpose!(transA::LA.TransposeFactorization{<:Any,<:LU}, B::AbstractVecOrMat, product::BigFloat)'),
 ('ldiv!(transpose(UnitLowerTriangular(A.factors)), ldiv!(transpose(UpperTriangular(A.factors)), B))','_ma_triangular!(transpose(UnitLowerTriangular(A.factors)), _ma_triangular!(transpose(UpperTriangular(A.factors)), B, product), product)'),
 ('_apply_inverse_ipiv_rows!(A, B)','_ma_inverse_ma_ipiv_rows!(A, B)')])
cand+='\n'+transform('triangular_normalization',L/'triangular.jl','function ldiv!(A::AbstractTriangular, B::AbstractVecOrMat)','function rdiv!(A::AbstractMatrix, B::AbstractTriangular)',[
 ('function ldiv!(A::AbstractTriangular, B::AbstractVecOrMat)','function _ma_triangular!(A::LA.AbstractTriangular, B::AbstractVecOrMat, product::BigFloat)'),
 ('_ldiv!(B, uppertriangular(A), B)','_ma_ldiv!(B, LA.uppertriangular(A), B, product)'),
 ('_ldiv!(B, lowertriangular(A), B)','_ma_ldiv!(B, LA.lowertriangular(A), B, product)')])
cand+='''\n_ma_ldiv!(C::AbstractVecOrMat, A::LA.UpperOrLowerTriangular, B::AbstractVecOrMat, product::BigFloat) =
    _ma_generic_trimatdiv!(C, LA.uplo_char(A), LA.isunit_char(A), LA._wrapperop(parent(A)), LA._unwrap_at(parent(A)), B, product)
\n'''
products=[('_ustrip(A[i,m]) * Cm','_dense_ma_mul!(product, _ustrip(A[i,m]), Cm)'),('_ustrip(A[i,j]) * Cj','_dense_ma_mul!(product, _ustrip(A[i,j]), Cj)'),('tfun(A[i,j]) * C[i,k]','_dense_ma_mul!(product, tfun(A[i,j]), C[i,k])'),('_ustrip(A[i,1]) * C1','_dense_ma_mul!(product, _ustrip(A[i,1]), C1)')]
cand+=transform('generic_eight_branches',L/'triangular.jl','function generic_trimatdiv!(C::AbstractVecOrMat, uploc, isunitc, tfun::Function, A::AbstractMatrix, B::AbstractVecOrMat)','\n# conjugate cases',[
 ('function generic_trimatdiv!(C::AbstractVecOrMat, uploc, isunitc, tfun::Function, A::AbstractMatrix, B::AbstractVecOrMat)','function _ma_generic_trimatdiv!(C::AbstractVecOrMat, uploc, isunitc, tfun::Function, A::AbstractMatrix, B::AbstractVecOrMat, product::BigFloat)'),*products])
write('candidate.jl',cand)
inst=head[head.index('function candidate_forward!'):]
inst=inst.replace('candidate_forward!','instrumented_forward!').replace('candidate_transpose!','instrumented_transpose!')
inst=inst.replace('    _dense_ma_eligible(dest, backend, rhs) || return reference_forward!(dest, backend, rhs)','    _route_entries[] += 1\n    if !_dense_ma_eligible(dest, backend, rhs)\n        _route_fallbacks[] += 1\n        return reference_forward!(dest, backend, rhs)\n    end')
inst=inst.replace('    _dense_ma_eligible(dest, backend, rhs) || return reference_transpose!(dest, backend, rhs)','    _route_entries[] += 1\n    if !_dense_ma_eligible(dest, backend, rhs)\n        _route_fallbacks[] += 1\n        return reference_transpose!(dest, backend, rhs)\n    end')
inst=inst.replace('    product = BigFloat()','    _route_scratches[] += 1\n    product = BigFloat()')
write('instrumented.jl','''# UNEXECUTED diagnostic-only entry clones. NEVER include in timing windows.
const _route_entries = Ref(0)
const _route_scratches = Ref(0)
const _route_fallbacks = Ref(0)
function reset_route_counts!()
    _route_entries[]=0; _route_scratches[]=0; _route_fallbacks[]=0
end
route_counts() = (entries=_route_entries[], scratches=_route_scratches[], fallbacks=_route_fallbacks[])
\n'''+inst)
write('JULIA-LICENSE.md',(J/'LICENSE.md').read_text())
(E/'environment').mkdir()
write('environment/Project.toml','''[deps]
JSimplex = "68c30f08-d64b-42cf-ac89-1dfed499aac3"
LinearAlgebra = "37e2e46d-f89d-539d-b4ee-838fcccc9c8e"
MutableArithmetics = "d8a4904e-b15c-11e9-3269-09a3773c0cb0"
Test = "8dfed614-e22c-5e08-85e1-65c5234f0b40"
TOML = "fa267f1f-6049-4f14-aa54-33bafae1ed76"

[compat]
MutableArithmetics = "=1.8.1"
julia = "=1.13.0"
''')
m=(R/'Manifest.toml').read_text(); lines=m.splitlines(keepends=True);m=''.join(x for x in lines if not x.startswith('project_hash = '));m=m.replace('path = "."','path = '+json.dumps(str(R)))
write('environment/Manifest.toml',m)
reach=[{'stage':'F L, lower present','normalized':'UnitLowerTriangular(Matrix)','flags':'L/U/identity','A':'Matrix'}, {'stage':'F L, upper/diagonal','normalized':'UpperTriangular(UnitLowerTriangular(Matrix))','flags':'U/N/identity','A':'UnitLowerTriangular(Matrix)'},{'stage':'F U','normalized':'UpperTriangular(Matrix)','flags':'U/N/identity','A':'Matrix'},{'stage':'B U transpose, upper present','normalized':'LowerTriangular(Transpose(Matrix))','flags':'U/N/transpose','A':'Matrix'},{'stage':'B U transpose, lower/diagonal','normalized':'UpperTriangular(LowerTriangular(Transpose(Matrix)))','flags':'U/N/identity','A':'LowerTriangular(Transpose(Matrix))'},{'stage':'B L transpose','normalized':'UnitUpperTriangular(Transpose(Matrix))','flags':'L/U/transpose','A':'Matrix'}]
write('source-map.json',json.dumps({'blocks':blocks,'reachable_normalizations':reach,'scope':'Exact native LU Matrix{BigFloat} only. All eight generic branches copied; only listed normalized classes are claimed reachable. No parse/dispatch/runtime claim. Square top-level ldiv! branch justified by eligibility. Two wrapper paths retain nested virtual zeros and ones.','product_sites':cand.count('_dense_ma_mul!(product,')-0,'environment_edits':['Direct diagnostic MA dep','JSimplex path . -> absolute current checkout','remove stale project_hash only; no resolve or selected-loader proof']},indent=2)+'\n')
print(json.dumps({'inverse_blocks':len(blocks),'candidate_bytes':len(cand.encode()),'generic_product_sites':blocks[-1]['candidate'].count('_dense_ma_mul!'),'reachable_classes':len(reach)}))
