from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common as c
c.put('source-host.json',c.host())
s=(D/'baseline/src/primal_simplex.jl').read_text();st=(D/'baseline/src/simplex_stalling.jl').read_text()
def region(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
ratio=region(s,'function _primal_ratio(workspace::SimplexWorkspace{T}', 'function _legacy_primal_iteration!')
bf=region(s,'function _primal_ratio(workspace::SimplexWorkspace{BigFloat}', 'function _legacy_primal_iteration!')
new=bf.replace('max(zero(T), raw_step)','_primal_nonnegative_step(raw_step)').replace('max(zero(T), relaxed)','_primal_nonnegative_step(relaxed)').replace('max(zero(T),\n                        (bound_value(bound) - workspace.primal[index]) / movement)','_primal_nonnegative_step(\n                        (bound_value(bound) - workspace.primal[index]) / movement)')
assert new!=bf and 'max(zero(T)' not in new
helpA='# Keep a fresh zero, NaN handling and signed-zero selection on the fallback path.\n_primal_nonnegative_step(value::BigFloat) = value > 0 ? value : max(zero(BigFloat),value)\n\n'
observe=st[st.index('function observe_progress!'):]
improvement=region(st,'_stagnation_improvement(anchor::Rational','function observe_progress!')
improvementbf=region(st,'function _stagnation_improvement(anchor::T','function observe_progress!').replace('anchor::T,current::T,scale::T) where {T<:AbstractFloat}','anchor::BigFloat,current::BigFloat,scale::BigFloat)').replace('zero(T)','zero(BigFloat)').replace('abs(anchor),abs(current)','_primal_direction_magnitude(anchor),_primal_direction_magnitude(current)')
helpB='_stagnation_step_magnitude(value) = abs(value)\n_stagnation_step_magnitude(value::BigFloat) = _primal_direction_magnitude(value)\n\n'
obB=observe.replace('abs(ps)/m.primal_scale','_stagnation_step_magnitude(ps)/m.primal_scale').replace('abs(ds)/m.dual_scale','_stagnation_step_magnitude(ds)/m.dual_scale')
entry=region(st,'function _observe_stagnation!(ws','function _rebase_dual_stagnation_costs!')
consumer=region(st,'function _observe_workspace_stagnation!','function StagnationMonitor{T}')
imports='''using JSimplex: SimplexWorkspace,StagnationMonitor,WorkspaceStagnation,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,bound_value,_lower_violation,_upper_violation,_primal_relaxed_step,_primal_bound_snap_feasible,_primal_step_bounds_feasible,_legacy_primal_row_validation_enabled,_primal_direction_magnitude,_finite_workspace,_with_recovery_precision,_stagnation_context,_new_workspace_stagnation,_rebase_dual_stagnation_costs!,_workspace_stagnation_values,_simplex_event!
'''
for arm in ('Reference','A','B','C','BC'):
 body=(helpA+ratio.replace(bf,new) if arm=='A' else ratio)+improvement+(improvementbf if arm in ('C','BC') else '')+(helpB+obB if arm in ('B','BC') else observe)+entry+consumer
 (D/(arm+'.jl')).write_text('module RM'+arm+'\n'+imports+body+'\nend\n')
changes=[dict(variant='A',file='src/primal_simplex.jl',old=bf,new=helpA+new),dict(variant='B',file='src/simplex_stalling.jl',old=observe,new=helpB+obB),dict(variant='C',file='src/simplex_stalling.jl',old=improvement,new=improvement+improvementbf)]
c.put('changes.json',changes)
c.put('source-clones.json',{arm:c.sha(D/(arm+'.jl')) for arm in ('Reference','A','B','C','BC')})
# Existing guard/supervisor are copied byte-for-byte; no old script is executed.
O=D.parents[1]/'generic-interval-stagnation-devex/2026-10-27';shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(D/'launch.py').write_text((O/'launch.py').read_text())
(D/'PLAN.md').write_text('''# BigFloat ratio zeros and stagnation magnitudes
Human-selected three short whole-function correctness/time/allocation comparisons and autonomous integration of accepted variants. Baseline master8ceff4f1. Existing linked diagnostic checkout reused; its src is not baseline. All old evidence/scripts frozen, no old numerical rerun. CIoff, automationpaused, HHreuse disabled; broader/fullsuite/x64 open. Fresh full629groups ANDsessions/boot/startticks/command/noJulia before every launch/continuation edit, exact unrelated WSL identity allowance retained.
A only BigFloat primal ratio: positive raw/relaxed/candidate steps bypass constructing unused zero; every zero/negative/nonfinite path retains max(freshzero,value), signedzero/NaN/ties/return ownership. Both full passes and feasibility/rejection/fallback/pivot guards intact. O(m) fewer temporary zero constructions; no shared mutable zero.
B conditional magnitude only in observe_progress! step predicates for BigFloat; other types originalabs. Same conversions, validation, shortcircuit, divisions/tolerance, history/callback/event/state changes. At most2 unused negations removed per observation.
C BigFloat-only stagnation improvement magnitude, after original equality gate. Same normalized division/subtraction/product order, fresh zero returns, max argument order and output/input ownership; at most2 unused negations per reached metric,3metrics per window.
Test exact source reference/private A/B/C/BC namespace spikes. BF64/128/256xfive modes and stored512, signedzeros/nonfinite/extremes, empty/rejected/unbounded/tolerated negative ratio, independent known pivot/monitor sequences, all input/scalar/array owners, complete monitor fields/exception partial state/context restoration. Float32/64/RationalBigInt/Int64 controls.
Measure whole ratio sparse/dense n16/64, positive/negative/mixed; whole observe_progress! for B/C/BC and full workspace observer/context for B/C/BC, cold/ordinary/window histories.3warm+9alternatingpairs, separately recorded fixture/reset/cold/warm/validation/GC preparation; every measuredcompile/recompile0, retain GC/outliers. Single admitted600s process, Julia/BLAS1 GC1,0 heap2GiB AS8GiB RAM6GiB/swap1GiB compiledmodulesexisting. No custom Test recorder/manual stacks.
Independent admission/result decision; permanent ordinary correctness+data-supported fixed3pair lowerEvents/lowerMedianBytes gates; witnessed originalRED before productionstagechanges. Complete affected existing regression files and earlier generic regressions, exact ordered list frozen; 3000s shared test limit for GREEN and actualMASTER due previous49file1716/1834s. No threshold weakening/old exception reuse. Wholebranch independent numerical/work-memory review, exact private-indexcommit/localff/actualMASTER samefiles+count/resultreview/normalnonforcepush, exactrefsverified. Finaldiagnosticpublication only after independent review/PASSclosure/exact stagedcommitted names+blobs. Preserve userfiles/indexes/worktrees/evidence; no cleanup. O(1) private locals+newcoldmethodmetadata, no new scans/solves/copies/conversions/persistentcache.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nTask1: source/private candidates prepared; fresh baseline539files and629hostgroups. No Julia yet.\nPre-flight: A independent; B/C share observe_progress!, BC measured separately without adding their separate timing claims.\nRuling: reuse existing isolation and guard, ordinary Test only; no reinstall/bootstrap probe or duplicate baseline runtime.\n')
shutil.copyfile(__file__,D/'source-prepare.py')
print('private exact-reference A/B/C/BC; plan prepared')
