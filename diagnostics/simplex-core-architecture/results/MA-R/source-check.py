from pathlib import Path
import hashlib,json,tomllib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-R';Q=E.parent/'MA-Q'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((E/'source-map.json').read_text());c=(E/'candidate.jl').read_text();r=(E/'reference.jl').read_text();t=(E/'tests.jl').read_text();inst=(E/'instrumented.jl').read_text();f=tomllib.loads((E/'fixtures.toml').read_text())
inv=[]
for b in m['blocks']:
 s=b['candidate']
 for old,new in reversed(b['replacements']):s=s.replace(new,old)
 inv.append(s==b['original'] and s in Path(b['source']).read_text() and (b['candidate'] in c or b['candidate'] in r))
a=c[c.index('function candidate_forward!'):c.index('\n_ma_apply_ma_ipiv_rows!')].strip()
b=inst[inst.index('function instrumented_forward!'):].replace('instrumented_forward!','candidate_forward!').replace('instrumented_transpose!','candidate_transpose!')
b=b.replace('    _route_entries[] += 1\n','').replace('    _route_scratches[] += 1\n','')
for dr in ['forward','transpose']:
 b=b.replace('    if !_dense_ma_eligible(dest, backend, rhs)\n        _route_fallbacks[] += 1\n        return reference_'+dr+'!(dest, backend, rhs)\n    end','    _dense_ma_eligible(dest, backend, rhs) || return reference_'+dr+'!(dest, backend, rhs)')
original_manifest=(R/'Manifest.toml').read_text();derived=(E/'environment/Manifest.toml').read_text();expected=''.join(x for x in original_manifest.splitlines(keepends=True) if not x.startswith('project_hash = ')).replace('path = "."','path = '+json.dumps(str(R)))
checks={
 'seven_exact_source_inverses':len(inv)==7 and all(inv),
 'instrumented_entry_inverse':a==b.strip(),
 'twelve_product_sites':m['blocks'][-1]['candidate'].count('_dense_ma_mul!')==12,
 'eight_branches_six_normalizations':len(m['reachable_normalizations'])==6 and c.count("if tfun === identity")==4,
 'only_product_mutated':'MA.operate_to!(product, *, a, b)' in c and c.count('MA.operate_to!')==1,
 'two_per_entry_scratch_sites':c.count('product = BigFloat()')==2 and '_route_' not in c,
 'shape_size_rounding_gate':all(x in c for x in ['n >= 16','length(dest) == n','length(rhs) == n','Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]']),
 'no_candidate_global_extension':not any(x in c for x in ['function LA.','function Base.','function JSimplex.','ccall(', 'muladd(', 'fma(']),
 '160_cases_162_calls_per_side':3*8*2*2+len(f['specials'])*2+4*2+4*2+2*2+2*2==160 and '==162' in t,
 'frozen52cost_cases':len(f['cost_cases'])==52 and sum(x['eligible'] for x in f['cost_cases'])==36 and len({x['id'] for x in f['cost_cases']})==52,
 'exceptions_caught_before_test':'result = f(x.dest,x.backend,x.rhs)' in t and '@test f(x.dest' not in t,
 'owner_and_partial_state_oracles':all(x in t for x in ['output_owner_map','old_owner_map','factor_owners','rhs_owners','previous.owners','expected_exception']),
 'diagnostic_env_exact_derivation':derived==expected and tomllib.loads((E/'environment/Project.toml').read_text())['compat']['MutableArithmetics']=='=1.8.1',
 'baseline_source_pins_unchanged':all(sha(p)==h for p,h in json.loads((Q/'source-check.json').read_text())['sha256'].items()),
 'six_continuation_bindings_preserved':all(sha(x['preserved'])==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings']),
}
inputs=list(json.loads((Q/'source-check.json').read_text())['sha256'])
inputs+=[p for p in json.loads((Q/'review.json').read_text())['sha256'] if p.endswith('adjtrans.jl')]
inputs+=[str(p) for p in sorted(E.rglob('*')) if p.is_file()]
obj={'scope':'Fresh offline literal/source checks and read-time hashes; no Julia parse/import/runtime proof. No old script executed.','checks':checks,'all_passed':all(checks.values()),'sha256':{p:sha(p) for p in inputs}}
with (E/'source-check.json').open('x') as out:json.dump(obj,out,indent=2);out.write('\n')
print(json.dumps({'checks':checks,'bindings':len(obj['sha256'])}))
if not obj['all_passed']:raise SystemExit(1)
