from pathlib import Path
import sys,json,hashlib,subprocess,ast
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27')
sys.path.insert(0,str(D));import common as c
c.unchanged();h=c.host();assert len(h['groups'])==637
pins=c.read('pins.json');assert len(pins['inventory'])==1246
for name in ['common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py']:
 ast.parse((D/name).read_text())
ref=(D/'Reference.jl').read_text()
changes=c.read('changes.json')
for ch in changes:
 baseline=(D/'baseline'/ch['file']).read_bytes()
 head=subprocess.check_output(['git','-C',str(c.M),'show',c.TARGET+':'+ch['file']])
 assert baseline==head
 assert head.decode().count(ch['old'])==1
 assert ref.count(ch['old'])==1
 actual=(D/(ch['variant']+'.jl')).read_text()
 expected=ref.replace('module BNIReference','module BNI'+ch['variant'],1).replace(ch['old'],ch['new'],1)
 assert actual==expected,(ch['variant'],'candidate differs from declared replacement')
 assert actual.replace(ch['new'],ch['old'],1).replace('module BNI'+ch['variant'],'module BNIReference',1)==ref
# Each unchanged private function region is an exact baseline fragment.
p=(D/'baseline/src/primal_simplex.jl').read_text();du=(D/'baseline/src/dual_simplex.jl').read_text()
def reg(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
regions=[reg(p,'function _primal_bound_snap_feasible(workspace::SimplexWorkspace{T}','function _primal_ratio(workspace::SimplexWorkspace{T}'),reg(p,'function _primal_ratio(workspace::SimplexWorkspace{T}','function _legacy_primal_iteration!'),reg(p,'function _primal_direction_weight(direction::AbstractVector{T})','function _primal_weighted_score'),reg(p,'function _primal_steepest_weight!','_primal_cacheable_weight(weight::T)'),reg(p,'function _primal_initialize_steepest!','function _primal_updated_weight'),reg(du,'function _floating_infeasibility_certified','function _dual_direction_residual_ok!')]
for r in regions: assert ref.count(r)==1
localnames={'_primal_bound_snap_feasible','_primal_step_bounds_feasible','_primal_ratio','_primal_direction_weight','_primal_steepest_weight!','_primal_initialize_steepest!','_floating_infeasibility_certified','_infeasibility_certified','_primal_bound_lower_violation','_primal_bound_upper_violation'}
imports=ref.splitlines()[2].split(':',1)[1].split(',')
assert not localnames.intersection(imports)
for arm in ['Reference','A','B','C']:
 s=(D/(arm+'.jl')).read_text();assert 'function Base.' not in s and 'function JSimplex.' not in s
assert 15*(2*2*3*6+2*2*2*3)+4*(2*2*1*6+2*2*2*3)==1632
assert 1632*9*2==29376
c.put('independent-admission-host.json',h)
report='''# Independent prelaunch admission

Rejected pending one edge-coverage correction. No Julia was executed by this reviewer. Static source/harness review and fresh pin/host checks passed. The norm edge loop uses singleton floatmax only: add multi-entry [floatmax,floatmax] with sign variants and explicit expected positive-overflow cap / finite-tie observations across rounding modes before launch. Singleton floatmax does not reliably drive the positive-overflow path in every intended mode; the central B cap rewrite needs direct branch coverage.

Bindings and isolation: all 1,246 inventory pins, authoritative master/origin/master/HEAD 9d29b1f0aa21932217b03ca7b35dd91281baaae6, protected files/indexes and environment match. Baseline primal/dual files equal git objects. Every unchanged Reference function region equals its baseline fragment. Each A/B/C private module equals Reference plus exactly its one declared replacement, with exact inverse equality. Imported JSimplex helper names do not overlap locally defined methods; no Base/JSimplex methods are extended. Ordinary Test is used without custom recorders or manual test stacks.

A: one private read-only zero at the first reached max, after original finite and early-return gates; step allocates it lazily. Lower subtraction then upper subtraction order is preserved. Rational BigInt snap retains the original early zero constructors. Boolean returns cannot publish the private zero. No callback, precision mutation, copy, new scan or solve appears in the guarded loop. Empty/nonfinite/dimension cases retain their original first failure sites. The per-row readiness branch is new work and must be included in measurement.

B: only BigFloat specializes the cap. Both norm passes and their arithmetic order remain. Multiplication creates a fresh current-precision BigFloat, so a finite product cannot exceed current floatmax; only positive infinity needs the fresh cap. Base AbstractFloat min returns the second operand on a finite tie, and propagates the product NaN. Signed zero and negative infinity therefore remain on the product path. Current runtime mpfr.jl/number.jl were read, not executed. Init and actual checked FTRAN call the private norm, while all cacheability checks remain unchanged. Other precisions/types retain baseline methods.

C: exactly three comparisons use integer zero, and conditional magnitudes replace eager abs only at the original allowance endpoint. Base abs(Real) uses eager ifelse(signbit(x),-x,x); the conditional helper selects the same returned operand and only avoids unused negation. Fresh accumulators, arithmetic order, prevfloat/nextfloat widenings, finite checks, one-sided sign rejection, allowance and final Boolean remain. No tolerance change.

Harness: 15 BigFloat contexts (64/128/256 x five rounding modes) have 96 cells each; four native/exact controls have 48 each: 1,632 cells, 29,376 measured windows. Each cell keeps one cold call per arm, three warm calls per arm, nine alternating pairs, zero compile/recompile assertions and all GC/outlier samples. Fixtures, resets, snapshots/validation, cold/warm and explicit context GC costs are retained separately. The Rational scalar sink and Base.one shadowing fixes are present with their original fixture preserved. All whole-function return shapes have sink methods. No additional static scoping or signature failure found. Fixture arithmetic gives positive snap/step outcomes and unit ratio winners; certificate construction gives valid witnesses and reversed invalid witnesses for both orientations. Edge comparisons cover dimension errors, empty/unbounded/nonfinite/bad state, stored 512-bit values/tolerances, signed zero, extreme norms, views and ownership. These are static expectations, not executed test outcomes. Broad random coverage, all possible mutation aliases and native retained-memory accounting are not claimed.

Resource/launch: fresh 637 historical groups AND sessions were checked with boot/start ticks/command identity and fixed unrelated WSL allowance; no live Julia and required memory headroom. Guard ownership uses lock, PID identities/pidfds, unreaped leaders, parent-death startup gate and bounded cleanup. Launch binds admission, pins, exclusive attempt, existing compiled modules, Julia/BLAS 1 and GC 1,0, 2 GiB hint/8 GiB AS, 592 s guard within 600 s total. No launch or old audit was run by this review.

Computational work and memory: found no unnecessary added full-vector/matrix scan, basis solve, copy, conversion or retained data cache. A removes repeated zero constructors but adds readiness tests; B removes one unused floatmax constructor on ordinary norms; C removes reached comparison-zero and unused positive-operand negations. Complexity remains O(rows) for bounds, O(direction length) with two scans for norms, and O(nnz+variables) for certificate. Initialization repeats norm per column; maintenance retains its existing checked solve. Duplicated specialized methods add cold compilation/code metadata. Required before/after time/bytes/events evidence is pending a subsequently admitted run; constructor counts are not allocation or native-live-memory measurements. No speedup, integration approval, or full-suite coverage is inferred here.
'''
with (D/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
script=D/'independent-admission.py'
with script.open('x') as f:f.write(Path(__file__).read_text())
bindings={str(D/n):c.sha(D/n) for n in ['pins.json','contract.json','changes.json','Reference.jl','A.jl','B.jl','C.jl','fixtures.jl','driver.jl','common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','ADMISSION-REVIEW.md','independent-admission-host.json','independent-admission.py']}
c.put('admission.json',dict(accepted=False,findings=[dict(id='B-overflow-coverage',file='fixtures.jl',detail='Singleton floatmax edge does not establish positive-overflow branch coverage. Add multi-entry floatmax sign variants and explicit cap/tie expectations across rounding modes before launch.')],bindings=bindings,scope='one bounded diagnostic launch only',Julia_executed=False,pin_count=1246,groups=637,cells=1632,windows=29376))
print(json.dumps(dict(accepted=False,pins=1246,groups=637,Julia_executed=False)))
