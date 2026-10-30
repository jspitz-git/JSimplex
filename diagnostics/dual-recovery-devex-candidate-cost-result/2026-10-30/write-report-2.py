from pathlib import Path
import json,tomllib,statistics,re,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-candidate-cost-result/2026-10-30';P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/cost-1/candidate-cost';F=R.parent/'reference-cost'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
post=read(D/'postcheck.json');audit=read(R/'audit.json');comp=read(R/'comparison.json');done=read(R/'completion.json');ad=read(R/'numerical-admission.json');data=tomllib.loads((R/'result.toml').read_text());log=(R/'guard/run.log').read_text();allzero=all(s[k]==0 for q in data['cases'] for s in q['samples'] for k in ('bytes','events','compile_seconds','recompile_seconds','gc_seconds'));summary=re.search(r'^TASK4_COST\s*\|\s*(\d+)\s+(\d+)\s+(\S+)\s*$',log,re.M)
if summary is None:raise RuntimeError('ordinary summary absent')
rows=[];preps=[]
for q,c in zip(data['cases'],comp['cases']):
 rs=c['reference'];cs=c['candidate'];g=c['gates'];kind='finite-unreliable' if c['unreliable'] else 'reliable'
 rows.append(f"|{c['type']}|{c['layout']}|{kind}|{rs['seconds']['median']*1e6:.6g}|{cs['seconds']['median']*1e6:.6g}|{c['median_time_ratio']:.6f}|{cs['seconds']['minimum']*1e6:.6g}–{cs['seconds']['maximum']*1e6:.6g}|{cs['seconds']['MAD']*1e6:.6g}|{cs['bytes']['median']:g}/{cs['events']['median']:g}|{c['reference_retained_julia_bytes']}/{c['candidate_retained_julia_bytes']}|{all(g.values())}|")
 a=c['reference_preparation'];b=c['candidate_preparation'];gc=c['candidate_post_warm_gc'];preps.append(f"|{c['type']}|{c['layout']}|{kind}|{a['seconds']:.9g}/{a['bytes']}/{a['events']}|{b['seconds']:.9g}/{b['bytes']}/{b['events']}|{gc['seconds']:.9g}/{gc['bytes']}/{gc['events']}|")
ids='\n'.join(f"- {role}: boot {v['boot_id']}, PID/PGID/SID {v['pid']}/{v['pgid']}/{v['sid']}, start ticks {v['start_ticks']}." for role,v in zip(('launcher','guard','child'),post['closed_owner_identities']))
passed=audit['accepted'] is True and comp['accepted'] is True
text=f'''# Devex fallback: candidate and reference normal-API cost comparison

**Ordinary candidate tests: {summary[1]}/{summary[2]}, child exit {post['process_exit']}. Canonical audit accepted: {audit['accepted']}. Strict paired cost gates accepted: {comp['accepted']}.** Independent result review remains required. Production admission and master integration are not granted by this result.

Exactly one candidate-cost process ran against the frozen accepted reference. Actual solver src/test/environment/CI/master were unchanged. The original driver, fixtures, source overlays, guards, numerical tolerances and all original assertions were preserved; no tuning or retry was performed. Prior failed GREEN and all earlier raw evidence remain unchanged.

## Concrete admission and work

The candidate was independently admitted with {len(ad['checks'])} true checks and {len(ad['bindings'])} SHA bindings, including all {post['pin_count']} exact pins and the full closed reference. Admitted HEAD is 14720147d8850525c0603921064dfe3ba83d3fcb; master remains c0fa748ffa61ccb7c1caaf248c40324f60bc737b. Seal SHA256: {sha(R/'seal.json')}; pins SHA256: {sha(R/'pins.json')}; admission SHA256: {sha(R/'numerical-admission.json')}. Fresh full739-group/session/identity/noJulia/resource/refs checks preceded admission and launch.

Eight fixed 64-dimensional Float32/Float64 cases cover sparse/dense coefficient patterns and reliable/finite-unreliable quality. Both matrix patterns are CSC, with190/4096 nonzeros; dense does not mean a distinct dense-array backend. Each case retains three warm and seven measured whole API calls plus one explicit post-warm GC. Per side there are80 whole API entries,40 real correction BTRAN entries,40 stop entries,eight explicit GCs and56 measured records. Whole calls retain original dimensions/alias guards, basis validation/assembly, RHS scratch copy, quality/refinement, stop and quality recording. A private factor forwards a real transposed solve before declaring zero correction in unreliable cases; this tests a controlled quality boundary, not native backend accuracy.

Reference uses the source-qualified exact legacy body with original helpers; candidate invokes the actual shared-kernel API. All74 files of its project match the tested GREEN2 candidate. All original input/policy/error/output bits, owner checks and work counts pass the ordinary assertions and complete canonical typed auditor. No generated-machine-code identity claim follows from source equivalence.

All56 candidate measured records have zero bytes/events/compile/recompile/in-windowGC: **{allzero}**. Reference had the same zero counters in all56 records. Paired per-case gates require median bytes/events and retained fixture graph not to increase, without a percentage waiver. Canonical audit error: `{audit['error']}`. All8 comparison entries and raw samples are retained even if a gate is false.

## Whole API comparison

Times are microseconds; ratio is candidate/reference. Ranges and MAD refer to candidate's seven samples. Graph is reference/candidate Julia fixture bytes.

|Type|Pattern|Quality|Reference median µs|Candidate median µs|Ratio|Candidate range µs|MAD µs|Candidate median B/events|Graph B|All strict gates|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
'''+ '\n'.join(rows)+f'''

These are short windows from one sequential process per side, not temporally interleaved. Outliers, clock variation and compilation placement limit timing inference. There is no universal elapsed-time speedup gate and no end-to-end solver speedup claim. The purpose is to detect normal-API work/allocation regressions while retaining the separately qualified changed recovery trajectory. No change in iteration count is used as kernel performance evidence.

## Preparation and GC

Preparation tuples are seconds/bytes/events. Explicit GC records are separate and are never subtracted from API time.

|Type|Pattern|Quality|Reference preparation|Candidate preparation|Candidate post-warm GC|
|---|---|---|---|---|---|
'''+ '\n'.join(preps)+f'''

Fixture preparation includes matrix/model/factor/workspace/private scratch setup. Owner census, saved input/model copies and result dictionaries are outside that profile and API windows but inside guarded process time. Entry compilation can occur outside individual profiles; measured zero compile counters do not mean process compilation is free. All warm/preparation/GC profiles and7 raw samples remain preserved. Base GC counters measure aggregate allocation traffic, potentially including native callbacks, not a native allocation/free ledger. summarysize(f) excludes surrounding snapshots/report dictionaries and hidden native memory; process RSS has a different scope.

## Process closure and shared limit

Candidate inclusive guarded elapsed: {done['elapsed_inclusive_seconds']!r}s. Previous use:1070.9948121299385s (including the actual37.39421487902291s reference and all prior failed time). Cumulative total: **{done['total_inclusive_seconds']!r}/1800s**, remaining **{post['remaining_seconds']!r}s**. Offline sealing/admission/final Python audit remain outside the defined guarded sum. Ordinary Test time {summary[3]} has a different scope and is not subtracted into startup/kernel cost.

All{post['resource_samples']} resource samples satisfy guards; minimum available RAM {post['min_available_kib']}KiB, maximum swap {post['max_swap_used_kib']}KiB. Exact command/environment/interpreter/invocation, permit/current/gate/PDEATH9 hashes and identities, child/supervisor exits, no-timeout/kill flags and all{post['pin_count']} unchanged inventory bindings were checked. Four dependency-import warnings remain verbatim; no loader repair was attempted. The canonical auditor explicitly deferred its live launcher, then standalone postexit closure and parent postcheck included it with all742 groups ANDsessions/noJulia.

{ids}

Child identity is the pre-exec gate, not a hidden Julia runtime command capture. Parent postcheck accepted is integrity/closure only; numerical/cost outcome remains the separate canonical audit. Standalone success closed.json exists only when canonical acceptance is true. All{len(post['portable'])} runtime files and{len(post['external_exact_copies'])} external artifacts have explicit byte-exact portable maps. No runtime file was added or edited after closed.json, and the reference tree remains fully frozen.

## Computational work, memory and decision scope

No new production code, scan, solve, copy, conversion, persistent field, precision or safeguard change was introduced by this measurement/publication. The inherited shared kernel uses the same owned scratch, arithmetic and short-circuit ordering. Original finite/residual checks and alias defenses remain. Recovery-only eligibility norm/revalidation/reset work is real and was separately reported in GREEN2; it is outside these normal-API windows and is not claimed as a normal-path saving. Fixture/native/import/setup and update-chain operations are not fully instrumented by the80/40/40 entry counts.

The measured cost gate result is **{passed}**. Functional GREEN2 and these normal-API comparisons have different scopes. Fixed64 Float32/64 cases do not prove general backend accuracy, all precisions, long chains, observer neutrality, native free balance, full-suite success or end-to-end solver speedup. Final independent paired result review is required. Any future production integration requires a separate concrete preparation/master verification step; this turn performs none. CI stays off, HH reuse disabled, all prior rejections remain preserved.
'''
with (D/'REPORT.md').open('x') as f:f.write(text)
print(json.dumps(dict(report_written=True,ordinary_pass=int(summary[1]),ordinary_total=int(summary[2]),audit_accepted=audit['accepted'],comparison_accepted=comp['accepted'],all56_zero=allzero,elapsed=done['elapsed_inclusive_seconds'],cumulative=done['total_inclusive_seconds'],remaining=post['remaining_seconds'])))
