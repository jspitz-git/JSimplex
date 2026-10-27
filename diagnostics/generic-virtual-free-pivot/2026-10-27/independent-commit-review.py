from pathlib import Path
import json,hashlib,subprocess,os,datetime,re
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];base='1a6b9d81e89b44c5c75b95b6c92e0916c2d19730';target='c01900c2dff3de465846ae44333903889c867626'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def raw(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def git(a,root=M):return raw(a,root).decode().strip()
def review(n):
 r=read(D/n);need(r['accepted'] is True and not r.get('findings',[]),'review '+n)
 for p,h in r['bindings'].items():need(sha(p)==h,'review binding '+p)
for n in ['production-review.json','publication-preparation-reviewed.json','preparation-review.json','GREEN-run/admission.json','GREEN-run/result-review.json']:review(n)
co=read(D/'production-commit.json');inv=read(D/'source-inverse.json');st=read(D/'staged-tree.json');names=inv['names']
need(co['commit']==target and co['parent']==base and co['names']==st['names']==names and len(names)==7,'commit metadata')
need(git(['rev-list','--parents','-n','1',target]).split()==[target,base],'single original parent')
need(git(['rev-parse',target+'^{tree}'])==co['tree']==st['tree'],'actual tree')
need(git(['rev-parse',co['branch']])==target,'candidate branch')
need(git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==base and git(['branch','--show-current'])=='master','master original')
def entries(ref):
 out={}
 for row in raw(['ls-tree','-rz',ref]).split(b'\0'):
  if row:
   a,n=row.split(b'\t');out[n.decode()]=a.decode()
 return out
old=entries(base);new=entries(target);changed=sorted(n for n in set(old)|set(new) if old.get(n)!=new.get(n));need(changed==names,'exact actual changed tree entries')
need(git(['diff-tree','--no-commit-id','--name-only','-r',base,target]).splitlines()==names,'actual diff paths')
need(raw(['diff-tree','--check',base,target])==b'','actual whitespace')
for n in names:
 data=raw(['show',target+':'+n]);need(data==(D/'GREEN'/n).read_bytes(),'actual blob bytes '+n);need(hashlib.sha256(data).hexdigest()==inv['candidate_sha256'][n]==st['sha256'][n],'actual candidate SHA '+n);need(new[n]=='100644 blob '+co['blobs'][n] and co['blobs'][n]==st['blobs'][n],'actual blob identity/mode '+n)
need({str(p.relative_to(D/'GREEN')):sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()}==inv['whole_stage'],'whole reviewed stage unchanged')
baseline=read(D/'baseline-tree.json')
for tree in ['src','test']:
 need({str(p.relative_to(M)):sha(p) for p in (M/tree).rglob('*') if p.is_file()}=={n:h for n,h in baseline.items() if n.startswith(tree+'/')},'actual master still baseline '+tree)
 for n in new:
  if n.startswith(tree+'/'):need(raw(['show',target+':'+n])==(D/'GREEN'/n).read_bytes(),'full committed tested '+n)
need(not git(['status','--porcelain=v1','--untracked-files=all','--',*names]),'clean target files')
protected=read(D/'protected-before.json')
for p,h in {**protected['files'],**protected['indexes']}.items():need(sha(p)==h,'real protected file/index '+p)
need(git(['rev-parse','HEAD'],R)==read(D/'host-before.json')['diagnostic_head'],'diagnostic ref unchanged')
a=read(D/'GREEN-run/audit.json');need(a['accepted'] is True and a['passed']==a['total']==218625 and a['expected_failures']==0,'GREEN total')
log=(D/'GREEN-run/output/run.log').read_text();need(re.search(r'^Virtual free pivot GREEN\s*\|\s*218625\s+218625\s',log,re.M) is not None,'actual GREEN summary');need(len(re.findall(r'^INCLUDING ',log,re.M))==36 and log.count('VFP_COMPLETED GREEN')==1,'actual full driver completion')
seed=read(D/'GREEN-run/result-review-host.json');groups=set(seed['groups']);need(len(groups)==605,'605 histories');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot')
allow=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','allowance');allowed=read(allow)['identities'];procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stt=(p/'stat').read_text().rsplit(')',1)[1].split();args=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();v=dict(pid=int(p.name),pgid=int(stt[2]),sid=int(stt[3]),start_ticks=int(stt[19]),command=args,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+args[:1]),'active Julia')
  if v['pgid'] in groups or v['sid'] in groups:need(v in allowed,'history identity')
  procs.append(v)
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'resources')
put(D/'commit-review-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report=f'''Independent actual production commit review — PASS.

Commit {target} has exactly one parent, authoritative base {base}, and actual tree {co['tree']}. Independently enumerating both entire Git trees finds exactly seven changed paths: five source files, the new ordinary test module and runtests inclusion. Every changed mode is100644; all seven actual committed blob identities and bytes match staged-tree.json, source-inverse.json and reviewed GREEN. Every unrelated tree entry is unchanged, and all committed src/test files equal the tested stage. Actual diff whitespace check passes.

Master, HEAD and origin/master remain at the original base; the candidate branch points at the reviewed commit. Actual master src/test membership and bytes still equal the original baseline. All originally protected user/config/environment files and both real master/diagnostic indexes retain original SHA256 values. Diagnostic HEAD remains unchanged. No Julia, old checker, commit or ref mutation was executed by this reviewer; only new offline Git/hash/proc checks ran.

Independent production, publication-preparation, finalization-preparation, GREEN admission and GREEN result reviews remain accepted with every binding verified. Actual ordinary GREEN log confirms218625passes/218625total,36whole-file includes and one completion marker; the accepted audit has zero expected failures. This remains the frozen expected total for actual-master verification. Fresh605historical groups AND sessions, full boot/start_ticks/command identities and the unchanged exact unrelated-identity allowance pass, with noJulia and the required memory/swap margin.

Numerical/work-memory findings remain unchanged because actual committed bytes exactly match the reviewed and measured source: no unnecessary new scan, solve, copy, conversion, repeated invariant check or retained numerical cache. A keeps full implicit terms/quality work, B keeps candidate/pool/callback work, and C keeps basis assembly and both complete certificates. Local scalar savings and O(1)cold method metadata are documented; C timing remains nonuniform and no end-to-end/native-dual speedup is inferred.

Accepted for the authorized ff-only local integration. This does not certify the later actual-master run or remote publication. Fresh actual-master admission, the same36files with frozen218625total under2400seconds, independent result acceptance and normal-push checks remain required. Full suite/x64 remain open.
'''
with (D/'COMMIT-REVIEW.md').open('x') as f:f.write(report)
files=['production-commit.json','staged-tree.json','source-inverse.json','production-review.json','publication-preparation-reviewed.json','preparation-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','GREEN-run/audit.json','GREEN-run/output/run.log','GREEN-run/output/process.json','protected-before.json','baseline-tree.json','commit-review-host.json','COMMIT-REVIEW.md','independent-commit-review.py'];bound={str(D/n):sha(D/n) for n in files}
for n in names:bound[str(D/'GREEN'/n)]=sha(D/'GREEN'/n)
put(D/'commit-review.json',dict(accepted=True,findings=[],bindings=bound,commit=target,parent=base,tree=co['tree'],names=names,all_actual_blobs_verified=True,all_unrelated_tree_entries_unchanged=True,real_indexes_unchanged=True,no_Julia_executed=True,actual_MASTER_expected_total=218625,unnecessary_new_work_or_retained_numeric_memory=False))
print(json.dumps(dict(accepted=True,commit=target,changed_paths=len(names),master_unchanged=True,indexes_unchanged=True,historical_groups=len(groups))))
