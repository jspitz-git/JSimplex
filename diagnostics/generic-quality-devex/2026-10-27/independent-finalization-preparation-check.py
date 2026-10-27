from pathlib import Path
import ast, hashlib, json, subprocess, tempfile, types, shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,message):
 if not v:raise AssertionError(message)
def reject(fn):
 try:fn()
 except (RuntimeError,AssertionError):return
 raise AssertionError('negative fixture unexpectedly accepted')
read=lambda n:json.loads((D/n).read_text())
checks=[]
# Parse only: never execute any canonical finalization/publication runner.
trees={n:ast.parse((D/n).read_text()) for n in ['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py']}
helper=next(n for n in trees['finalization_checks.py'].body if isinstance(n,ast.FunctionDef));ns={'Path':Path};exec(compile(ast.Module([helper],[]),'pure reviewed helper','exec'),ns);verify=ns['verify_protected_files']
with tempfile.TemporaryDirectory(prefix='independent-quality-finalization-') as tmp:
 p=Path(tmp);files={};maps={};current={}
 for name in ['STATUS.md','roadmap.md']:
  old=p/(name+'.before');old.write_text('old evidence '+name+'\n');live=p/name;live.write_bytes(b'new accepted prefix\n'+old.read_bytes());files[str(live)]=sha(old);maps[str(live)]={'before':str(old),'sha256':sha(old)};current[str(live)]=sha(live)
 user=p/'userfile';user.write_text('user bytes');files[str(user)]=sha(user);allowed=set(maps)
 verify(files,maps,allowed,current,sha,need);checks.append('fixed helper accepts exact old/new continuation bytes and unchanged userfiles')
 first=next(iter(maps));old=Path(maps[first]['before']);saved=old.read_bytes();old.write_bytes(b'corrupt');reject(lambda:verify(files,maps,allowed,current,sha,need));old.write_bytes(saved)
 live=Path(first);saved=live.read_bytes();live.write_bytes(b'wrong prefix\n'+old.read_bytes());reject(lambda:verify(files,maps,allowed,current,sha,need));live.write_bytes(saved)
 saved=user.read_bytes();user.write_bytes(b'corrupt');reject(lambda:verify(files,maps,allowed,current,sha,need));user.write_bytes(saved)
 reject(lambda:verify(files,maps,allowed,{k:v for k,v in current.items() if k!=first},sha,need))
 reject(lambda:verify(files,{**maps,str(user):{'before':str(user),'sha256':sha(user)}},allowed,current,sha,need))
 live.write_bytes(b'accepted hash but missing old suffix');changed={**current,first:sha(live)};reject(lambda:verify(files,maps,allowed,changed,sha,need))
 checks.append('six independent negative fixtures reject corrupted before/current/user bytes, missing binding, extra map, removed suffix')
 selfpath=p/'finalize.py';selfpath.write_text('source');guard=next(n for n in trees['finalize.py'].body if isinstance(n,ast.If) and '__file__' in ast.unparse(n.test));exec(compile(ast.Module([guard],[]),'canonical selfcopy fixture','exec'),{'Path':Path,'D':p,'__file__':str(selfpath),'shutil':shutil});assert selfpath.read_text()=='source';checks.append('canonical self-copy guard preserves source without SameFileError')
# The mandatory preparation verdict and all binding checks precede any output write.
text=(D/'finalize.py').read_text();assert text.index("prep=c.read('preparation-review.json')")<text.index("c.put('final-host.json'") and "prep['accepted'] is True and prep['findings']==[]" in text and "for p,h in prep['bindings'].items():c.need(c.sha(p)==h" in text
pub=(D/'diagnostic-publish.py').read_text();assert pub.index('protect_files();protect_indexes(True)')<pub.index("'add','-f'")
assert pub.index('protect_files();protect_indexes(False)')<pub.index("'push','origin'")
assert pub.rindex('protect_files();protect_indexes(False)')>pub.index("'push','origin'")
assert "expected[str(plan.relative_to(R))]=blob(plan.read_bytes())" in pub and "for n,b in expected.items():c.need(g(['rev-parse',':'+n])==b" in pub and "for n,b in expected.items():c.need(g(['rev-parse',new+':'+n])==b" in pub
checks.append('preparation gate precedes writes; protection before staging/push and after; plan self-blob verified before/after commit')
originals={'finalize.py':'5f583d1687ceda3682130a5ddceef18989312477be2535996103f58d55e1847e','closure.py':'df4644b05038aeb9f86ee3774c572de41241d9355122e9a4813f13147ebe4fcc','diagnostic-publish.py':'c6fa2f4ea02eb37e5a971104ffcbbba1217f9880bb84c5c71e9fe201a768c257'}
for n,h in originals.items():assert sha(D/(n+'.before-review-fix'))==h
fix=read('finalization-fix-tests.json');assert fix['accepted'] and fix['count']==11 and all(x['passed'] for x in fix['checks'])
for p,h in fix['bindings'].items():assert sha(p)==h
checks.append('all original rejected scripts preserved exactly; author eleven-check result bindings exact')
git=lambda *args:subprocess.check_output(['git','-C',str(M),*args]);target=read('production-commit.json')['commit'];names=git('diff-tree','--no-commit-id','--name-only','-r',target).decode().splitlines();assert names==read('source-inverse.json')['names']
paths=git('ls-tree','-r','--name-only',target,'--','src','test').decode().splitlines();assert len(paths)==532
for n in paths:assert git('show',target+':'+n)==(M/n).read_bytes()==(D/'GREEN'/n).read_bytes()
changes=read('changes.json')
for n in sorted({v['file'] for v in changes.values()}):
 old=git('show',target+'^:src/'+n).decode();new=git('show',target+':src/'+n).decode();s=old
 for v in changes.values():
  if v['file']==n:assert s.count(v['old'])==1;s=s.replace(v['old'],v['new'],1)
 assert s==new
 for v in reversed(list(changes.values())):
  if v['file']==n:assert s.count(v['new'])==1;s=s.replace(v['new'],v['old'],1)
 assert s==old
checks.append('all 532 commit/current/GREEN source-test blobs equal; five changes and exact three-source forward/inverse')
for n,h in read('baseline-tree.json').items():assert sha(D/'baseline'/n)==h
mapped=0;hist=read('integration-historical-path-map.json')
for phase in [D,D/'RED-run',D/'GREEN-run',D/'MASTER-run']:
 pins=json.loads((phase/'pins.json').read_text());assert set(pins['files'])==set(pins['inventory'])
 for p,v in pins['inventory'].items():
  assert str(Path(p).resolve(strict=True))==v['resolved']
  if sha(p)==v['sha256']:continue
  if p in hist['master_index_before']:q=Path(hist['master_index_before'][p]['before'])
  else:assert Path(p).is_relative_to(M/'src') or Path(p).is_relative_to(M/'test');q=D/'baseline'/Path(p).relative_to(M)
  assert sha(q)==v['sha256'];mapped+=1
checks.append('all four phase pin inventories resolve with '+str(mapped)+' exact historical source/index beforeimages')
print(json.dumps({'accepted':True,'checks':checks,'no_Julia':True,'no_runner_execution':True,'no_git_mutation':True},indent=2))
