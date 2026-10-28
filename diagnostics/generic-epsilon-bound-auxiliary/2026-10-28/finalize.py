from pathlib import Path
import sys,json,shutil,statistics as stats
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
M=c.M;R=c.R
# Validate the accepted preparation and every review binding before any mutation.
from publication_checks import verify_historical_maps
integration_map=c.read('integration-historical-path-map.json');protected=c.read('protected-before.json');baseline=c.read('baseline-tree.json');production=c.read('production-commit.json')
main_index=c.git(['rev-parse','--path-format=absolute','--git-path','index'])
prospective=dict(master_source_before=integration_map['source_before'],master_index_before=integration_map['master_index_before'])
verify_historical_maps(D,M,main_index,c.TARGET,production['names'],integration_map,prospective,protected,baseline,c.need,c.sha)
exact_before={**integration_map['source_before'],**integration_map['master_index_before']}
for n in ['finalization-preparation-review.json','publication-preparation-reviewed.json','production-review.json','commit-review.json','MASTER-run/result-review.json','GREEN-run/result-review.json']:
 r=c.read(n);c.need(r['accepted'] is True and r['findings']==[],'review '+n)
 for bound_path,bound_hash in r['bindings'].items():
  if c.sha(bound_path)==bound_hash:continue
  c.need(bound_path in exact_before,'unresolved prefinal review binding '+bound_path)
  old=exact_before[bound_path];c.need(old['sha256']==bound_hash and c.sha(old['before'])==bound_hash,'exact prefinal before binding '+bound_path)
# Require the complete current protected state before any finalization write.
for protected_path,protected_hash in protected['files'].items():
 c.need(c.sha(protected_path)==protected_hash,'current protected file before finalization '+protected_path)
for protected_path,protected_hash in c.read('MASTER-run/protected-before.json')['indexes'].items():
 c.need(c.sha(protected_path)==protected_hash,'current protected index before finalization '+protected_path)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'master published')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
c.need(c.git(['branch','--show-current'])=='master' and c.git(['rev-parse','master'])==target,'current master branch/ref before finalization')
c.need(c.git(['branch','--show-current'],R)=='codex/simplex-core-architecture','current diagnostic branch before finalization')
expected_diagnostic=c.read('host-before.json')['diagnostic_head']
c.need(c.git(['rev-parse','HEAD'],R)==c.git(['rev-parse','origin/codex/simplex-core-architecture'],R)==c.git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]==expected_diagnostic,'diagnostic local/tracking/live refs before first mutation')
g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-run/audit.json');cmp=c.read('audit.json');c.need(g['passed']==m['passed'] and g['expected_failures']==m['expected_failures']==0,'same all-pass GREEN/MASTER')
for tree in ['src','test']:c.need({str(p.relative_to(M)):c.sha(p) for p in (M/tree).rglob('*') if p.is_file()}=={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN'/tree).rglob('*') if p.is_file()},'actual tested whole tree')
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
h=c.host(extra);c.put('finalization-host.json',h)
I=D/'before-diagnostic';I.mkdir();ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R);shutil.copyfile(ri,I/'diagnostic.index');c.put('diagnostic-index-before.json',{ri:dict(before=str(I/'diagnostic.index'),sha256=c.sha(I/'diagnostic.index'))})
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n')
B=D/'continuation-before';B.mkdir();cont=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in cont:
 c.need(c.sha(p)==c.read('protected-before.json')['files'][str(p)],'continuation original bytes');f=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,f);mapping[str(p)]=dict(before=str(f),sha256=c.sha(f))
hist=c.read('integration-historical-path-map.json');c.put('historical-path-map.json',dict(master_before=c.TARGET,master_source_before=hist['source_before'],master_index_before=hist['master_index_before'],continuation_before=mapping,all_older_maps_preserved=True))
accepted=c.read('result-review.json')['accepted_variants']
report=f"""# Epsilon, bound placeholder and auxiliary basis integration

Production `{target}`, sole parent `{c.TARGET}`, is normally pushed and remotely verified after independent source/work-memory review and ordinary RED/GREEN/actualMASTER qualification. Exact changed paths: {', '.join(co['names'])}. Accepted variants: {','.join(accepted)}.

A shares the same fresh eps(one(BigFloat)) once per complete direction residual check, retaining the first T(256) construction and every arithmetic/finite/index/dimension/pivot guard. No cross-call/context cache or new pass/solve. Across360 BigFloat cells:30fewer aggregate allocation events and912–1200fewer bytes per call; median-of-cell paired time ratios about0.94–0.95, with the slower cell/outliers preserved.

B avoids unused zero(BigFloat/RationalBigInt) endpoint placeholders only. Existing value is read numerically only behind the original corresponding bound predicate; finite conversions and every metric operation/output scalar alias remain. Frequency is initial refinement metrics and each reached candidate metric;0..2 avoided zeros per variable, same O(m+n) traversal, no new field/cache/solve. Free-bound time ratios about0.57/0.60 for BigFloat/RationalBigInt; mixed about0.89/0.925. Fully bounded controls have no intended savings; all small byte/event/time fluctuations remain recorded with cause unqualified.

C passes fresh first-copy/vcat basis vectors to the existing owned constructor, removing two duplicate arrays plus m Int and m+n+k enum element copies. Later workspace basis copying and factor/recompute/solver/witness/finally/stop/observer work remain. All68 supported floating cell medians save4aggregate allocation events and160–192bytes. Timing benefit is unestablished: BigFloat median ratio0.998, native about0.99; many individual/cell slowdowns remain. BigFloat540pairs include one92-event increase and two100-event decreases; all others save4events. Float64 individual byte savings0–320 disallow an all-pair positive-byte claim. Native strict event and median-byte regression gates are used; no timing threshold.

Original comparison remains FAILED:55,626passed/1failed/2errors, exit1, unsupported original precision(Rational) wrapper before C changed body. Exact types are already excluded by the real LP controller. No solver precision fix or numerical workaround. Separate strict prefix audit accepts only1,196complete cells/21,528windows; a separately admitted completion measured only30 previously missing B/RationalInt64 cells/540windows and passed1,428ordinary assertions. Corrected conventional RationalC tests preserve MethodError and unchanged parent values/owners/budget. Eight RationalC performance cells are excluded; no RationalC body/performance qualification is claimed. All original failed scripts/raw/rejections/pins and beforeimages remain frozen. Early offline count/metadata/provenance corrections were separate, never retroactive launch pins.

The complete supported union is1,226cells/22,068measured windows/1,266preparation records across19contexts (BigFloat64/128/256 and five rounding modes, native/fixed/exact controls). Every measured compile/recompile count is zero; all4GCwindows remain included. Each cell has3warm and9alternating measured pairs. Fixture/reset/cold/warm/validation/consumption/GC costs remain separate. First measured cold calls followed correctness tests, not isolated process startup. Full metrics, input/scalar-limb/array ownership, stored precision, signed/nonfinite/empty/dimension/index controls, real auxiliary result/witness/shared budget, callback failure and finite/expired stop checks are retained. See MEASUREMENT.md, summary.json/groups.json and both raw TOMLs for exact per-cell ratios/extrema/MAD/outliers. Aggregate GC allocation traffic may include native allocations; it is not a native malloc/free or retained-memory ledger, nor end-to-end/universal speedup proof.

Original production RED: {red['passed']}PASS + exactly {red['expected_failures']} expected allocation failures, total {red['total']}. Twelve permanent3warm/3alternating-pair gates require fewer events in each pair and lower median bytes; all old tests/thresholds remain byte-identical, no exception or timing assertion. GREEN and actualMASTER pass {g['passed']}/{m['passed']} in the same {len(c.read('MASTER-run/contract.json')['files'])} ordered complete files, shared {g['elapsed_shared_seconds']:.3f}/{m['elapsed_shared_seconds']:.3f}s. Ordinary Test, no own recorder/manual stack. Broader/full-suite/x64/platform coverage remains OPEN.

Independent review found no unnecessary added production scans, solves, copies, conversions, repeated invariant checks or persistent data memory. B/C add cold method/code metadata whose native retention is unmeasured. Numerical ordering, safeguards/tolerances, ownership, callback/repair semantics and fallbacks remain. Private-index exact commit, ff-only actualmaster, full tested trees, normal push and remote refs are verified. User files/environment/unrelated indexes remain protected. Exact older source/index/continuation bindings map only to baseline/before-master/continuation-before; all older maps preserved. Final host covers {len(h['groups'])}groups ANDsessions, boot/start_ticks/command/noJulia; sole exact unrelated WSL identity allowance unchanged. CIoff, automationpaused, HHreuse disabled; no cleanup or automatic next experiment.

This record is prepared after production verification/publication. At preparation, diagnostic closure/publication are still pending; canonical closure.json, diagnostic-publication-plan.json and publication-after.json record their subsequent outcomes.
"""
(D/'FINAL-REPORT.md').write_text(report)
head=f"""# Current continuation — epsilon, bound and auxiliary integration completed, 2026-10-28

Master/origin/master `{target}` normally pushed/remotely verified; A/B/C accepted only within documented supported routes. A modest whole BigFloat direction savings; B absent-bound savings; C allocation savings without established timing speedup. See diagnostics/generic-epsilon-bound-auxiliary/2026-10-28/FINAL-REPORT.md and independent reviews.

Original comparison FAILED55626PASS/1FAIL/2ERROR remains frozen; supported prefix1196cells plus separate30B/RationalInt64 completion1428PASS =>1226cells/22068compilezero windows/4GC retained. RationalC wrapper unsupportedoriginalMethodError preserved; no productionprecisionfix or RationalC performance claim. OriginalRED{red['passed']}PASS+{red['expected_failures']}expectedcostFAIL; GREEN/actualMASTER{m['passed']}PASS each/{len(c.read('MASTER-run/contract.json')['files'])}samewholefiles. Exactsourceinverse/privateindex/actualcommitreview/ffonly/freshMASTER/normalpush verified. At preparation, diagnosticclosure/publication remain pending; canonical records contain later outcomes. Older actualM235eedf source/test/index bindings resolve ONLY newbaseline/before-master; prior O current STATUS/roadmap bindings ONLY newcontinuation-before; all older maps stay unchanged. ALL evidence/scripts/raw/rejections frozenNEVERRERUN/rewrite. Userfiles/env/unrelatedindexes protected; fullgroupsANDsessions/boot/start_ticks/command/noJulia. CIoff automationpaused HHdisabled; broader/fullsuite/x64/native-retentionOPEN. No automatic next experiment/cleanup.

## Previous continuation — preserved verbatim below

"""
for p in cont:p.write_bytes(head.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'Accepted {accepted}; original failedcomparison preserved; supported1226cells/22068windows, RED{red["passed"]}+{red["expected_failures"]}expected, GREEN/MASTER{m["passed"]}PASS; normalmasterpush remotelyverified; broaderOPEN.\n')
print('final report and exact continuation prepared',target)
