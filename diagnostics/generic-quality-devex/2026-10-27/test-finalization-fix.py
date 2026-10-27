from pathlib import Path
import ast,hashlib,tempfile,types,shutil,json,importlib.util
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');results=[]
def need(x,s):
 if not x:raise RuntimeError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rejected(name,f,kind=RuntimeError):
 try:f()
 except kind:results.append(dict(name=name,passed=True))
 else:raise RuntimeError('expected rejection '+name)
spec=importlib.util.spec_from_file_location('qc_finalization',D/'finalization_checks.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
with tempfile.TemporaryDirectory(prefix='quality-finalization-pure-') as temp:
 root=Path(temp)
 def fixture(name):
  p=root/name;p.mkdir();old={};maps={};current={};files={}
  for n in ['STATUS.md','roadmap.md']:
   before=p/(n+'.before');before.write_text('original '+n+'\n');live=p/n;live.write_text('accepted prefix\n'+before.read_text());files[str(live)]=sha(before);maps[str(live)]=dict(before=str(before),sha256=sha(before));current[str(live)]=sha(live)
  user=p/'settings.json';user.write_text('user settings\n');files[str(user)]=sha(user)
  return p,files,maps,current,set(maps),user
 p,files,maps,current,allowed,user=fixture('old-red')
 tree=ast.parse((D/'closure.py.before-review-fix').read_text());node=next(n for n in tree.body if isinstance(n,ast.For) and ast.unparse(n.iter)=="protected['files'].items()")
 def old_loop():exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-old-protected-loop','exec'),dict(protected={'files':files},c=types.SimpleNamespace(need=need),digest=sha))
 rejected('RED_actual_old_closure_rejects_intended_continuations',old_loop)
 h.verify_protected_files(files,maps,allowed,current,sha,need);results.append(dict(name='GREEN_mapped_continuations_and_unchanged_userfile',passed=True))
 for case in ['before_corruption','current_corruption','unmapped_user_corruption','missing_current_binding','extra_mapping','wrong_old_hash','removed_verbatim_suffix']:
  p,files,maps,current,allowed,user=fixture(case);first=next(iter(maps))
  if case=='before_corruption':Path(maps[first]['before']).write_text('bad')
  elif case=='current_corruption':Path(first).write_text('changed prefix\n'+Path(maps[first]['before']).read_text())
  elif case=='unmapped_user_corruption':user.write_text('bad')
  elif case=='missing_current_binding':del current[first]
  elif case=='extra_mapping':maps[str(user)]=dict(before=str(user),sha256=sha(user))
  elif case=='wrong_old_hash':maps[first]['sha256']='0'*64
  elif case=='removed_verbatim_suffix':Path(first).write_text('bad');current[first]=sha(first)
  rejected('reject_'+case,lambda:h.verify_protected_files(files,maps,allowed,current,sha,need))
 selfpath=root/'finalize.py';selfpath.write_text('unchanged source\n');ns=dict(__file__=str(selfpath),D=root,Path=Path,shutil=shutil)
 oldtree=ast.parse((D/'finalize.py.before-review-fix').read_text());old=next(n for n in oldtree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value).startswith("shutil.copyfile(__file__,"))
 rejected('RED_actual_canonical_selfcopy',lambda:exec(compile(ast.Module([old],[]),'old-selfcopy','exec'),ns),shutil.SameFileError)
 newtree=ast.parse((D/'finalize.py').read_text());new=next(n for n in newtree.body if isinstance(n,ast.If) and '__file__' in ast.unparse(n.test))
 exec(compile(ast.Module([new],[]),'guarded-selfcopy','exec'),ns);need(selfpath.read_text()=='unchanged source\n','canonical self source');results.append(dict(name='GREEN_actual_canonical_path_no_selfcopy',passed=True))
other=root/'other.py' if False else None
out=dict(accepted=True,checks=results,count=len(results),no_Julia=True,no_source_ref_index_change=True,bindings={str(D/n):sha(D/n) for n in ['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py','finalize.py.before-review-fix','closure.py.before-review-fix']})
with (D/'finalization-fix-tests.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('PASS',len(results),'disposable offline checks, actual old AST RED -> fixed helper/canonical path GREEN')
