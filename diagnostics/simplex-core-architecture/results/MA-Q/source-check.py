from pathlib import Path
import hashlib, json
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/MA-Q'
J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia')
M=Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc')
paths=[R/'src/factorization.jl',R/'src/JSimplex.jl',R/'Project.toml',R/'test/factorization_tests.jl',R/'test/refactorization_factor_tests.jl',R/'test/refactorization_failure_tests.jl',J/'base/mpfr.jl',J/'stdlib/v1.13/LinearAlgebra/src/factorization.jl',J/'stdlib/v1.13/LinearAlgebra/src/lu.jl',J/'stdlib/v1.13/LinearAlgebra/src/triangular.jl',M/'src/implementations/BigFloat.jl',M/'Project.toml',R/'docs/superpowers/specs/2026-10-14-ma-denselu-bigfloat-design.md',R/'docs/superpowers/plans/2026-10-14-ma-denselu-bigfloat.md',R/'diagnostics/simplex-core-architecture/CURRENT-MASTER-TIME-BREAKDOWN.md',E/'host.json',E/'continuation-map.json',E/'STATUS.md.before-MA-Q',E/'roadmap.md.before-MA-Q',E/'source-check.py']
texts={str(p):p.read_text() for p in paths}; f=texts[str(paths[0])]; mp=texts[str(paths[6])]; tr=texts[str(paths[9])]; ma=texts[str(paths[10])]; plan=texts[str(paths[13])]; spec=texts[str(paths[12])]
checks={
 'shared_dense_backend':'_copy_backend(backend::DenseLUBackend) = backend' in f,
 'original_forward':'ldiv!(destination, backend.factorization, rhs)' in f,
 'original_transpose':'ldiv!(destination, transpose(backend.factorization), rhs)' in f,
 'base_ambient_result':'z = BigFloat()' in mp and 'z, x, y, rounding_raw(BigFloat)' in mp,
 'base_scoped_rounding':'Base.ScopedValues.get(CURRENT_ROUNDING_MODE)' in mp,
 'ma_global_rounding':'(:mpfr_mul, :libmpfr)' in ma and 'Base.MPFR.ROUNDING_MODE[]' in ma,
 'triangular_normalization':'if istriu(A)' in tr and '_wrapperop(parent(A)), _unwrap_at(parent(A))' in tr,
 'single_product_preserves_publication':'one call-local BigFloat product only' in spec and 'Ordinary subtraction still creates' in spec,
 'whole_fallback_rounding_gate':'Base.MPFR.ROUNDING_MODE[]' in spec and 'BEFORE copying/permuting/writing' in spec,
 'no_leaf_retry':'do not introduce a leaf fallback' in spec,
 'cost_schedule':36+16==52 and 52*3*10*2*4==12480 and '12480cost calls' in plan,
 'five_review_classes':all(x in plan for x in ['1. Scoped/global','2. Shared LU','3. Diagonal','4. Singular','5. Small']),
 'no_runtime_claim':'documentation/source review only' in plan and 'not a measured optimum' in spec,
 'beforecopy_six_bindings':all(hashlib.sha256(Path(x['preserved']).read_bytes()).hexdigest()==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings']) and len(json.loads((E/'continuation-map.json').read_text())['old_bindings'])==6,
}
obj={'scope':'New read-time source and plan bindings, not launch pins or runtime qualification. Literal checks supplement semantic independent review. No old script executed.', 'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
with (E/'source-check.json').open('x') as out: json.dump(obj,out,indent=2); out.write('\n')
print(json.dumps({'checks':len(checks),'bindings':len(paths),'all_passed':obj['all_passed']}))
if not obj['all_passed']: raise SystemExit(1)
