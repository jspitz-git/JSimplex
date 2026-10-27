from pathlib import Path
import sys,json,re,ast
sys.dont_write_bytecode=True
O=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');D=O/'comparison-2';sys.path.insert(0,str(D));import common as c
c.unchanged();h=c.host();assert len(h['groups'])==639
assert len(c.read('pins.json')['inventory'])==1306
for name in ['pins.json','pins-reviewed.json','pins-ready.json']:
 for n,v in json.loads((O/name).read_text())['inventory'].items():assert c.sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved']
p=json.loads((O/'output/process.json').read_text());assert p['returncode']==1 and p['pins_unchanged']
assert json.loads((O/'supervisor.json').read_text())['accepted'] is False
log=(O/'output/run.log').read_text();assert 'invalid method definition' in log and '_primal_nonnegative_step' in log and 'CONTEXT ' not in log
inventory={}
for arm in ['Reference','A','B','C']:
 s=(D/(arm+'.jl')).read_text();old=(O/(arm+'.jl')).read_text();assert s==old.replace(',_primal_nonnegative_step,',',',1)
 defs=set(re.findall(r'^(?:function\s+)?([A-Za-z_][\w!.]*)\(',s,re.M));imports=set(s.splitlines()[2].split(':',1)[1].strip().split(','));assert not imports&defs
 assert '_primal_nonnegative_step' in defs and '_primal_nonnegative_step' not in imports
 assert all('.' not in name for name in defs)
 inventory[arm]=dict(definitions=sorted(defs),imports=sorted(imports),overlap=[])
ref=(D/'Reference.jl').read_text()
for ch in json.loads((O/'changes.json').read_text()):
 assert (D/(ch['variant']+'.jl')).read_text()==ref.replace('module BNIReference','module BNI'+ch['variant'],1).replace(ch['old'],ch['new'],1)
assert (D/'fixtures.jl').read_bytes()==(O/'fixtures.jl').read_bytes()
assert (D/'extra-tests.jl').read_bytes()==(O/'extra-tests-ready.jl').read_bytes()
assert (D/'driver.jl').read_text()==(O/'driver-ready.jl').read_text().replace('extra-tests-ready.jl','extra-tests.jl')
for name in ['common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py']:ast.parse((D/name).read_text())
assert (D/'launch.py').read_text()==(O/'launch.py').read_text()
assert (D/'common.py').read_text()==(O/'common.py').read_text()
for name in ['guard_reviewed.py','supervisor_reviewed.py','entry_gate.py']:assert (D/'guard'/name).read_bytes()==(O/'guard'/name).read_bytes()
co=c.read('contract.json');oldco=json.loads((O/'contract-ready.json').read_text());oldco['command'][-2:]=[str(D/'driver.jl'),str(D/'output/results.toml')];assert co==oldco
c.put('independent-host.json',h);c.put('independent-symbol-inventory.json',inventory)
report='''# Independent admission of comparison-2

Accepted for one new bounded comparison-2 diagnostic attempt. No Julia, parser probe, query or diagnostic rerun was executed by this reviewer.

Correction of prior review: the earlier hand-maintained definition inventory missed the short-form `_primal_nonnegative_step(value::BigFloat) = ...` definition embedded between the copied ratio methods. The previous statement that imported/local names did not overlap was incorrect. The first actual run failed while loading Reference, before any CONTEXT, test or measured window, with exit 1 and unchanged pins; supervisor rejected it. That record remains a failure and this admission does not retroactively pass it.

Concrete fix: each of Reference/A/B/C removes exactly the `_primal_nonnegative_step` symbol from the using-import list. Its exact copied baseline definition remains private in each module. An explicit import would instead permit unintended JSimplex extension and is not used. Independent inventory now reads both long-form and short-form definitions in all four files: no local definition overlaps the JSimplex import list and no qualified Base/JSimplex definition exists. Candidate inverse replacement checks pass unchanged.

All fixtures and READY extra tests are byte-identical, and the driver only renames its extra-test include. The 1,632 cells/29,376 windows, 3 warmups/9 alternating pairs, ordinary Test, compilation-zero gates, preparation costs and coverage are unchanged from READY. Guards, common checks and launch script are byte-identical to their original counterparts; the contract only relocates driver/output into comparison-2. Each directory has its own exclusive reservation/output and single bounded attempt. No old output is reused as numerical evidence.

All 1,306 new pins and all three prior pin inventories were verified, alongside authoritative refs/protected files/indexes/environment. Fresh no-Julia host inspection covers 639 historical groups AND sessions with boot/start-ticks/command identities, fixed WSL allowance and memory limits. New host and symbol inventory evidence are bound to this admission.

Numerical and computational-work/memory assessment is unchanged by this import-only correction: no added production scan, solve, copy, conversion, arithmetic or retained cache. The private copied helper already existed; making it locally owned adds diagnostic method metadata only. A readiness checks and specialized-method cold costs remain documented; performance, allocation and native retained-memory results remain pending. No tests passed or speedup is claimed by this static admission.
'''
with (D/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
with (D/'independent-admission.py').open('x') as f:f.write(Path(__file__).read_text())
names=['pins.json','contract.json','load-fix.json','Reference.jl','A.jl','B.jl','C.jl','fixtures.jl','extra-tests.jl','driver.jl','common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','ADMISSION-REVIEW.md','independent-host.json','independent-symbol-inventory.json','independent-admission.py']
c.put('admission.json',dict(accepted=True,findings=[],bindings={str(D/n):c.sha(D/n) for n in names},Julia_executed=False,pins=1306,groups=639,scope='comparison-2 single bounded attempt only'))
print('accepted comparison-2, 1306 pins, 639 groups, no Julia')
