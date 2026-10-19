"""New offline source verification; no old scripts or execution entrypoints."""
from pathlib import Path
import ast,json,hashlib
import control as c
D=Path(__file__).resolve().parent
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
check('python_syntax',True)
c.validate_environment();c.validate_stage_binding();c.validate_probe();c.validate_typed();c.validate_sources();check('actual_stage_candidate_repair_runtime_baselines',True)
check('copied_controls',all(c.sha(D/n)==c.sha(v['source'])==v['sha256'] for n,v in c.rd(D/'copied-files.json').items()))
check('current_280_groups',len(c.rd(D/'historical-groups.json')['groups'])==280)
check('no_run_paths',all(not (D/n).exists() for n in ['runs','outers','reservation.json','sealed.json']))
check('synthetic_checks',c.rd(D/'tests.json')['all_passed'] and c.rd(D/'tests.json')['count']==864)
check('synthetic_source_bindings',all(c.sha(D/n)==v for n,v in c.rd(D/'tests.json')['sha256'].items()))
text=(D/'driver.jl').read_text()
check('top_level_includes_before_main',text.index('const TESTS_LOAD')<text.index('function main'))
check('one_full_suite_entry',text.count('B.run_task1_tests()')==1)
check('one_additional_probe',text.count('B.p011_probe(setup.value)')==1)
check('phase_configs',all(c.config(p)['seconds']==300 and c.config(p)['expected_exit']==e for p,e in [('p011-red300',1),('p011-green300',0)]))
check('stage_has_75_files',len(c.rd(D/'stages.json')['red']['sha256'])==75)
check('runtime_has_609_files',len(c.rd(D/'runtime-inputs-complete.json')['inventory'])==609)
files=[p for p in D.iterdir() if p.is_file()]
c.save(D/'source-check.json',dict(all_passed=True,checks=checks,scope='Python AST/literal and current source/hash checks only; Julia entirely unexecuted',sha256={str(p):c.sha(p) for p in sorted(files)}))
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(files))))
