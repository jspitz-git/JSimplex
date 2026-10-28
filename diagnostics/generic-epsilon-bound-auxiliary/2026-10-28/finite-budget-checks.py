from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28')
p=D/'fixtures.jl';s=p.read_text();needle='   for tag in (Val(:original),Val(:C))\n    sentinel=ErrorException'
insert='''   for tag in (Val(:original),Val(:C)),expired in (false,true)
    a=fixture(T,8,:sparse,:positive,:auxiliary);before=deepcopy(inputvalues(a));budget=a.budget[]
    budget.time_limit_seconds=expired ? 0.0 : 1e9
    expired&&(budget.start_ns=UInt64(0))
    initial=(budget.start_ns,budget.iterations,budget.refactorizations)
    stop=J._guard_stop_callback(()->J._budget_expired(budget))
    out=modof(tag)._lp_auxiliary_run_at_working_precision(a.w,a.problem,a.map,budget,a.policy,stop)
    @test expired ? out===(nothing,nothing,nothing) : !isnothing(out[2])&&out[2].status==J.OPTIMAL
    @test expired ? (budget.start_ns,budget.iterations,budget.refactorizations)==initial : out[1].options.time_limit==1e9&&out[1].progress.start_ns==budget.start_ns==initial[1]
    @test same(before,inputvalues(a))
   end
'''
assert s.count(needle)==1;s=s.replace(needle,insert+needle);p.write_text(s)
p=D/'CALL-BUDGET.md';s=p.read_text().replace('The observer throw tests','Per-solve measured fixture limits are Inf (external shared process guard900s); they are not finite-clock or real-expiry observations. Separate Float64/BigFloat tests exercise unexpired finite budgets and deliberately expired zero budgets through the actual _budget_expired guard. The observer throw tests');p.write_text(s)
shutil.copyfile(__file__,D/'finite-budget-checks.py')
print('Finite budget and expiry checks added before sealing; no Julia')
