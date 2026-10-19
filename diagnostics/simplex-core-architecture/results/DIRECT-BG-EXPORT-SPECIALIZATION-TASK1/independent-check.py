"""Fresh Task1 source review checker, saved before execution. No Julia/parser.
Checks literal byte/source properties; no numerical or dispatch acceptance.
"""
from pathlib import Path
import hashlib, json, subprocess
D=Path(__file__).resolve().parent
R=D.parents[3]
C=R/'diagnostics/direct-bg-export-specialized/reproduce'
G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')
checks={}; pins={}
def blob(path):
 p=Path(path); p=p if p.is_absolute() else R/p
 b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
def txt(p): return blob(p).decode()
def obj(p): return json.loads(blob(p))
def check(name,ok): checks[name]=bool(ok)
def rename(s): return s.replace('_bgx_','_bgxs_').replace('BGExport','BGSpecializedExport').replace('_BGXBuildOwner','_BGXSBuildOwner')
def reverse(s): return s.replace('_bgxs_','_bgx_').replace('BGSpecializedExport','BGExport').replace('_BGXSBuildOwner','_BGXBuildOwner')
# Verify the prior checker as data; do not execute/import it.
author=obj(D/'source-check.json')
bad=[]
for path,h in author['sha256'].items():
 if hashlib.sha256(blob(path)).hexdigest()!=h:bad.append(path)
check('all_406_author_bindings_current',len(author['sha256'])==406 and not bad)
check('author_saved_result_41_checks',author['all_passed'] and len(author['checks'])==41 and all(author['checks'].values()))
expected=[
 ('workspace','function _bgxs_scratch_core!(owner::O,role::Symbol,n::Int,l::Int,u::Int,allocate::A) where {O,A}','_bgxs_scratch_core!(owner,role,n,l,u,allocate)'),
 ('export','function _bgxs_checked_basis_lu_core(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner::O,allocate::A) where {O,A}','_bgxs_checked_basis_lu_core(L,U,p,q,scaling,divide,owner,allocate)'),
 ('export','function _bgxs_scale_mode_core(F::FT,L::LT,U::UT,p::PT,q::QT,scaling::ST,owner::O,n::Int,l::Int,u::Int,allocate::A) where {FT,LT,UT,PT,QT,ST,O,A}','_bgxs_scale_mode_core(F,L,U,p,q,scaling,owner,n,l,u,allocate)'),
 ('export','_bgxs_export_core(backend::B,owner::O,allocate::A) where {B,O,A}=_bgxs_drop!(owner)',None),
 ('export','function _bgxs_export_core(backend::B,owner::O,allocate::A) where {B<:UMFPACKBackend,O,A}','_bgxs_export_core(backend,owner,allocate)'),
 ('export','function _bgxs_export_core(backend::B,owner::O,allocate::A) where {B<:MarkowitzBackend{Float64},O,A}','_bgxs_export_core(backend,owner,allocate)'),
 ('import','@inline function _bgxs_import_upper_core(U::SparseMatrixCSC{Float64,Int},normalize::Bool,allocate::A) where A','_bgxs_import_upper_core(U,normalize,allocate)'),
 ('factor','function _bgxs_build_core(B::M,backend::Val{R},policy::_NativePivotPolicy,normalize::Bool,owner::O,factorize::FZ,export_parts::EX,import_upper::IM,allocate::AL,make_inner::MK) where {M<:AbstractMatrix{Float64},R,O,FZ,EX,IM,AL,MK}','_bgxs_build_core(B,backend,policy,normalize,owner,factorize,export_parts,import_upper,allocate,make_inner)'),
 ('factor','function _bgxs_refactor_core!(f::BGSpecializedExportFactor{I},B::M,factorize::FZ,export_parts::EX,import_upper::IM,allocate::AL,make_inner::MK,check_inner::CK) where {I,M<:AbstractMatrix{Float64},FZ,EX,IM,AL,MK,CK}','_bgxs_refactor_core!(f,B,factorize,export_parts,import_upper,allocate,make_inner,check_inner)')]
inv=obj(C/'source-inverse.json'); check('four_expected_files',set(inv['files'])=={'workspace','export','import','factor'})
for name,record in inv['files'].items():
 old=txt(record['source']);new=txt(C/(name+'.jl'));back=new
 wanted=[x for x in expected if x[0]==name]
 check(name+'_edit_count',len(wanted)==len(record['edits']))
 for i,(edit,(_,core,call)) in enumerate(zip(record['edits'],wanted)):
  if call is None:
   insertion='@inline _bgxs_export(backend,owner;allocate=_bgxs_allocate)=_bgxs_export_core(backend,owner,allocate)\n'+core
  else: insertion='@inline '+edit['before']+'\n    '+call+'\nend\n\n'+core
  check(name+'_header_and_single_forward_'+str(i),edit['after']==insertion and back.count(insertion)==1 and rename(old).count(edit['before'])==1)
  back=back.replace(insertion,edit['before'])
 check(name+'_full_byte_inverse',reverse(back).encode()==old.encode())
 check(name+'_declared_hashes',record['source_sha256']==pins[record['source']] and record['candidate_sha256']==pins[str(C/(name+'.jl'))])
code='\n'.join(txt(C/(n+'.jl')) for n in inv['files'])
check('exactly_ten_inline_hints',code.count('@inline ')==10)
check('no_codegen_or_dimension_val',not any(x in code for x in ['@eval','@generated','Val{n}','Val{l}','Val{u}']))
prepared=obj(D/'tests-prepared.json');seal=obj(G/'runs/green2-300/sealed.json');driver=txt(G/'driver.jl');gi=obj(G/'inverse.json')
for name,row in prepared['test_lineage'].items():
 old=txt(row['source']);new=txt(C/name)
 check(name+'_lineage',new==rename(old) and pins[row['source']]==row['original_sha256']==seal['inventory'][row['source']]['sha256'] and pins[str(C/name)]==row['candidate_sha256'])
 check(name+'_actual_green2_include','include("'+row['source']+'")' in driver)
check('corrected_import_fixed_hash',pins[gi['amended']]=='628a74265bc5ed75e0a9507b9a7f3f453ba76d413ccbcb8a90e177e9e2329260')
check('green2_import_exact_single_amendment',txt(gi['amended']).count(gi['after'])==1 and txt(gi['amended']).replace(gi['after'],gi['before'])==txt(gi['original']))
check('recorded_test_first_only',prepared['candidate_absent'] is True and prepared['execution']=='NONE; test definitions prepared before candidate')
boundary=txt(C/'boundary-tests.jl')
check('boundary_prepared_input_identical',blob(C/'boundary-tests.jl')==blob(D/'boundary-tests.input.jl'))
check('boundary_fixed_logs', 'Vector{Tuple{Any,Int}}(undef,256)' in boundary and 'Vector{Symbol}(undef,5)' in boundary)
check('separate_owner_types', 'workspace::Union{Nothing,X.BGExportWorkspace}' in boundary and 'workspace::Union{Nothing,X.BGSpecializedExportWorkspace}' in boundary)
check('three_boundary_definitions',all('function '+n+'()' in boundary for n in ['boundary_request_equivalence','boundary_hook_order','boundary_hot_and_hook_agree']))
m=obj(C/'overlay-manifest.json');base=Path(m['base']);stage=Path(m['stage'])
for label,root,size in [('base',base,79),('stage',stage,83)]:
 actual={str(p.relative_to(root)):hashlib.sha256(blob(p)).hexdigest() for p in root.rglob('*') if p.is_file()}
 check(label+'_exact_membership_and_hashes',actual==m[label+'_sha256'] and len(actual)==size)
check('stage_exact_four_additions',set(m['stage_sha256'])-set(m['base_sha256'])=={'src/_bgxs_'+n+'.jl' for n in inv['files']})
check('all_78_nonroot_inherited_bytes_unchanged',all(blob(base/p)==blob(stage/p) for p in m['base_sha256'] if p!='src/JSimplex.jl'))
root=txt(stage/'src/JSimplex.jl');addition=''.join('include("_bgxs_'+n+'.jl")\n' for n in ['workspace','export','import','factor'])
check('stage_root_exact_inverse',m['root_addition']==addition and root.count(addition)==1 and root.replace(addition,'')==txt(base/'src/JSimplex.jl'))
check('new_sources_exact_stage',all(blob(C/(n+'.jl'))==blob(stage/('src/_bgxs_'+n+'.jl')) for n in inv['files']))
check('test_load_order',m['test_order']==[str(C/n) for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl','boundary-tests.jl']])
fixture=(C/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve();blob(fixture)
check('fixture_relative_include_resolves',str(fixture).endswith('/diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl'))
# Prospective counts independently derived from manually reviewed source loops.
request_sum=sum(2*n+3+norm for n in [0,1,3,2,2] for norm in [0,1])
hook_cases=2*2*6
hook_factor=hook_cases+2*2*5
builds=2*2*3*2*2
budget={'import_request_sum_per_side':request_sum,'factorize_api_entries':hook_factor+builds,'factor_solves':builds*2,'refactor_attempts':hook_cases,'importer_entries':20+2*request_sum+36+builds+8,'request_recorders':12+20+2*request_sum+builds+4,'synthetic_orientation_solves':2*(2+2),'native_orientation_upper_bound':20+24}
check('new_test_budget_reconciled',budget=={'import_request_sum_per_side':67,'factorize_api_entries':92,'factor_solves':96,'refactor_attempts':24,'importer_entries':246,'request_recorders':218,'synthetic_orientation_solves':8,'native_orientation_upper_bound':44})
host=obj(D/'host.json');check('host_record_limits_explicit',len(host['groups'])==256 and host['matches']==[] and bool(host['unreadable_exe_pids']) and 'visibility limit' in host['scope'])
check('refs_current',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='1744ea4e61dea9d25a5848a9ccae7e1b0357072d' and subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='26e2291745999f485a74f643298ca997d65c7205')
check('tracked_content_unchanged',subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=R,text=True).strip()=='')
for path in [Path(__file__),D/'REPORT.md',D/'prepare.py',D/'tests-prepare.py',C/'work-memory-ledger.md',D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-PLAN')/'review.md']:blob(path)
out={'scope':'BG export specialization Task1','all_passed':all(checks.values()),'checks':checks,'prospective_new_test_budget':budget,'sha256':pins,'limits':'Offline source-only checks. No Julia/parser/import/compile/numerics/benchmark. Host evidence is recorded, not a fresh runtime admission. Test-first preparation is not an executed TDD cycle.'}
with (D/'independent-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':len(checks),'bindings':len(pins),'failed':[k for k,v in checks.items() if not v]}))
if not out['all_passed']:raise SystemExit(1)
