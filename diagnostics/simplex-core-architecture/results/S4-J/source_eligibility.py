"""Exclusive S4-J source/evidence analysis; zero Julia/old auditor calls."""
from pathlib import Path
import json,hashlib,subprocess,re,shutil
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S4-J';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();hh=(r/'src/huangfu_hall_factorization.jl').read_text();fac=(r/'src/factorization.jl').read_text();model=(r/'src/model.jl').read_text();opt=(r/'src/options.jl').read_text();wp=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl');w=wp.read_text();host=json.loads(Path('/tmp/s4-j-host.json').read_text());pre=json.loads((d/'results/S4-I/preflight.json').read_text());cp=r/'.superpowers/simplex-core-architecture/S4-C/triplet-focused-1-pins.json';pins=json.loads(cp.read_text())['inventory'];driver=d/'reproduce/hh_scratch_focused_tests.jl';log=d/'results/S4-C/triplet-focused-1-run.log'
files=['src/huangfu_hall_factorization.jl','src/factorization.jl','src/options.jl','test/hh_dimension_scratch_tests.jl','test/huangfu_hall_tests.jl','test/huangfu_hall_precision_tests.jl','test/huangfu_hall_markowitz_tests.jl','test/huangfu_hall_scalar_integration_tests.jl','test/huangfu_hall_integration_tests.jl']
compare={f:sha(r/f)==pins[str(r/f)]['sha256'] for f in files}
labels={'HH dimension change releases obsolete solve scratch':8,'HH scratch publication preserves scalar and failure contracts':336,'Refactorization scratch, copies and failure isolation':10}
rows=[]
for no,line in enumerate(log.read_text().splitlines(),1):
 for label,n in labels.items():
  if line.startswith(label+' |'):
   fields=line.split('|')[1].split();rows.append({'label':label,'line':no,'text':line,'pass':int(fields[0]),'total':int(fields[1]),'expected':n})
ref=hh[hh.index('function refactorize!(f::HuangfuHall'):hh.index('function copy_basis_factorization(f::HuangfuHall')];wrapper=w[w.index('function lu!(F::UmfpackLU{Tv, Ti}, S::AbstractSparseMatrixCSC;'):w.index('size(F::UmfpackLU)')];numeric=w[w.index('function umfpack_numeric!(U::UmfpackLU{Float64'):w.index('function umfpack_numeric!(U::UmfpackLU{ComplexF64')]
controls=[{'file':str(p.relative_to(r)),'line':n,'text':line} for p in (r/'src').glob('*.jl') for n,line in enumerate(p.read_text().splitlines(),1) if re.search(r'\.control\b',line)]
checks={
'host_clear':not host['matches'],
'refs_expected':host['refs'].splitlines()==['2d8bc0a5502ca458b5fa361783884044face8fb0','0eb75c3190096946b0e91e5360230ccd7166f298'],
'user_hashes':all(sha(k)==v for k,v in pre['user_hashes'].items()),
'production_test_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
'HH_Float64_Int64_only':'T !== Float64 || Int === Int64' in opt,
'Float64_native_sparse':'_hh_native_lu(B::AbstractMatrix{Float64})=lu(convert(SparseMatrixCSC{Float64,Int},B))' in hh,
'other_native_dense':'_hh_native_lu(B::AbstractMatrix{T}) where {T}=lu!(Matrix{T}(B))' in hh,
'empty_initial_native':'_hh_initial_lu(B::AbstractMatrix{Float64})=iszero(size(B,1)) ? nothing' in hh,
'empty_refactor_early':'size(B,1)==0 && return nothing' in hh,
'dimension_fresh':'(isnothing(F) || size(F)!=size(B)) && return _hh_native_lu(B)' in hh,
'nonsquare_before_try':ref.index('throw(DimensionMismatch')<ref.index('    try'),
'HH_no_input_finite_scan':'all(isfinite' not in ref and 'isfinite(B' not in ref,
'extraction_diagonal_guard':'isfinite(U.nzval[U.colptr[i+1]-1])' in hh and '!iszero(U.nzval[U.colptr[i+1]-1])' in hh,
'offdiagonal_not_blanket_reject':'finite_upper &= isfinite(U.nzval[k])' in hh and 'HHBase(L,U,p,q,invperm(q),s,divide,rowptr,columns,finite_upper)' in hh,
'wrapper_owned_control_CSC':'copy(control)' in w and 'copy(nonzeros(S))' in w,
'wrapper_mutation_before_numeric':wrapper.index('F.m = size(S, 1)')<wrapper.index('F.nzval .= nonzeros(S)')<wrapper.index('return lu!(F; reuse_symbolic, check, q)'),
'symbolic_early_return':'_isnotnull(U.symbolic) && return U' in w,
'numeric_uses_controls_values':'U.colptr, U.rowval, U.nzval, U.symbolic, tmp, U.control, U.info' in numeric,
'default_IRSTEP_zero':'control[JL_UMFPACK_IRSTEP] = 0' in w,
'production_no_control_property_access':not controls,
'production_reuse_false':'reuse_symbolic=false' in hh,
'model_conversion_finite':'isfinite(converted) || throw(ArgumentError("$label must be finite"))' in model,
'pattern_helper_index_only':'factor.rowval[index] == B.rowval[index] - offset' in fac,
'C_all_nine_sources_match':len(compare)==9 and all(compare.values()),
'C_three_rows_executed':len(rows)==3 and all(x['pass']==x['total']==x['expected'] for x in rows),
'C_actual_includes':all('"'+f+'"' in driver.read_text() and 'Starting '+f in log.read_text() for f in ['hh_dimension_scratch_tests.jl','huangfu_hall_tests.jl','huangfu_hall_precision_tests.jl']),
'I_wrapper_launch_match':sha(wp)==json.loads((d/'results/S4-I/assembly-1-pins.json').read_text())['inventory'][str(wp)]['sha256'],
}
paths={r/p for p in files}|{wp,cp,driver,log,Path(__file__),r/'docs/superpowers/plans/2026-10-12-hh-reuse-eligibility-contract.md'}|set(map(Path,pre['user_hashes']))
for tree in ['src','test']:paths.update(p for p in (r/tree).rglob('*') if p.is_file())
for stage,names in {'S4-F':['boundary-1-report.toml','boundary-1-audit.json'],'S4-G':['publication-1-report.toml','publication-1-audit.json'],'S4-I':['assembly-1-report.toml','assembly-1-audit.json','assembly-1-pins.json']}.items():
 paths.update(d/'results'/stage/n for n in names)
missing=[str(p) for p in paths if not p.is_file()];assert not missing,missing
result={'checks':checks,'all_passed':all(checks.values()),'hashes':{str(p.resolve()):sha(p) for p in sorted(paths)},'C_source_comparisons':compare,'C_executed_rows':rows,'source_control_property_access':controls,'scope':'source/evidence only; zero Julia; no native C implementation proof','decision':'separate bounded nonfinite same-pattern HH rejection qualification; no production eligibility guard implemented'}
with (o/'source-eligibility.json').open('x') as f:json.dump(result,f,indent=2)
shutil.copyfile('/tmp/s4-j-host.json',o/'host-preflight.json');print({'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'hashes':len(result['hashes'])});assert result['all_passed']
