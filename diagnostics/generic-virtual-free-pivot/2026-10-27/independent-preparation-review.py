from pathlib import Path
import json,hashlib,ast,statistics,tempfile
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');M=Path('/home/jspitz/JSimplex.jl')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
files=['commit-integrate-publish.py','publication_checks.py','finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py','common_ready.py']
for n in files:ast.parse((D/n).read_text(),filename=str(D/n))
# Only newly reviewed pure definitions are executed with synthetic temporary data.
ns={};exec(compile((D/'publication_checks.py').read_text(),str(D/'publication_checks.py'),'exec'),ns)
fs={};exec(compile((D/'finalization_checks.py').read_text(),str(D/'finalization_checks.py'),'exec'),fs)
test_count=0
def reject(f,label):
 global test_count
 try:f()
 except RuntimeError:test_count+=1
 else:raise RuntimeError('did not reject '+label)
with tempfile.TemporaryDirectory(prefix='vfp-review-pure-') as tmp:
 r=Path(tmp);master=r/'M';stage=r/'S'
 for t in ['src','test']:
  for root in [master,stage]:(root/t).mkdir(parents=True);(root/t/'a').write_text(t)
 pins={'inventory':{str(p):{'resolved':str(p.resolve()),'sha256':sha(p)} for p in master.rglob('*') if p.is_file()}}
 ns['verify_tested_trees'](master,stage,pins,need,sha);test_count+=1
 (master/'test/extra').write_text('x');reject(lambda:ns['verify_tested_trees'](master,stage,pins,need,sha),'extra tree file');(master/'test/extra').unlink()
 (stage/'src/a').write_text('bad');reject(lambda:ns['verify_tested_trees'](master,stage,pins,need,sha),'changed stage bytes');(stage/'src/a').write_text('src')
 old=r/'old';current=r/'current';other=r/'other';old.write_bytes(b'original\n');current.write_bytes(b'new\noriginal\n');other.write_bytes(b'unchanged')
 protected={str(current):sha(old),str(other):sha(other)};cont={str(current):{'before':str(old),'sha256':sha(old)}};bound={str(current):sha(current)}
 fs['verify_protected_files'](protected,cont,{str(current)},bound,sha,need);test_count+=1
 reject(lambda:fs['verify_protected_files'](protected,{},set(cont),bound,sha,need),'missing continuation map')
 current.write_bytes(b'new changed original');bound[str(current)]=sha(current);reject(lambda:fs['verify_protected_files'](protected,cont,set(cont),bound,sha,need),'missing verbatim continuation')
 current.write_bytes(b'new\noriginal\n');bound[str(current)]=sha(current);other.write_bytes(b'bad');reject(lambda:fs['verify_protected_files'](protected,cont,set(cont),bound,sha,need),'changed userfile')
 (r/'baseline/src').mkdir(parents=True);(r/'baseline/src/a').write_text('src');(r/'before-master').mkdir();idx=r/'before-master/master.index';idx.write_bytes(b'index')
 original_index=str(master/'index');baseline={'src/a':sha(r/'baseline/src/a')};hist={'master_before':'base','source_before':{str(master/'src/a'):{'before':str(r/'baseline/src/a'),'sha256':baseline['src/a']}},'master_index_before':{original_index:{'before':str(idx),'sha256':sha(idx)}}};continuation={'master_source_before':hist['source_before'],'master_index_before':hist['master_index_before']};prot={'indexes':{original_index:sha(idx)}}
 call=lambda:ns['verify_historical_maps'](r,master,original_index,'base',['src/a','test/new'],hist,continuation,prot,baseline,need,sha)
 call();test_count+=1
 hist['master_before']='wrong';reject(call,'changed original ref');hist['master_before']='base'
 hist['source_before'][str(master/'src/a')]['sha256']='wrong';reject(call,'wrong original source bytes')
rows=read(D/'comparison-3/summary-final.json')['cases'];scopes=['audit','virtual','virtual_transposed','enter_dantzig','enter_devex','partial_hit','partial_rebuild','summary','pivot'];table={}
for scope in scopes:
 rr=[r for r in rows if r['scope']==scope and r['type']=='BigFloat'];need(rr and all(r['original']['bytes']>0 and r['original']['events']>0 for r in rr),'report rows '+scope);table[scope]={'cells':len(rr),'time_ratio':statistics.median(r['paired_ratio'] for r in rr),'byte_ratio':statistics.median(r['candidate']['bytes']/r['original']['bytes'] for r in rr),'event_ratio':statistics.median(r['candidate']['events']/r['original']['events'] for r in rr)}
evidence=dict(accepted=True,findings=[],static_ast_files=files,pure_synthetic_checks=test_count,report_table=table,existing_launchers_or_publishers_executed=False,no_Julia_executed=True,new_checker_sha256=sha(__file__))
put(D/'PREPARATION-CHECKS.json',evidence)
report='''Independent publication/finalization preparation review — PASS.

Scope is the unexecuted commit/integrate/push and finalize/closure/diagnostic-publication helpers, not acceptance of future test results or commits. The new independent preparation checker parsed all seven Python files, exercised ten synthetic success/rejection checks of the newly reviewed pure tree/map/protected-file helpers, and verified that all nine report-table scopes exist with nonzero byte/event denominators. It did not execute any launcher, numeric checker, commit, integration, push, finalizer or publisher; no Julia operation occurred. Synthetic fixtures were temporary and unrelated to production.

Commit uses a private temporary Git index initialized from the exact base, explicit seven names and reviewed stage bytes, checks exact tree membership and whitespace, creates one base-parent commit and an exclusive branch, then rechecks committed blobs and original real indexes. Integration requires independent actual-commit review, original local/tracking/remote base, clean target paths and exact commit/stage blobs. It saves the original master index and maps original source hashes to immutable baseline bytes before ff-only merge. It verifies target bytes, unrelated index entries/staged diff, diagnostic index and protected user files afterward. No force push, reset, cleanup or user-file rewrite is present.

Push requires accepted independent actual-master results, matching observed GREEN total and zero failures, current tested/pinned source/test membership and resolved targets, exact preserved baseline and source/index maps, approved origin endpoint and unchanged remote base or target. It performs a normal explicit master-ref push and verifies local/tracking/remote identity. These runtime gates and subsequent independent review remain required; this preparation review does not replace them.

Finalization requires accepted publication/refs and GREEN/MASTER results, source/test equality, fresh historical-group/session host checks, and exact original continuation hashes before copying. Original diagnostic index and STATUS/roadmap are saved; the only continuation edits prepend new evidence to original bytes. Report wording preserves rejected diagnostics, post-exit auditor provenance, nonuniform C timing, measured/preparation separation and full-suite/x64/retention limits. Old raw/pins/rejections are not rewritten. New helper and evidence bindings use immutable diagnostic baseline/stage/artifacts, never current master source or index bytes that integration changes.

Closure verifies independent reviews and all launch pins either at unchanged current paths or their explicit exact beforeimages, unchanged baseline membership, current actual/tested trees, accepted numerical results, original existing test bytes, current protected indexes, continuation suffixes and fresh process/resource state. It emits a closed artifact inventory. Diagnostic publication requires accepted closure and final review, verifies every closed binding, rejects unrelated staging/new unclosed files and remote/ref drift, stages only explicit artifacts plus the two reviewed continuations, checks every staged and committed blob including its self-describing plan, and uses normal nonforce branch push followed by remote verification. Only preserved diagnostic whitespace exceptions are allowed. Baseline/stages/index beforeimages remain private. Final independent review and exact closure/publication checks remain mandatory.

No blocking helper defect or copied-case assumption was found in this scope. These are cold publication/checking paths and do not alter production iteration work, allocations or retained numerical memory. No performance benchmark is warranted for these helpers.
'''
with (D/'PREPARATION-REVIEW.md').open('x') as f:f.write(report)
immutable=['source-inverse.json','changes.json','baseline-tree.json','protected-before.json','host-before.json','host-seed.json','common_ready.py','PLAN.md','PREPARATION-REVIEW.md','PREPARATION-CHECKS.json','comparison-3/result-review.json','comparison-3/audit-final.json','comparison-3/summary-final.json','RED-ready-run/result-review.json','production-review.json','independent-preparation-review.py']
def bound(names):return {str(D/n):sha(D/n) for n in names}
publication=bound(immutable+['commit-integrate-publish.py','publication_checks.py'])
put(D/'publication-preparation-reviewed.json',dict(accepted=True,findings=[],bindings=publication,preparation_only=True,no_Julia_executed=True,no_mutable_master_source_or_index_bindings=True))
final=bound(immutable+['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py','publication_checks.py','publication-preparation-reviewed.json'])
put(D/'preparation-review.json',dict(accepted=True,findings=[],bindings=final,preparation_only=True,no_Julia_executed=True,no_mutable_master_source_or_index_bindings=True))
print(json.dumps(dict(accepted=True,pure_synthetic_checks=test_count,publication_bindings=len(publication),finalization_bindings=len(final))))
