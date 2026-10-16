"""New offline actual-dispatch bindings and source-derived access ledger; not Julia."""
from pathlib import Path
import hashlib,json
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce';S=R/'.superpowers/sdd/2026-10-16-direct-lu-policy-adapters/driver-stages/green/src'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
records=[];text=''
for fn,lo,hi,names,note in [('triangular_indices.jl',90,143,['_dbg_backsolve!','_dbg_transpose_upper!'],'Actual stable physical BG dispatch; same operation sequence, linked slot reads replace paired packed ids/values.'),('triangular_factorization.jl',172,183,['_dbg_entry','_dbg_value'],'Original packed binary row lookup replaced by column-tail ordered linked lookup.'),('triangular_factorization.jl',387,409,['_dbg_begin_update!','copy_basis_factorization'],'Track/finish/cache helpers reused; invalidate is separately adapted.'),('triangular_factorization.jl',147,170,['_dbg_replace_column!'],'Original packed-column omission of exact zeros and finite eligibility stores.')]:
 lines=(S/fn).read_text().splitlines(keepends=True);excerpt=''.join(lines[lo-1:hi]);text+=f'# {fn}:{lo}-{hi}\n'+excerpt+'\n';records.append(dict(source=str(S/fn),first=lo,last=hi,candidate_helpers=names,excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),note=note))
with (E/'actual-dispatch-excerpts.jl').open('x') as f:f.write(text)
save(C/'actual-dispatch-bindings.json',dict(scope='Supplement to reviewed18groups; actual stable BG solve dispatch explicitly bound, not a runtime claim',records=records,sha256={str(p):sha(p) for p in [S/'triangular_indices.jl',S/'triangular_factorization.jl',C/'dynamic-bg-reviewed.jl',E/'actual-dispatch-excerpts.jl']}))
# Index-only witness from review R1. No matrix solve/Julia arithmetic. Each old
# absent stable-column lookup restarts at the row head. New code scans carried
# row once after the first tail/top+lower predicates, then reads lower tails.
rows=[]
for k in (4,8,16,32):
 stable=list(range(1,k+2));queries=list(range(k+2,2*k+1));old=0
 for cid in queries:
  for x in stable:
   if x>=cid:break
   old+=1
 # Two node inspections in first top query, one first lower, k+1 blocker slots,
 # and k-2 remaining lower tails. Bound includes absent-test overhead separately.
 new_node_bound=2+1+len(stable)+max(0,k-2)
 if old!=(k-1)*(k+1) or new_node_bound>2*k+3:raise RuntimeError('source witness')
 rows.append(dict(n=2*k,carried_row_degree=k+1,successful_chain=k-1,old_row_next_visits=old,new_node_inspection_bound=new_node_bound))
save(E/'lookup-work-witness.json',dict(scope='SOURCE-DERIVED integer access witness only; not runtime/instrumentation/benchmark or a general all-state bound',rows=rows,immediate_rejection='First top/lower predicates before carried-row scan; tail queries O(1)/O(2) on valid Hessenberg pivots.',remaining_cost='If first pivot is pure but next fails, a full carried-row scan can be additional work; arbitrary non-Hessenberg diagnostic states may need longer column walks. Task3 cost gates unchanged.',sha256={str(p):sha(p) for p in [C/'dynamic-bg.jl',C/'dynamic-bg-reviewed.jl',Path(__file__).resolve()]}))
print('Actual stable dispatch supplement4groups and source access witness4sizes PASS; no Julia')
