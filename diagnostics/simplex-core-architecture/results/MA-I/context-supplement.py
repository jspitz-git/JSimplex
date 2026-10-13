from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;s=(D/'driver.jl').read_text();old=json.loads((D/'additional-tests.json').read_text())
checks={'original_false_only_literal': [k for k,v in old['checks'].items() if not v]==['context_finally'],'actual_Julia_finally': 'finally\n            Test.get_testset()===parent_testset && Test.get_testset_depth()==parent_depth || error("test scope restoration")' in s,'scoped_macro': 'Test.@with_testset ts begin' in s,'removed_API_absent': 'Test.push_testset' not in s and 'Test.pop_testset' not in s}
with (D/'context-supplement.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,cause='New Python literal incorrectly expected a colon after Julia finally. Driver unchanged; original26/27FALSE preserved.',sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['driver.jl','additional-tests.py','additional-tests.json',Path(__file__).name]}),f,indent=2);f.write('\n')
print(checks)
if not all(checks.values()):raise SystemExit(1)
