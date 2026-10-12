from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-Q';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
review='''# S4-Q independent numerical and work review

Fresh gpt-6-astra/high review: S4-Q accepted within its diagnostic scope.
No unresolved Critical, Important or Minor findings.

Prelaunch read-only driver review found no findings: exact schedule/counters, prepared
immediate update path, ordinary F API, no factor escape and scalar timer values,
fixed output retention and strict compile/oracle stop. No numerical launch by reviewer.

Final independent inline Python/Fraction checks reconstructed all19,138 P input entries
and Q TOML bits, all960 exact residual inequalities (all nonzero, maximum normalized
ratio0.06196430492264961), all96 measured compile/recompilezero windows,40 schedules/
counters/control/pool captures and all16 measured output-bit-equal pairs. Independently
recomputed six ratio series including dense second-refactor5.757909 outlier. Inclusive
GC-dominated windows do not establish consistent acceleration; cause of outlier unknown.

Reviewer rehashed16 SELECTED launch files, checked5 raw/portable identities, inverseclone,
G's two source matches, unchanged src/test/CI and process-group closure. This was NOT
full558 rehash. Author full558/P567/11checks is separate. No supplied scripts, Julia,
native calls, library loading, hooks, numerical factorizations or benchmarks executed.

One Minor report issue: Q TOML wrongly described as containing all19,138 values including
known solutions. Author treated this as Important for exact file attribution, preserved
the prior report and fixed once offline RED2/GREEN3. P JSON holds19,138 values, Q TOML
19,042 matrix/RHS/incoming values;96 known-solution values remain in pinned P. No raw,
driver, input, clone, plan, pins or auditor edit/rerun. No unresolved or deferred issue.

No unnecessary production computational work, allocations or retained-memory cost
introduced. Diagnostic scans/output storage/nested timers/GC overhead are bounded and
disclosed; numerical safeguards unchanged. Native counts source-derived, not instrumented.
No native-free completion or allocation balance proof; native retention OPEN and reuse
disabled. Proposed source-only S4-R respects these limits, no automatic hook/solver run.
'''
(D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT-REVIEW.md').write_text(review)
p=D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md';s=p.read_text().replace('Fresh independent numerical/work review pending.','Fresh independent gpt-6-astra review accepted, no unresolved Critical/Important/Minor.\nReviewer all19,138inputs/all960exactresiduals/16selectedhashes/raw5/stats; authorfull558\nseparate. One input-file wording issue fixed offline RED2/GREEN3, prior report preserved.');p.write_text(s)
p=D/'STATUS.md';s=p.read_text().replace('S4-Q nonsymmetric fixed-history measurement completed, final independent review closing','S4-Q nonsymmetric fixed-history measurement accepted',1).replace('Reports S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md/REVIEW,results/S4-Q. Final review pending.','Reports S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md/REVIEW,results/S4-Q. Freshgpt6astra\naccepted/no unresolved findings/no unnecessary production work/memory. Reviewerallinputs/\nall960residuals/16samplehashes/raw5; authorfull558 separate. No newdeferredMinor.',1);p.write_text(s)
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';s=p.read_text().replace('work/diagnostic/owner limits explicit, native retentionOPEN. Final review pending;','work/diagnostic/owner limits explicit, native retentionOPEN. Freshgpt6astra accepted,\nno unresolved findings/no unnecessary production work/memory; reviewerallinputs/residuals/\n16samplehashes/raw5, authorfull558 separate;',1);p.write_text(s)
p=E/'ledger.md';s=p.read_text().replace('Fresh final independent review pending.','Fresh gpt-6-astra final review accepted/no unresolved findings/no unnecessary production\nwork/memory. Reviewerall19,138inputs/all960residuals/16selectedhashes/raw5/inverseclone/\nsource/work/statistics; authorfull558 separate. No newly deferred Minor.');p.write_text(s)
a=[];proc=json.loads((E/'cost-1-process.json').read_text());groups={proc[n]['pgid'] for n in ['runner','child']}
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if int(st[2]) in groups or (p/'comm').read_text().strip().startswith('julia'):a.append([p.name,st[2],st[19],cmd])
 except (OSError,ValueError):pass
h=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),matches=a,pids_present=[proc[n]['pid'] for n in ['runner','child'] if Path('/proc',str(proc[n]['pid'])).exists()],time_ns=time.time_ns(),refs=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True),remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True))
with (E/'host-final.json').open('x') as f:json.dump(h,f,indent=2);f.write('\n')
pins=json.loads((E/'cost-1-pins.json').read_text());pre=json.loads((E/'preflight.json').read_text());audit=json.loads((E/'audit.json').read_text());ind=json.loads((E/'independent.json').read_text());fix=json.loads((E/'review-fix.json').read_text())
checks={'full558_unchanged':all(sha(p)==v['sha256'] for p,v in pins['inventory'].items()),'user6_unchanged':all(sha(p)==v for p,v in pre['user_hashes'].items()),'both_groups_pids_noJulia':not h['matches'] and not h['pids_present'],'same_boot':h['boot_id']==proc['runner']['boot_id'],'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298','production_test_ci_equal':not subprocess.check_output(['git','diff','master','--','src','test','.github']),'audit28_independent11':audit['all_passed'] and len(audit['checks'])==28 and ind['all_passed'] and len(ind['checks'])==11,'offline_fix_preserved':fix['all_passed'] and (E/'report-before-input-wording.md').exists(),'next_source_only':'SOURCE/EVIDENCE ONLY' in (R/'docs/superpowers/plans/2026-10-12-hh-public-controller-reuse-contract.md').read_text(),'review_accepted':'No unresolved Critical, Important or Minor findings.' in review}
files=[p for p in E.iterdir() if p.is_file()]+[D/'STATUS.md',D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md',D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-12-hh-public-controller-reuse-contract.md']
with (E/'closure.json').open('x') as out:json.dump(dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in files},scope='Closure hashes; post-exit documents/auditor are NOT launch pins'),out,indent=2);out.write('\n')
print(checks);assert all(checks.values())
