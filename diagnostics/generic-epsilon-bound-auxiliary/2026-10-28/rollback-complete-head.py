from pathlib import Path
import sys,json,subprocess,os,shutil
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'counter-gc-preparation'));import common as c
M=c.M;R=c.R;BASE='235eedf33901fe8c4cc06a3d8c3508ef2fcbb718';CAND=c.TARGET;OLD='90848b35ca1090522f472d4111d678642b9fef4a'
def raw(a,root=M,**kw):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],timeout=60,**kw)
def g(a,root=M):return raw(a,root).decode().strip()
def put(n,x):
 with (D/n).open('x')as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def read(n):return json.loads((D/n).read_text())
def tree():return {str(p.relative_to(M)):c.sha(p) for t in ['src','test'] for p in (M/t).rglob('*')if p.is_file()}
def refs(detached):
 c.need(g(['rev-parse','HEAD'])==(CAND if detached else BASE) and g(['rev-parse','master'])==g(['rev-parse','origin/master'])==BASE,'exact local refs')
 c.need(g(['branch','--show-current'])==('' if detached else 'master'),'HEAD attachment')
 c.need(g(['rev-parse','refs/heads/codex/generic-epsilon-bound-auxiliary'])==CAND and g(['rev-list','--parents','-n','1',CAND]).split()==[CAND,BASE],'backup')
 c.need(g(['ls-remote','origin','refs/heads/master']).split()[0]==BASE,'remote master')
 c.need(g(['rev-parse','HEAD'],R)==g(['rev-parse','origin/codex/simplex-core-architecture'],R)==g(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]==OLD,'diagnostic refs')
 for root in [M,R]:c.need(g(['remote','get-url','--push','--all','origin'],root)=='git@github.com:jspitz-git/JSimplex.git','approved endpoint')
review=read('rollback-head-review.json');c.need(review['accepted'] is True and review['bindings'][str(Path(__file__).resolve())]==c.sha(__file__),'independent exact recovery review')
c.need(read('rollback-failure.json')['accepted'] is False and read('rollback-failure.json')['last_step']==2 and not(D/'rollback-after.json').exists(),'exact interrupted transaction')
refs(True);b=read('baseline-tree.json');expected={p:h for p,h in b.items()if p.startswith(('src/','test/'))};c.need(tree()==expected,'source already exactly baseline')
idx=Path(g(['rev-parse','--path-format=absolute','--git-path','index']));ridx=Path(g(['rev-parse','--path-format=absolute','--git-path','index'],R))
original=read('rollback-before.json');env=dict(os.environ,GIT_INDEX_FILE=str(D/'before-master/master.index'));c.need(raw(['ls-files','--stage','-z'])==raw(['ls-files','--stage','-z'],env=env),'ALL index entries exactly original baseline')
c.need(raw(['diff','--cached','--raw','-z',BASE]).hex()==original['cached_diff_raw'],'original staged state relative to BASE')
c.need(raw(['ls-files','--others','--exclude-standard','-z']).hex()==original['untracked'],'untracked state')
for p,h in original['protected_files'].items():c.need(c.sha(p)==h,'user/protected file '+p)
c.need(c.sha(ridx)==original['diagnostic_index'],'diagnostic index')
extra=set()
for p in D.rglob('output/process.json'):
 x=json.loads(p.read_text());extra.update(x[k][v]for k in ['runner','child']for v in ['pgid','sid'])
host=c.host(extra);saved=D/'rollback-before/head-completion.index';shutil.copyfile(idx,saved);ih=c.sha(idx)
put('rollback-head-before.json',dict(accepted=True,host=host,HEAD=CAND,master=BASE,already_baseline_source_files=len(expected),all_index_entries_equal_original=True,index_sha256=ih,index_before=str(saved),no_source_index_write_planned=True))
try:
 # Tree/index were already restored by failed switch; only finish HEAD attachment.
 subprocess.run(['/usr/bin/git','-C',str(M),'symbolic-ref','-m','Complete reviewed rollback of unpromoted candidate','HEAD','refs/heads/master'],check=True,timeout=60)
 refs(False);c.need(c.sha(idx)==ih and tree()==expected,'HEAD-only completion changed no index/source')
 for p,h in original['protected_files'].items():c.need(c.sha(p)==h,'protected file '+p)
 c.need(c.sha(ridx)==original['diagnostic_index'],'diagnostic index unchanged')
 c.need(raw(['diff','--cached','--raw','-z']).hex()==original['cached_diff_raw'] and raw(['ls-files','--others','--exclude-standard','-z']).hex()==original['untracked'],'staged/untracked unchanged')
 for p,v in read('production-commit.json')['blobs'].items():c.need(g(['rev-parse',CAND+':'+p])==v and raw(['show',CAND+':'+p])==(D/'rollback-before'/p).read_bytes(),'backup blobs')
 put('rollback-after.json',dict(accepted=True,local_master=BASE,remote_master=BASE,candidate_preserved=CAND,backup_ref=original['backup_ref'],no_production_push=True,protected_files_unchanged=True,unrelated_staged_and_untracked_unchanged=True,whole_source_files=len(expected),current_indexes={str(idx):c.sha(idx),str(ridx):c.sha(ridx)},source_before=original['source_before'],index_before=original['index_before'],initial_switch_failure_preserved=True,completion='Only HEAD symbolic-ref after proving source and entire index already equal baseline',host=c.host(extra)))
 print(json.dumps(dict(accepted=True,master=BASE,candidate_preserved=CAND,source_files=len(expected),HEAD_only_completion=True)))
except BaseException as error:
 put('rollback-head-failure.json',dict(accepted=False,error=repr(error),HEAD=g(['rev-parse','HEAD']),master=g(['rev-parse','master']),branch=g(['branch','--show-current']),index_sha256=c.sha(idx),instruction='STOP, preserve all states. Do not rerun or reset. Inspect whether HEAD completion succeeded before separate reviewed validation.'))
 raise
