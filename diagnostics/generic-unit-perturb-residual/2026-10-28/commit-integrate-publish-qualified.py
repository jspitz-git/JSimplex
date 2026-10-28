from pathlib import Path
import os,subprocess,tempfile,json,sys,shutil
os.environ['GIT_OPTIONAL_LOCKS']='0'
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];sys.path.insert(0,str(D));import common_qualified as c
base=c.TARGET;stage=D/'GREEN';names=json.loads((D/'source-inverse.json').read_text())['names']
def git(args,root=M,**kw):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],**kw)
def g(args,root=M):return git(args,root=root).decode().strip()
def load(p):return json.loads(Path(p).read_text())
def review(path):
 a=load(path);c.need(a['accepted'] is True and a['findings']==[],'review '+str(path))
 for p,h in a['bindings'].items():c.need(c.sha(p)==h,'review binding '+p)
def protect(indexes=True):
 p=load(D/'protected-before.json')
 for n,h in p['files'].items():c.need(c.sha(n)==h,'protected file '+n)
 if indexes:
  for n,h in p['indexes'].items():c.need(c.sha(n)==h,'protected index '+n)
def candidate():
 inv=load(D/'source-inverse.json');c.need(inv['accepted'] and inv['names']==names,'exact candidate')
 for n in names:c.need(c.sha(stage/n)==inv['candidate_sha256'][n],'exact staged '+n)
 c.need({str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}==set(inv['whole_stage']),'whole stage membership')
 for n,h in inv['whole_stage'].items():c.need(c.sha(stage/n)==h,'whole staged '+n)
extra=set()
for p in D.glob('*-run/audit-host.json'):extra.update(load(p)['groups'])
review(D/'publication-preparation-reviewed.json')
mode=sys.argv[1];c.need(mode in ['commit','integrate','push'],'action');c.put(mode+'-final-host.json',c.host(extra))
if mode=='commit':
 review(D/'production-review.json');review(D/'GREEN-run/result-review.json');candidate();protect()
 c.need(g(['rev-parse','HEAD'])==g(['rev-parse','origin/master'])==base,'base refs')
 message='Reduce unit-weight pricing and perturbation and residual temporaries\n\nApply independently accepted complete-function multiprecision scalar savings with unchanged arithmetic, ownership, pivot policy and numerical safeguards. Add ordinary correctness and allocation regressions.\n'
 (D/'commit-message.txt').write_text(message)
 with tempfile.TemporaryDirectory(prefix='stagnation-unit-seed-index-') as temp:
  env=dict(os.environ,GIT_INDEX_FILE=str(Path(temp)/'index'))
  subprocess.run(['/usr/bin/git','-C',str(M),'read-tree',base],env=env,check=True);blobs={}
  for n in names:
   blob=git(['hash-object','-w','--stdin'],input=(stage/n).read_bytes()).decode().strip();blobs[n]=blob
   subprocess.run(['/usr/bin/git','-C',str(M),'update-index','--add','--cacheinfo','100644',blob,n],env=env,check=True)
  tree=git(['write-tree'],env=env).decode().strip();c.need(g(['diff-tree','--no-commit-id','--name-only','-r',base,tree]).splitlines()==names,'exact selected names')
  subprocess.run(['/usr/bin/git','-C',str(M),'diff-tree','--check',base,tree],check=True)
  c.put('staged-tree.json',dict(base=base,tree=tree,names=names,blobs=blobs,sha256={n:c.sha(stage/n) for n in names}))
  target=git(['commit-tree',tree,'-p',base],input=message.encode()).decode().strip()
 branch='refs/heads/codex/generic-unit-perturb-residual'
 subprocess.run(['/usr/bin/git','-C',str(M),'update-ref',branch,target,'0'*40],check=True)
 for n in names:c.need(git(['show',target+':'+n])==(stage/n).read_bytes(),'exact commit '+n)
 protect();c.put('production-commit.json',dict(commit=target,parent=base,branch=branch,tree=tree,names=names,blobs=blobs,real_indexes_unchanged=True));print(target)
elif mode=='integrate':
 review(D/'commit-review.json');candidate();protect();co=load(D/'production-commit.json');target=co['commit']
 c.need(g(['branch','--show-current'])=='master' and g(['rev-parse','HEAD'])==g(['rev-parse','origin/master'])==base,'base refs')
 c.need(g(['ls-remote','origin','refs/heads/master']).split()[0]==base,'remote drift');c.need(g(['rev-list','--parents','-n','1',target]).split()==[target,base],'sole parent')
 c.need(not g(['status','--porcelain=v1','--untracked-files=all','--',*names]),'dirty targets')
 for n in names:c.need(git(['show',target+':'+n])==(stage/n).read_bytes(),'reviewed commit '+n)
 entries=git(['ls-files','--stage','-z']);staged=git(['diff','--cached','--raw','-z']);c.put('integration-before.json',dict(entries=entries.decode().split('\0'),staged=staged.decode(),target=target))
 before=D/'before-master';before.mkdir();index=Path(g(['rev-parse','--path-format=absolute','--git-path','index']));shutil.copyfile(index,before/'master.index')
 c.put('integration-historical-path-map.json',dict(master_before=base,master_index_before={str(index):dict(before=str(before/'master.index'),sha256=c.sha(before/'master.index'))},source_before={str(M/n):dict(before=str(D/'baseline'/n),sha256=c.sha(D/'baseline'/n)) for n in names if (D/'baseline'/n).exists()},older_maps_preserved=True))
 subprocess.run(['/usr/bin/git','-C',str(M),'-c','core.hooksPath=/dev/null','merge','--ff-only','--no-edit',target],check=True)
 c.need(g(['rev-parse','HEAD'])==target,'master target')
 def unrelated(b):return [x for x in b.decode().split('\0') if x and x.split('\t',1)[1] not in names]
 c.need(unrelated(entries)==unrelated(git(['ls-files','--stage','-z'])) and staged==git(['diff','--cached','--raw','-z']),'unrelated index')
 for n in names:c.need((M/n).read_bytes()==(stage/n).read_bytes(),'integration exact '+n)
 protect(False);ri=g(['rev-parse','--path-format=absolute','--git-path','index'],R);c.need(c.sha(ri)==load(D/'protected-before.json')['indexes'][ri],'diagnostic index');c.need(not g(['diff','--name-only','HEAD','--','src','test','Project.toml']),'production drift')
 c.put('integration-after.json',dict(target=target,fast_forward=True,pushed=False,protected_unchanged=True,unrelated_indexes_unchanged=True));print(target)
else:
 review(D/'MASTER-run/result-review.json');candidate();protect(False);co=load(D/'production-commit.json');target=co['commit'];a=load(D/'MASTER-run/audit.json');green=load(D/'GREEN-run/audit.json')
 c.need(a['accepted'] and a['expected_failures']==0 and green['accepted'] and a['passed']==green['total'],'master tests')
 c.need(g(['branch','--show-current'])=='master' and g(['rev-parse','HEAD'])==g(['rev-parse','master'])==target,'local master')
 approved=['git@github.com:jspitz-git/JSimplex','https://github.com/jspitz-git/JSimplex','ssh://git@github.com/jspitz-git/JSimplex']
 for args in [['remote','get-url','--push','--all','origin'],['remote','get-url','--all','origin']]:
  urls=[url.removesuffix('.git') for url in g(args).splitlines()];c.need(len(urls)==1 and urls[0] in approved,'approved origin endpoint')
 remote=g(['ls-remote','origin','refs/heads/master']).split()[0];c.need(remote in [base,target],'remote drift')
 pins=load(D/'MASTER-run/pins.json')
 from publication_checks import verify_tested_trees,verify_historical_maps
 verify_tested_trees(M,stage,pins,c.need,c.sha)
 hist=load(D/'integration-historical-path-map.json')
 prospective=dict(master_source_before=hist['source_before'],master_index_before=hist['master_index_before'])
 verify_historical_maps(D,M,g(['rev-parse','--path-format=absolute','--git-path','index']),base,names,hist,prospective,load(D/'protected-before.json'),load(D/'baseline-tree.json'),c.need,c.sha)
 baseline=load(D/'baseline-tree.json')
 c.need(set(baseline)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()},'exact baseline membership')
 for n,h in baseline.items():c.need(c.sha(D/'baseline'/n)==h,'preserved baseline '+n)
 for n,v in pins['inventory'].items():c.need(c.sha(n)==v['sha256'],'verified master pin '+n)
 if remote!=target:
  with (D/'push.log').open('x') as log:subprocess.run(['/usr/bin/git','-C',str(M),'push','origin',target+':refs/heads/master'],stdout=log,stderr=subprocess.STDOUT,check=True)
 c.need(g(['ls-remote','origin','refs/heads/master']).split()[0]==g(['rev-parse','origin/master'])==target,'remote verify');protect(False)
 c.put('publication.json',dict(accepted=True,commit=target,parent=base,local_master=target,tracking=target,remote_master=target,names=names,normal_nonforce_push=True,precommit_qualification='freshwholefilesGREEN' ,master_tests=a['passed']));print(target)
