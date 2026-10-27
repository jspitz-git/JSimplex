from pathlib import Path
import ast,importlib.util,hashlib,json,tempfile,sys
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,m):
 if not x:raise AssertionError(m)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def put(p,obj):
 with Path(p).open('x') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
files=['commit-integrate-publish-reviewed.py','publication_checks.py','finalization_checks.py','finalize-reviewed.py','closure-reviewed.py','diagnostic-publish-reviewed.py']
for n in files:ast.parse((D/n).read_text(),filename=n)
finalizer=(D/'finalize-reviewed.py').read_text();prior=(D/'finalize-reviewed.py.before-review').read_text()
need(finalizer==prior.replace("for arm in ['GREEN','MASTER']:","for arm in ['GREEN-2','MASTER']:",1),'only dynamic loop correction')
need("for arm in ['GREEN-2','MASTER']:" in finalizer,'accepted corrected run dynamically selected')
for n in ['commit-integrate-publish-reviewed.py','finalize-reviewed.py','closure-reviewed.py']:
 text=(D/n).read_text();need("D/'GREEN-2'" in text and 'GREEN-2-run' in text,'corrected stage/result selected '+n)
need("for phase in [D,D/'GREEN-run']:" in (D/'closure-reviewed.py').read_text(),'both rejected originals checked')
need("(D/'GREEN-run','pins.json'),(D/'GREEN-2-run','pins.json')" in (D/'closure-reviewed.py').read_text(),'both original and corrected inventories')
for n in ['closure-reviewed.py','diagnostic-publish-reviewed.py']:
 need("private={'baseline','RED','GREEN','GREEN-2'" in (D/n).read_text(),'corrected private source excluded '+n)

pub=load(D/'publication_checks.py','new_pub_review');fin=load(D/'finalization_checks.py','new_fin_review');passes=[]
def rejects(label,func):
 try:func()
 except (AssertionError,KeyError):passes.append(label)
 else:raise AssertionError('did not reject '+label)
with tempfile.TemporaryDirectory(prefix='ssu-helper-review-') as td:
 root=Path(td);master=root/'master';stage=root/'stage';pins={'inventory':{}}
 for tree in ['src','test']:
  for folder in [master,stage]:(folder/tree).mkdir(parents=True);(folder/tree/'x').write_bytes(tree.encode())
  p=master/tree/'x';pins['inventory'][str(p)]={'resolved':str(p.resolve()),'sha256':sha(p)}
 pub.verify_tested_trees(master,stage,pins,need,sha);passes.append('identical complete tested trees')
 (master/'src/x').write_bytes(b'drift');rejects('actual source drift',lambda:pub.verify_tested_trees(master,stage,pins,need,sha));(master/'src/x').write_bytes(b'src')
 (stage/'test/new').write_bytes(b'new');rejects('stage added member',lambda:pub.verify_tested_trees(master,stage,pins,need,sha));(stage/'test/new').unlink()
 p=str(master/'src/x');orig=pins['inventory'][p]['resolved'];pins['inventory'][p]['resolved']='wrong';rejects('changed resolved alias',lambda:pub.verify_tested_trees(master,stage,pins,need,sha));pins['inventory'][p]['resolved']=orig
 baseline={};names=['src/x','test/x','test/new'];source={}
 for n in names[:2]:
  before=root/'baseline'/n;before.parent.mkdir(exist_ok=True,parents=True);before.write_bytes(n.encode());baseline[n]=sha(before);source[str(master/n)]={'before':str(before),'sha256':sha(before)}
 (root/'before-master').mkdir();before=root/'before-master/master.index';before.write_bytes(b'index');idx=str(master/'index');protected={'indexes':{idx:sha(before)}};hist={'master_before':'base','source_before':source,'master_index_before':{idx:{'before':str(before),'sha256':sha(before)}}};cont={'master_source_before':source,'master_index_before':hist['master_index_before']}
 def maps():pub.verify_historical_maps(root,master,idx,'base',names,hist,cont,protected,baseline,need,sha)
 maps();passes.append('exact source and index before maps');hist['master_before']='other';rejects('wrong baseline ref map',maps);hist['master_before']='base';before.write_bytes(b'drift');rejects('changed original index bytes',maps);before.write_bytes(b'index')
 source[str(master/'src/x')]['before']=str(root/'baseline/test/x');rejects('wrong source before path',maps);source[str(master/'src/x')]['before']=str(root/'baseline/src/x')
 path=root/'continuation';prior=root/'before-continuation';prior.write_bytes(b'old\n');path.write_bytes(b'new\nold\n');other=root/'user';other.write_bytes(b'user');protected_files={str(path):sha(prior),str(other):sha(other)};mapping={str(path):{'before':str(prior),'sha256':sha(prior)}};allowed={str(path)};bindings={str(path):sha(path)}
 def continuation():fin.verify_protected_files(protected_files,mapping,allowed,bindings,sha,need)
 continuation();passes.append('exact continuation prefix and unrelated user file')
 path.write_bytes(b'new\nmodified\n');bindings[str(path)]=sha(path);rejects('lost verbatim original suffix',continuation);path.write_bytes(b'new\nold\n');bindings[str(path)]=sha(path)
 bindings[str(path)]='wrong';rejects('unreviewed current continuation',continuation);bindings[str(path)]=sha(path)
 other.write_bytes(b'drift');rejects('unrelated user file drift',continuation);other.write_bytes(b'user')
 allowed.add('extra');rejects('extra continuation allowance',continuation)
(D/'helper-source-review-checker-2.py').write_bytes(Path(__file__).read_bytes())
put(D/'helper-source-review-checks-2.json',{'accepted':True,'checks':passes,'scope':'New offline AST and synthetic fail-closed helper checks only; no Julia, process sweep, prior validator, actual Git mutation or publishing script execution.'})
common=[D/n for n in ['common_reviewed.py','source-inverse-reviewed.json','baseline-tree.json','protected-before.json','host-before.json','helper-fix-1.json','finalize-reviewed.py.before-review','helper-source-review-checker-2.py','helper-source-review-checks-2.json']]
put(D/'publication-preparation-reviewed-2.json',{'accepted':True,'findings':[],'scope':'Static source acceptance of unexecuted exact-four-path private-index commit, independently reviewed ff-only integration and fresh actual-master normal push helper. Future result/commit/master reviews and runtime guards remain required.','bindings':{str(p):sha(p) for p in common+[D/'commit-integrate-publish-reviewed.py',D/'publication_checks.py']}})
protected=json.loads((D/'protected-before.json').read_text());extra=[Path(p) for p in protected['files']]
# The linked diagnostic index is unchanged across production integration; the master index necessarily changes and is guarded by its later MASTER protected snapshot.
extra += [Path(p) for p in protected['indexes'] if '/worktrees/' in p]
put(D/'preparation-review-2.json',{'accepted':True,'findings':[],'scope':'Static source acceptance of unexecuted finalizer, exact beforeimage/continuation checks, PASS closure and exact diagnostic publication. Does not certify future results or authorize bypassing final review/closure.','bindings':{str(p):sha(p) for p in common+[D/n for n in ['finalization_checks.py','finalize-reviewed.py','closure-reviewed.py','diagnostic-publish-reviewed.py','publication_checks.py']]+extra}})
(D/'PUBLICATION-PREPARATION-REVIEW-2.md').write_text('''# Publication helper source review

No outstanding actionable findings. Accepted the unexecuted commit/integrate/push helper and publication_checks.py under exact absolute SHA bindings. This is prospective source review; it does not claim any future numerical result, commit, integration or publication succeeded.

Commit requires accepted corrected production and GREEN-2 result reviews, the complete exact staged tree and protected actual files/indexes. A temporary private index starts from authoritative master and stages exactly four explicit byte streams; tree membership and diff whitespace are checked before commit-tree. A new codex ref uses zero-old-ref creation. Actual committed blobs are compared to staged bytes. Real indexes are preserved.

Integration separately requires actual commit review, unchanged candidate/user files, baseline local/tracking/remote refs, sole expected parent and clean target paths. It saves exact main index and source-before mappings before ff-only merge with hooks disabled, then checks actual target bytes, unrelated index entries/staged data, diagnostic index and unchanged production tree. No reset, force, discard or unrelated staging is introduced.

Push separately requires accepted fresh actual-master result review and equal GREEN-2/master counts. It checks approved read/push endpoints, local exact target and acceptable remote ref, complete actual/tested/pinned src/test trees, every MASTER pin, exact baseline/source/index before maps and original bytes. Push is normal nonforce with an explicit commit/refspec and remote/tracking verification; errors fail fast. The later MASTER preparation/result review must bind the exact same 45 ordered files and frozen GREEN count; this helper does not substitute for that admission.

New offline synthetic checks exercised matching complete trees and rejection of source drift, extra membership and changed resolution, plus exact historical maps and rejection of wrong baseline, wrong before path and changed original index bytes. No original validator, Julia, host sweep during active GREEN, Git write or helper action was executed. No unsupported runtime/performance claim is made for these cold diagnostic paths.
''')
(D/'PREPARATION-REVIEW-2.md').write_text('''# Finalization and diagnostic publication source review

Resolved finding: the first unexecuted corrected finalizer retained a dynamic GREEN audit loop. That would require an accepted audit from the rejected original GREEN. The exact one-line correction now selects GREEN-2 and MASTER, with previous text and helper-fix-1 evidence preserved. This review binds only the corrected helper hash.

No outstanding actionable findings. Accepted unexecuted finalize-reviewed.py, closure-reviewed.py, diagnostic-publish-reviewed.py and their definitions-only checks under exact absolute SHA bindings. Bound protected file bytes and the unchanged linked-worktree index constrain future finalization preparation; actual-master index checks come from its later snapshot. Future final review and PASS closure remain prerequisites.

Finalizer verifies exact published master refs, accepted GREEN-2/master results with identical counts, complete actual/tested source trees and fresh full historical groups AND sessions/boot/start-ticks/commands/no-Julia before continuation writes. Existing continuation bytes must match the protected snapshot; copies and maps are made before prefixing, preserving the original verbatim suffix. Only current continuation files and new case artifacts are written. Report separates measured local work/event reductions from timing variation and records the rejected first comparison and finite coverage.

Closure rechecks actual master/parent, diagnostic ref, complete source and baseline bytes, protected files/indexes and all accepted reviews. Historical changed master source/index and continuation bindings resolve only through exact beforeimages. It checks every phase pin and tree membership, accepted counts and frozen master total, verbatim continuation, original diagnostic index and fresh process/session quiescence. Its accepted result binds every nonprivate case artifact and current continuation, excluding only explicit self/publication records.

Diagnostic publication verifies final review/PASS closure, all bound bytes, expected local/remote diagnostic ref and approved endpoint, published master and no unrelated staged changes. It enumerates explicit nonprivate case paths, rejects new unclosed files, calculates expected Git blobs, stages only those paths and the self-describing plan, verifies exact staged names/blobs, commits, then verifies exact parent and every committed name/blob before fail-fast normal nonforce push. Master/user files and non-diagnostic indexes are checked before and after; the intentionally changed diagnostic index must be clean after commit. Frozen diagnostic trailing whitespace is narrowly recognized without rewriting raw evidence. Original failed GREEN process/pins and corrected GREEN-2 evidence are separately checked; both private stages and index copies are excluded from publication.

New synthetic fail-closed checks cover exact protected continuations, unrelated user files, original suffix corruption, mismatched reviewed current hash and extra continuation allowances. Source AST parses successfully. No helper action, Julia, existing auditor, active-process sweep or Git mutation was run. These source acceptances are prospective; future artifacts and actual final review are not presumed accepted. Declined-to-judge behaviors: none.
''')
print(json.dumps({'accepted':True,'synthetic_checks':len(passes),'helpers':files}))
