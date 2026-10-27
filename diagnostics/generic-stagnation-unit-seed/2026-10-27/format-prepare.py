from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');sys.path.insert(0,str(D));import common_reviewed as c
c.unchanged();c.need(not (D/'production-commit.json').exists(),'no commit was made');c.put('precommit-failure-host.json',c.host(c.read('GREEN-2-run/audit-host.json')['groups']))
(D/'PRECOMMIT-FAILURE.md').write_text('''The first private-index commit preparation stopped before commit-tree/update-ref at git diff-tree --check: exactly src/simplex.jl:779: new blank line at EOF. No production ref/source/index changed. Unreachable Git blobs/tree may exist, harmless and preserved. Original helper/commit-host/stage/reviews remain frozen. Prepare a separately reviewed one-LF-only clean final stage; keep GREEN-2 source/result intact and perform full fresh actual-master validation before push.
''')
shutil.copytree(D/'GREEN-2',D/'GREEN-final');p=D/'GREEN-final/src/simplex.jl';s=p.read_bytes();c.need(s.endswith(b'end\n\n'),'exact two final LF');p.write_bytes(s[:-1]);old=c.read('source-inverse-reviewed.json');names=old['names']
changes=c.read('changes-reviewed.json');c.need(changes[0]['new'].endswith('\n\n'),'method finalLF');changes[0]['new']=changes[0]['new'][:-1];c.put('changes-final.json',changes)
for n in names:
 if not n.startswith('src/'):continue
 t=(D/'GREEN-final'/n).read_text()
 for ch in reversed(changes):
  if ch['file']==n:c.need(t.count(ch['new'])==1,'one finalinverse');t=t.replace(ch['new'],ch['old'])
 c.need(t==(D/'baseline'/n).read_text(),'finalinverse '+n)
tree={str(p.relative_to(D/'GREEN-final')):c.sha(p) for p in (D/'GREEN-final').rglob('*') if p.is_file()};c.need(set(tree)==set(old['whole_stage']),'same membership');diff=[n for n in tree if tree[n]!=old['whole_stage'][n]];c.need(diff==['src/simplex.jl'],'sole LF file')
c.put('source-inverse-final.json',dict(accepted=True,names=names,candidate_sha256={n:c.sha(D/'GREEN-final'/n) for n in names},whole_stage=tree,production_baseline=c.TARGET,all_numerical_checks_retained=True,no_added_scans_solves_copies=True,formatting_only_from_qualified_GREEN_2=dict(file='src/simplex.jl',removed_exact_final_bytes='0a',old_sha256=c.sha(D/'GREEN-2/src/simplex.jl'),new_sha256=c.sha(p))))
# Previous qualified source/result/pins are preserved; final code differs only by a final LF.
for oldname,newname in [('commit-integrate-publish-reviewed.py','commit-integrate-publish-final.py'),('finalize-reviewed.py','finalize-final.py'),('closure-reviewed.py','closure-final.py'),('diagnostic-publish-reviewed.py','diagnostic-publish-final.py')]:
 t=(D/oldname).read_text().replace("D/'GREEN-2'","D/'GREEN-final'").replace('source-inverse-reviewed.json','source-inverse-final.json').replace('publication-preparation-reviewed-2.json','publication-preparation-final.json').replace('preparation-review-2.json','preparation-review-final.json')
 if oldname.startswith('commit-'):
  t=t.replace("c.put(mode+'-host.json'","c.put(mode+'-final-host.json'")
  t=t.replace("review(D/'publication-preparation-final.json')","review(D/'publication-preparation-final.json');review(D/'formatting-review.json')")
 elif oldname.startswith('finalize-'):
  t=t.replace('/GREEN-2/\\n','/GREEN-2/\\n/GREEN-final/\\n').replace("D/'finalize-reviewed.py'","D/'finalize-final.py'")
  t=t.replace('Exact source inverse, reviewed private-index commit','A separate final stage removes only one trailing LF from simplex.jl (end\\n\\n to end\\n); accepted GREEN-2 numerical code/tests remain exact modulo that final whitespace, independently qualified without redundant GREEN. First commit preparation stopped failfast before commit on the EOF warning and is preserved. Fresh actualMASTER loads the clean final bytes with all45files/257423expectations. Exact source inverse, reviewed private-index commit')
 else:
  t=t.replace("'GREEN-2','before-master'","'GREEN-2','GREEN-final','before-master'")
 if oldname.startswith('closure-'):
  t=t.replace("'production-review-2.json'","'production-review-2.json','formatting-review.json'")
 ast.parse(t);(D/newname).write_text(t)
shutil.copyfile(__file__,D/'format-prepare.py');print('final one-LF source stage and exactinverse prepared; originalqualifiedstage frozen')
