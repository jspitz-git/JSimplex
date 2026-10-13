"""One-shot correction of three literal selectors; no raw/numerical rerun."""
from pathlib import Path
import json,hashlib
G=Path(__file__).resolve().parent;R=G.parents[3];E=G.parent/'MA-E';F=G.parent/'MA-F-repair';pins={}
def read(p):
 b=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b.decode()
read(Path(__file__));a=json.loads(read(G/'analysis.json'));read(G/'analyze.py')
c=read(E/'overlays/candidate/src/markowitz_factorization.jl');r=read(E/'overlays/reference/src/markowitz_factorization.jl');d=read(F/'driver.jl')
failed=[k for k,v in a['checks'].items() if not v]
checks={'exact_original_three_false':failed==['four_repetitions','bigfloat_rounding_before_ma_loop','no_other_factor_source_change'],
 'full_four':'measured(full_window!,out,b,rhs,4)' in d,
 'upper_four_actual_target_name':'measured(upper_window!,target,w,b,initial,4)' in d,
 'rounding_before_loop':c.index('if !_markowitz_ma_rounding_matches()') < c.index('return _markowitz_ma_upper_solve!(work, upper, diagonal, sparse_pivots)',c.index('if !_markowitz_ma_rounding_matches()')),
 'prefix_including_added_comment':r[:r.index('function _backend_forward_solve!')]==c[:c.index('# Private scalar scratch exists only during a single upper substitution.')],
 'suffix_unchanged':r[r.index('function _backend_transpose_solve!'):]==c[c.index('function _backend_transpose_solve!'):],
 'all_other_original_gates_pass':all(v for k,v in a['checks'].items() if k not in failed),
 'original_false_preserved':a['all_passed'] is False}
o={'all_passed':all(checks.values()),'checks':checks,'sha256':pins,'explanation':'Initial analyze.py exited 1: wrong upperfun identifier, whitespace-sensitive helper string and omitted inserted comment. All raw computations remain preserved. Supplement fixes source selectors only; no rewrite or rerun.'}
with (G/'source-supplement.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(o,indent=2))
if not o['all_passed']:raise SystemExit(1)
