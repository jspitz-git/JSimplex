from pathlib import Path
import sys,json,ast
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27')
sys.path.insert(0,str(D))
# Final reviewed filenames are supplied explicitly after the author's syntax correction.
common_name,launch_name,driver_name,extra_name,contract_name,pins_name=sys.argv[1:]
c=__import__(common_name.removesuffix('.py'))
c.unchanged();h=c.host();assert len(h['groups'])==637
old=c.read('admission.json');assert not old['accepted']
for n,v in old['bindings'].items():assert c.sha(n)==v
ref=(D/'Reference.jl').read_text()
for ch in c.read('changes.json'):
 assert (D/(ch['variant']+'.jl')).read_text()==ref.replace('module BNIReference','module BNI'+ch['variant'],1).replace(ch['old'],ch['new'],1)
assert (D/driver_name).read_text()==(D/'driver.jl').read_text().replace('include(joinpath(@__DIR__,"fixtures.jl"))','include(joinpath(@__DIR__,"fixtures.jl"))\ninclude(joinpath(@__DIR__,"'+extra_name+'"))',1).replace('t=@timed correctness(T);','t=@timed begin;correctness(T);extra_correctness(T);end;',1)
for n in [common_name,launch_name]:ast.parse((D/n).read_text())
contract=c.read(contract_name);assert contract['cases']==1632 and contract['measured_windows']==29376 and contract['command'][-2]==str(D/driver_name)
assert 'wide ? setprecision' not in (D/extra_name).read_text()
report='''# Independent follow-up admission

Accepted for one bounded diagnostic launch only. No Julia, Julia parser probe, prior audit or diagnostic was executed by this reviewer. Original rejection and all its bindings remain intact.

The sole original finding is resolved by explicit two-entry floatmax vectors with positive/negative/mixed signs at current and stored 512-bit precision. The reference and B outputs must equal current floatmax, retain fresh ownership across calls and avoid aliasing inputs. A separate current-precision positive product checks positive overflow for Nearest/Up/FromZero and finite-cap equality for Down/ToZero. The extra fixture uses explicit if/else for the wide-precision do-block, removing the avoidable ternary parse ambiguity. All new code was read for scoping, return shapes and signatures.

Added certificate tests preserve actual 512-bit rho inputs for both orientations/signs. The exact-zero two-term sparse-column case must remain false with an unbounded lower side because interval widening straddles zero. Existing source, guards and numerical safeguards are unchanged; native controls run the applicable rejection test.

The reviewed driver differs only by including the extra test file and counting its execution in preparation/correctness cost. All 1,632 cells, 29,376 windows, 3 warmups and 9 alternating pairs remain unchanged. Exact source inverses and all original admission bindings were rechecked. Reviewed pins, authoritative refs, protected files/indexes and environment passed. Fresh 637-group/session boot/start-ticks/command/no-Julia and fixed WSL allowance checks passed. The reviewed launcher retains the original exclusive single-attempt 600-second guard protocol.

Computational work/memory assessment from ADMISSION-REVIEW.md remains valid: no unnecessary added production scan, solve, copy, conversion or retained cache; readiness checks and cold method metadata remain counted. Added correctness fixtures are outside measured kernels and their cost is retained. This admission makes no speedup, actual numerical-pass, allocation reduction, native retained-memory or production integration claim; those require the admitted results and later review.
'''
c.put('independent-ready-host.json',h)
with (D/'ADMISSION-READY.md').open('x') as f:f.write(report)
with (D/'independent-ready.py').open('x') as f:f.write(Path(__file__).read_text())
names=[common_name,launch_name,driver_name,extra_name,contract_name,pins_name,'admission.json','ADMISSION-REVIEW.md','independent-ready-host.json','ADMISSION-READY.md','independent-ready.py']
bindings={str(D/n):c.sha(D/n) for n in names}
c.put('admission-ready.json',dict(accepted=True,findings=[],bindings=bindings,Julia_executed=False,scope='one bounded diagnostic launch only',pin_count=len(c.read(pins_name)['inventory']),groups=637,cells=1632,windows=29376))
print(json.dumps(dict(accepted=True,pins=len(c.read(pins_name)['inventory']),Julia_executed=False)))
