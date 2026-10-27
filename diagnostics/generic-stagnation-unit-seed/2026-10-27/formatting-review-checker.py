from pathlib import Path
import json,hashlib,importlib.util,ast,sys,subprocess
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');M=Path('/home/jspitz/JSimplex.jl')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def need(v,m):
 if not v:raise AssertionError(m)
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
spec=importlib.util.spec_from_file_location('format_common',D/'common_reviewed.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
c.unchanged();host=c.host(read(D/'GREEN-2-run/audit-host.json')['groups']);need(len(host['groups'])==617,'617 full group/session sweep');put(D/'formatting-review-host.json',host)
old=read(D/'source-inverse-reviewed.json');new=read(D/'source-inverse-final.json');base=read(D/'baseline-tree.json')
for path,mapping in [(D/'GREEN-2',old['whole_stage']),(D/'GREEN-final',new['whole_stage'])]:
 need({str(p.relative_to(path)) for p in path.rglob('*') if p.is_file()}==set(mapping),'whole membership')
 for name,h in mapping.items():need(sha(path/name)==h,'whole bytes '+str(path/name))
need(set(old['whole_stage'])==set(new['whole_stage']) and len(new['whole_stage'])==538,'exact 538 membership')
delta=[n for n in sorted(new['whole_stage']) if old['whole_stage'][n]!=new['whole_stage'][n]];need(delta==['src/simplex.jl'],'sole formatting delta')
a=(D/'GREEN-2/src/simplex.jl').read_bytes();b=(D/'GREEN-final/src/simplex.jl').read_bytes();need(a==b+b'\n' and a.endswith(b'end\n\n') and b.endswith(b'end\n'),'exact sole final LF removed')
need(old['names']==new['names']==sorted(n for n in set(base)|set(new['whole_stage']) if base.get(n)!=new['whole_stage'].get(n)) and len(new['names'])==4,'exact four changed files')
for ch in read(D/'changes-final.json'):
 need(ch['new'] in (D/'GREEN-final'/ch['file']).read_text(),'final source region')
for n in [p for p in new['names'] if p.startswith('src/')]:
 text=(D/'GREEN-final'/n).read_text()
 for ch in reversed(read(D/'changes-final.json')):
  if ch['file']==n:need(text.count(ch['new'])==1,'unique inverse');text=text.replace(ch['new'],ch['old'],1)
 need(text==(D/'baseline'/n).read_text(),'exact final inverse')
for name in ['production-review-2.json','GREEN-2-run/result-review.json','publication-preparation-reviewed-2.json','preparation-review-2.json']:
 review=read(D/name);need(review['accepted'] is True and review['findings']==[],'accepted previous review '+name)
 for p,h in review['bindings'].items():need(sha(p)==h,'frozen previous review binding '+p)
review=read(D/'GREEN-2-run/result-review.json');need(review['passed']==review['total']==257423 and review['whole_files']==45,'qualified totals')
need(not (D/'production-commit.json').exists(),'no actual production commit yet')
need(subprocess.check_output(['git','-C',str(M),'ls-remote','origin','refs/heads/master']).decode().split()[0]==c.TARGET,'remote unchanged')
# Independently verify all final helper changes against the already reviewed originals.
old_commit=(D/'commit-integrate-publish-reviewed.py').read_text();new_commit=(D/'commit-integrate-publish-final.py').read_text()
expect=old_commit.replace("D/'GREEN-2'","D/'GREEN-final'").replace('source-inverse-reviewed.json','source-inverse-final.json').replace('publication-preparation-reviewed-2.json','publication-preparation-final.json').replace("c.put(mode+'-host.json'","c.put(mode+'-final-host.json'").replace("review(D/'publication-preparation-final.json')","review(D/'publication-preparation-final.json');review(D/'formatting-review.json')")
need(expect==new_commit,'only reviewed commit helper substitutions')
for n in ['commit-integrate-publish-final.py','finalize-final.py','closure-final.py','diagnostic-publish-final.py']:ast.parse((D/n).read_text(),filename=n)
f=(D/'finalize-final.py').read_text();need("for arm in ['GREEN-2','MASTER']:" in f and "D/'GREEN-final'" in f,'finalizer correct qualified arm and final source');need('/GREEN-final/\\n' in f,'finalizer private ignore');need("D/'finalize-final.py'" in f,'no old script overwrite')
cl=(D/'closure-final.py').read_text();need("D/'GREEN-final'" in cl and "'formatting-review.json'" in cl and "'publication-preparation-final.json'" in cl and "'preparation-review-final.json'" in cl,'closure final bindings')
need("for phase in [D,D/'GREEN-run']:" in cl and "(D/'GREEN-run','pins.json'),(D/'GREEN-2-run','pins.json')" in cl,'original failed attempts and qualified source retained')
for n in ['closure-final.py','diagnostic-publish-final.py']:need("'GREEN-2','GREEN-final','before-master'" in (D/n).read_text(),'all source stages private')
need((D/'diagnostic-publish-final.py').read_text()==(D/'diagnostic-publish-reviewed.py').read_text().replace("'GREEN-2','before-master'","'GREEN-2','GREEN-final','before-master'"),'publisher only private exclusion change')
(D/'formatting-review-checker.py').write_bytes(Path(__file__).read_bytes())
paths=[D/n for n in ['source-inverse-reviewed.json','source-inverse-final.json','changes-final.json','format-prepare.py','PRECOMMIT-FAILURE.md','precommit-failure-host.json','formatting-review-host.json','formatting-review-checker.py','GREEN-2-run/result-review.json','GREEN-2-run/audit.json','GREEN-2-run/contract.json','production-review-2.json']]+[D/s/n for s in ['GREEN-2','GREEN-final'] for n in new['names']]
put(D/'formatting-review.json',{'accepted':True,'findings':[],'scope':'Independent sole-final-LF formatting qualification from frozen accepted GREEN-2; no extra GREEN numerical rerun required. Fresh actual-master run and commit review remain mandatory.','qualified_GREEN_total':257423,'required_MASTER_total':257423,'required_whole_files':45,'sole_delta':'src/simplex.jl: end\\n\\n -> end\\n; one byte 0a removed, all preceding bytes identical','numerical_semantics_unchanged':True,'unnecessary_added_production_work_or_memory_found':False,'bindings':{str(p):sha(p) for p in paths}})
common=[D/n for n in ['common_reviewed.py','source-inverse-final.json','baseline-tree.json','protected-before.json','host-before.json','formatting-review.json','publication_checks.py','finalization_checks.py','helper-source-review-checks-2.json']]
put(D/'publication-preparation-final.json',{'accepted':True,'findings':[],'scope':'Final unexecuted commit/integrate/push helper source acceptance, with exact formatting qualification prerequisite and unique final host records. Future actual commit/master result reviews required.','bindings':{str(p):sha(p) for p in common+[D/'commit-integrate-publish-final.py']}})
protected=read(D/'protected-before.json');extra=[Path(p) for p in protected['files']]+[Path(p) for p in protected['indexes'] if '/worktrees/' in p]
put(D/'preparation-review-final.json',{'accepted':True,'findings':[],'scope':'Final unexecuted finalizer/closure/diagnostic publisher source acceptance; final source stage retained separately from frozen GREEN-2 qualification. Future final review and PASS closure required.','bindings':{str(p):sha(p) for p in common+[D/n for n in ['finalize-final.py','closure-final.py','diagnostic-publish-final.py']]+extra}})
(D/'FORMATTING-REVIEW.md').write_text('''# Independent final formatting qualification

No findings. GREEN-final contains the identical 538 paths and differs from the accepted GREEN-2 stage in exactly one byte: src/simplex.jl has one final LF removed, changing its suffix from `end\\n\\n` to `end\\n`. Every preceding source byte, every test, project/environment file, numerical expression, method signature and body is unchanged. This preserves Julia tokens and semantics; a further numerical GREEN run would add no useful coverage for this whitespace change. Fresh actual-master execution remains required with the exact same 45 files and frozen 257423 pass total.

Independently verified every file hash/membership in both stages, exact four production diff paths and inverse to baseline, frozen production/GREEN-2 review bindings, local/tracking/remote baseline, protected user files/indexes and a fresh 617-group/session host sweep with boot/start ticks/commands and no Julia. Accepted GREEN-2 is 257423 passes across 45 whole files. No old numerical run, launcher or validator was rerun. Original EOF precommit failure, accepted tested stage and prior reviews remain frozen. No additional production computation, allocation or retained memory is introduced by this formatting change.

The new commit helper differs only in final stage/inverse selection, unique final host records and a required formatting-review binding. It retains private-index exact four-path/blob checks, actual commit review before ff-only integration, fresh actual-master result before push and normal nonforce publication. Actual commit bytes remain to be reviewed independently.
''')
(D/'PUBLICATION-PREPARATION-FINAL.md').write_text('''# Final publication and finalization helper source review

No outstanding findings. Reviewed the four new final helpers against their accepted predecessors. Commit requires this explicit sole-LF qualification and uses GREEN-final/source-inverse-final with unique host records. Finalizer and closure compare actual source to GREEN-final while retaining accepted GREEN-2 results and its frozen count. The dynamic finalizer loop remains GREEN-2/MASTER. Reports describe the formatting-only exception and preserved fail-fast precommit warning. All three source stages remain excluded from diagnostic publication and ignored; old scripts are not overwritten.

Closure now requires the formatting and final preparation reviews, retains both rejected original attempts and all original/corrected pin inventories, and verifies exact beforeimages. Diagnostic publisher changes only the private-stage exclusion; its exact staged/committed names/blobs and fail-fast normal push are unchanged. Definitions-only helper checks are unchanged from thirteen accepted synthetic checks. Every reviewed script parsed statically; no publication action or Julia ran. Future actual commit review, fresh 45-file actual-master result with 257423 passes, final review and PASS closure are still prerequisites.
''')
print(json.dumps({'accepted':True,'sole_delta':delta,'removed_bytes':1,'files':538,'required_MASTER_passes':257423,'host_groups':617}))
