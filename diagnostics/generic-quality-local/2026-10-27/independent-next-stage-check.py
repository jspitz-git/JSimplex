"""New read-only review checker; invoke only after prior stage acceptance and Julia exit.
Modes: commit (before local integration), master-admission (after local fast-forward).
Never launches Julia or mutates a Git object, index, ref, or production source.
"""
from pathlib import Path
import json,hashlib,subprocess,os,sys,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27')
M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];S=D/'GREEN';BASE='ca64312f7f74b1d7bec047718399f229674b3e1d'
NAMES=['src/primal_updates.jl','src/simplex_numerics.jl','test/generic_quality_local_tests.jl','test/runtests.jl']
ENV=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*a,root=M,env=None):return subprocess.check_output(['git','-C',str(root),*a],env=env or ENV)
def g(*a,root=M):return git(*a,root=root).decode().strip()
def review(p):
 r=read(p);need(r['accepted'] is True and r['findings']==[],'required acceptance '+str(p))
 for n,h in r['bindings'].items():need(sha(n)==h,'required binding '+n)
 return r
def environment(q):
 overrides=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
 need(all(not os.environ.get(k) for k in overrides),'environment override')
 found={k:os.environ[k] for k in overrides+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}
 need(found==read(q/'environment.json')['inherited'],'inherited environment')
def protect(q):
 p=read(q/'protected-before.json')
 for block in p.values():
  for n,h in block.items():need(sha(n)==h,'protected file/index '+n)
 return p
def fresh_host(seed_path):
 seed=read(seed_path);groups=set(seed['groups']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot drift')
 allowance=read(D/'host-identity-allowance.json');need(sha(D/'host-identity-allowance.json')=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed full-identity allowance')
 need(sha(allowance['historical_record'])==allowance['historical_sha256'] and read(allowance['historical_record'])['child']==allowance['historical_child'],'archived historical identity')
 processes=[];collisions=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   st=(p/'stat').read_text().rsplit(')',1)[1].split();args=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();a=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
   if a['pgid'] in groups or a['sid'] in groups:need(a in allowance['identities'],'historical group/session or changed occupant');collisions.append(a)
   need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+args[:1]),'Julia active; review forbidden');processes.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory')
 return dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,no_Julia=True,historical_numerical_identities_absent=True,verified_unrelated_collisions=collisions,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
def tree(ref):
 out={}
 for entry in git('ls-tree','-rz',ref).split(b'\0'):
  if entry:
   left,name=entry.split(b'\t',1);out[name.decode()]=tuple(left.decode().split())
 return out
def stage_identity():
 inv=read(D/'source-inverse.json');need(inv['accepted'] and inv['names']==NAMES,'stage manifest')
 actual={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()};need(actual==inv['whole_stage'],'whole stage')
 base=read(D/'baseline-tree.json');need(sorted(n for n in base.keys()|actual.keys() if base.get(n)!=actual.get(n))==NAMES,'exact four changes')
 for n,h in base.items():need(sha(D/'baseline'/n)==h,'frozen baseline '+n)
 return inv,base
def actual_commit(co):
 target=co['commit'];need(co['parent']==BASE and co['names']==NAMES,'commit contract')
 need(g('rev-list','--parents','-n','1',target).split()==[target,BASE] and g('rev-parse',target+'^{tree}')==co['tree'],'actual parent/tree')
 need(g('rev-parse',co['branch'])==target and co['branch']=='refs/heads/codex/generic-quality-local','dedicated branch')
 old,new=tree(BASE),tree(target);need(sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))==NAMES,'actual full tree difference')
 selected={n:v for n,v in new.items() if n.startswith(('src/','test/'))};need(set(selected)=={str(p.relative_to(S)) for folder in ['src','test'] for p in (S/folder).rglob('*') if p.is_file()},'complete committed/staged membership')
 committed={}
 proc=subprocess.Popen(['git','-C',str(M),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=ENV)
 try:
  for n,(mode,kind,oid) in selected.items():
   need(mode=='100644' and kind=='blob','ordinary source/test blob');proc.stdin.write((oid+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().split();need(header[:2]==[oid,'blob'],'blob header');data=proc.stdout.read(int(header[2]));need(proc.stdout.read(1)==b'\n','blob terminator');h=hashlib.sha256(data).hexdigest();need(h==sha(S/n),'actual committed source equals tested stage '+n);committed[n]=h
 finally:
  proc.stdin.close();need(proc.wait()==0,'cat-file completion')
 inv=read(D/'source-inverse.json');staged=read(D/'staged-tree.json');need(staged['base']==BASE and staged['names']==NAMES and staged['tree']==co['tree'],'private staged tree')
 for n in NAMES:need(new[n][2]==co['blobs'][n]==staged['blobs'][n] and committed[n]==staged['sha256'][n]==inv['candidate_sha256'][n],'actual changed blob '+n)
 changes=read(D/'changes.json')
 for n in NAMES:
  if n.startswith('src/'):
   s=git('show',target+':'+n).decode()
   for key in ['C','B','A']:
    x=changes[key]
    if n=='src/'+x['file']:need(s.count(x['new'])==1,'one inverse '+key);s=s.replace(x['new'],x['old'])
   need(s.encode()==git('show',BASE+':'+n)==(D/'baseline'/n).read_bytes(),'whole actual source inverse')
 need(git('show',target+':test/runtests.jl')==git('show',BASE+':test/runtests.jl')+b'\ninclude("generic_quality_local_tests.jl")\n','ordinary include only')
 subprocess.run(['git','-C',str(M),'diff-tree','--check',BASE,target],env=ENV,check=True)
 return committed

def commit_review():
 need(not (D/'commit-review.json').exists(),'new commit review only')
 host=fresh_host(D/'GREEN-run/audit-host.json')
 green=review(D/'GREEN-run/result-review.json');review(D/'production-review.json');review(D/'publication-preparation-reviewed.json');inv,baseline=stage_identity();environment(D/'GREEN-run');protect(D)
 ga=read(D/'GREEN-run/audit.json');need(ga['accepted'] and ga['expected_failures']==0 and ga['passed']==ga['total'],'allpass GREEN')
 co=read(D/'production-commit.json');committed=actual_commit(co)
 for ref in ['HEAD','master','origin/master']:need(g('rev-parse',ref)==BASE,'pre-ff base ref')
 need(g('branch','--show-current')=='master' and not g('diff','--name-only','HEAD','--','src','test','Project.toml'),'pre-ff source state')
 for n,h in baseline.items():need(sha(M/n)==h,'actual M baseline '+n)
 need(g('rev-parse','HEAD',root=R)==read(D/'GREEN-run/host-before.json')['diagnostic_head'],'diagnostic ref')
 put(D/'independent-commit-host.json',host)
 report=f'''Verdict: actual commit {co['commit']} ACCEPTED for local ff-only integration; no unresolved findings. The complete actual Git tree differs from its sole parent {BASE} in exactly four reviewed paths. Every one of the {len(committed)} committed source/test blobs was read and compared with the entire accepted GREEN tree, including ordinary file modes and complete membership. Private staged tree/blob/hash evidence matches actual Git objects. Inverting the two committed source files reproduces the complete parent files. Existing tests and all numerical thresholds are unchanged; the new test and ordinary include are exact. Git diff-tree --check passes.

The exact production numerical/work/memory review applies: A reuses only private product magnitude, B retains five finalizer passes and generic/scalar-roundoff and hardware-wide safeguards, C constructs its call-private unit only after recompute/guards/first finite old. No unnecessary scans, solves, copies, conversions or retained roots were added; independent measurements support scoped work/allocation reductions with documented timing regressions and coverage limits. No old failure exception is transferred. GREEN is independently accepted with {ga['passed']} ordinary passes, zero failures and all35files. All required current review bindings, environment, user files and real M/R indexes remain protected; M remains at the parent before ff. Fresh historical process identity checks found no Julia. Any exact unrelated numeric-ID collision is recorded separately, not mistaken for an old numerical process.

This reviewer ran no Julia and changed no source/index/ref. Actual-master admission and fresh same35file all-pass qualification, followed by its independent result review and all pre-push preservation checks, remain mandatory before normal nonforce publication.
'''
 with (D/'COMMIT-REVIEW.md').open('x') as f:f.write(report)
 files=[D/n for n in ['production-commit.json','staged-tree.json','commit-host.json','production-review.json','PRODUCTION-REVIEW.md','production-review-count-clarification.json','GREEN-run/result-review.json','GREEN-run/RESULT-REVIEW.md','GREEN-run/audit.json','source-inverse.json','changes.json','publication-preparation-reviewed.json','commit-integrate-publish.py','publication_checks.py','common_next.py','host-identity-allowance.json','COMMIT-REVIEW.md','independent-commit-host.json','independent-next-stage-check.py']]
 put(D/'commit-review.json',dict(accepted=True,findings=[],commit=co['commit'],parent=BASE,tree=co['tree'],names=NAMES,committed_source_test_files=len(committed),actual_commit_sha256=committed,review=str(D/'COMMIT-REVIEW.md'),bindings={str(p):sha(p) for p in files}))
 print(json.dumps(dict(accepted=True,mode='commit',commit=co['commit'],source_test_files=len(committed),review_sha256=sha(D/'commit-review.json'))))

def master_admission():
 q=D/'MASTER-run';need(not (q/'admission.json').exists() and not (q/'output').exists() and not (q/'reservation.json').exists(),'exclusive unlaunched master')
 host=fresh_host(q/'host-seed.json');need(read(q/'host-seed.json')==read(D/'GREEN-run/audit-host.json'),'continuous history')
 cr=review(D/'commit-review.json');co=read(D/'production-commit.json');target=co['commit'];need(cr['commit']==target and cr['parent']==BASE,'reviewed target');inv,baseline=stage_identity();environment(q);protected=protect(q)
 for ref in ['HEAD','master',co['branch']]:need(g('rev-parse',ref)==target,'actual target refs')
 need(g('rev-parse','origin/master')==BASE and g('branch','--show-current')=='master','unpublished tracking')
 need(g('rev-parse',target+'^{tree}')==cr['tree'] and g('rev-list','--parents','-n','1',target).split()==[target,BASE],'immutable reviewed tree/parent')
 for directory in ['src','test']:
  paths={str(p.relative_to(M)) for p in (M/directory).rglob('*') if p.is_file()};need(paths=={n for n in cr['actual_commit_sha256'] if n.startswith(directory+'/')},'complete actual M membership')
  for n in paths:need(sha(M/n)==sha(S/n)==cr['actual_commit_sha256'][n],'actual committed/tested bytes '+n)
 need(not g('diff','--name-only','HEAD','--','src','test','Project.toml'),'actual source clean')
 hist=read(D/'integration-historical-path-map.json');oldprot=read(D/'protected-before.json');idx=g('rev-parse','--path-format=absolute','--git-path','index');need(hist['master_before']==BASE and hist['older_maps_preserved'],'original source mapping')
 need(set(hist['source_before'])=={str(M/n) for n in NAMES if n in baseline},'exact original source map keys')
 for n,v in hist['source_before'].items():rel=str(Path(n).relative_to(M));need(v['before']==str(D/'baseline'/rel) and v['sha256']==baseline[rel]==sha(v['before']),'source beforeimage')
 need(set(hist['master_index_before'])=={idx},'original index path');before=hist['master_index_before'][idx];need(before['before']==str(D/'before-master/master.index') and before['sha256']==oldprot['indexes'][idx]==sha(before['before']),'original index bytes')
 original=git('ls-files','--stage','-z',env=dict(ENV,GIT_INDEX_FILE=before['before']));current=git('ls-files','--stage','-z');ib=read(D/'integration-before.json')
 need(original.decode().split('\0')==ib['entries'],'preserved original entries')
 def unrelated(data):return [x for x in data.decode().split('\0') if x and x.split('\t',1)[1] not in NAMES]
 need(unrelated(original)==unrelated(current) and git('diff','--cached','--raw','-z').decode()==ib['staged'],'unrelated/staged indexes unchanged')
 need(protected['files']==oldprot['files'] and set(protected['indexes'])==set(oldprot['indexes']),'protected membership')
 for n,h in protected['indexes'].items():need(n==idx or h==oldprot['indexes'][n],'unrelated diagnostic index')
 pins=read(q/'pins.json')
 for n,v in pins['inventory'].items():p=Path(n);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'latest master pin '+n)
 for tr in pins['trees']:need({str(p) for p in Path(tr).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tr)},'master pin tree membership')
 need(str(D/'commit-review.json') in pins['inventory'],'actual commit review pinned')
 c=read(q/'contract.json');gc=read(D/'GREEN-run/contract.json');ga=read(D/'GREEN-run/audit.json');gr=read(D/'GREEN-run/result-review.json');need(gr['accepted'] and gr['findings']==[] and ga['accepted'] and ga['expected_failures']==0,'accepted GREEN')
 need(c['files']==gc['files'] and len(c['files'])==35 and len(set(c['files']))==35 and c['expected_total']==ga['total']==ga['passed'],'exact35/frozen total')
 need(c['arm']=='MASTER' and c['attempts']==1 and c['source_root']==str(M) and c['expected_exit']==c['expected_failures']==0 and c['expected_failure_locations']==[] and c['shared_limit_seconds']==2400 and c['guard_limit_seconds']==2392,'master contract')
 need(c['command']==[a.replace(str(D/'GREEN-run'),str(q)).replace('--project='+str(S),'--project='+str(M)) for a in gc['command']],'exact actual M command')
 need((q/'tests.jl').read_text()==(D/'GREEN-run/tests.jl').read_text().replace(str(S),str(M)).replace('Local quality GREEN','Local quality MASTER').replace('COMPLETED GREEN','COMPLETED MASTER'),'ordinary driver only source/arm changes')
 for name in ['launch.py','audit.py']:need((q/name).read_bytes()==(D/'GREEN-run'/name).read_bytes(),'execution guards unchanged')
 for name in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((q/'guard'/name).read_bytes()==(D/'GREEN-run/guard'/name).read_bytes(),'runtime guard unchanged')
 expected=(D/'GREEN-run/common.py').read_text().replace("TARGET='"+BASE+"'","TARGET='"+target+"'").replace("git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET","git(['rev-parse','HEAD'])==git(['rev-parse','master'])==TARGET and git(['rev-parse','origin/master'])=='"+BASE+"'")
 need((q/'common.py').read_text()==expected,'only target-ref common changes');need(g('rev-parse','HEAD',root=R)==read(q/'host-before.json')['diagnostic_head'],'diagnostic ref')
 put(q/'independent-admission-host.json',host)
 report=f'''Verdict: actual MASTER ADMITTED for one prospective2400-second attempt,2392-second guard cutoff, no unresolved findings. Actual M HEAD/master is reviewed commit{target}; origin/master remains parent{BASE}. All{len(cr['actual_commit_sha256'])} actual source/test files and memberships match the immutable reviewed commit and accepted GREEN stage. Original source/index beforeimages, unrelated staged/index entries, user files and diagnostic index remain preserved. Every latest inventory hash/resolved path and complete tree has been checked, including the actual-commit review binding.

The exact same35 ordinary test files must yield {ga['total']} passes, zero failures/errors/broken/skips and exit0. All original numerical safeguards, generic/scalar-roundoff and hardware fallback semantics, allocation thresholds and ownership/precision checks remain unchanged. No old exception is transferred. The driver asserts actual M source/project identity and one Julia/BLAS thread. Launch/audit/guard/entry/supervisor are byte-identical to GREEN; common changes only target refs. Shared2400/inner2392 deadlines cover preparation/execution/cleanup/final checks with Julia/BLAS1/GC1,0,heap2GiB/AS8GiB,RAMavailable6GiB/swap1GiB, entry permit/parent-death and owned cleanup.

Fresh evidence examines every historical group AND session with boot/startticks/command identity and no live Julia. The sole fixedSHA unrelated WSL full-tuple allowance remains exact; any observed permitted collision is separately recorded, never described as absence of its numeric ID. Launcher must refresh pins/refs/environment/protected files/process checks and reject drift or an existing attempt. This reviewer ran no Julia and changed no source/index/ref. This is prospective admission only; independent actual-master all-pass result review and pre-push tested-tree/history checks remain required before normal nonforce publication.
'''
 with (q/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
 files=[Path(n) for n in pins['inventory']]+[p for p in q.rglob('*') if p.is_file()]+[D/n for n in ['commit-review.json','COMMIT-REVIEW.md','GREEN-run/result-review.json','GREEN-run/RESULT-REVIEW.md','integration-before.json','integration-after.json','integration-historical-path-map.json','source-inverse.json','host-identity-allowance.json','HOST-IDENTITY.md','independent-next-stage-check.py']]
 put(q/'admission.json',dict(accepted=True,findings=[],attempts=1,expected_failures=0,expected_total=ga['total'],shared_limit_seconds=2400,guard_limit_seconds=2392,inventory_entries=len(pins['inventory']),review=str(q/'ADMISSION-REVIEW.md'),bindings={str(p):sha(p) for p in files}))
 print(json.dumps(dict(accepted=True,mode='master-admission',target=target,total=ga['total'],pins=len(pins['inventory']),review_sha256=sha(q/'admission.json'))))

if __name__=='__main__':
 need(len(sys.argv)==2 and sys.argv[1] in ['commit','master-admission'],'explicit review mode')
 if sys.argv[1]=='commit':commit_review()
 else:master_admission()
