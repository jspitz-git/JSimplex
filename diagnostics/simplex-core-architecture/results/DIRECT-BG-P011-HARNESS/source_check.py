"""Source/routing contract, never executes a launcher or frozen checker."""
from pathlib import Path
import json,hashlib,ast
import control as c
D=Path(__file__).resolve().parent
checks={}
for n in ('control.py','launch.py','seal.py','outer.py','post-return.py','guard.py','supervisor.py','audit.py','oracle.py','tests.py','source_check.py'):
 ast.parse((D/n).read_text());checks['python_syntax_'+n]=True
cfg=c.config('p011-300');launch=(D/'launch.py').read_text();seal=(D/'seal.py').read_text();audit=(D/'audit.py').read_text();control=(D/'control.py').read_text()
checks.update(exact_driver=cfg['command'][-3]==str(c.PROBE/'driver.jl'),two_args=len(cfg['command'])==12,
 payload_separate=Path(cfg['payload']).parent==Path(cfg['output']).parent and cfg['payload']!=cfg['output'],
 reservation_before_payload=launch.index("save(res,")<launch.index("Path(cfg['payload']).mkdir")<launch.index('supervisor.run('),
 output_preexists_refused="not Path(cfg['output']).exists() and not Path(cfg['payload']).exists()" in launch,
 old_phase_forbidden="phase == 'p011-300'" in control,
 independent_exact_receipt='P011 diagnostic exact-run admission' in launch and 'P011 diagnostic exact-run admission' in (D/'outer.py').read_text(),
 probe_tree="trees=[cfg['stage'],str(C),str(PROBE)]" in seal and "sealed['trees']==[cfg['stage'],str(C),str(PROBE)]" in control,
 probe_hash=c.sha(c.PROBE/'driver.jl')=='29c8d67755e4f86a7375f89536d24a0cb119a06a583650bc3f31bc9eccc956bf',
 future_controls_unexecuted=not (D/'runs').exists() and not (D/'outers').exists(),
 copied_controls=all(c.sha(D/n)==c.sha(v['source'])==v['sha256'] for n,v in c.rd(D/'copied-files.json').items()),
 payload_parser="tomllib.loads(p.read_text())" in audit,
 original_entry_not_called='run_task1_tests()' not in (c.PROBE/'driver.jl').read_text(),
 no_production_diff=not c.git('diff','HEAD','--name-only'),
 synthetic_tests=c.rd(D/'tests.json')['all_passed'] is True)
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(D/n):c.sha(D/n) for n in ('control.py','launch.py','seal.py','outer.py','post-return.py','guard.py','supervisor.py','audit.py','oracle.py','tests.py','ADMISSION.md')})
c.save(D/'source-check.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks)))
if not result['all_passed']:raise RuntimeError('Source contract refusal')
