from pathlib import Path
import hashlib,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/S2-B'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R).decode().strip()
files=git('ls-files','src','test','.github').splitlines()
comparisons={f: hashlib.sha256((R/f).read_bytes()).hexdigest()==hashlib.sha256(subprocess.check_output(['git','show','master:'+f],cwd=R)).hexdigest() for f in files}
p=(R/'src/primal_updates.jl').read_text();q=(R/'src/simplex_numerics.jl').read_text()
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/abstractarray.jl');b=base.read_text()
ap=R/'diagnostics/simplex-core-architecture/results/S6-AP/closure.json';a=json.loads(ap.read_text())
old={path:sha(path)==value for path,value in a['sha256'].items()}
users=[root/f for root in (R,Path('/home/jspitz/JSimplex.jl')) for f in ('Manifest.toml','LocalPreferences.toml','.vscode/settings.json')]
checks={
 'base_refs':git('rev-parse','HEAD')=='c44472e7a43533fb9ec337eba86189aabbe6ac61' and git('rev-parse','master')=='d02416c108f06fcd41d58e0a1980b70a51fef9ef',
 'source_test_ci_match_master':all(comparisons.values()),
 'all_AP_closure_bindings_unchanged':a['all_passed'] is True and len(old)==40 and all(old.values()),
 'prediction_copies_preserved':'predicted = copy(ws.primal)' in p and 'predicted_costs = copy(ws.reduced_costs)' in p,
 'one_target':p.count('values = vcat(ws.scratch.rho,predicted)')==1,
 'fresh_quality_scratch':'scratch = SolveQualityScratch(T,length(ws.costs))' in p,
 'three_ordered_quality_sections':'for j in axes(A,2), p in nzrange(A,j)' in p and 'for i in 1:m' in p and 'for i in 1:n+m' in p,
 'quality_abstract_input':'x::AbstractVector{T}, rhs::AbstractVector{T}' in q,
 'quality_alias_guard':'Base.mightalias(array,x)' in q,
 'quality_precisions':'T === BigFloat && return _wide_solve_quality!' in q and 'if _is_exact(T) === Val(true)' in q,
 'base_alias_ownership':'dataids(A::AbstractArray) = (objectid(A),)' in b and 'dataids(C::CustomArray) = dataids(C.parent)' in b,
 'predecessor_continuation_saved':sha(R/'diagnostics/simplex-core-architecture/STATUS.md')==sha(D/'STATUS.md.before-S2-B') and sha(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')==sha(D/'roadmap.md.before-S2-B'),
 'no_julia_or_candidate':'NO Julia execution' in (R/'docs/superpowers/plans/2026-10-13-price-audit-values-preparation.md').read_text() and not list(D.glob('*.jl')),
}
inputs=[R/f for f in files]+users+[base,ap,R/'diagnostics/simplex-core-architecture/S2-FLIPS.md',R/'diagnostics/simplex-core-architecture/S2-INVENTORY-NOTES.md',R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-STORAGE.md',R/'docs/superpowers/plans/2026-10-13-price-audit-values-preparation.md',R/'docs/superpowers/specs/2026-10-11-simplex-core-architecture-design.md',R/'AGENTS.md',D/'source-check.py',D/'STATUS.md.before-S2-B',D/'roadmap.md.before-S2-B',D/'read-errors.txt']
out={'checks':checks,'all_passed':all(checks.values()),'source_comparisons':comparisons,'AP_closure_bindings':old,'sha256':{str(p):sha(p) for p in inputs},'scope':'Literal source checks and read-time hashes only; no Julia/parser/runtime/numerical validation.'}
with (D/'source-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'source_files':len(files),'pins':len(out['sha256']),'all_passed':out['all_passed']}))
assert out['all_passed']
