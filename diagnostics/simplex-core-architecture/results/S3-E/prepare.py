from pathlib import Path
import hashlib,json,shutil
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S3-E';o.mkdir(exist_ok=False)
shutil.copyfile('/tmp/s3e-host.json',o/'host-before.json')
files=['src/hypersparse_factorization.jl','src/hypersparse_updates.jl','src/huangfu_hall_factorization.jl','src/factorization.jl','src/simplex_precision.jl','src/simplex.jl','diagnostics/simplex-core-architecture/S5-INVENTORY-NOTES.md','diagnostics/simplex-core-architecture/S5-ENTRY.md','test/lp_refinement_state_tests.jl','docs/superpowers/plans/2026-10-13-dse-mixed-route-driver.md']
sp=(r/files[0]).read_text();up=(r/files[1]).read_text();hh=(r/files[2]).read_text();ft=(r/files[3]).read_text()
checks={
 'sparse_native_solve_internal':'solution = F \\ rhs' in sp,
 'sparse_extract_calls_scale':'divide = _umfpack_scale_mode(F,L,U,p,q,scaling)' in sp,
 'cache_counter_after_return':up.index('cache.base_view = sparse_solve_view(factor.base)')<up.index('cache.base_builds += 1'),
 'hh_native_solve_internal':'ldiv!(auxiliary,F,work)' in hh,
 'hh_extract_calls_scale':'divide=_hh_base_scale_mode(F,L,U,p,q,s,work,auxiliary)' in hh,
 'hh_constructor_extracts':'_hh_extract_base(F,work,auxiliary,extraction)' in hh,
 'hh_update_internal_unit':'unit=_hh_unit_transpose!(f,p)' in hh,
 'native_owner_concrete':'factorization::Union{Nothing,Float64UMFPACK}' in ft,
 'frozen_three_clones_delegate':all('sparse_solve_view' not in (d/'results/S3-D'/n).read_text() and '_hh_scale_mode' not in (d/'results/S3-D'/n).read_text() for n in ['checked-clone.txt','weights-clone.txt','dse-clone.txt']),
 'prior_closure_pass':json.loads((d/'results/S3-D/closure.json').read_text())['all_passed']}
prior=json.loads((d/'results/S3-D/source-check.json').read_text())['sha256'];sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
checks['all69_prior_pins_unchanged']=all(sha(p)==h for p,h in prior.items())
paths=set(map(Path,prior))|{r/f for f in files}|set((d/'results/S3-D').iterdir())|{d/'S3-DSE-MIXED-ROUTE-PREPARATION.md',d/'S3-DSE-MIXED-ROUTE-PREPARATION-REVIEW.md',o/'host-before.json'}
res={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in sorted(paths) if p.is_file()},'scope':'New literal source and read-time integrity checks; not numerical execution or a general impossibility proof'}
with (o/'source-check.json').open('x') as f:json.dump(res,f,indent=2);f.write('\n')
assert res['all_passed'];print(len(checks),'checks',len(res['sha256']),'pins')
(o/'search-note.md').write_text('One exploratory rg used absent src/eta_factorization.jl and exited 2 after returning other matches. Actual PFI source is src/factorization.jl, subsequently read directly. This was not an audit or Julia execution.\n')
