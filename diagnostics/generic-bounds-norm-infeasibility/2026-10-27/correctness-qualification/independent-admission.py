from pathlib import Path
import sys,json,re,tomllib,ast
sys.dont_write_bytecode=True
O=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');Q=O/'comparison-2';D=O/'correctness-qualification';sys.path.insert(0,str(D));import common as c
c.unchanged();h=c.host();assert len(h['groups'])==641 and len(c.read('pins.json')['inventory'])==1340
for n,v in c.read('oracle-correction.json')['bindings'].items():assert c.sha(n)==v
for n,v in json.loads((Q/'admission.json').read_text())['bindings'].items():assert c.sha(n)==v
log=(Q/'output/run.log').read_text();sites=re.findall(r'Test Failed at ([^\n]+)',log);assert len(sites)==18 and set(sites)=={str(Q/'extra-tests.jl')+':13'}
assert '51891 passed, 18 failed, 0 errored, 0 broken' in log
r=tomllib.loads((Q/'output/results.toml').read_text());assert len(r['cells'])==1632 and sum(len(c['windows']) for c in r['cells'])==29376
assert all(w['compile_seconds']==w['recompile_seconds']==0 for cell in r['cells'] for w in cell['windows'])
p=json.loads((Q/'output/process.json').read_text());assert p['returncode']==1 and p['pins_unchanged'] and not json.loads((Q/'supervisor.json').read_text())['accepted']
s=(D/'extra-corrected.jl').read_text();old=(Q/'extra-tests.jl').read_text();start=s.index('    poisoned =');end=s.index('    x=whole',start)
assert s[:start]+'    @test r[1]===:value&&same(r[2][2],floatmax(BigFloat))\n'+s[end:]==old
assert 'wide && any(sign<0 for sign in signs) && rounding(BigFloat) in (RoundNearest,RoundUp,RoundFromZero)' in s
assert s.count('@test')==old.count('@test')+4
co=c.read('contract.json');assert co['cases']==co['measured_windows']==0 and co['expected_exit']==0
sdriver=(D/'driver.jl').read_text();assert '@timed' not in sdriver and 'timed(' not in sdriver and 'cell(' not in sdriver
for name in ['Reference','A','B','C','fixtures']:assert str(Q/(name+'.jl')) in sdriver
for name in ['common.py','launch.py']:assert (D/name).read_bytes()==(Q/name).read_bytes();ast.parse((D/name).read_text())
for name in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (D/'guard'/name).read_bytes()==(Q/'guard'/name).read_bytes()
c.put('independent-host.json',h)
report='''# Independent correctness-only qualification admission

Accepted for one bounded correctness-only launch. No Julia, parser/query probe or benchmark rerun was executed by this reviewer. Fresh 1,340 pins/protected refs/files/environment and 641 historical groups AND sessions with identity/no-Julia/memory checks passed.

The comparison-2 failure is preserved: 51,891 pass, 18 fail, zero errors; all 18 failure sites are the unconditional cap assertion at extra-tests.jl:13. Independent raw-data inspection found 1,632 cells, 29,376 windows and zero compile/recompile time in every measured window. The process remains exit1, pins unchanged, supervisor rejected. No retroactive PASS is granted and raw performance data is not qualified by this admission alone.

Source-derived correction: a stored 512-bit finite negative floatmax input undergoes current-precision unary negation in _primal_direction_magnitude. Base mpfr.jl implements unary minus with a fresh current-precision BigFloat and mpfr_neg. Under Nearest/Up/FromZero this overflows to positive infinity. Scale becomes infinity, finite coefficients divided by scale and inv(scale) are zero, factor is zero, and the final product is NaN. Reference and B preserve that NaN. This applies to precisely 3 precisions x 3 modes x 2 negative-containing wide patterns = 18 cases; the other 72 cap expectations remain. My earlier broad cap expectation was incorrect and this review explicitly corrects it.

The new extra-corrected file differs only at that assertion: a narrow source-derived classifier expects NaN in those 18 cases, retains cap equality elsewhere, and adds four checks for finite stored512 negative input, current-precision positive infinite magnitude, zero ratios/inverse, and NaN product. All existing parity, precision, context, ownership, certificate and native/exact checks remain. No tolerance, arithmetic, production candidate, original fixture or original raw record changes.

The new driver includes the exact comparison-2 private modules and fixtures, runs original correctness plus corrected extra checks in all 19 contexts using ordinary Test, and has no timing/window call. Resource/ownership guards and common/launch files are identical to comparison-2. Contract has zero measured cells/windows and expected exit zero. Subsequent cost-data qualification must separately link a successful correctness run to the unchanged original raw records while continuing to describe comparison-2 as failed.

Computational work/memory: no production change or added retained cache, scan, solve, copy or conversion. Four extra stage assertions only run in correctness qualification; no performance benefit is inferred. Previous A readiness and cold method metadata costs remain part of the pending performance assessment.
'''
with (D/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-admission.py').open('x') as f:f.write(Path(__file__).read_text())
names=['pins.json','contract.json','oracle-correction.json','driver.jl','extra-corrected.jl','common.py','launch.py','ADMISSION-REVIEW.md','independent-host.json','independent-admission.py']
c.put('admission.json',dict(accepted=True,findings=[],bindings={str(D/n):c.sha(D/n) for n in names},Julia_executed=False,pins=1340,groups=641,scope='one correctness-only qualification; no measured windows'))
print('accepted correctness-only qualification; 1340 pins; 641 groups; no Julia')
