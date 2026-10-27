from pathlib import Path
import sys,json,re,ast
sys.dont_write_bytecode=True
O=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');D=O/'RED-run';Q=O/'comparison-2';K=O/'correctness-qualification';R=O/'RED';sys.path.insert(0,str(D));import common as c
c.unchanged();h=c.host();assert len(h['groups'])==643 and len(c.read('pins.json')['inventory'])==1299
co=c.read('contract.json');assert co['expected_exit']==1 and co['expected_failures']==10 and co['shared_limit_seconds']==3000 and co['guard_limit_seconds']==2992
assert co['files']==['generic_bounds_norm_infeasibility_tests.jl']
t=(O/'new-test.jl').read_text();target=R/'test/generic_bounds_norm_infeasibility_tests.jl';assert target.read_text()==t
assert (Q/'Reference.jl').read_text() in t and (Q/'fixtures.jl').read_text() in t and (K/'extra-corrected.jl').read_text() in t
assert 'const BNIA=JSimplex\nconst BNIB=JSimplex\nconst BNIC=JSimplex' in t
for p in (c.M/'src').rglob('*'):
 if p.is_file():assert p.read_bytes()==(R/'src'/p.relative_to(c.M/'src')).read_bytes()
assert {p.relative_to(R/'src') for p in (R/'src').rglob('*') if p.is_file()}=={p.relative_to(c.M/'src') for p in (c.M/'src').rglob('*') if p.is_file()}
assert co['expected_failure_locations']==[[str(target),727]]*10 and '# RED whole-call allocation gate' in t.splitlines()[726]
assert t.count('# RED whole-call allocation gate')==1 and 'for k in 1:3\n' in t
assert 'all(new["events"]<old["events"] for (old,new) in pairs)&&median([new["bytes"] for (old,new) in pairs])<median([old["bytes"] for (old,new) in pairs])' in t
assert 'new["seconds"]<' not in t
for arm in ['Reference']:
 s=(Q/(arm+'.jl')).read_text();defs=set(re.findall(r'^(?:function\s+)?([A-Za-z_][\w!.]*)\(',s,re.M));imports=set(s.splitlines()[2].split(':',1)[1].strip().split(','));assert not defs&imports
for n in ['common.py','launch.py']:ast.parse((D/n).read_text())
assert (D/'common.py').read_bytes()==(Q/'common.py').read_bytes()
assert (D/'launch.py').read_text()==(Q/'launch.py').read_text().replace('592','2992').replace('600','3000')
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (D/'guard'/n).read_bytes()==(Q/'guard'/n).read_bytes()
ast.parse(Path('/tmp/bni-phase-audit.py').read_text())
assert not (D/'output').exists() and not (D/'reservation.json').exists()
c.put('independent-host.json',h)
report='''# Independent RED admission

Accepted for one prospective original-source RED run with expected exit1 and exactly ten allocation-gate failures, all at frozen new-test line 727. No Julia, query/parser probe or old audit was executed by this reviewer. Fresh 1,299 pins and protected refs/files/environment plus 643 historical groups/sessions/boot/start-ticks/command/no-Julia/memory checks passed. Original production remains at 9d29b1f0.

The RED source tree is byte-identical to authoritative current production. The new ordinary test file embeds the exact comparison-2 Reference with its private nonnegative-step helper, exact fixtures and corrected qualification extra tests. All candidate arm constants target JSimplex, so the preimplementation run compares baseline to baseline. Both long- and short-form Reference definitions were checked against imports, with no overlap. The qualified 18-NaN/72-cap expectations and original numerical controls remain unchanged.

Ten fixed gates cover A snap/step/whole ratio for BigFloat and Rational BigInt, B initialization and actual checked-FTRAN maintenance for BigFloat, and C finite/one-sided full certificates below=true. Each gate has three warmups and three alternating measured pairs, compile/recompile-zero assertions, lower events in every pair plus lower median bytes. There is no time threshold, old-test modification, numerical tolerance relaxation or custom Test recorder. All 15,881 qualified correctness assertions plus 30 compile checks and ten cost checks imply 15,921 total assertions if the same branches execute; the contract deliberately requires exact failure locations/count rather than claiming this total has already run.

The source-pinned ordinary include driver binds source/project/thread identity and includes the one complete new test file. Resource ownership/guard code is unchanged; launch only scales the established absolute/shared limits to 2,992/3,000 seconds. This is a ceiling, not an expected duration. The post-exit phase-auditor template was inspected but not executed: it checks exact ordinary summary headers without errors/skips/broken tests, all ten failure locations, ordered includes/source marker, expected exit, gate/permit/hash identities, full resource/terminal checks and post-exit closure. Actual RED evidence remains required before production staging.

The separate offline preparation failure is retained; it did not launch Julia and is not treated as a successful run. No existing record is replaced by this admission.

Computational work/memory review: this phase adds test-only fixtures, a cold private baseline method copy and fixed measurement loops. It introduces no production scan, solve, copy, arithmetic or retained cache. Existing accepted candidate costs and readiness/code-metadata qualifications remain in RESULT-REVIEW.md. The test gates measure allocation events/bytes, not native memory release or an end-to-end speedup.
'''
with (D/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-admission.py').open('x') as f:f.write(Path(__file__).read_text())
paths=[D/n for n in ['pins.json','contract.json','tests.jl','common.py','launch.py','ADMISSION-REVIEW.md','independent-host.json','independent-admission.py']]+[O/'new-test.jl',target,Path('/tmp/bni-phase-audit.py')]
c.put('admission.json',dict(accepted=True,findings=[],bindings={str(p):c.sha(p) for p in paths},expected_exit=1,expected_failures=10,Julia_executed=False,scope='one original-source RED run before candidate staging'))
print('accepted RED admission; 1299 pins; 643 groups; expected 10 allocation failures; no Julia')
