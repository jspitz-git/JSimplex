"""Two selector corrections, separate from preserved28/30 FALSE author record."""
from pathlib import Path
import json,hashlib,re
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((E/'offline-check.json').read_text());s=(C/'dynamic-bg-reviewed.jl').read_text()
failed={k for k,v in a['checks'].items() if not v}
checks=dict(original_false_exactly_two=failed=={'Task1_oracle_inverse','no_hot_checker_or_materialization'},original28remain_true=sum(a['checks'].values())==28,original_bindings_unchanged=all(sha(Path(n))==h for n,h in a['sha256'].items()),oracle_exact_prefix=(C/'slot-oracles.jl').read_text()==(C/'slot-upper-tests-reviewed.jl').read_text().split('_bg_test_matrix() =',1)[0].replace('::BGSlotUpper','::J.BGSlotUpper'),no_hot_checker_materialization_sort='_check_bg_slots' not in s and '_bg_selected_state' not in s and 'Matrix(' not in s and not re.search(r'(?<![A-Za-z_])sort!?\(',s),existing_sorted_cache_lookup_retained='searchsortedfirst(c.active_upper,first)' in s)
paths=[Path(__file__).resolve(),E/'offline-check.json',E/'offline-check.py',C/'slot-oracles.jl',C/'slot-upper-tests-reviewed.jl',C/'dynamic-bg-reviewed.jl']
with (E/'offline-check-supplement.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,explanation='Initial oracle marker incorrectly included function keyword; initial sort substring also matched searchsortedfirst. Correct selectors only, no Julia or old script rerun.',sha256={str(p):sha(p) for p in paths}),f,indent=2);f.write('\n')
print('Author selector supplement',sum(checks.values()),'/',len(checks))
if not all(checks.values()):raise SystemExit(1)
