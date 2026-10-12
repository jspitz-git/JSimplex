"""Exclusive source/evidence audit. No Julia or numerical backend calls."""
from pathlib import Path
import hashlib,json,subprocess,time
root=Path.cwd(); d=root/'diagnostics/simplex-core-architecture';out=d/'results/S4-E'
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git',*a],text=True).strip()
u=runtime/'share/julia/stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl'
h=root/'src/huangfu_hall_factorization.jl';f=root/'src/factorization.jl'
hh=h.read_text();pf=f.read_text();um=u.read_text()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();active=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   comm=(p/'comm').read_text().strip();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
   if comm.startswith('julia') or ('python' in comm and ('attempt.py' in cmd or 'guarded_run.py run' in cmd)):
    active.append({'pid':int(p.name),'command':cmd,'start_ticks':(p/'stat').read_text().split(') ',1)[1].split()[19]})
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
oldb=root/'.superpowers/simplex-core-architecture/S4-B/native-components-2-pins.json'
oldc=root/'.superpowers/simplex-core-architecture/S4-C/triplet-focused-1-pins.json'
bp=json.loads(oldb.read_text());cp=json.loads(oldc.read_text());rp=json.loads((d/'results/S6-R/replay-1-pins.json').read_text())
comparisons=[]
for label,pins in [('S4-B',bp),('S4-C-focused',cp),('S6-R',rp)]:
 for p in [h,f,root/'test/huangfu_hall_tests.jl',root/'test/basis_matrix_reuse_allocation_tests.jl',u,runtime/'bin/julia',root/'Manifest.toml',root/'LocalPreferences.toml']:
  old=pins['inventory'].get(str(p));comparisons.append({'evidence':label,'path':str(p),'historical_sha256':old['sha256'] if old else None,'current_sha256':sha(p),'match':old['sha256']==sha(p) if old else None})
ba=json.loads((d/'results/S4-B/native-components-2-audit.json').read_text())
clog=(d/'results/S4-C/triplet-focused-1-run.log').read_text()
checks={
'expected_branch':git('branch','--show-current')=='codex/simplex-core-architecture',
'expected_master':git('rev-parse','master')=='0eb75c3190096946b0e91e5360230ccd7166f298',
'production_test_ci_equal_master':not git('diff','master','--','src','test','.github'),
'no_numerical_runner':not active,
'prior_pids_absent':all(not Path('/proc',str(p)).exists() for p in (433429,433431,433420)),
'hh_symbolic_disabled':'lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=false)' in hh,
'pf_index_offset_guard':'factor.rowval[index] == B.rowval[index] - offset' in pf,
'private_failure_discard':'f.refactor_workspace=nothing\n        rethrow()' in hh,
'publication_after_extraction':hh.index('base=_hh_extract_base(F,work,auxiliary,f.extract_workspace)')<hh.index('f.base=base;f.refactor_workspace=F'),
'prepared_invalidated_after_publication':hh.index('f.base=base;f.refactor_workspace=F')<hh.index('empty!(f.updates);f.prepared_valid=false'),
'saved_factor_without_native_workspace':'false,nothing,HHUnitWorkspace(n,T)' in hh,
'native_constructor_owns_values':'copy(nonzeros(S)), 0, UmfpackWS' in um,
'native_updates_values_before_numeric':um.index('F.nzval .= nonzeros(S)')<um.index('return lu!(F; reuse_symbolic, check, q)'),
'symbolic_receives_values_controls':'U.rowval, U.nzval, tmp, U.control, U.info)' in um,
'existing_symbolic_short_circuit':'_isnotnull(U.symbolic) && return U' in um,
'lu_bang_forces_new_numeric':'umfpack_numeric!(F; reuse_numeric = false, q)' in um,
'default_refinement_disabled':'control[JL_UMFPACK_IRSTEP] = 0' in um,
'shallow_copy_shares_arrays':'F.colptr,\n        F.rowval,\n        F.nzval,' in um,
'wrapper_matches_historical_R':rp['inventory'][str(u)]['sha256']==sha(u),
'B_saved_audit_accepted':ba['accepted'] and all(ba['checks'].values()),
'B_raw_report_hash':ba['reference_sha256']==sha(d/'results/S4-B/native-components-2-reference.toml'),
'B_pin_manifest_hash':ba['pins_sha256']==sha(oldb),
'C_HH_test_source_matches':cp['inventory'][str(root/'test/huangfu_hall_tests.jl')]['sha256']==sha(root/'test/huangfu_hall_tests.jl'),
'C_HH_source_matches':cp['inventory'][str(h)]['sha256']==sha(h),
'C_log_executes_HH_tests':'Starting huangfu_hall_tests.jl' in clog and 'Refactorization scratch, copies and failure isolation' in clog,
}
files=set([h,f,u,runtime/'bin/julia',runtime/'lib/julia/libumfpack.so.6.3.5',runtime/'share/julia/stdlib/v1.13/SparseArrays/src/solvers/LibSuiteSparse.jl',runtime/'share/julia/stdlib/v1.13/SuiteSparse_jll/src/SuiteSparse_jll.jl',oldb,oldc,Path(__file__).resolve()])
for tree in ['src','test','.github']:
 files.update(p for p in (root/tree).rglob('*') if p.is_file())
for p in [root,Path('/home/jspitz/JSimplex.jl')]:
 files.update(p/n for n in ['Manifest.toml','LocalPreferences.toml','.vscode/settings.json'] if (p/n).exists())
files.update(p for p in (d/'results/S4-B').glob('*') if p.is_file())
files.update([d/'results/S6-R/replay-1-pins.json',d/'results/S4-C/triplet-focused-1-run.log',d/'reproduce/hh_scratch_focused_tests.jl',d/'reproduce/hh_component_attribution.jl'])
result={'scope':'source/evidence only; no Julia, backend, solver, old parser/auditor calls','created_ns':time.time_ns(),'boot_id':boot,'active':active,'head':git('rev-parse','HEAD'),'master':git('rev-parse','master'),'status':git('status','--short'),'checks':checks,'all_passed':all(checks.values()),'comparisons':comparisons,'hashes':{str(p):sha(p) for p in sorted(files)},'provenance_limit':'Current wrapper matches S6-R launch pin. S4-B did not pin wrapper/libumfpack; current hash is not a retroactive native-library execution pin.'}
with (out/'source-contract.json').open('x') as io:json.dump(result,io,indent=2)
print(json.dumps({'checks':len(checks),'all_passed':result['all_passed'],'false':[k for k,v in checks.items() if not v],'hashes':len(files),'comparisons':comparisons},indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
