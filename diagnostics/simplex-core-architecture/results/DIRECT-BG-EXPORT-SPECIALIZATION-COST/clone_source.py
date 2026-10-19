"""Functions for new untimed probe source inversion; no execution on import."""
def clone_sources(C):
 output={};edits={}
 header='''# Untimed source-inverse instrumentation; no timed factory uses these methods.
const _bgxsp_counts=Dict{String,Int}(k=>0 for k in ("allocation_requests","requested_payload","factorizations","extractions","orientation_solves","orientation_products","triangle_checks","permutation_checks","normalized_stores","raw_stores","fallback_stores","index_stores","refactor_entries"))
const _bgxsp_coexist_peak=Ref(0)
_bgxsp_count!(k,n=1)=(_bgxsp_counts[string(k)]+=n;nothing)
function _bgxsp_reset!()
    for k in keys(_bgxsp_counts);_bgxsp_counts[k]=0;end
    _bgxsp_coexist_peak[]=0;nothing
end
function _bgxsp_capture_build(inner,backend,parts,owner)
    _bgxsp_coexist_peak[]=max(_bgxsp_coexist_peak[],Base.summarysize((inner,backend,parts,owner)))
    inner
end
'''
 for name in ('workspace','export','import','factor'):
  original=(C/(name+'.jl')).read_text();s=original.replace('_BGXSBuildOwner','_BGXSPBuildOwner').replace('BGSpecializedExport','BGSpecializedProbeExport').replace('_bgxs_','_bgxsp_');pairs=[]
  def change(a,b,count=1):
   nonlocal s
   if s.count(a)!=count:raise RuntimeError((name,a,s.count(a),count))
   s=s.replace(a,b);pairs.append([a,b,count])
  if name=='workspace':
   change('_bgxsp_allocate(::Type{T},n::Int) where T = Vector{T}(undef,n)','_bgxsp_allocate(::Type{T},n::Int) where T = (_bgxsp_count!(:allocation_requests);_bgxsp_count!(:requested_payload,n*sizeof(T));Vector{T}(undef,n))')
   change('_bgxsp_allocate(::Type{Bool},n::Int) = falses(n)','_bgxsp_allocate(::Type{Bool},n::Int) = (_bgxsp_count!(:allocation_requests);_bgxsp_count!(:requested_payload,8*cld(n,64));falses(n))')
  elif name=='export':
   change('        _check_export_triangle(L,n,true)','        _bgxsp_count!(:triangle_checks);_check_export_triangle(L,n,true)')
   change('        _check_export_triangle(U,n,false)','        _bgxsp_count!(:triangle_checks);_check_export_triangle(U,n,false)')
   change('        _check_export_permutation(p,n,seen)','        _bgxsp_count!(:permutation_checks);_check_export_permutation(p,n,seen)')
   change('        _check_export_permutation(q,n,seen)','        _bgxsp_count!(:permutation_checks);_check_export_permutation(q,n,seen)')
   change('        ldiv!(auxiliary,F,work)','        _bgxsp_count!(:orientation_solves);ldiv!(auxiliary,F,work)')
   change('        mul!(work,U,permuted);mul!(transformed,L,work)','        _bgxsp_count!(:orientation_products);mul!(work,U,permuted);_bgxsp_count!(:orientation_products);mul!(transformed,L,work)')
   change('        _hh_abs_mul!(work,U,permuted);_hh_abs_mul!(auxiliary,L,work)','        _bgxsp_count!(:orientation_products);_hh_abs_mul!(work,U,permuted);_bgxsp_count!(:orientation_products);_hh_abs_mul!(auxiliary,L,work)')
   change('        L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())','        _bgxsp_count!(:extractions);L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())')
   change('        L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())','        _bgxsp_count!(:extractions);L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())')
  elif name=='import':
   change('row=U.rowval[slot];ids[k]=row','row=U.rowval[slot];_bgxsp_count!(:index_stores);ids[k]=row')
   change('                    values[k]=value','                    _bgxsp_count!(:normalized_stores);values[k]=value')
   change('                values[k]=old','                _bgxsp_count!(:raw_stores);values[k]=old')
   change('for k in eachindex(values);values[k]=U.nzval[first+k-1];end','for k in eachindex(values);_bgxsp_count!(:fallback_stores);values[k]=U.nzval[first+k-1];end')
  else:
   change('    ordinary=factorize(B,backend,policy)','    _bgxsp_count!(:factorizations);ordinary=factorize(B,backend,policy)')
   change('return make_inner(BartelsGolubFactorization,base,upper,collect(1:n))','return _bgxsp_capture_build(make_inner(BartelsGolubFactorization,base,upper,collect(1:n)),ordinary,parts,owner)')
   change('return make_inner(BartelsGolubFactorization,base,upper,parts.columns)','return _bgxsp_capture_build(make_inner(BartelsGolubFactorization,base,upper,parts.columns),ordinary,parts,owner)')
   change('    f.busy && throw(ArgumentError("BG export workspace is busy"))\n    f.busy=true','    _bgxsp_count!(:refactor_entries)\n    f.busy && throw(ArgumentError("BG export workspace is busy"))\n    f.busy=true')
  inverse=s
  for a,b,count in reversed(pairs):
   if inverse.count(b)!=count:raise RuntimeError('Inverse occurrence')
   inverse=inverse.replace(b,a)
  inverse=inverse.replace('_bgxsp_','_bgxs_').replace('BGSpecializedProbeExport','BGSpecializedExport').replace('_BGXSPBuildOwner','_BGXSBuildOwner')
  if inverse!=original:raise RuntimeError('Whole source inverse '+name)
  output[name]=(header if name=='workspace' else '')+s;edits[name]=pairs
 return output,edits,header
