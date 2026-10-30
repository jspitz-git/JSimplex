from pathlib import Path
import json,tomllib,statistics
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30'
p=json.loads((D/'postcheck.json').read_text());audit=json.loads((D/'reference-cost/audit.json').read_text());proc=json.loads((D/'reference-cost/guard/process.json').read_text());data=tomllib.loads((D/'reference-cost/result.toml').read_text());cases=data['cases'];samples=[s for q in cases for s in q['samples']]
if not(p['canonical_audit_accepted'] and p['test_summary']==dict(Pass=272,Total=272) and len(cases)==8 and len(samples)==56):raise SystemExit('unexpected reference result')
def dist(v):
 m=statistics.median(v);return m,min(v),max(v),statistics.median(abs(x-m) for x in v)
all_zero=all(s['bytes']==s['events']==s['compile_seconds']==s['recompile_seconds']==s['gc_seconds']==0 for s in samples)
report="""# Task4 reference normal-API cost result

**Reference stage passed: 272 PASS / 0 FAIL / 0 ERROR / 0 BROKEN, total272; exit0.** Canonical cost audit and one standalone full postexit closure both passed. Independent result review remains required. Candidate cost has NOT run; this reference alone qualifies no candidate allocation/performance improvement, paired cost acceptance, production or master integration.

Exactly one new guarded reference process ran with the unchanged source-qualified legacy refinement body, unchanged original cost.jl and its original overlays/reference project. Existing solver source/test/environment/CI/master were untouched. OriginalRED accepted7/1, rejectedfirstGREEN and acceptedGREEN25774/5774 remain frozen unchanged; failed records were not relabeled passing.

## Exact admission, controls and measurements

Fresh independent concrete numerical admission passed4664checks/801bindings, with all566 pins,560committed publication blobs and the actual seal/pins/report/command bound. Admitted HEADd618023b27a42170438c26995c50a036af01c2b4,codex/native-quality-finite;masterc0fa748ffa61ccb7c1caaf248c40324f60bc737b. SealSHA4456da15f6621f4bcd44b79bae753065e25c08ce5db10cbd24b4c34abcea985a;pinsSHAc422ea44a387cf346cae88358c132f90dba61afda225d3f1ae5ba63de203e709;admissionSHAb1dbc1375c6b0d3acb9048981a9924ed0f49fdc15a3d3c15f9a8e01e15d29089. Parent/fresh launcher full736groupsANDsessions/noJulia/resources/refs passed before the exclusive attempt.

The eight cases are Float32/Float64 x sparse/dense coefficient pattern x reliable/finite-unreliable, n64, CSC model matrix with190/4096nonzeros, diagonal64/signed1..5 divided64 offdiagonals. RHS=B' e1; initial point=e1/0.5e1; independent original256eps policy bits preserved. A private factor wrapper forwards the real transposed solve and only then declares zero correction for the bad case. It is a controlled quality-boundary fixture, not a native backend accuracy claim or a solver trajectory benchmark. All original dimensions/alias guards, basis validation/assembly, RHS scratch copy, quality/refinement, stop and quality recording remain inside whole API timing.

Actual ordinary Test272/272 and side-specific completion passed. All8case/input/policy/error bit patterns, owners, work totals,3warm/7measured profiles, preparation/GC records and measured compile/recompile-zero gates passed the canonical auditor. There are80wholeAPIcalls,40real correctionBTRAN entries,40stop entries,8explicitpostwarmGCs and56measured records. Counts are declared API/wrapper entries, not a complete native/import/setup factor budget. The measured graph is summarysize(f), not surrounding metadata or hidden native memory. No test recorder or manual Test stack was added.

"""
report+=f"All56 measured records have zero bytes/events/compile/recompile/in-windowGC: **{all_zero}**. This is observed reference allocation-counter traffic in these windows, not proof of no native allocation or universal allocation freedom. Warm/preparation/explicitGC and initial compilation outside these @timed regions remain separate.\n\n"
report+="| Type | Pattern | Quality | Median time µs | Range µs | MAD µs | Median bytes/events | Retained fixture Julia B |\n|---|---|---|---:|---:|---:|---:|---:|\n"
for q in cases:
 m,lo,hi,mad=dist([s['seconds']*1e6 for s in q['samples']]);b=statistics.median(s['bytes'] for s in q['samples']);e=statistics.median(s['events'] for s in q['samples'])
 report+=f"|{q['type']}|{q['layout']}|{'finite-unreliable' if q['unreliable'] else 'reliable'}|{m:.9g}|{lo:.9g}–{hi:.9g}|{mad:.9g}|{b}/{e}|{q['retained_julia_bytes']}|\n"
report+="""
All seven raw sample values are retained in result.toml. These are short repeated whole-API measurements in one reference process, not before/after results or evidence of speedup. Both patterns are CSC; dense describes coefficient density, not a distinct dense-array backend. The reference is the previously qualified legacy body with original JSimplex helpers, source-equivalent to original routines after JS qualification, not an identical-generated-code assertion.

## Preparation and explicit GC observations

Fixture preparation times include its model/factor/workspace/private-buffer setup. Owner census, saved input/model copies and result dictionaries are outside that profile and API windows but inside guarded process time. Compiler placement may put entry compilation outside individual profile records; zero measured compile values do not make total process compilation free. These per-case preparation and GC profiles are not subtracted from API timings.
"""
report+="\n| Type | Pattern | Quality | Preparation seconds/bytes/events | Post-warm GC seconds/bytes/events | Warm compile/recompile seconds |\n|---|---|---|---|---|---|\n"
for q in cases:
 a=q['preparation'];g=q['post_warm_gc'];c=sum(s['compile_seconds'] for s in q['warm']);rc=sum(s['recompile_seconds'] for s in q['warm'])
 report+=f"|{q['type']}|{q['layout']}|{'finite-unreliable' if q['unreliable'] else 'reliable'}|{a['seconds']}/{a['bytes']}/{a['events']}|{g['seconds']}/{g['bytes']}/{g['events']}|{c}/{rc}|\n"
report+="""
## Ownership, process closure and cumulative ceiling

All566 inventory hashes/resolved targets stayed unchanged. Guard reasonexit0,pins_unchanged=true; child/guardexit0 and supervisoracceptedtrue; all timeout/kill/term/abnormal/child-cleanup flags false. Current/permit/gate identities/hashes,parent-death9, exact invocation and admitted pre/post/currentHEAD/resource controls passed the canonical audit. The original four dependency-import warnings match previous runs and remain verbatim; they are not Test errors, and no loader/dependency repair was attempted.

After the launcher exited, the prepared standalone close.py reference-cost ran once, verified full739historical/currentgroupsANDsessions/noJulia and all raw/admission/report/pin bindings, and wrote immutable closed.json. The canonical audit's own snapshot explicitly deferred its still-live launcher, never falsely claiming launcher exit. The separate parent postcheck11 again verified full739 with no launcher exclusion, resources/prior-time/all566pins/canonicalaudit/closed hashes, clean refs/tree and absent candidate reservation. Its accepted=true is integrity/closure; numerical reference acceptance is separately canonical audittrue. No auditor/numerical/close script was rerun.
"""
for role,a in zip(('launcher','guard','child'),p['closed_owner_identities']):
 report+=f"\n- {role}: PID/PGID/SID{a['pid']}/{a['pgid']}/{a['sid']},start_ticks{a['start_ticks']},boot{a['boot_id']}.\n"
report+=f"\nThe child identity is its pre-exec entry gate, not an invented hidden Julia-command capture. Reference inclusive guarded elapsed={p['elapsed_inclusive_seconds']}s; prior1033.6005972509156s plus reference gives total{p['total_inclusive_seconds']}s of1800; remaining{p['remaining_seconds']}s. All{p['resource_samples']} samples meet bounds, minavailable{p['min_available_kib']}KiB,maxswap{p['max_swap_used_kib']}KiB; childpeakRSS{proc['child_maxrss_kib']}KiB is process memory, not native allocation/free accounting. Ordinary Test3.9s and inclusive elapsed include different scopes and cannot be differenced into a pure kernel/startup benchmark. Offline preflight/admission/finalPython audit remain outside the defined guarded sum.\n"
report+=f"\nAll{len(p['portable'])} runtime files including closed.json and all bound external/admission-review temporary artifacts are copied byteexact under explicit maps. Portable copies/publication are outside the reference runtime tree: **no file there is added or edited after closed.json**. This preserves the candidate prerequisite's exact membership/hash check. Source files, raw attempts, reviews and failed history remain frozen; copied postcheck source is supplemental, not a retroactive launch pin.\n"
report+="""
## Work/memory limits and next gate

No NEW production code, numerical scan, solve, copy, callback, precision/tolerance/safeguard change or retained field was introduced by measurement/result handling. Cold Python hashing/Git/proc/type/bit/metadata/copy/report work is outside numerical API windows. The legacy whole call still performs original dimensional/alias checks, basis validation/assembly and finite/quality scans; bad cases retain one real correction solve and stop, while setup/backend/update-chain work is not fully instrumented. The future candidate's recovery-only revalidation/reset is outside these normal-API windows and cannot be credited as normal-path savings.

GC stats are aggregate Julia counter traffic, potentially including native allocations routed through Julia callbacks. summarysize(f) excludes hidden native buffers, input snapshots and result dictionaries; RSS/resource data is separate. No observer-neutrality, native-free, general backend, all-precision, long-chain, full-LP or full-suite claim follows from these fixed64cases. Short samples, one process per side and noninterleaving constrain any later timing comparison.

The candidate phase remains UNEXECUTED. It needs fresh host739groupsANDsessions/boot+start_ticks+command/noJulia/refs/resources, its own actual seal/full pins and independent numerical admission. It must bind this closed reference and actual remaining729.0051878700615s, not reuse the original766.399allowance or ignore prior failures. Raw reference runtime/external admission/report dependencies stay frozen and available. Candidate must keep all original work/owner/input/output/compile-zero oracles and per-case median bytes/events/retained graph nonincrease; with this reference's measured-zero baseline, any positive candidate median fails without percentage waiver.

Reference success alone is not paired cost acceptance or candidate promotion. No candidate process, retry or integration ran in this turn. Final paired review and separate production/master verification remain required. CI off,HH reuse disabled,masterc0fa748funchanged; future references to this closure are historical evidence, not fresh preflight.
"""
with (D/'REPORT.md').open('x') as f:f.write(report)
print(json.dumps(dict(reference_pass=True,all56_measured_zero=all_zero,candidate_run=False,remaining=p['remaining_seconds'])))
