"""Functions for new untimed probe source inversion; no execution on import."""
def clone_sources(C):
 output={};edits={}
 header='''# Untimed source-inverse instrumentation; no timed factory uses these methods.
const _bgxp_counts=Dict{String,Int}(k=>0 for k in ("allocation_requests","requested_payload","factorizations","extractions","orientation_solves","orientation_products","triangle_checks","permutation_checks","normalized_stores","raw_stores","fallback_stores","index_stores","refactor_entries"))
const _bgxp_coexist_peak=Ref(0)
_bgxp_count!(k,n=1)=(_bgxp_counts[string(k)]+=n;nothing)
function _bgxp_reset!()
    for k in keys(_bgxp_counts);_bgxp_counts[k]=0;end
    _bgxp_coexist_peak[]=0;nothing
end
function _bgxp_capture_build(inner,backend,parts,owner)
    _bgxp_coexist_peak[]=max(_bgxp_coexist_peak[],Base.summarysize((inner,backend,parts,owner)))
    inner
end
'''
 for name in ('workspace','export','import','factor'):
  original=(C/(name+'.jl')).read_text();s=original.replace('_BGXBuildOwner','_BGXPBuildOwner').replace('BGExport','BGProbeExport').replace('_bgx_','_bgxp_');pairs=[]
  def change(a,b,count=1):
   nonlocal s
   if s.count(a)!=count:raise RuntimeError((name,a,s.count(a),count))
   s=s.replace(a,b);pairs.append([a,b,count])
  if name=='workspace':
   change('_bgxp_allocate(::Type{T},n::Int) where T = Vector{T}(undef,n)','_bgxp_allocate(::Type{T},n::Int) where T = (_bgxp_count!(:allocation_requests);_bgxp_count!(:requested_payload,n*sizeof(T));Vector{T}(undef,n))')
   change('_bgxp_allocate(::Type{Bool},n::Int) = falses(n)','_bgxp_allocate(::Type{Bool},n::Int) = (_bgxp_count!(:allocation_requests);_bgxp_count!(:requested_payload,8*cld(n,64));falses(n))')
  elif name=='export':
   change('        _check_export_triangle(L,n,true)','        _bgxp_count!(:triangle_checks);_check_export_triangle(L,n,true)')
   change('        _check_export_triangle(U,n,false)','        _bgxp_count!(:triangle_checks);_check_export_triangle(U,n,false)')
   change('        _check_export_permutation(p,n,seen)','        _bgxp_count!(:permutation_checks);_check_export_permutation(p,n,seen)')
   change('        _check_export_permutation(q,n,seen)','        _bgxp_count!(:permutation_checks);_check_export_permutation(q,n,seen)')
   change('        ldiv!(auxiliary,F,work)','        _bgxp_count!(:orientation_solves);ldiv!(auxiliary,F,work)')
   change('        mul!(work,U,permuted);mul!(transformed,L,work)','        _bgxp_count!(:orientation_products);mul!(work,U,permuted);_bgxp_count!(:orientation_products);mul!(transformed,L,work)')
   change('        _hh_abs_mul!(work,U,permuted);_hh_abs_mul!(auxiliary,L,work)','        _bgxp_count!(:orientation_products);_hh_abs_mul!(work,U,permuted);_bgxp_count!(:orientation_products);_hh_abs_mul!(auxiliary,L,work)')
   change('        L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())','        _bgxp_count!(:extractions);L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())')
   change('        L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())','        _bgxp_count!(:extractions);L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())')
  elif name=='import':
   change('row=U.rowval[slot];ids[k]=row','row=U.rowval[slot];_bgxp_count!(:index_stores);ids[k]=row')
   change('                    values[k]=value','                    _bgxp_count!(:normalized_stores);values[k]=value')
   change('                values[k]=old','                _bgxp_count!(:raw_stores);values[k]=old')
   change('for k in eachindex(values);values[k]=U.nzval[first+k-1];end','for k in eachindex(values);_bgxp_count!(:fallback_stores);values[k]=U.nzval[first+k-1];end')
  else:
   change('    ordinary=factorize(B,backend,policy)','    _bgxp_count!(:factorizations);ordinary=factorize(B,backend,policy)')
   change('return make_inner(BartelsGolubFactorization,base,upper,collect(1:n))','return _bgxp_capture_build(make_inner(BartelsGolubFactorization,base,upper,collect(1:n)),ordinary,parts,owner)')
   change('return make_inner(BartelsGolubFactorization,base,upper,parts.columns)','return _bgxp_capture_build(make_inner(BartelsGolubFactorization,base,upper,parts.columns),ordinary,parts,owner)')
   change('    f.busy && throw(ArgumentError("BG export workspace is busy"))\n    f.busy=true','    _bgxp_count!(:refactor_entries)\n    f.busy && throw(ArgumentError("BG export workspace is busy"))\n    f.busy=true')
  inverse=s
  for a,b,count in reversed(pairs):
   if inverse.count(b)!=count:raise RuntimeError('Inverse occurrence')
   inverse=inverse.replace(b,a)
  inverse=inverse.replace('_bgxp_','_bgx_').replace('BGProbeExport','BGExport').replace('_BGXPBuildOwner','_BGXBuildOwner')
  if inverse!=original:raise RuntimeError('Whole source inverse '+name)
  output[name]=(header if name=='workspace' else '')+s;edits[name]=pairs
 return output,edits,header
