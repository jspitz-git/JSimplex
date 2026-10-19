from pathlib import Path
import json,hashlib,sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=H.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
(H/'manifest.py').write_bytes(Path(__file__).read_bytes())
with (H/'REPORT.md').open('x') as f:f.write('''# Blocked U BG Task2 harness preparation

Prepared OFFLINE concrete RED/GREEN driver, diagnostic-only exact-inverse test clones, fixed160-site inventory and event-conditioned assertion rules, pre-entry API accounting, full saved-result auditor, exact-stage seal/release/one-attempt process controls and300s resource admission. No Julia or runtime acceptance. Common candidate component prechecks are identical in both modes; RED streams use the scalar suffix and expect exactly6 named coverage failures. GREEN streams use blocking and require every test to pass.

Author verification:56 pure saved-data mutation checks,226 source/clone inverse checks,28 full auditor synthetic wiring checks PASS. Initial source checker exit1 retained: literal forbidden-token search matched an explanatory comment; separate comment-aware source-check-2 passes, without editing Julia. No numerical experiment or old accepted script rerun. The candidate14files, Task2 overlay, production source/test/environment/CI/master, global STATUS/roadmap are unchanged. Fresh host entry verified268 groups AND sessions absent, no Julia, boot and both remote refs.

Actual dynamic test count is intentionally not fabricated: all160source sites and occurrence formulas are frozen before execution, with512 numerical trace completions and fixed28unit roster independently required. This interpretation of the plan requires explicit independent boundary review. The full cold exact-rational oracles may exceed300s; no fit or performance claim. See ADMISSION.md and MEMORY-WORK.md for precise work, retention, prefix and future admission boundaries.

Independent review, closure and exact publication records are separate. No outer/seal/reservation/output is present; future RED requires fresh exact admission and later GREEN requires accepted RED closure/result review. Task3 measurement is not prepared here.
''')
paths=set(str(p) for p in H.iterdir() if p.is_file())|set(str(p) for p in C.iterdir())
paths|={str(R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md'),str(R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md'),str(R/'AGENTS.md'),str(Q/'review.json'),str(Q/'closure.json'),str(Q/'publication.json')}
paths|=set(json.loads((Q/'review.json').read_text())['sha256'])
req=H/'required-paths.json';paths.add(str(req));save(req,{'paths':sorted(paths)})
save(H/'preparation-pins.json',{'scope':'Offline prepared sources; no launch admission','sha256':{p:sha(p) for p in sorted(paths)}})
print('Preparation exact paths',len(paths),'no launch artifacts')
