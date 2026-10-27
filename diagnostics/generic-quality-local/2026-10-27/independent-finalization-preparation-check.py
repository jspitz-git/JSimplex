from pathlib import Path
import ast,json,hashlib,subprocess,statistics,tempfile,types,copy
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda n:json.loads((D/n).read_text());checks=[]
def need(v,s):
 if not v:raise AssertionError(s)
def reject(f):
 try:f()
 except (RuntimeError,AssertionError):return
 raise AssertionError('expected fixture rejection')
files=['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py','prepare-finalization.py','common_next.py'];trees={n:ast.parse((D/n).read_text()) for n in files}
try:ast.parse((D/'prepare-finalization.syntax-failed.py').read_text())
except SyntaxError:pass
else:raise AssertionError('original syntax rejection lost')
checks.append('all intended future scripts parse; failed generator source remains rejected; completed generator is provenance only')
# Evaluate only report/table expressions with dummy future totals, never canonical effects.
t=trees['finalize.py'];selected=[];start=False
for node in t.body:
 if isinstance(node,ast.Import) and any(a.name=='statistics' for a in node.names):start=True
 if not start:continue
 if isinstance(node,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='prefix' for a in node.targets):selected.append(node);break
 if isinstance(node,(ast.Import,ast.Assign,ast.For)):
  if isinstance(node,ast.For) and ast.unparse(node.target)!='(arm, scope, label)':continue
  selected.append(node)
fake=types.SimpleNamespace(read=read);ns={'c':fake,'target':'FUTURE_REVIEWED_COMMIT','green':{'passed':200000,'elapsed_shared_seconds':1000.0},'master':{'passed':200000,'elapsed_shared_seconds':1001.0}}
exec(compile(ast.Module(selected,[]),'report expressions only','exec'),ns)
assert ns['table'].count('\n')==5 and '| 0.9466 |' in ns['table'] and '| 0.9806 |' in ns['table'] and '| 0.4824 |' in ns['table'] and '| 0.9076 |' in ns['table'] and '| 0.9087 |' in ns['table'] and '| 0.9656 |' in ns['table']
for x in ['63391','2172cells/39096windows','152.583s','all805GCwindows','63389PASS+2','REJECTED','No literal numeric-group absence claim','No custom recorder/manualTeststack','Fullsuite/x64'] :assert x in ns['report'],x
assert 'FUTURE_REVIEWED_COMMIT' in ns['report'] and '200000PASS' in ns['report']
checks.append('actual report AST expressions evaluated without writes: all six metric rows, measured counters, rejection and host/coverage wording match')
helper=next(n for n in trees['finalization_checks.py'].body if isinstance(n,ast.FunctionDef));hns={'Path':Path};exec(compile(ast.Module([helper],[]),'pure protection helper','exec'),hns);verify=hns['verify_protected_files']
with tempfile.TemporaryDirectory(prefix='local-quality-review-') as tmp:
 root=Path(tmp);protected={};mapping={};current={}
 for n in ['STATUS.md','roadmap.md']:
  old=root/(n+'.before');old.write_text('old '+n);live=root/n;live.write_bytes(b'prefix\n'+old.read_bytes());protected[str(live)]=sha(old);mapping[str(live)]={'before':str(old),'sha256':sha(old)};current[str(live)]=sha(live)
 user=root/'user';user.write_text('user');protected[str(user)]=sha(user);allowed=set(mapping)
 verify(protected,mapping,allowed,current,sha,need)
 first=next(iter(mapping));old=Path(mapping[first]['before']);saved=old.read_bytes();old.write_bytes(b'changed');reject(lambda:verify(protected,mapping,allowed,current,sha,need));old.write_bytes(saved)
 saved=Path(first).read_bytes();Path(first).write_bytes(b'changedprefix\n'+old.read_bytes());reject(lambda:verify(protected,mapping,allowed,current,sha,need));Path(first).write_bytes(saved)
 user.write_text('changed');reject(lambda:verify(protected,mapping,allowed,current,sha,need));user.write_text('user')
 reject(lambda:verify(protected,{**mapping,str(user):{'before':str(user),'sha256':sha(user)}},allowed,current,sha,need))
 reject(lambda:verify(protected,mapping,allowed,{},sha,need))
checks.append('pure helper accepts only two exact preserved/reviewed continuations and rejects five corruption/missing-binding/extra-map fixtures')
allow=read('host-identity-allowance.json');assert sha(D/'host-identity-allowance.json')=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92';assert sha(allow['historical_record'])==allow['historical_sha256']
assert len(allow['identities'])==1 and allow['identities'][0]['command']==['/usr/libexec/wsl-pro-service'];assert allow['identities'][0]['boot_id']!=allow['historical_child']['boot_id'] and allow['identities'][0]['start_ticks']!=allow['historical_child']['start_ticks']
actual=allow['identities'][0];assert actual in allow['identities']
for key in ['pid','pgid','sid','start_ticks','boot_id','command']:
 altered=copy.deepcopy(actual);altered[key]=(['julia'] if key=='command' else 'other' if key=='boot_id' else altered[key]+1);assert altered not in allow['identities']
source=(D/'common_next.py').read_text();assert "need(actual in permitted" in source and source.index("need(not any(Path(v).name.lower().startswith('julia')")>source.index('need(actual in permitted')
checks.append('hard-pinned host allowance matches historical evidence; full tuple required; changing any identity field rejects; Julia check remains unconditional')
fin=(D/'finalize.py').read_text();cl=(D/'closure.py').read_text();pub=(D/'diagnostic-publish.py').read_text()
assert fin.index("prep=c.read('preparation-review.json')")<fin.index("c.put('final-host.json'") and "prep['accepted'] is True and prep['findings']==[]" in fin
assert "for p,h in prep['bindings'].items():c.need(c.sha(p)==h" in fin and "Path(__file__).resolve()!=(D/'finalize.py').resolve()" in fin
assert "rejected['accepted'] is False" in cl and "for p,h in rejected['bindings'].items():before(p,h)" in cl and "original['returncode']==1" in cl
assert "[D,D/'comparison-2',D/'RED-run',D/'GREEN-run',D/'MASTER-run']" in cl and "'comparison-2/admission.json','comparison-2/result-review.json'" in cl
assert pub.index('protect_files();protect_indexes(True)')<pub.index("'add','-f'") and pub.index('protect_files();protect_indexes(False)')<pub.index("'push','origin'")
assert "expected[str(plan.relative_to(R))]=blob(plan.read_bytes())" in pub and "':'+n" in pub and "new+':'+n" in pub and "'push','origin',new+':refs/heads/codex/simplex-core-architecture'" in pub
checks.append('preparation/allpass/publication gates before finalizer effects; explicit original-rejection and all-five-phase closure; exact plan/self/staged/committed blobs and normal push')
inv=read('source-inverse.json');assert inv['accepted'] and len(inv['names'])==4
for n,h in inv['whole_stage'].items():assert sha(D/'GREEN'/n)==h
assert set(inv['whole_stage'])=={str(p.relative_to(D/'GREEN')) for p in (D/'GREEN').rglob('*') if p.is_file()}
changes=read('changes.json');git=lambda *a:subprocess.check_output(['git','-C',str(M),*a]);base='ca64312f7f74b1d7bec047718399f229674b3e1d'
for name in {v['file'] for v in changes.values()}:
 old=git('show',base+':src/'+name).decode();s=old
 for v in changes.values():
  if v['file']==name:assert s.count(v['old'])==1;s=s.replace(v['old'],v['new'],1)
 assert s==(D/'GREEN/src'/name).read_text()
 for v in reversed(list(changes.values())):
  if v['file']==name:assert s.count(v['new'])==1;s=s.replace(v['new'],v['old'],1)
 assert s==old
for n,h in read('baseline-tree.json').items():assert sha(D/'baseline'/n)==h
checks.append('exact GREEN inventory and hashes; declared changes reconstruct both whole staged sources and reverse exactly to authoritative base')
phasecounts={}
for phase in [D,D/'comparison-2',D/'RED-run',D/'GREEN-run']:
 pins=json.loads((phase/'pins.json').read_text());phasecounts[str(phase.relative_to(D))]=len(pins['inventory']);assert set(pins['files'])==set(pins['inventory'])
 for p,v in pins['inventory'].items():assert sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'],p
 for tree in map(Path,pins['trees']):assert {str(p) for p in tree.rglob('*') if p.is_file()}=={p for p in pins['inventory'] if Path(p).is_relative_to(tree)}
for p,h in {**read('protected-before.json')['files'],**read('protected-before.json')['indexes']}.items():assert sha(p)==h,p
r=read('result-review.json');assert r['accepted'] is False and read('output/process.json')['returncode']==1
for n in ['result-review.json','comparison-2/admission.json','comparison-2/result-review.json','RED-run/result-review.json']:
 for p,h in read(n)['bindings'].items():assert sha(p)==h,(n,p)
assert read('comparison-2/audit.json')['assertions']==63391 and read('RED-run/audit.json')['passed']==16579 and read('RED-run/audit.json')['expected_failures']==4
checks.append('four existing phase pins/tree memberships, protected files/indexes and rejected/accepted review bindings exact; future MASTER gate remains required')
result={'accepted':True,'checks':checks,'phase_inventory_counts':phasecounts,'scope':'preparation only; no future GREEN/MASTER/publication acceptance','no_Julia':True,'no_canonical_script_execution':True,'no_git_mutation':True}
Path('/tmp/independent-local-finalization-preparation-output.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
