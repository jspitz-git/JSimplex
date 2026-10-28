from pathlib import Path
import sys,json,subprocess,shutil,os,hashlib
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'counter-gc-preparation'));import common as c
M=c.M;R=c.R;BASE='235eedf33901fe8c4cc06a3d8c3508ef2fcbb718';CAND=c.TARGET;OLD='90848b35ca1090522f472d4111d678642b9fef4a'
def raw(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],timeout=60)
def g(a,root=M):return raw(a,root).decode().strip()
def put(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def indexentries():return [r.decode() for r in raw(['ls-files','--stage','-z']).split(b'\0') if r and r.split(b'\t',1)[1].decode() not in names]
def tree(root):return {str(p.relative_to(root)):c.sha(p) for n in ['src','test'] for p in (root/n).rglob('*') if p.is_file()}
def refs():
 c.need(g(['remote','get-url','--push','--all','origin'])=='git@github.com:jspitz-git/JSimplex.git','endpoint')
 c.need(g(['rev-parse','refs/heads/codex/generic-epsilon-bound-auxiliary'])==CAND,'backup ref')
 c.need(g(['rev-list','--parents','-n','1',CAND]).split()==[CAND,BASE],'sole parent')
 c.need(g(['ls-remote','origin','refs/heads/master']).split()[0]==g(['rev-parse','origin/master'])==BASE,'remote master unchanged')
 c.need(g(['rev-parse','HEAD'],R)==g(['rev-parse','origin/codex/simplex-core-architecture'],R)==g(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0]==OLD,'diagnostic refs')
co=json.loads((D/'production-commit.json').read_text());names=co['names'];c.need(len(names)==4,'four owned paths')
c.need(json.loads((D/'gc-preparation-decision.json').read_text())['production_candidate_admitted'] is False,'negative decision')
c.need(json.loads((D/'rollback-review-final.json').read_text())['accepted'] is True,'review required')
c.need(json.loads((D/'rollback-review-final.json').read_text())['bindings'][str(Path(__file__).resolve())]==c.sha(__file__),'review binds script')
c.unchanged();refs();c.need(g(['branch','--show-current'])=='master','branch')
c.need(tree(M)==tree(D/'GREEN'),'exact tested candidate source tree')
c.need(not raw(['diff','--cached','--raw','-z','--',*names]),'owned targets staged clean')
extra=set()
for p in D.rglob('output/process.json'):
 x=json.loads(p.read_text());extra.update(x[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
host=c.host(extra)
B=D/'rollback-before';B.mkdir(exist_ok=False)
idx=Path(g(['rev-parse','--path-format=absolute','--git-path','index']));shutil.copyfile(idx,B/'master.index')
images={}
for n in names:
 p=M/n;q=B/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);images[str(p)]=dict(before=str(q),sha256=c.sha(p),mode=p.stat().st_mode,resolved=str(p.resolve(strict=True)))
files=c.read('protected-before.json')['files'];before=dict(accepted=True,master=CAND,base=BASE,backup_ref='refs/heads/codex/generic-epsilon-bound-auxiliary',backup_commit=CAND,host=host,source_before=images,index_before={str(idx):dict(before=str(B/'master.index'),sha256=c.sha(idx))},unrelated_index_entries=indexentries(),cached_diff_raw=raw(['diff','--cached','--raw','-z']).hex(),untracked=raw(['ls-files','--others','--exclude-standard','-z']).hex(),protected_files=files,diagnostic_index=c.read('protected-before.json')['indexes'][str(Path(g(['rev-parse','--path-format=absolute','--git-path','index'],R)))])
put('rollback-before.json',before)
# Reversible rollback of this agent's unpublished fast-forward only. No reset-hard.
def state():
 return dict(HEAD=g(['rev-parse','HEAD']),master=g(['rev-parse','master']),branch=g(['branch','--show-current']),backup=g(['rev-parse',before['backup_ref']]),index_sha256=c.sha(idx),source_tree=tree(M))
commands=[['-c','core.hooksPath=/dev/null','switch','--detach',CAND],['update-ref','refs/heads/master',BASE,CAND],['-c','core.hooksPath=/dev/null','switch','--no-guess','master']]
try:
 for i,command in enumerate(commands):
  put('rollback-step-'+str(i)+'-before.json',dict(command=command,state=state()))
  subprocess.run(['/usr/bin/git','-C',str(M),*command],check=True,timeout=120)
  put('rollback-step-'+str(i)+'-after.json',dict(command=command,state=state()))
except BaseException as error:
 # Never rerun blindly or overwrite user files. Candidate ref and both index/source
 # beforeimages remain intact; no automatic broad reset/recovery is attempted.
 try:observed=state()
 except BaseException as survey_error:observed=dict(survey_error=repr(survey_error))
 put('rollback-failure.json',dict(accepted=False,error=repr(error),last_step=i,observed=observed,candidate_backup=CAND,original_master=BASE,recovery='STOP. Do not rerun this exclusive transaction. Review the recorded step states, protected file/index hashes and a fresh host survey. If master=BASE and HEAD=CAND detached, all candidate contents remain on the backup ref and source/index beforeimages; a separately checked switch to master can finish the rollback. If the branch switch already succeeded, verify BASE/source/user state and finish validation only. Never use reset-hard, clean, force-push, or overwrite unrelated changes.'))
 raise
c.need(g(['branch','--show-current'])=='master' and g(['rev-parse','HEAD'])==g(['rev-parse','master'])==BASE,'restored local master');refs()
base=json.loads((D/'baseline-tree.json').read_text());expected={n:h for n,h in base.items() if n.startswith(('src/','test/'))};c.need(tree(M)==expected,'whole baseline tree restored')
for n,h in files.items():c.need(c.sha(n)==h,'protected file '+n)
c.need(indexentries()==before['unrelated_index_entries'] and raw(['diff','--cached','--raw','-z']).hex()==before['cached_diff_raw'],'unrelated index and staged state')
c.need(raw(['ls-files','--others','--exclude-standard','-z']).hex()==before['untracked'],'untracked membership')
ridx=Path(g(['rev-parse','--path-format=absolute','--git-path','index'],R));c.need(c.sha(ridx)==before['diagnostic_index'],'diagnostic index')
for n,b in co['blobs'].items():c.need(g(['rev-parse',CAND+':'+n])==b and raw(['show',CAND+':'+n])==(B/n).read_bytes(),'backup source blob '+n)
c.need(not g(['diff','--name-only','HEAD','--','src','test','Project.toml']),'baseline source clean')
put('rollback-after.json',dict(accepted=True,local_master=BASE,remote_master=BASE,candidate_preserved=CAND,backup_ref=before['backup_ref'],no_production_push=True,protected_files_unchanged=True,unrelated_staged_and_untracked_unchanged=True,whole_source_files=len(expected),current_indexes={str(idx):c.sha(idx),str(ridx):c.sha(ridx)},source_before=images,index_before=before['index_before'],host=c.host(extra)))
print(json.dumps(dict(accepted=True,master=BASE,candidate_preserved=CAND,source_files=len(expected))))
