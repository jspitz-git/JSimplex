from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/PRESOLVE-LARGE-PROFILE';P=D.with_name('PRESOLVE-EXACT-CACHE-PIPELINE')
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
put('prepare.py',Path(__file__).read_text())
put('guard.py',(P/'guard.py').read_text())
put('supervisor.py',(P/'supervisor.py').read_text().replace('started+64','started+114').replace('started+68','started+118').replace('started+70','started+120').replace('<=70','<=120'))
put('control.py',(P/'control.py').read_text().split('def stage_audit')[0])
s=(R/'src/presolve.jl').read_text();a=s.index('function presolve_problem(');b=s.index('\nfunction restore_basis(step::',a);original=s[a:b]
clone=original.replace('function presolve_problem(problem::LinearProblem{T}) where {T}','function profile_large_presolve(problem::LinearProblem{T}, observer) where {T}').replace('for _ in 1:12','for round in 1:12').replace('next = _dispatch_presolve_pass!(current, steps, propagation_trace, index)','next = profile_large_dispatch(current, steps, propagation_trace, index, round, observer)')
put('original-controller.jl',original);put('controller.jl',clone)
put('wrapper.jl','''function profile_large_dispatch(current, steps, trace, index, round, observer)
    observer(:start, round, index, current, nothing)
    timed = @timed _dispatch_presolve_pass!(current, steps, trace, index)
    observer(:finish, round, index, current, timed)
    return timed.value
end
''')
put('plan.md','''# Large-model presolver attribution, 2026-10-14

User requests a SHORT pass-by-pass profile of runtime, medium, test and a concrete
optimization proposal with no allocation growth. They report presolve <1minute on
each. This is diagnostic attribution of unchanged master6f68e24, NOT a candidate
comparison, not a full solve, not a repeat of the small-model cache experiment.

Three serial processes, one per input in that order. Each guard setup+Julia <=114s,
supervisor TERM114/KILL118/reap120, total<=360s. No retry. Prior186groups ORsessions,
boot/start_ticks/command and actual refs checked. One Julia, BLAS1, heap2GiB hint,
VM8GiB, availableRAM>=6GiB, swap<=1GiB, existing compiled modules, no package changes.
Fresh copy of accepted guard; supervisor ONLY changes64/68/70 to114/118/120.
Ordinary frozen reference overlay identical to current master; candidate not loaded.

One native Float64 read_mps per model, parsing separately timed. Controller copied
byte-exact with only name+observer argument, round variable and dispatch wrapper.
No method overwrite; dispatcher/pass code identical. Each dispatch timed includes
trace maintenance/postsolve append, excludes observer serialization/hashing.
Up to THREE profiled presolves (first cold, subsequent warmed candidates), then ONE
untimed public presolve result control if at least20s remain before the cooperative
100s deadline. Before each pass observer refuses at elapsed>=100s, preserves partial
journal and explicit incomplete status; never modifies numerical policy or returns
a partial model as success. Hard guard protects non-yielding calls. No per-pass
retry or skipped pass. Model order/caps fixed before observations. A safely stopped
model may be followed by the next independent model only after clean groups/pins;
resource/pin/identity/ordinary error stops sequence. Hard timeout partial data are
not accepted complete timing, and never a license to rerun.

Before/after each complete profiled/public presolve, streaming SHA covers original
model values (typed primitive numeric bits, structural fields, ordered arrays,
strings) and owned array identities; complete result hash covers reduced model and
full postsolve stack. Public control and completed repeats must agree. No full
model clones or retained successive results. Fixed <=324 finish/start record pairs
per model plus<=3 profile result records; no Julia Profile sampling/no solver calls.

Report each pass call, round, input/output dims+storednnz, changed flag, elapsed,
GC, compile/recompile, aggregate GC-counter bytes/events. Model load separate.
Do not discard GC or compilation windows; only compile-zero repetitions may inform
warm ranking. Compilation and GC are subsets, not a proven additive decomposition.
Instrumentation and hashing can affect GC/cache; this is observed attribution, not
observer-neutral throughput, peak-memory accounting or speedup. If no warm complete
run, label evidence partial/cold. Ranking must distinguish repeated pass invocation
and cumulative work. Suggest optimization from measured dominant source path only;
no implementation, no claim of allocation-neutrality until before/after tests.
No changes src/test/env/CI/master, frozen old evidence retained. Separate independent
numerical/work/memory admission, result review and exact publication required.
''')
put('authorization.json',json.dumps({'request':'Změř tedy krátce, které průchody presolveru zabírají nejvíc času na úlohách runtime, medium a test, a podle výsledků navrhni konkrétní optimalizaci bez nárůstu alokací.','additional_input':'Ani na jedné úloze netrvá presolve déle než minutu.','max_processes':3,'inclusive_cap_seconds_each':120,'max_total_seconds':360},indent=2)+'\n')
print('Prepared new files',len(list(D.iterdir())))
