from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];S=D/'GREEN';BASE='ce5d4a74019e0dc2e656d08161641c498b159e7b';TARGET='bb765d008c6e8aab6187aa0ea49d49a4f8a03309';DIAG='c01e9376bdbcda7cb54ba55735cf053299b9af45';os.environ['GIT_OPTIONAL_LOCKS']='0'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,s):
 with Path(p).open('x') as f:f.write(s)
def put(p,v):save(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
def git(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a])
def g(a,root=M):return git(a,root).decode().strip()
def review(p):
 r=read(p);need(r['accepted'] is True and r['findings']==[],'review '+str(p))
 for n,h in r['bindings'].items():need(sha(n)==h,'binding '+n)
 return r
def tree(ref):
 out={}
 for entry in git(['ls-tree','-r','-z',ref]).split(b'\0'):
  if entry:
   meta,path=entry.split(b'\t',1);mode,kind,blob=meta.decode().split();out[path.decode()]=(mode,kind,blob)
 return out
script=D/'independent-commit-review.py';save(script,Path(__file__).read_text())
co=read(D/'production-commit.json');st=read(D/'staged-tree.json');inv=read(D/'source-inverse.json')
names=['src/dual_simplex.jl','src/factorization.jl','test/generic_sum_rational_growth_tests.jl','test/runtests.jl']
need(co['commit']==TARGET and co['parent']==st['base']==BASE and co['names']==st['names']==inv['names']==names,'exact selected metadata')
need(co['tree']==st['tree']==g(['rev-parse',TARGET+'^{tree}']),'actual committed tree')
need(co['branch']=='refs/heads/codex/generic-sum-rational-growth' and g(['rev-parse',co['branch']])==TARGET,'actual private branch')
need(g(['rev-list','--parents','-n','1',TARGET]).split()==[TARGET,BASE],'sole correct parent')
need(g(['diff-tree','--no-commit-id','--name-only','-r',BASE,TARGET]).splitlines()==names,'exact actual changed paths')
diff=subprocess.run(['/usr/bin/git','-C',str(M),'diff-tree','--check',BASE,TARGET],capture_output=True,text=True);need(diff.returncode==0 and not diff.stdout and not diff.stderr,'actual commit strict whitespace')
old,new=tree(BASE),tree(TARGET);need(set(new)==set(old)|{names[2]},'whole repository membership only one added test')
for name in set(old)-set(names):need(old[name]==new[name],'all unrelated tree modes/types/blobs '+name)
for name in names:
 data=(S/name).read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 need(new[name]==('100644','blob',blob) and blob==co['blobs'][name]==st['blobs'][name],'actual/staged/GREEN blob '+name)
 need(git(['show',TARGET+':'+name])==data,'actual committed bytes '+name)
 need(sha(S/name)==st['sha256'][name]==inv['candidate_sha256'][name],'actual candidate SHA '+name)
for sub in ['src','test']:
 actual={n for n in new if n.startswith(sub+'/')};stage={str(p.relative_to(S)) for p in (S/sub).rglob('*') if p.is_file()};need(actual==stage,'whole committed/tested membership '+sub)
 for n in actual:
  data=(S/n).read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();need(new[n]==('100644','blob',blob),'whole committed equals tested '+n)
need(set(inv['whole_stage'])=={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()},'actual stage whole membership')
for n,h in inv['whole_stage'].items():need(sha(S/n)==h,'reviewed stage '+n)
for n,h in read(D/'baseline-tree.json').items():need(sha(M/n)==sha(D/'baseline'/n)==h,'master baseline unchanged '+n)
for file in names[:2]:
 source=(S/file).read_text()
 for ch in reversed(read(D/'changes.json')):
  if ch['file']==file:need(source.count(ch['new'])==1,'exact inverse region');source=source.replace(ch['new'],ch['old'])
 need(source==(D/'baseline'/file).read_text(),'whole source inverse '+file)
green=review(D/'GREEN-run/result-review.json');need(green['passed']==green['total']==345121 and green['whole_files']==57 and green['expected_failures']==0,'accepted GREEN total/files')
for n in ['production-review.json','publication-preparation-reviewed.json','result-review.json']:review(D/n)
for root in [D,D/'GREEN-run']:
 protected=read(root/'protected-before.json')
 for n,h in {**protected['files'],**protected['indexes']}.items():need(sha(n)==h,'protected original bytes '+n)
need(g(['rev-parse','HEAD'])==g(['rev-parse','master'])==g(['rev-parse','origin/master'])==BASE and g(['branch','--show-current'])=='master','master/tracking remains original')
need(g(['rev-parse','HEAD'],R)==DIAG,'diagnostic remains original')
need(g(['ls-remote','origin','refs/heads/master']).split()[0]==BASE,'remote master remains original')
need(not g(['diff','--name-only','HEAD','--','src','test','Project.toml']),'no live production drift')
overrides=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in overrides),'no environment override')
need({k:os.environ[k] for k in overrides+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(D/'environment.json')['inherited'],'inherited environment exact')
seed=read(D/'GREEN-run/host-seed.json');groups=set(seed['groups'])
for path in D.rglob('output/process.json'):
 process=read(path)
 for role in ['runner','child']:
  for k in ['pgid','sid']:groups.add(process[role][k])
need(len(groups)==657,'all657 historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'same boot')
allow=D.parents[1]/'generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed unrelated identity evidence');permitted=read(allow)['identities'];procs=[];allowed=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  stat=(proc/'stat').read_text().rsplit(')',1)[1].split();command=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();ident=dict(pid=int(proc.name),pgid=int(stat[2]),sid=int(stat[3]),start_ticks=int(stat[19]),boot_id=boot,command=command)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+command[:1]),'live Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in permitted,'historical group/session occupied '+str(ident));allowed.append(ident)
  procs.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'resource headroom')
put(D/'independent-commit-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,allowed_seen=allowed,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],observer_pid=os.getpid(),observer_parent_pid=os.getppid(),observer_command=sys.argv,refs=dict(master=BASE,tracking=BASE,remote_master=BASE,diagnostic=DIAG,candidate=TARGET)))
report=f'''# Independent actual production commit review

Accepted actual commit `{TARGET}` for the planned fast-forward-only integration. Its sole parent is `{BASE}`, and actual tree `{co['tree']}` matches the private staged-tree record. Exactly four paths change: src/dual_simplex.jl, src/factorization.jl, test/generic_sum_rational_growth_tests.jl and test/runtests.jl. Every actual committed mode/type/blob and byte for those paths equals the accepted GREEN stage, source-inverse hashes and staged/commit metadata. Whole-repository membership adds only the new regression file; all unrelated tree entries are identical to the parent. The complete committed src/test membership and every blob match the tested stage. Actual commit whitespace checks pass, and both production source files reverse exactly to baseline.

The independently accepted GREEN result remains bound at345,121/345,121 passes in57 whole files. Production numerical/work/memory review and qualified cost evidence are unchanged. This commit adds no source change beyond those measured and reviewed A/B/C edits, so their work-frequency, scaling, ownership, exception and measurement limitations continue to apply; no additional benchmark or new performance claim is warranted.

Live master, origin/master and remote master remain at the original baseline. Master source/test/environment files and all protected user files/indexes remain byte-identical; the diagnostic ref also remains unchanged. The private codex/generic-sum-rational-growth branch points to the candidate. Fresh host checks cover all657 historical groups AND sessions with boot/start_ticks/command identity, no active Julia, existing exact unrelated identity allowance and sufficient resource headroom.

The review used new exclusive offline reviewer code and read-only Git/host checks only. No Julia, previous script execution/import, measurement rerun or Git mutation occurred. Fast-forward integration is accepted; actual-master execution still requires fresh concrete admission with the same57 files, frozen total345,121 and shared3000-second budget, followed by independent result review before normal publication. Full-suite/x64/native-retention and end-to-end performance remain unclaimed.
'''
md=D/'COMMIT-REVIEW.md';save(md,report)
paths=[script,md,D/'independent-commit-host.json']+[D/n for n in ['production-commit.json','staged-tree.json','source-inverse.json','baseline-tree.json','changes.json','production-review.json','publication-preparation-reviewed.json','GREEN-run/result-review.json','GREEN-run/audit.json','GREEN-run/pins.json','result-review.json','protected-before.json','environment.json','commit-integrate-publish.py']]+[S/n for n in names]
put(D/'commit-review.json',dict(accepted=True,findings=[],commit=TARGET,parent=BASE,tree=co['tree'],names=names,whole_tree_independently_verified=True,committed_source_equals_tested=True,real_indexes_unchanged=True,fast_forward_integration_authorized=True,push_authorized=False,required_actual_MASTER_total=345121,required_actual_MASTER_files=57,historical_groups_and_sessions=657,Julia_executed=False,Git_mutated=False,bindings={str(p):sha(p) for p in sorted(set(paths))}))
print(json.dumps(dict(accepted=True,commit=TARGET,sole_parent=BASE,exact_paths=4,whole_tree_verified=True,historical_groups_and_sessions=657,Julia_executed=False,Git_mutated=False)))
