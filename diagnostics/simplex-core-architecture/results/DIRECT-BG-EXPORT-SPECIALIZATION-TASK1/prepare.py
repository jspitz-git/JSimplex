"""Task1 offline source transformation and isolated stage. No Julia parser."""
from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-specialized/reproduce';OLD=R/'diagnostics/direct-bg-export-workspace/reproduce';P=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def ren(s):return s.replace('_bgx_','_bgxs_').replace('BGExport','BGSpecializedExport').replace('_BGXBuildOwner','_BGXSBuildOwner')
def unren(s):return s.replace('_bgxs_','_bgx_').replace('BGSpecializedExport','BGExport').replace('_BGXSBuildOwner','_BGXBuildOwner')
specs=[]
def kernel(file,old,core,call):
 facade='@inline '+ren(old)+'\n    '+call+'\nend\n\n'
 specs.append((file,ren(old),facade+core))
kernel('workspace', 'function _bgx_scratch!(owner,role::Symbol,n::Int,l::Int,u::Int;allocate=_bgx_allocate)',
 'function _bgxs_scratch_core!(owner::O,role::Symbol,n::Int,l::Int,u::Int,allocate::A) where {O,A}',
 '_bgxs_scratch_core!(owner,role,n,l,u,allocate)')
kernel('export','function _bgx_checked_basis_lu(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},\n                           p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner;allocate=_bgx_allocate)',
 'function _bgxs_checked_basis_lu_core(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner::O,allocate::A) where {O,A}',
 '_bgxs_checked_basis_lu_core(L,U,p,q,scaling,divide,owner,allocate)')
kernel('export','function _bgx_scale_mode(F,L,U,p,q,scaling,owner,n::Int,l::Int,u::Int;allocate=_bgx_allocate)',
 'function _bgxs_scale_mode_core(F::FT,L::LT,U::UT,p::PT,q::QT,scaling::ST,owner::O,n::Int,l::Int,u::Int,allocate::A) where {FT,LT,UT,PT,QT,ST,O,A}',
 '_bgxs_scale_mode_core(F,L,U,p,q,scaling,owner,n,l,u,allocate)')
specs.append(('export',ren('_bgx_export(backend,owner;allocate=_bgx_allocate)=_bgx_drop!(owner)'),
 '@inline _bgxs_export(backend,owner;allocate=_bgxs_allocate)=_bgxs_export_core(backend,owner,allocate)\n_bgxs_export_core(backend::B,owner::O,allocate::A) where {B,O,A}=_bgxs_drop!(owner)'))
for backend in ['UMFPACKBackend','MarkowitzBackend{Float64}']:
 kernel('export',f'function _bgx_export(backend::{backend},owner;allocate=_bgx_allocate)',
 f'function _bgxs_export_core(backend::B,owner::O,allocate::A) where {{B<:{backend},O,A}}',
 '_bgxs_export_core(backend,owner,allocate)')
kernel('import','function _bgx_import_upper(U::SparseMatrixCSC{Float64,Int},normalize::Bool;allocate=_bgx_allocate)',
 '@inline function _bgxs_import_upper_core(U::SparseMatrixCSC{Float64,Int},normalize::Bool,allocate::A) where A',
 '_bgxs_import_upper_core(U,normalize,allocate)')
kernel('factor','function _bgx_build(B::AbstractMatrix{Float64},backend::Val{R},policy::_NativePivotPolicy,\n                    normalize::Bool,owner;factorize=_factorize_basis,export_parts=_bgx_export,\n                    import_upper=_bgx_import_upper,allocate=_bgx_allocate,\n                    make_inner=_init_direct_manager) where R',
 'function _bgxs_build_core(B::M,backend::Val{R},policy::_NativePivotPolicy,normalize::Bool,owner::O,factorize::FZ,export_parts::EX,import_upper::IM,allocate::AL,make_inner::MK) where {M<:AbstractMatrix{Float64},R,O,FZ,EX,IM,AL,MK}',
 '_bgxs_build_core(B,backend,policy,normalize,owner,factorize,export_parts,import_upper,allocate,make_inner)')
kernel('factor','function _bgx_refactor_with!(f::BGExportFactor,B::AbstractMatrix{Float64};\n        factorize=_factorize_basis,export_parts=_bgx_export,import_upper=_bgx_import_upper,\n        allocate=_bgx_allocate,make_inner=_init_direct_manager,check_inner=nothing)',
 'function _bgxs_refactor_core!(f::BGSpecializedExportFactor{I},B::M,factorize::FZ,export_parts::EX,import_upper::IM,allocate::AL,make_inner::MK,check_inner::CK) where {I,M<:AbstractMatrix{Float64},FZ,EX,IM,AL,MK,CK}',
 '_bgxs_refactor_core!(f,B,factorize,export_parts,import_upper,allocate,make_inner,check_inner)')
records={}
for file in ['workspace','export','import','factor']:
 src=OLD/(file+'.jl');text=ren(src.read_text());edits=[]
 for f,before,after in specs:
  if f!=file:continue
  if text.count(before)!=1:raise RuntimeError('Signature not unique: '+before)
  text=text.replace(before,after);edits.append({'before':before,'after':after})
 with (C/(file+'.jl')).open('x') as f:f.write(text)
 inverse=text
 for e in reversed(edits):
  if inverse.count(e['after'])!=1:raise RuntimeError('Inverse ambiguity')
  inverse=inverse.replace(e['after'],e['before'])
 if unren(inverse).encode()!=src.read_bytes():raise RuntimeError('Full source inverse')
 records[file]={'source':str(src),'source_sha256':sha(src),'candidate_sha256':sha(C/(file+'.jl')),'edits':edits,'exact_inverse':True}
save(C/'source-inverse.json',{'files':records,'rename':{'_bgx_':'_bgxs_','BGExport':'BGSpecializedExport','_BGXBuildOwner':'_BGXSBuildOwner'},'scope':'Complete byte inverse; no Julia parse/dispatch/runtime claim'})
base=Path(json.loads((P/'stages.json').read_text())['green']['path'])
# This inherited stage already contains packed DIRECT and the original workspace candidate.
basefiles={str(p.relative_to(base)):sha(p) for p in base.rglob('*') if p.is_file()}
if len(basefiles)!=79:raise RuntimeError('Expected exact79 source stage')
for file in records:
 if sha(base/'src'/('_bgx_'+file+'.jl'))!=records[file]['source_sha256']:raise RuntimeError('Old stage candidate mismatch')
W=R/'.superpowers/sdd/2026-10-19-direct-bg-export-specialization';W.mkdir(exist_ok=True,parents=True);stage=W/'task1-stage'
shutil.copytree(base,stage)
root=stage/'src/JSimplex.jl';before=root.read_text();ending='end\n'
if not before.endswith('include("_bgx_factor.jl")\n'+ending):raise RuntimeError('Root ending mismatch')
addition=''.join('include("_bgxs_'+file+'.jl")\n' for file in records)
root.write_text(before[:-len(ending)]+addition+ending)
for file in records:shutil.copyfile(C/(file+'.jl'),stage/'src'/('_bgxs_'+file+'.jl'))
after={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()}
if len(after)!=83 or root.read_text().replace(addition,'')!=before:raise RuntimeError('Stage inverse')
if any(after[n]!=h for n,h in basefiles.items() if n!='src/JSimplex.jl'):raise RuntimeError('Stage old file changed')
save(C/'overlay-manifest.json',{'base':str(base),'base_sha256':basefiles,'stage':str(stage),'stage_sha256':after,'root_addition':addition,'root_before_sha256':basefiles['src/JSimplex.jl'],'root_after_sha256':after['src/JSimplex.jl'],'candidate':{str(C/(n+'.jl')):sha(C/(n+'.jl')) for n in records},'test_order':[str(C/n) for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl','boundary-tests.jl']],'test_entries':['BGSpecializedExportWorkspaceTests.run_workspace_tests()','BGSpecializedExportImportTests.run_import_tests()','BGSpecializedExportLifecycleTests.run_lifecycle_tests()','BGSpecializedBoundaryTests.run_boundary_tests()'],'scope':'83-file ordinary stage, definition load only; no driver or automatic invocation; UNEXECUTED'})
save(D/'preparation.json',{'all_passed':True,'core_families':7,'method_splits':len(specs),'candidate_files':4,'base_files':79,'stage_files':83,'full_inverses':4,'tests_prepared_first':json.loads((D/'tests-prepared.json').read_text())['candidate_absent'],'sha256':{str(p):sha(p) for p in list(C.glob('*.jl'))+[Path(__file__),C/'source-inverse.json',C/'overlay-manifest.json']}})
print(json.dumps({'all_passed':True,'splits':len(specs),'inverses':4,'stage':str(stage),'stage_files':83}))
