from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');sys.path.insert(0,str(D));import common as c
c.put('source-host.json',c.host())
def region(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
s=(D/'baseline/src/dual_simplex.jl').read_text();f=(D/'baseline/src/factorization.jl').read_text();q=(D/'baseline/src/simplex_start.jl').read_text()
a=region(s,'function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},','# A fresh floating LU')
ab=region(a,'function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},\n                                  rho::Vector{T}, leaving_row::Int) where {T<:BigFloat}','#PLACEHOLDER') if False else a[a.index('function _dual_row_residual_ratio',a.index('function _dual_row_residual_ratio')+1):]
na=ab.replace('    worst_ratio = zero(T)\n','    worst_ratio = zero(T)\n    expected_zero = worst_ratio\n',1).replace('expected = basis_row == leaving_row ? one(T) : zero(T)','expected = basis_row == leaving_row ? one(T) : expected_zero')
b=region(f,'_pivot_magnitude(value::Real)','function _same_umfpack_pattern')
bb=region(b,'_pivot_magnitude(value::BigFloat)','function replace_column!')
nb='''function _pivot_magnitude(value::BigFloat)
    isfinite(value) && value > 0 && return value
    return setprecision(BigFloat, precision(value)) do
        # Retain stored-precision negation and all exceptional/zero cases.
        abs(value)
    end
end

'''
cc=region(q,'function _crash_rows!','function _crash_workspace_impl')
nc=cc.replace('function _crash_rows!(rows,ws,column,policy)','function _crash_rows!(rows,ws,column::Vector{T},policy) where {T<:Union{BigFloat,Rational{BigInt}}}').replace('        abs(column[row]) > cutoff || continue','        magnitude = abs(column[row])\n        magnitude > cutoff || continue').replace('findfirst(r->abs(column[row])>abs(column[r]),rows)','findfirst(r->magnitude>abs(column[r]),rows)')
imports='''using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,_primal_direction_magnitude,PFIFactorization,_is_exact,_positive_tolerance,_backend_dimension,PackedEta
_crash_violation(args...) = JSimplex._crash_violation(args...)
'''
for arm in ['Reference','A','B','C']:
 body=a.replace(ab,na) if arm=='A' else a
 body+=(b.replace(bb,nb) if arm=='B' else b)
 body+=cc+(nc if arm=='C' else '')
 (D/(arm+'.jl')).write_text('module RPC'+arm+'\nimport JSimplex\n'+imports+body+'\nend\n')
c.put('changes.json',[dict(variant='A',file='src/dual_simplex.jl',old=ab,new=na),dict(variant='B',file='src/factorization.jl',old=bb,new=nb),dict(variant='C',file='src/simplex_start.jl',old=cc,new=cc+nc)])
c.put('source-clones.json',{arm:c.sha(D/(arm+'.jl')) for arm in ['Reference','A','B','C']})
O=D.parents[1]/'generic-sum-rational-growth/2026-10-28';shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(D/'launch.py').write_text((O/'launch-ready.py').read_text().replace('common_ready','common').replace('admission-ready.json','admission.json').replace('contract-ready.json','contract.json').replace('pins-ready.json','pins.json'))
(D/'common.py').write_text((D/'common.py').read_text().replace('contract-ready.json','contract.json').replace('pins-ready.json','pins.json'))
(D/'DESIGN.md').write_text('''# Residual seed, stored pivot magnitude and crash candidate reuse
The human selected all three proposals for short complete-function comparisons and autonomous accepted production integration with unchanged numerical checks and independent review.
A only BigFloat dual-row residual check: retain a read-only binding to the original fresh worst_ratio zero before any iteration, and use it for expected zero on non-leaving rows. All residual negations/products/sums/scale/tolerance/divisions and bounds/dimension/finite guards stay ordered. No shared cross-call or persistent zero, new array, pass or constructor; returned zero still fresh per invocation. Empty/early/error and scratch/input scalar ownership are checked.
B only BigFloat _pivot_magnitude: finite strictly positive values can be read directly by its comparison-only callers; all zeros, negatives, NaN and infinities retain original stored-precision setprecision/abs. Audit every caller (PFI, HH, triangular, BG; BigFloat Markowitz has its own existing method). Whole PFI replace_column! includes tolerance conversion, validation, inverse/divisions, counts/packing, recycled/new update publication. Direct helper and HH/triangular correctness controls check shared helper reachability; no HH reuse or prototype policy change. No scalar escapes into published coefficients from this magnitude helper.
C only ordinary Vector{BigFloat}/Vector{Rational{BigInt}} _crash_rows!: hold the first existing abs(column[row]) in a local and reuse it as the left operand inside bounded ranking comparisons. Keep the original maximum/zero guard/cutoff scan, violation check, right-side abs calls, insertion/pop order, tie ordering and candidate cap. No new magnitudes array/cache or scan. Generic/custom-array/native/fixed-rational routes stay original. No conditional abs substitution here: stored/ambient precision semantics are unchanged. Work belongs to optional crash initialization, not ordinary iterations.
Alternatives excluded: persistent seed/magnitude caches need invalidation; sharing writable results or skipping checks violates the ownership/safeguard contract. No arithmetic reassociation, dropped coefficients, tolerance/precision/pivot-policy changes.
''')
(D/'PLAN.md').write_text('''# Residual pivot crash implementation plan
> For agentic workers: execute inline with superpowers:executing-plans; independent reviewers handle admission/result/whole production.
**Goal:** Measure all three approved ideas and integrate only independently accepted complete-function improvements.
**Architecture:** Private exact-source Reference/A/B/C, ordinary Test, fixed sparse/dense fixtures and alternating @timed pairs; original cost RED before production stage. Baseline actual master bb765d00, never stale diagnostics src.
**Tech Stack:** Installed Julia1.13, Test/SparseArrays/LinearAlgebra/TOML, existing guarded single Julia process.
**Spec:** DESIGN.md and direct human request.
## Constraints
Preserve userfiles/env/indexes/worktrees and frozen raw evidence. Fresh refs/full659groups ANDsessions/boot/start_ticks/command/noJulia before pinned changes; only exact fixed WSL identity allowance. BLAS/Julia1 GC1,0 heap2GiB AS8GiB availableRAM6GiB swap<=1GiB compiled-modules existing. CIoff automationpaused HHreuse disabled; broader/fullsuite/x64/native retention OPEN. No huge LP. Use ordinary tests/no custom recorders or manual testset stacks. Existing thresholds/exceptions unchanged. Cold/setup/reset/view construction/validation/GC/capture separately recorded. Short comparison900s, normal GREEN/MASTER3600s to allow recent57file runtime~1900s plus affected files; no multi-hour attempt.
## Review focus
Stored512 versus ambient64/128/256 under five rounding modes; signed zeros/NaN/Inf and threshold boundaries; empty/dimension/index/alias paths with unchanged partial effects; reused factor packing/recycled/new chains plus input owners and actual solves; crash ties/candidate caps/zero and early violation plus custom array fallback. Concrete assertions must exercise each.
## Task1: comparison
- [ ] Private exact inverse fragments and ordinary independent hand-derived correctness/owners/context tests before measuring.
- [ ] BF64/128/256 x5modes plus RationalBigInt Float32/64 RatInt64 controls; n16/64 sparse/dense +/-/mixed; residual structural/slack, PFI update, crash sorted/tied/zero/none. Three warm pairs and nine alternating measured pairs, compilation zero, all GC/outliers retained.
- [ ] Independent concrete admission before one900s guarded attempt; complete raw/context/source/resource audit and independent pervariant acceptance. No tune/rerun-to-pass.
## Task2: accepted production
- [ ] Ordinary permanent correctness and meaningful fixed3pair allocation gates; original RED expected cost failures only, preserve original tests.
- [ ] Stage accepted changes exact inverse and full production numerical/work/memory review, fresh GREEN previous57wholefiles+newtest+affected crash/factor wholefiles as needed3600s.
- [ ] Private index commit/actualcommitreview/ff-only integration/fresh samefiles frozen total MASTER3600s/independent result/normal push remoteverify.
## Task3: closure
- [ ] Exact continuation beforeimages/maps, final report and independent review; separate PASS closure + complete exact staged/committed blobs before failfast diagnostics commit/push. No cleanup or automatic next experiment.
''')
(D/'WORK-MEMORY.md').write_text('''# Computational work and memory
A reached BigFloat legacy BTRAN residual validation: m-1 expected-zero constructors become zero additional constructors by retaining the original accumulator seed. O(1) pointer binding, same O(m+nnzB) arithmetic/scans; same fresh returned result category. No numerical cache/solve/copy/conversion/callback change.
B per factor update/pivot comparison: two cheap finite/sign comparisons remove one stored-precision context switch and abs result on finite positive pivots. Other signs/nonfinite retain original work plus guard. Count full update including scans, inverse, packing/recycled buffers and allocations. Markowitz BF already owns a separate magnitude helper. O(1) local, no retained numerical memory or additional solve/scan. Cold method metadata and branches are costs, not free.
C per candidate crash column: original O(m) abs maximum plus eligibility and up to m*k bounded ranking comparisons (k=max_pivot_candidates) retained. Left ranking abs construction is removed after each row's original threshold magnitude; same right-side reads/abs, all row violation calculations and rows-vector insertion work. One live local scalar instead of temporary repeated values; no new O(m) storage/cache/scan. Result is original integer rows buffer; numeric temporary never published. Matrix/backend setup and whole-function preparation measured separately. This is initialization only.
Source constructor counts are not allocations or native free/retention measurements. Whole-call time/bytes/events determine admission; no end-to-end promise.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nTask1: fresh659groups refs boot/noJulia; baseline542files and protected user state preserved.\nRuling: user explicitly chose all3 and autonomous integration, so execute approved design inline without extra permission. Preserve workspaces; no cleanup. Exact production RED precedes production staging; private text only before admission.\n')
shutil.copyfile(__file__,D/'source-prepare.py');print('RPC private fragments and plan ready; noJulia')
