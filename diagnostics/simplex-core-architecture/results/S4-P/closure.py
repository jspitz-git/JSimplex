from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-P';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
review='''# S4-P independent numerical and work-contract review

Fresh gpt-6-astra/high read-only review. Critical: none. Important: none. Minor: none.
S4-P accepted as an offline contract; S4-Q remains prospective, no numerical execution.

Reviewer independently decoded and reconstructed all19,138 coefficient/RHS/incoming/
solution entries with fresh inline Python/Fractions, no supplied script reruns or
factorization. All14 stages/12 transitions, exact formulas, patterns, return to B0,
dominance, nonunit directions and exact pivot>39/40 bounds verified. Rounded HH
correctness remains a future gate, not established by this proof.

Actual HH paths support40 constructors,80 refactors,240 updates,960 direct solves,
1200 history applications,240 internal unit transposes,120 source-derived native
numeric/extraction entries and<=120 orientation solves. Prepared copies/immediate
consumption and refactor history/cache clearing checked directly against source.
Owner no-escape, nested timing/GC, output storage, residual work outside windows,
compile-zero and no-retry requirements are adequate implementation gates, NOT already
demonstrated runtime properties. Side output differences remain visible.

No unnecessary production computational work, allocations or retained memory cost
introduced. Production/test/CI match master. Planned diagnostic scans/copies, packing,
reachability/sorting, retirement and output retention are bounded and accounted for.
Numerical safeguards preserved; documentation benchmarks unwarranted. Mixed GC counters
are not native allocation balance; GC/absent roots/flat RSS do not prove native frees.
Native retention OPEN, production reuse disabled, broader obligations unchanged.

Reviewer independently rehashed12 SELECTED files, matched HH/factorization sources
against G pins, checked equality/inclusion of all554 M inventory entries, and all40
prospective schedule entries. This is NOT a full567-file rehash; author full567/11checks
is separate. Reviewer verified actual refs/no Julia/prior whole groups absent. No
file edits, Julia/native/library calls/hooks/compilation, accepted-script reruns or
numerical experiments. No correction pass and no newly deferred Minor.
'''
(D/'S4-HISTORY-LIFECYCLE-COST-CONTRACT-REVIEW.md').write_text(review)
p=D/'STATUS.md';s=p.read_text().replace('S4-P source-only fixed-history lifecycle cost contract under independent review','S4-P source-only fixed-history lifecycle cost contract accepted',1).replace('results/S4-P and separate Q plan. Independent review pending; all rejections unchanged.','results/S4-P and separate Q plan. Freshgpt6astra no Critical/Important/Minor, no\nunnecessary production work/memory. Reviewer all19,138input reconstruction,12selected\nhashes/Gsource/554M inventory comparison; authorfull567 separate. All rejections unchanged.',1);p.write_text(s)
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';s=p.read_text().replace('and mixed GC counters explicitly qualified. Independent review pending.','and mixed GC counters explicitly qualified. Freshgpt6astra nofindings/no unnecessary\nproduction work/memory; reviewerall19,138inputs/12selectedhashes, authorfull567 separate.',1);p.write_text(s)
p=E/'ledger.md';s=p.read_text().replace('Independent fresh gpt-6-astra numerical/work review pending.','Fresh gpt-6-astra/high review no Critical/Important/Minor and no unnecessary production\nwork/memory. Reviewer independently all19,138inputs,12samplehashes/Gsources/554M inventory\ncomparison/40schedule; authorfull567 separate. No fix pass/new deferred Minor. Final\nwhole groups/PIDs/Julia absent, refs and user6 unchanged. Closure hashes separate from\nread-time source inventory; future plan remains unexecuted.');p.write_text(s)
a=json.loads((E/'source-contract.json').read_text());h=json.loads((E/'host-before.json').read_text());f=json.loads((E/'host-final.json').read_text());i=json.loads((E/'independent.json').read_text())
checks={'all567_readtime_hashes_unchanged':all(sha(p)==v for p,v in a['sha256'].items()),'user6_unchanged':h['user_hashes']==f['user_hashes'] and all(sha(p)==v for p,v in h['user_hashes'].items()),'whole_groups_and_old_pids_absent':not f['matches'] and not f['old_pids_present'],'same_boot':h['boot_id']==f['boot_id'],'master_source_test_ci_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298','source26_independent11_pass':a['all_passed'] and i['all_passed'] and len(a['checks'])==26 and len(i['checks'])==11,'review_no_findings':'Critical: none. Important: none. Minor: none.' in review,'prospective_plan_no_execution':'No execution has occurred.' in (R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-measurement.md').read_text()}
files=[p for p in E.iterdir() if p.is_file()]+[D/'STATUS.md',D/'S4-HISTORY-LIFECYCLE-COST-CONTRACT.md',D/'S4-HISTORY-LIFECYCLE-COST-CONTRACT-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-measurement.md']
with (E/'closure.json').open('x') as out:json.dump(dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in files},scope='P closure document hashes, NOT future launch pins'),out,indent=2);out.write('\n')
print(checks);assert all(checks.values())
