"""Exclusive offline source preparation check; no Julia execution."""
import json,hashlib
from pathlib import Path
r=Path.cwd();d=r/'diagnostics/simplex-core-architecture';o=d/'results/S3-D'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
c=json.loads((d/'results/S3-C/source-contract.json').read_text());paths=set(map(Path,c['sha256']))
paths.update(r/'src'/n for n in ['simplex.jl','simplex_numerics.jl','hypersparse_factorization.jl','refactorization_policy.jl','factorization.jl'])
paths.update([d/'S3-DSE-CONSUMER-CONTRACT.md',d/'S3-DSE-CONSUMER-CONTRACT-REVIEW.md',d/'results/S3-C/review-fix.json',d/'reproduce/pipeline_support_census.jl',r/'docs/superpowers/plans/2026-10-12-dse-mixed-route-qualification.md'])
paths.update(p for p in o.iterdir() if p.is_file())
s=(r/'src/simplex.jl').read_text();policy=(r/'src/simplex_numerics.jl').read_text();hh=(r/'src/huangfu_hall_factorization.jl').read_text();up=(r/'src/hypersparse_updates.jl').read_text()
manifest=json.loads((o/'source-manifest.json').read_text());fixtures=(d/'reproduce/pipeline_support_census.jl').read_text()
checks={'existing_m16_fixture':'m=16' in fixtures and 'A[2,1]=T(1//8)' in fixtures,'state_initializer_single_factory':'factorization = _basis_factorization(initial_basis, typed_options)' in s,'finish_is_separate':'_finish_workspace_initialization!(_initialize_workspace_state' in s,'native_refinement_default_false':'solve_refinement::Bool=(numerical_profile == :checked)' in policy and 'numerical_profile::Symbol=:native' in policy,'hh_update_internal_unit':'unit=_hh_unit_transpose!(f,p)' in hh,'hh_native_reuse_disabled':'reuse_symbolic=false' in hh,'base_view_once':'if !cache.base_ready' in up and 'cache.base_ready = true' in up,'inner_fallback_visible':'cache.dense_fallbacks += 1' in up,'clones_three_inverse':len(manifest)==3 and all(v['inverse_exact'] for v in manifest.values()),'all_C_53_unchanged':all(sha(p)==h for p,h in c['sha256'].items())}
assert all(checks.values())
v={'checks':checks,'all_passed':True,'sha256':{str(p):sha(p) for p in sorted(paths)},'scope':'Read-time source/input pins; no execution, bootstrap qualification or measured work counts'}
with (o/'source-check.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'pins':len(paths),'all_passed':True}))
