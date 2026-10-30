from pathlib import Path
import hashlib,json,subprocess,os,sys,shutil
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');M=Path('/home/jspitz/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';T=Path('/tmp/devex-production-integration-20261030');D=W/'diagnostics/dual-recovery-devex-production-integration/2026-10-30';BASE='c0fa748ffa61ccb7c1caaf248c40324f60bc737b';HEAD='c9966bf1635b43a5a39177df2d3e14d3a67bc440';BRANCH='refs/heads/codex/devex-dual-recovery-production'
sys.path.insert(0,str(W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'));import common as C
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(root,*a,env=None):return subprocess.check_output(['git','-C',str(root),*a],text=True,env=env).strip()
def fresh(p,v):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
h=C.host();need(len(h['checked_groups'])==742 and not h['still_active_current_launcher'],'fresh742');need(git(W,'rev-parse','HEAD')==HEAD and git(M,'rev-parse','HEAD')==BASE,'refs before');need(git(M,'branch','--show-current')=='master' and not git(M,'diff','--cached','--name-only'),'master/index');need(git(M,'diff','--name-only')=='.vscode/settings.json','unexpected master changes');need(not git(W,'diff','HEAD','--name-only') and not git(W,'diff','--cached','--name-only'),'diagnostic tracked/index changes')
manifest=json.loads((P/'manifest.json').read_text());review=json.loads((P/'review-final.json').read_text());need(review['accepted'] and not review['runtime_qualified'] and not review['production_admission'],'prep review')
# Recheck historical review through exact before maps; source still baseline here.
rb=review.get('bindings',review.get('read_bindings',{}));need(all(sha(p)==v for p,v in rb.items()),'preparation review hashes');need(all(sha(P/'prepared'/n)==v for n,v in manifest['payload_sha256'].items()),'payload hashes')
user={str(M/n):sha(M/n) for n in ('.vscode/settings.json','Manifest.toml','LocalPreferences.toml')};need(all(not (M/n).exists() for n in manifest['payload'] if n not in manifest['baseline_sha256']),'new path collision')
for rel,v in manifest['baseline_sha256'].items():need(sha(M/rel)==sha(W/rel)==sha(P/'baseline'/rel)==v,'four exact baselines')
D.mkdir(parents=True,exist_ok=False);fresh(D/'before.json',dict(host=h,diagnostic_head=HEAD,master=BASE,master_status=git(M,'status','--porcelain','-uall'),user_hashes=user,before_maps={str(root/rel):dict(copy=str(P/'baseline'/rel),sha256=v) for root in (W,M) for rel,v in manifest['baseline_sha256'].items()},source_preparation_commit=HEAD,scope='before local integration; no Julia or publication'))
# Preserve caller's primary index: production tree is built through a private index.
env=os.environ.copy();env['GIT_INDEX_FILE']=str(T/'production.index');git(W,'read-tree',BASE,env=env)
blobs={}
for rel in manifest['payload']:
 blob=git(W,'hash-object','-w','--no-filters',str(P/'prepared'/rel));git(W,'update-index','--add','--cacheinfo','100644',blob,rel,env=env);blobs[rel]=blob
tree=git(W,'write-tree',env=env);commit=git(W,'commit-tree',tree,'-p',BASE,'-m','Allow Devex fallback for inconclusive dual recovery weights')
need(git(W,'diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()==manifest['payload'],'production exact11names');need(all(git(W,'rev-parse',commit+':'+n)==v for n,v in blobs.items()),'production exact11blobs')
need(subprocess.run(['git','-C',str(W),'show-ref','--verify','--quiet',BRANCH]).returncode==1,'production branch exists');git(W,'update-ref',BRANCH,commit,'0'*40)
fresh(D/'production-commit.json',dict(commit=commit,parent=BASE,tree=tree,branch=BRANCH,names=manifest['payload'],blobs=blobs,scope='local exact11-file production commit; no remote publication'))
# Local reversible integration is explicitly requested; remote master remains old until tests/review pass.
git(M,'merge','--ff-only',commit);need(all(sha(M/n)==v for n,v in user.items()),'user files changed');need(git(M,'status','--porcelain','-uall')==json.loads((D/'before.json').read_text())['master_status'],'master dirty state changed')
# Keep this existing diagnostic checkout on the same production tree without merging diagnostics into master.
git(W,'merge','--no-edit',BRANCH);diag=git(W,'rev-parse','HEAD');need(not git(W,'diff',commit,diag,'--','src','test','Project.toml','.github'),'diagnostic production paths differ');need(not git(W,'diff','HEAD','--name-only') and not git(W,'diff','--cached','--name-only'),'diagnostic dirty after merge');need(git(M,'rev-parse','HEAD')==commit and git(M,'rev-parse','origin/master')==BASE,'master local refs')
for root in (W,M):need(all(sha(root/n)==v for n,v in manifest['payload_sha256'].items()),'integrated payload mismatch')
fresh(D/'integration.json',dict(accepted=True,production_commit=commit,production_branch=BRANCH,diagnostic_head=diag,diagnostic_before=HEAD,remote_master_before=BASE,actual_master=str(M),user_hashes=user,before_maps=json.loads((D/'before.json').read_text())['before_maps'],payload_sha256=manifest['payload_sha256'],source_preparation_report=str(P/'INTEGRATION-PREPARATION.md'),numerical_used_seconds=1108.3747013349202,remaining_seconds=691.6252986650798,verification_unexecuted=True,master_push_performed=False,scope='local integration only; one newly admitted actual-master verification required before push'))
shutil.copyfile(__file__,D/'integrate.py');print(json.dumps(dict(local_integration=True,production_commit=commit,diagnostic_head=diag,exact_files=11,user_files_unchanged=True,master_pushed=False,Julia=False,remaining=691.6252986650798)))
