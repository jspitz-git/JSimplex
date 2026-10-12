"""Single offline documentation correction; exclusive preservation/output."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[4];r=Path(__file__).resolve().parent
report=root/'diagnostics/simplex-core-architecture/S4-PUBLIC-CONTROLLER-ATTEMPT-CONTRACT.md'
plan=root/'docs/superpowers/plans/2026-10-12-hh-postsolve-dual-work-contract.md'
a=report.read_text();b=plan.read_text()
red={'body_count_off_by_one':'caps nonprogress rounds at min(2,max_recovery_rounds)' in a,'remaining_dependency_overclaim':'The exact\nremaining dependency is' in a,'partial_budget_gate':'If finite composition is supported' in b}
assert all(red.values())
for p,s in [(r/'report-before-review.md',a),(r/'next-plan-before-review.md',b)]:
 with p.open('x') as f:f.write(s)
a=a.replace('caps nonprogress rounds at min(2,max_recovery_rounds), resetting after progress and\n  permitting a final verification. This is not three total factorizations or verifications.', 'checks rounds >= min(2,max_recovery_rounds) AFTER the body verification/method dispatch,\n  then increments rounds. Starting at zero permits at most cap+1 bodies without progress\n  (three at cap=2), plus a conditional final verification. Progress resets rounds; repeated\n  signatures or earlier guards can stop sooner. This is not three total factorizations\n  or verifications across the whole controller.')
a=a.replace('The exact\nremaining dependency is a branch/rank composition for the original-cleanup dual route,\nincluding legacy recursive numerical repairs and auxiliary ownership.', 'The next selected unresolved\ndependency is a branch/rank composition for the original-cleanup dual route, including\nlegacy recursive numerical repairs and auxiliary ownership. Other UNKNOWN multiplicities,\nincluding the direct primal candidate-retry aggregate above, remain separate blockers;\nclosing the selected dual composition alone would not establish the whole public budget.')
b=b.replace('If finite composition is supported, write one subsequent\nsource-only minimal PRE-forward attempt accounting design with exact inverse/ownership and\nbounded overhead; it still cannot authorize loading or a numerical pair while bootstrap\nis OPEN.', 'Only if a finite COMPLETE prospective public-route budget is supported, including every\nother W UNKNOWN multiplicity such as direct primal candidate retries, may a subsequent\nsource-only minimal PRE-forward accounting design be selected. Closing the selected dual\ncomposition alone is insufficient. Any design must provide exact inverse/ownership and\nbounded overhead, and cannot authorize loading or a numerical pair while bootstrap is OPEN.')
green={'body_limit_explicit':'cap+1 bodies without progress' in a,'ordering_explicit':'AFTER the body verification/method dispatch' in a,'other_unknowns_kept':'direct primal candidate-retry aggregate' in a,'complete_budget_gate':'finite COMPLETE prospective public-route budget' in b,'selected_composition_insufficient':'Closing the selected dual\ncomposition alone is insufficient.' in b}
assert all(green.values())
report.write_text(a);plan.write_text(b)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out={'red_expected_findings':red,'green':green,'all_passed':all(green.values()),'scope':'Source/text correction only; no numerical calls, old evidence/scripts unchanged','ledger_amendment':'cleanup driver row: at most cap+1 consecutive no-progress loop bodies from rounds=0, since rounds limit is checked after verification/dispatch; cap=min(2,max_recovery_rounds). At most three at cap=2, plus conditional final verification. Progress resets; no whole-controller bound.', 'sha256':{str(p.relative_to(root)):sha(p) for p in [report,plan,r/'report-before-review.md',r/'next-plan-before-review.md',r/'source-contract.json',r/'attempt-ledger.json',r/'independent.json']}}
with (r/'review-fix.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'red':red,'green':green,'all_passed':out['all_passed']}))
