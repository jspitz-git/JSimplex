from pathlib import Path
import sys,json,shutil
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));n=__import__('negative-common')
n.need(n.read('rollback-after.json')['accepted'] is True,'rollback finished');n.refs();n.baseline_and_backup();n.protected()
h=n.host();n.put('negative-finalization-host.json',h)
B=D/'continuation-before';B.mkdir(exist_ok=False);I=D/'before-diagnostic';I.mkdir(exist_ok=False)
ridx=n.git(['rev-parse','--path-format=absolute','--git-path','index'],n.R);shutil.copyfile(ridx,I/'diagnostic.index');n.put('negative-diagnostic-index-before.json',{ridx:dict(before=str(I/'diagnostic.index'),sha256=n.sha(I/'diagnostic.index'))})
paths=[n.R/'diagnostics/simplex-core-architecture/STATUS.md',n.R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in paths:
 old=n.read('protected-before.json')['files'][str(p)];n.need(n.sha(p)==old,'original continuation');q=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,q);mapping[str(p)]=dict(before=str(q),sha256=old)
im=n.read('integration-historical-path-map.json');rb=n.read('rollback-before.json')
n.put('negative-historical-map.json',dict(master_before=n.BASE,master_source_before=im['source_before'],master_index_before=im['master_index_before'],unpromoted_source_before=rb['source_before'],unpromoted_index_before=rb['index_before'],continuation_before=mapping,all_older_maps_preserved=True,absent_introduced_file_resolves_only_exact_rollback_before=True))
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/before-master/\n/rollback-before/\n/before-diagnostic/\n**/__pycache__/\n/negative-publication-after.json\n')
report='''# Epsilon, bound and auxiliary measurements — not promoted

The bounded measurement and production qualification are closed with a negative promotion decision. Combined candidate `717ef2d5dc40b57bfaff198a0a4a48f7198d00db` is preserved on local `codex/generic-epsilon-bound-auxiliary`; it is NOT admitted or pushed to production. The agent's unpublished local fast-forward was reversed with reviewed, recorded steps. The final switch failed on an unrelated broken Codex turn-diff reference after restoring baseline files/index, leaving HEAD detached at717. A separately reviewed HEAD-only completion first proved the whole source tree and ALL index entries already equal baseline235, then attached HEAD to master without source/index writes. The failure, intermediate states and completion evidence remain preserved; no broken reference was removed or rewritten. Actual local and remote master remain `235eedf33901fe8c4cc06a3d8c3508ef2fcbb718`. User files, environment, unrelated staged/untracked state and exact source/index beforeimages are preserved. No permanent GC, threshold change or historical exception was used. Diagnostic publication is separately gated below.

## Whole-function measurements

The supported union contains 1,226 cells / 22,068 windows / 1,266 preparation records across 19 contexts. Each measured cell has three warm pairs and nine alternating measured pairs. Every measured compile/recompile count is zero; all four GC windows, slower cells and outliers remain included. Preparation/reset/validation/consumption costs are separate. Ratios below are medians of cell paired time ratios, not pooled or end-to-end speedups; MEASUREMENT.md and saved raw data give exact distributions.

| Variant | Complete affected function | Supported result |
|---|---|---|
| A: one fresh epsilon per call | BigFloat direction residual check | Time ratios 0.941 bad / 0.952 good; 30 fewer allocation-counter events and 912–1,200 fewer bytes per call. Native controls unchanged. |
| B: avoid unused absent-bound zeros | `_lp_errors` | BigFloat/Rational{BigInt} free-bound time ratios 0.573/0.597; mixed 0.894/0.925. Savings depend on absent bounds; fully bounded controls have no intended saving. |
| C: use existing owned Basis constructor | Actual `_lp_auxiliary_run_at_working_precision` | Supported floating cell medians save four allocation-counter events and 160–192 bytes. Timing benefit unestablished: BigFloat ratio 0.998 and native about 0.99, with slower cases retained. |

A retains construction/order/rounding/pivot guards and no cross-call cache. B removes zero constructors only for numerically unused endpoints; all original finite-bound conversions, traversal, metric operations and returned scalar ownership remain. C retains fresh first-copy/vcat and later independent workspace Basis copying, while avoiding two duplicate vectors (m Int and m+n+k state elements); all actual factor/recompute/solver/witness/stop/callback/finally work remains. No new numerical data field, persistent owner, full scan or basis solve is added. Cold method/code metadata from B/C is unmeasured retained native memory. Independent source/work-memory review found no unnecessary added computational work or retained data memory; it is not final production acceptance.

C is deliberately qualified only for supported floating routes. The initial original measurement remains FAILED: 55,626 pass / one fail / two errors, exit 1 at the already unsupported `precision(Rational)` auxiliary wrapper before C's changed body. The actual LP controller excludes exact types. No solver precision fix or workaround was introduced. A separate strict prefix auditor accepts only its 1,196 completed cells / 21,528 windows; a separately admitted completion measured only the 30 missing B/Rational{Int64} cells / 540 windows, with 1,428 ordinary assertions passing. Eight originally planned Rational C performance cells are excluded, not passed. Conventional exact tests preserve original MethodError, inputs, owners and budget. All initial count/provenance rejections and failed scripts/raw/pins are frozen, never retroactive launch pins.

C's individual floating allocation fluctuations also remain: 540 BigFloat pairs comprise 537 reductions of four events, two reductions of 100 and one increase of 92; cell medians are smaller. Native 72 pairs all save four events; Float64 individual byte savings range 0–320. No all-pair positive-byte or universal timing claim follows.

## Production qualification and stopping decision

Ordinary Test was used throughout, without a custom recorder or manual testset stack. The candidate adds 7,337 assertions, including twelve strict three-warm/three-pair allocation gates. Existing tests, batch sizes, thresholds, arithmetic, safeguards and tolerances are unchanged.

| Phase | Result | Decision |
|---|---|---|
| Original production RED | 7,325 pass + exactly 12 expected cost failures = 7,337 | Expected RED accepted. |
| Private GREEN, same complete regression cohort | 380,372 / 380,372, 83 whole files | Private GREEN accepted. |
| Actual locally integrated MASTER | 380,370 pass + two cost failures = 380,372, same 83 files | Rejected; never pushed. New 7,337 assertions passed. |
| Named counter diagnostic, three whole files | 23,661 pass + two cost failures = 23,663 | Data accepted only; ordinary run failed. |
| One preregistered post-warm full-GC control | 23,662 pass + one cost failure = 23,663 | GC intervention insufficient; stop. |

Actual MASTER's unchanged legacy failures are `generic_unit_perturb_residual_tests.jl:581` (caller601, Rational{BigInt}/C/residual/n64/sparse/mixed/unit) and `generic_dual_comparisons_tests.jl:709` (Rational{BigInt} dense128/free batched update). The former requires fewer events in every pair and lower median bytes; the latter requires over 3% byte AND event reduction in each pair. All numerical assertions and the new candidate gates passed, but that does not waive these two cost conditions. Historical `7e306e24` exception is NOT reused. Source/direct helpers and these old tests are byte-identical to baseline; a direct new-ABC causal mechanism is unproved.

The named diagnostic reproduced both byte failures with measured GC/compile/recompile zero. Residual reference bytes [89456,89968,90032] versus candidate [91024,92192,91440], events 2254→2251 in each pair. The dense/free second pair saved only about 2.6% bytes despite events 43736→41720. This is data-only diagnosis, not exact full-suite allocator-state replay.

Installed GMP uses `jl_gc_counted_malloc` / `jl_gc_counted_realloc_with_old_size`; aggregate GC byte traffic includes usable native capacity and positive capacity growth. Fewer events do not force lower byte counts. These sources/data do not establish the particular allocator cause. A fixed single full-GC-after-warmup intervention was therefore measured once, outside all windows with preparation cost retained and every original assertion/warmup/pair/order/threshold unchanged. Four preparation GCs cost 0.227029106, 0.221508906, 0.255886376 and 0.249671976 seconds (total 0.954096364 seconds). Residual bytes still fail: reference [95632,99376,93344], candidate [104464,104464,91008], median 95632→104464, events 2254→2251. Both dense predicates pass only in this trial; causation/general GC repair is not established.

Independent stopping decision rejects permanent GC preparation and further adaptive GC, batch growth, filtering, retry-until-pass or threshold waiver. No such repair is integrated. This does not prove any individual A/B/C optimization invalid or impossible, or a numerical solver defect. Isolating/promoting a different subset would be a new separately reviewed qualification, not an outcome of this completed bounded attempt.

Original MASTER audit.py executed once and failed while opening absent completed.json; exit/error are preserved. The separate reviewed failure postcheck, data-only counter audits and independent reviews preserve rejected outcomes. No old auditor or numerical attempt is rerun/relabelled. All admitted original and corrected scripts, manifests, raw files, reviews and rejected drafts are frozen.

## Preservation, memory and limits

Actual MASTER/GREEN shared elapsed time was 3438.091/3399.695 seconds, including compilation/regression work; not a benchmark. Available-memory minima were 18,250,636/18,120,700 KiB, swap zero, child max RSS 4,778,952/4,785,460 KiB. All original process, command, pin, supervisor, terminal and resource evidence remains. Aggregate allocation traffic is not a native malloc/free, live-memory or retained-memory ledger. No solver-wide/universal/native-free/observer-neutrality or cross-platform full-suite claim is made.

Reviewed rollback preserves candidate717 and all four exact Git blobs, both local index states and original baseline544 files; actual master541 source/test files are restored, new candidate test absent. Historical235 and717 source/index bindings map ONLY explicit baseline/before-master/rollback-before copies; deleted newtest bindings resolve only exact rollback-before bytes. Prior O current STATUS/roadmap bindings map ONLY continuation-before saved bytes; previous text is appended verbatim and all older mappings remain. Full historical groups AND sessions, boot/start_ticks/command/noJulia are freshly checked; the sole exact unrelated WSL identity allowance is unchanged. CI remains off, HH reuse disabled, automation paused, broader plan/fullsuite/x64/native-retention OPEN. No cleanup or automatic next experiment.

This decision report is prepared before diagnostic closure/publication. `negative-closure.json`, `negative-publication-plan.json` and local `negative-publication-after.json` record their later exact outcomes. A PASS negative closure means truthful preservation, never production acceptance. Old positive finalize/closure/publisher scripts remain UNEXECUTED and blocked by failed MASTER.
'''
(D/'FINAL-REPORT.md').write_text(report)
head=f'''# Current continuation — epsilon/bound/auxiliary qualification closed UNPROMOTED, 2026-10-28

Actual local/tracking/live master `{n.BASE}` restored/unchanged. Candidate `{n.CAND}` remains on local codex/generic-epsilon-bound-auxiliary, NOT production-admitted or pushed. Supported helper measurements show A modest BigFloat savings, B absent-bound savings, C allocation saving without established timing benefit. See diagnostics/generic-epsilon-bound-auxiliary/2026-10-28/FINAL-REPORT.md.

Supported union1226cells/22068windows/1266prep/19contexts compilezero/all4GC retained; original55626PASS/1FAIL/2ERROR remains FAILED (unsupported original RationalC wrapper; no productionprecisionfix). Missing30B/RationalInt64 cells1428PASS separately. OriginalRED7325PASS+12expectedcostFAIL; privateGREEN380372PASS/83files; actualMASTER380370PASS+2unchangedlegacycostFAIL remainsREJECTED. Namedcounter23661PASS+2FAIL; onefixedpostwarmGC23662PASS+1FAIL, preparation0.954096364s insufficient. No thresholdwaiver, permanentGC, adaptiveGC/batchgrowth/filter/retry or historical7e306exception. No further tuning under this bounded attempt; no automatic nextexperiment. IndividualA/B/C impossibility or solverdefect NOTproved.

Reviewed reversible rollback preserves candidate717/exact4blobs andsource/indexbeforeimages/userfiles/unrelatedstaged-untrackedstate. Older235bindings ONLY baseline/before-master;717bindings ONLY rollback-before;newtestabsent mappedexactly. PriorO STATUS/roadmapbindings ONLY continuation-before; ALLoldermaps/text preserved. At preparation, separate negativeclosure/diagnosticpublication pending; canonicalnegative records give lateroutcomes and NEVER imply productionacceptance. All scripts/raw/pins/rejections/reviews FROZEN NEVER RERUN/rewrite; oldpositivefinalizers blocked/unexecuted. FreshfullgroupsANDsessions/boot/start_ticks/command/noJulia. CIoff automationpaused HHdisabled; broaderplan/fullsuite/x64/native-retentionOPEN, no cleanup.

## Previous continuation — preserved verbatim below

'''
for p in paths:p.write_bytes(head.encode()+Path(mapping[str(p)]['before']).read_bytes())
print(json.dumps(dict(accepted=True,scope='negative report/continuation preparation only',master=n.BASE,groups=len(h['groups']))))
