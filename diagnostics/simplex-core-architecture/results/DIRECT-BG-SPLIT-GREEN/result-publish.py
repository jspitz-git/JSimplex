"""Reviewer publication; final run result-review.json is the last run-directory write."""
from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-DRIVER-PREPARATION';E=D.parent/'DIRECT-BG-SPLIT-GREEN';run=D/'runs/green300'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
c=json.loads((E/'result-check.json').read_text());assert c['all_passed'] is True and len(c['checks'])==35 and all(c['checks'].values())
assert all(sha(n)==h for n,h in c['sha256'].items())
review='''# Independent GREEN300 saved-result review

Accepted: split BG GREEN result, phase green300. No findings. This accepts the single authorized frozen-stage correctness result only. It does not accept a performance improvement, memory saving, public-solver behavior, production integration or any further numerical attempt.

The reviewer saved and executed NEW result-check.py once. It uses only standard-library text/hash/raw arithmetic plus read-only Git and host checks, imports no project code and invokes no Julia, old checker, launcher, seal, guard or auditor. All35 independent checks passed. All original run/evidence files remained untouched. There are17 original run files, each bound by the final result-review.json envelope; supplementary evidence is separately bound. No run-directory file may be added or changed after that envelope.

Integrity: freshly rehashed the full1,893-file sealed inventory and resolved paths, exact launch membership/inventory and output pins, admission's exact bindings and supplementary evidence, audit's exact pre-audit membership/hashes and the17-check post-run supplement. Preparation and entry bindings remain exact. Accepted RED result-review membership/evidence and sealed inventory remain unchanged. Both75-file RED and81-file GREEN stages match their frozen sources and exact membership. Independent text inverses reproduced the original upper storage outside its approved reservation replacement, the complete block adapter from the split adapter, its parent numerical adapter, and the original differential tests after removal of the specified additions; original fixtures remain byte-identical. This establishes provenance, not universal numerical equivalence.

Raw results: complete=true, fatal empty, exactly34 ordered leaf groups matching both expected JSON and TOML,25 structural plus9 adapter,15,929 passed assertions, zero failed/errored/broken assertions and no failure strings or hidden nested children. Root counters are zero. Raw module paths contain exactly JSimplex from the admitted candidate stage plus SparseArrays, LinearAlgebra, TOML, Test and PrecompileTools; Julia and BLAS report one thread. The log is exactly the driver BEGIN and nine paired BEGIN/END sections, with no warning/world-age/failure/fatal/count-mismatch text. The frozen driver writes raw evidence before aggregate validation. Saved audit and supplement agree with the independently recomputed raw outcome.

Execution: normal Julia exit0 and guard/supervisor success, no soft/hard timeout, kill, termination or cleanup error. Reservation binds the exact admitted command, admission and launch pins. Guard command has292-second inner absolute deadline; supervisor/launcher stay within300seconds. Runner PID/PGID/SID22695,start_ticks1195082 and child22696,start_ticks1195134 match current/process/invocation records, boot1ecae454-f1f5-4e2e-a95c-7b5474243126, and exact recorded commands. Ownership code inspected during admission retains boot/start/command checks, PGID AND SID coverage and pidfd cleanup. No cleanup signal was required in this result.

Observed correctness-run durations are launcher23.04206111199892seconds, supervisor23.042030512000565seconds and guard22.500985758000752seconds. All22 saved resource samples and terminal sample satisfy RAM>=6GiB/swap<=1GiB. Minimum available RAM was22,513,844KiB, swap0; terminal RAM23,223,760KiB/swap0, child maxRSS807,556KiB. These cold correctness durations include loading/JIT/test oracles and are not paired kernel benchmarks. RSS and periodic samples do not measure allocation traffic or complete physical/native peak and release behavior.

Closure: saved pre/post records preserve head/master/boot and expand coverage from242 to244 historical/new groups. Fresh independent review checks all244 identifiers against BOTH process-group and session fields and checks comm/readable executable names for Julia. No matches or visible Julia were found. Fresh available RAM23,175,788KiB, swap0. Inaccessible executable links remain a recorded visibility limit. HEAD and remote diagnostic branch remain1062b4cbd87dc042d7182a7fc3bd1a7b25ce15bd; local/production/remote master remains26e2291745999f485a74f643298ca997d65c7205. Diagnostic/production tracked source membership and bytes match their baseline; tracked changes are absent.

Computational work and memory verdict: no unnecessary new production work, allocation or retained-memory mechanism was found in this run/result step. Frozen numerical/storage kernels and fields were not changed; reviewer and reporting work is diagnostic only. Existing candidate target selection/bin search, metadata growth, relocation/clearing and fragmentation costs remain the explicit qualification subject, not an inferred improvement. The source-derived ledger's706 explicit probe operations,419 injected throws,10,392 callback attempts/9,973 completed requests and389 outer factorization attempts are not separately captured runtime counters or a complete native/loader budget. Full invariant traversals O(n+C+R+K), two n-entry Int conversions/sorts, bookkeeping allocations, snapshots, materializations, exact Rational residuals and fixture construction remain intentional additional test costs. Header/backing/lower/backend/cache/history and old/new copy/refactor coexistence remain included in the bound ledger. No allocation reduction, speedup or release claim is made. Float64/Int private DIRECT BG scope and both fixed policies remain unchanged; this is not an all-precision/general-solver qualification.

The single GREEN allowance is consumed. No retry or cost run is authorized here. The separate Task3 comparative cost driver, all eight fixed cells, allocation bytes/events and checkpoint/final graph gates remain future separately requested work. Original preparation findings/corrections and accepted RED evidence remain preserved; this result required no correction or test relaxation.
'''
with (E/'result-review.md').open('x') as f:f.write(review)
runfiles=sorted(p for p in run.rglob('*') if p.is_file());assert len(runfiles)==17 and not (run/'result-review.json').exists()
evidence=sorted(p for p in E.iterdir() if p.is_file())
v=dict(accepted=True,findings=[],scope='split BG GREEN result',phase='green300',sha256={str(p):sha(p) for p in runfiles},evidence_sha256={str(p):sha(p) for p in evidence})
assert set(v['sha256'])=={str(p) for p in runfiles}
with (run/'result-review.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
assert {str(p) for p in run.rglob('*') if p.is_file() and p!=run/'result-review.json'}==set(v['sha256'])
assert all(sha(n)==h for n,h in v['sha256'].items()) and all(sha(n)==h for n,h in v['evidence_sha256'].items())
print(json.dumps(dict(accepted=True,scope=v['scope'],phase=v['phase'],run_files=len(runfiles),evidence_files=len(evidence),result_review_sha256=sha(run/'result-review.json'))))
