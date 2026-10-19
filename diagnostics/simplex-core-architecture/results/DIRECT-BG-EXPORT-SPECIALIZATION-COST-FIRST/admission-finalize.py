"""Fresh independent inverse and immediate host/receipt finalization; no numerical action."""
from pathlib import Path
import json,hashlib,sys,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name(P.name+'-FIRST');RUN=P/'runs/cost1-300';O=P/'outers/cost1-300';C=R/'diagnostics/direct-bg-export-specialized/reproduce'
sys.path.insert(0,str(P));import control as c
checks={}
def ck(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
s=rd(RUN/'sealed.json');base=rd(Q/'admission-check.json');ck(base['accepted'] is True and base['findings']==[],'fresh base check accepted')
inv=rd(C/'source-inverse.json');probe=rd(P/'probe-inverse.json');stage=Path(c.config('cost1-300')['stage']);seed=Path(probe['seed'])
for name,record in inv['files'].items():
 candidate=(C/(name+'.jl')).read_text();ck(sha(C/(name+'.jl'))==record['candidate_sha256'],name+' candidate hash')
 restored=candidate
 for e in reversed(record['edits']):
  ck(restored.count(e['after'])==1,name+' facade unique '+e['before'][:50]);restored=restored.replace(e['after'],e['before'])
 for old,new in inv['rename'].items():restored=restored.replace(new,old)
 ck(restored==Path(record['source']).read_text(),name+' full original byte inverse')
 text=(P/('probe-'+name+'.jl')).read_text();ck(text==(stage/'src'/('_bgxsp_'+name+'.jl')).read_text(),name+' staged probe exact')
 if name=='workspace':ck(text.startswith(probe['header']),'probe header');text=text[len(probe['header']):]
 for old,new,count in reversed(probe['edits'][name]):
  ck(text.count(new)==count,name+' counter inverse '+old[:50]);text=text.replace(new,old)
 for old,new in probe['rename']:text=text.replace(new,old)
 ck(text==candidate,name+' probe full byte inverse')
ck((stage/'src/JSimplex.jl').read_text().replace(probe['stage_addition'],'')==(seed/'src/JSimplex.jl').read_text(),'root only four probe includes')
for p in seed.rglob('*'):
 if p.is_file() and p!=seed/'src/JSimplex.jl':ck(p.read_bytes()==(stage/p.relative_to(seed)).read_bytes(),'preserved GREEN seed '+str(p.relative_to(seed)))
frozen=rd(P/'reviewer-final-check.json');ck(frozen['all_passed'] is True and not frozen['failures'] and len(frozen['checks'])==13235 and frozen['original_reproductions']==21 and frozen['final_counter_reproductions']==23,'13235 frozen checks and 44 malformed rejections preserved')
# Rehash the full exact seal before the near-receipt fresh host boundary.
ck(c.guard.pins_match(s),'final full seal hashes unchanged')
primary={n:sha(n) for n in s['files']+[str(RUN/'sealed.json')]}
ck(len(primary)==2618,'exact2618 receipt primary bindings')
h=c.full_host(s['groups']);m=c.guard.memory();i=c.verify_outer('cost1-300',s,live=True)
ck(c.host_safe(h) and len(h['groups'])==265,'final full265 prior groups AND sessions/noJulia')
ck(all(h[k]==s[k] for k in ('head','master','boot_id')),'final refs boot')
ck(i['pid']==i['pgid']==i['sid']==140961 and i['start_ticks']==11823805,'final live outer start/command/boot identity')
env=dict(x.split('=',1) for x in Path('/proc/140961/environ').read_bytes().decode().split('\0') if '=' in x);expected=rd(P/'environment.json')
ck({k:env.get(k) for k in expected}==expected,'final actual outer environment')
ck(not c.guard.pressure(m),'final RAM swap')
ck(not any((O/n).exists() for n in ['release.json','outer-invocation.json','outer-outcome.json']),'still waiting unreleased')
ck(not any((RUN/n).exists() for n in ['reservation.json','output','admission.json']),'no existing numerical attempt or receipt')
save(Q/'admission-final-check.json',dict(accepted=True,findings=[],checks=checks,count=len(checks),host=h,memory=m,outer_identity=i,checked_at=time.time()))
report='''# Independent exact cost1-300 admission review

Accepted; findings=[]. Scope: BG specialized export cost admission, phase cost1-300 ONLY. This receipt permits the separately released first 300-second process with a 292-second inner guard. It does not release the outer, run Julia, admit a second process or admit 600 seconds.

The saved new admission-check.py passed 8,069 checks. admission-finalize.py independently reconstructs all four specialized files byte-for-byte to the original workspace sources and all four private probe files to the specialized sources, checks the preserved GREEN stage and immediately rechecks the host before receipt. Its exact count and fresh memory/identity observations are in admission-final-check.json. Neither frozen checkers nor operational seal/launch/audit tools were executed. Imports were definitions only.

Exact bindings: 2,617 sealed files plus sealed.json = 2,618 primary receipt hashes; 2,609 canonical preparation paths; accepted final review with 2,610 primary bindings and its evidence; 87 staged files preserving all 83 GREEN files and four probe additions; accepted greengc300 with 81 RUN, 24 evidence and eight external-closure bindings, including matching successful outer outcome identity. The two rejected rounds, all 44 malformed reproductions and accepted 13,235-check final correction evidence remain frozen. Publication and historical hashes are unchanged.

HEAD and remote diagnostic are e149671cd2c9560ae2a91b80614d36799b845240; local/remote master and production HEAD remain 26e2291745999f485a74f643298ca997d65c7205. The full 265 previous PGIDs AND sessions are absent and no visible Julia is present. Isolated waiting PID=PGID=SID140961 retains boot1ecae454-f1f5-4e2e-a95c-7b5474243126, start_ticks11823805, exact sealed command and checkout cwd. Its actual /proc environment equals every pinned environment.json value. Unreadable executable links are recorded as a visibility limitation; no unreadable process identities are accepted. The wrapper chain and runtime inventory are bound; Julia/BLAS1, GCthreads1,0, existing compiled modules, heap2GiB, VM8GiB, RAM>=6GiB and swap<=1GiB are enforced.

Source review covered source guard, seal, outer, launch, supervisor, audit, evidence and strict record schema. Exclusive one-attempt release/reservation, live identity linkage, exact command and stage membership, inclusive timeout/cleanup, resource and terminal samples, measured compilation refusal, warning/world-age/fatal rejection and strict Boolean/scalar schemas remain intact. Pure timeout requires preserved valid prefix and separate review; no longer attempt is admitted here. All eight performance gates are required before any separately admitted second process; allocation-only success does not qualify.

Numerical review: arbitrary callable hooks still cross one thin facade into one original core body, in the original factorize/export/import/make_inner/check_inner order with unchanged exceptions and failure prefixes. Native nonunit orientation keeps its existing solve, four products, scaling/permutation/finite/tolerance safeguards; empty and all-unit paths and Markowitz permutations retain original behavior. Private refactor builds publish once only after mandatory type validation; failures can drop cache while preserving active inner, reentrant guards and independent saved copies. Checked budget arithmetic, exact-shape scratch reuse/eviction, raw-bit fallback refill after partial normalization rejection, output ownership and retained layouts are unchanged. Full byte inverses support these judgments; accepted structural GREEN evidence supports runtime coverage already obtained, without claiming new execution.

Fixed workload: four sparse/dense32/96 fixtures times native threshold_one and Markowitz default; three warm plus seven measured alternating pairs each, 160 windows/112 measured. Total204 constructors,412 refactors,1472 updates,2944FTRAN,1472BTRAN,four copies, plus one synthetic orientation and three importer controls. API counts exclude hidden native work; up to308 genuine native orientation solves remain an upper bound. Eleven probe checkpoints and the private old+new/backend/export coexistence seam are untimed. Timed whole-result capture is symmetric and six nested clocks are subsets. Natural aggregate GC/outliers remain; Task3 has no explicit GC and Task2's amendment is not generalized. Measured compile/recompile must be zero. Every cell requires median paired time<=0.95, median bytes/events nonincrease, each warm/measured/probe graph<=1.10reference, at least3/7 faster and all correctness/input/policy/residual gates. Second-process qualification would additionally need both processes and10/14 faster, under a new admission.

No unnecessary NEW production computational work, allocations or retained-memory cost was found. This admission modifies no production or candidate source. The specialization preserves all original algorithmic bodies and array requests; nine facade/core call boundaries may affect code size/compilation/materialization and require the admitted measurement. Existing export validation scales O(n+l+u), import traversal O(n+u), orientation O(n+l+u) plus the native solve, and update-history/cache costs remain unchanged. Cold hashing scales with pinned bytes; strict post-exit scalar/schema validation includes13 counters per eight probes and does not enter timed Julia. Cache policy512+8ceil(n/64), optionally32n under min(1MiB,P0/16), is a policy charge, not physical memory. No new full scan, solve, copy, conversion, invariant check or retained field was added to production paths.

Declined judgments: no present speedup, zero-allocation, compiler-elimination, universal peak, native allocation/free balance, observer-neutrality, public solver improvement or other-precision generalization is established. Source inverses and Python checks do not execute Julia parsing/dispatch/numerics. Reachable graph size and RSS cannot fully describe hidden native storage or collection timing. Runtime failures, compilation and outliers must be preserved without retuning or omitted samples. First-result review and external closure remain necessary.
'''
with (Q/'admission-review.md').open('x') as f:f.write(report)
evidence_names=['admission-check.py','admission-check.json','admission-finalize.py','admission-final-check.json','admission-review.md','request.txt','entry.py','entry.json','host-entry.json']
evidence={str(Q/n):sha(Q/n) for n in evidence_names}
receipt=dict(scope='BG specialized export cost admission',phase='cost1-300',accepted=True,findings=[],pins_sha256=sha(RUN/'sealed.json'),sha256=primary,evidence_sha256=evidence)
# Verify exact receipt in memory before exclusive publication; no launch/release action.
c.verify_review(receipt,RUN/'sealed.json',s['files']+[str(RUN/'sealed.json')],receipt['scope'],'cost1-300')
save(RUN/'admission.json',receipt)
print(json.dumps(dict(accepted=True,checks=len(checks),primary_bindings=len(primary),evidence_bindings=len(evidence),memory=m,receipt=str(RUN/'admission.json'),receipt_sha256=sha(RUN/'admission.json'))))
