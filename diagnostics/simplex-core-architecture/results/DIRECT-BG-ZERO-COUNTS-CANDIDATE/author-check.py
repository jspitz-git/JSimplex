"""Independent author read-pass of saved preparation; no Julia or old checker runs."""
from pathlib import Path
import hashlib,json,re,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((E/'source-check.json').read_text());red=json.loads((E/'structural-red.json').read_text());t=(E/'zero-counts-tests.jl').read_text()
sections=t.split('    @testset ')[1:];literal=[len(re.findall(r'@test(?:_throws)?\b',x)) for x in sections];expanded=sum(x*y for x,y in zip(literal,[1,20,1,13,1]))
checks={'saved_source_pass':s['all_passed'] is True and all(s['checks'].values()),'all_source_hashes':all(sha(Path(n))==h for n,h in s['sha256'].items()),'saved_text_red':red['expected_red'] is True and not any(red['checks'].values()),'red_hashes':all(sha(Path(n))==h for n,h in red['sha256'].items()),'literal_test_counts':literal==[7,15,10,2,7],'prospective_assertions':expanded==350,'only_definition_no_autoentry':t.count('run_zero_counts_tests()')==1,'old_P011_preserved':'@check "P011" (@allocated K._bgb_eligibility(f,1)) == 0' in (R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl').read_text(),'tracked_unchanged':not subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).strip()}
paths=[E/x for x in ['REPORT.md','panel.jl','zero-counts-tests.jl','source-check.json','structural-red.json','author-check.py']]
result={'all_passed':all(checks.values()),'checks':checks,'literal_per_testset':literal,'prospective_assertions':expanded,'sha256':{str(p):sha(p) for p in paths},'scope':'Read/hash/literal checks only; no Julia syntax, runtime or allocation qualification'}
with (E/'author-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'prospective_assertions':expanded}))
if not result['all_passed']:raise SystemExit(1)
