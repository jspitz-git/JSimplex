"""One-shot textual provenance/inverse, NOT a Julia parser or semantic checker."""
from pathlib import Path
import json,hashlib,difflib,subprocess,tempfile,re
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
S=R/'.superpowers/sdd/2026-10-16-direct-lu-policy-adapters/driver-stages/green/src'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
# Each adapted behavior has an exact original excerpt; new arena mechanics explicitly
# do not claim to be byte-identical source. All originals are also whole-file pinned.
groups=[
('construction','direct-factor.jl',116,148,['_dynamic_bg_with_exporter','_dynamic_bg_factor'],'Same real factorization/export/normalization; tighter two-arm rejection; direct arena import replaces packed construction.'),
('metadata','triangular_factorization.jl',343,350,['_dynamic_bg_storage_count','_dynamic_bg_growth','_dynamic_bg_finite'],'Count logical live coefficients, not reserved slots; finite helper is new cold metadata.'),
('dimensions','triangular_factorization.jl',517,524,['_dbg_dimensions','_dynamic_bg_dimension'],'Same RHS then output length checks and backend dimension.'),
('prepared','triangular_spikes.jl',1,123,['_dbg_begin_prepared!','_dbg_invalidate_destination!','_dbg_copy_prepared!','_dbg_save_prepared!'],'Two slots and eviction/provenance retained, no unsupported sparse buffers; reuse original finish helper.'),
('rows','triangular_rows.jl',14,68,['_dbg_sync_rows!'],'Reuse exact BartelsGolubUpdate compiler and subtract helper.'),
('eligibility','triangular_rows.jl',120,155,['_dbg_begin_update!','_dbg_columns'],'Dirty suffix/diagonal/identity eligibility unchanged, no finite scan.'),
('ftran','triangular_rows.jl',159,187,['_dbg_forward!'],'Same history/arithmetic/map handoff; row_order comes from arena.'),
('ftran-entry','triangular_factorization.jl',756,773,['forward_solve!','forward_solve','_ordinary_forward_solve!'],'Same aliases and prepare=false eviction. Only Vector Float64 accepted; keywords rejected.'),
('upper-ftran','triangular_factorization.jl',655,679,['_dbg_backsolve!','_dbg_diagonal','_dbg_value','_dbg_entry'],'Traverse logical column rows in same order; one stored value per shared slot.'),
('upper-btran','triangular_factorization.jl',681,705,['_dbg_transpose_upper!'],'Same scalar subtract then divide; ordered column links.'),
('btran-entry','triangular_factorization.jl',801,860,['_unit_transpose_rhs','_dbg_transpose_rhs!','transpose_solve!','transpose_solve'],'Same unit metadata, scratch aliases, dimensions and invalidation; dense subset only.'),
('btran-history','triangular_rows.jl',189,206,['_dbg_transpose_rhs!'],'Same separate upper/history map handoff and reverse history; implementation in transpose_solve!.'),
('btran-prefix','triangular_rows.jl',226,241,['_dbg_transpose_start!'],'Same prefix division order and full suffix arithmetic; integer start instead of view.'),
('spike','triangular_factorization.jl',862,908,['_dbg_prepare_spike!','_dbg_replace_column!'],'Same tolerance, pivot, provenance and reconstruction order. New column mechanics preserve q IDs.'),
('pure-swaps','bartels_golub_rows.jl',57,68,['_dbg_last_pure'],'Same exact zero and pivot magnitude decisions.'),
('update','triangular_factorization.jl',1112,1187,['_dynamic_bg_replace!','_dbg_eliminate_row!','replace_column!'],'Same branching, stable-column arithmetic, history success publication. Linked row union replaces packed target lookup/insertion.'),
('copy','triangular_factorization.jl',1285,1296,['copy_basis_factorization'],'Copy all arena arrays, preserve physical IDs; original packed copy rebases physical IDs. Logical state and independent history map preserved.'),
('refactor','direct-factor.jl',164,176,['_dynamic_bg_refactor_with_exporter!','refactorize!','_dynamic_bg_mode'],'Complete candidate then same concrete type publication; no reuse.')]
bundle=[];records=[]
for key,fn,lo,hi,names,note in groups:
 lines=(S/fn).read_text().splitlines(keepends=True);need(lo<=len(lines),'bad start '+key);hi=min(hi,len(lines))
 text=''.join(lines[lo-1:hi]);need(text,'empty '+key)
 bundle.append('# SOURCE '+key+' '+fn+':'+str(lo)+'-'+str(hi)+'\n'+text+'\n')
 records.append(dict(group=key,source=str(S/fn),first=lo,last=hi,excerpt_sha256=hashlib.sha256(text.encode()).hexdigest(),candidate_helpers=names,intentional_difference=note))
original=''.join(bundle);candidate=(C/'dynamic-bg-reviewed.jl').read_text()
(E/'reference-excerpts-reviewed.jl').write_text(original)
patch=''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/text.jl',tofile='b/text.jl'))
(E/'reference-to-candidate-reviewed.patch').write_text(patch)
# An exact reversible TEXT delta, not a claim that every line is merely storage.
with tempfile.TemporaryDirectory(prefix='bg-task2-inverse-') as td:
 p=Path(td)/'text.jl';p.write_text(original)
 for reverse,expected in [(False,candidate),(True,original)]:
  args=['git','apply','--unsafe-paths']+(['--reverse'] if reverse else [])+[str(E/'reference-to-candidate-reviewed.patch')]
  out=subprocess.run(args,cwd=td,text=True,capture_output=True)
  need(out.returncode==0,out.stderr);need(p.read_text()==expected,'Text inverse mismatch')
# Coverage of function declaration names; this is lexical only.
names=set(re.findall(r'^(?:Base\.@noinline )?(?:@inline )?function (\w+!?)(?:\(|\s)',candidate,re.M))
names|=set(re.findall(r'^(\w+!?)\([^\n]*=',candidate,re.M))
mapped={n for rec in records for n in rec['candidate_helpers']}
need(names<=mapped,'Unmapped candidate names '+repr(names-mapped))
inputs=sorted({S/rec['source'].split('/')[-1] for rec in records}|{C/'slot-upper-reviewed.jl',C/'dynamic-bg-reviewed.jl'})
save(C/'reference-bindings-reviewed.json',dict(scope='Exact source excerpt bindings and reversible text delta; numerical equivalence UNQUALIFIED',groups=records,candidate_declared_names=sorted(names),text_inverse_forward=True,text_inverse_reverse=True,sha256={str(p):sha(p) for p in inputs+[E/'reference-excerpts-reviewed.jl',E/'reference-to-candidate-reviewed.patch']}))
print('Task2 reference groups',len(groups),'declared helper names',len(names),'forward/reverse text delta PASS; no Julia')
