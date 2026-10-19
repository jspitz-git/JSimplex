from pathlib import Path
import json,sys
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS')
sys.path.insert(0,str(E));import control as c
c.preparation() # requires completed independent review; never launches
ledger=c.R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
c.require(ledger.read_bytes()==(E/'progress.md.before-zero-harness').read_bytes(),'Continuation drift')
h=c.full_host();c.require(c.host_safe(h),'Fresh closure host')
c.save(E/'host-closure.json',h)
with ledger.open('a') as f:f.write('''

Immutable zero-count harness OFFLINE independently accepted. Separate reference/candidate modules, unchanged accepted candidate and350 structural assertions. Five comparison cases (zero tuple, mutable constructor, dimensions, concrete eligibility, original-shaped control),60 records/69 payload files/204 source-schedule calls; four alternating measured pairs per case, seven preparation records including overlapping module loads and tests. Source18 PASS, initial synthetic1104 and extended1298 PASS, independent2950 PASS. Initial constructor observation Dict typing finding fixed by exact one-line Dict{String,Any} change; original preserved. Exact227 preparation inputs plus manifest bound by independent receipt; launch_admitted=false. Ruling: no Julia/query/parser/import/compile/IR, no outer/seal/reservation/output, no old script rerun. Future one300s zero-counts-300 needs fresh host/source/runtime and exact independent admission, then complete audit/external closure/result review. All old P011/RED failures remain unchanged; no production/master/global STATUS/roadmap changes, no allocation-elimination or speedup acceptance. Broader plan remains open; existing worktrees and evidence preserved.
''')
with (E/'progress.md.after-zero-harness').open('xb') as f:f.write(ledger.read_bytes())
with (E/'REPORT.md').open('x') as f:f.write('''# Immutable zero-count harness: offline preparation complete

The concrete driver, guarded controls and strict result auditor are independently accepted for preparation only. Julia has not been started, parsed, imported or compiled. No run, reservation, outer process or numerical result exists.

The driver loads the original and accepted candidate into distinct modules and runs the unchanged candidate tests once: 350 prospective assertions, including independent mutable counters and checked overflow. Five separate cost cases cover all three changed sites and two eligibility caller shapes. Each case has four alternating measured pairs after first-call and warm records. All 60 records preserve separate byte/event invocations and consumed-result costs. Seven preparation records include module loading, fixture/snapshot work and structural-test costs; module records overlap the total load.

Future phase `zero-counts-300` has a 300-second inclusive bound (292-second inner guard plus 8-second cleanup), one Julia/BLAS thread, the existing memory limits, fresh host/source/runtime pins and a separate independent exact-run admission. The auditor requires all 69 payload files, exact test counts, unchanged inputs and owners, strict process/pin/resource linkage and warning-free logs. Nonzero allocations, compilation or GC remain diagnostic data; they do not automatically accept or reject performance.

Offline validation: 18 source checks, 1,104 initial synthetic Python checks, 1,298 revised synthetic checks and 2,950 independent checks passed. Review found one diagnostic dictionary type issue; its original version is preserved and the exact repair was independently checked. Final review has no unresolved findings and found no unnecessary new production work or memory. Initial tests.json's oracle hash maps only to oracle.py.initial; all other initial test hash subjects are unchanged. Source snapshots, old candidate, old P011 and historical failed RED evidence remain frozen.

No production, test, environment, CI or master change. Narrow rejected 32-row path only; the dense 64-row replacement is not an eligible numerical execution. No full BG correctness, native allocation elimination, historical P011 acceptance or end-to-end speedup is claimed. See ADMISSION.md for the complete schedule, memory/work ledger and interpretation limits; review.md and review.json contain the independent conclusion.
''')
closure='''"""One-shot offline preparation closure; no Julia or launch entrypoints."""
from control import *
def main():
 prepared=preparation();validate_environment();validate_stage_binding();validate_probe()
 h=rd(D/'host-closure.json')
 checks={
 'accepted_independent_preparation':rd(D/'review.json')['accepted'] is True and rd(D/'review.json')['launch_admitted'] is False,
 'source18':rd(D/'source-check.json')['all_passed'] is True and len(rd(D/'source-check.json')['checks'])==18 and bindings(rd(D/'source-check.json')),
 'extended1298':rd(D/'tests-extended.json')['all_passed'] is True and rd(D/'tests-extended.json')['count']==1298,
 'independent2950':rd(D/'independent-check.json')['all_passed'] is True and rd(D/'independent-check.json')['count']==2950 and bindings(rd(D/'independent-check.json')),
 'dict_fix3':rd(D/'dict-fix.json')['all_passed'] is True and bindings(rd(D/'dict-fix.json')),
 'fresh_host_277':host_safe(h) and len(h['groups'])==277 and h['head']==ENTRY,
 'master_unchanged':git('rev-parse','master')==MASTER,
 'tracked_index_clean':not git('diff','--name-only') and not git('diff','--cached','--name-only'),
 'no_launch':not (D/'runs').exists() and not (D/'outers').exists(),
 'ledger_snapshot':(R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md').read_bytes()==(D/'progress.md.after-zero-harness').read_bytes(),
 }
 # Only initial oracle was revised after the initial1104 checks.
 initial=rd(D/'tests.json');checks['initial1104_preserved']=initial['all_passed'] is True and initial['count']==1104 and all(sha(D/(n+'.initial' if n=='oracle.py' else n))==v for n,v in initial['sha256'].items())
 checks['extended_bindings']=all(sha(D/n)==v for n,v in rd(D/'tests-extended.json')['sha256'].items())
 paths=sorted(p for p in D.iterdir() if p.is_file())
 record=dict(all_passed=all(checks.values()),checks=checks,julia_invoked=False,sha256={str(p):sha(p) for p in paths})
 save(D/'closure.json',record);require(record['all_passed'],'Closure failed')
 print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(paths))))
if __name__=='__main__':main()
'''
with (E/'closure.py').open('x') as f:f.write(closure)
with (E/'close-preparation.py').open('x') as f:f.write(Path(__file__).read_text())
print('closure/report/continuation saved; no Julia')
