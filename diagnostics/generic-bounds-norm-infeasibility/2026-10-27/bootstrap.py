from pathlib import Path
import os,json,hashlib,subprocess,shutil,datetime
M=Path('/home/jspitz/JSimplex.jl');R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');O=R/'diagnostics/generic-ratio-monitor/2026-10-27';D=R/'diagnostics/generic-bounds-norm-infeasibility/2026-10-27';BASE='9d29b1f0aa21932217b03ca7b35dd91281baaae6'
os.environ['GIT_OPTIONAL_LOCKS']='0'
def need(x,m):
 if not x:raise RuntimeError(m)
def git(*a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],text=True).strip()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
need(git('rev-parse','HEAD')==git('rev-parse','master')==git('rev-parse','origin/master')==BASE,'master refs');need(git('ls-remote','origin','refs/heads/master').split()[0]==BASE,'remote master');need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'source drift')
need(git('rev-parse','--git-dir',root=R)!=git('rev-parse','--git-common-dir',root=R) and not git('rev-parse','--show-superproject-working-tree',root=R),'existing linked isolation')
old=json.loads((O/'closure-host.json').read_text());groups=set(old['groups']);allow=json.loads((R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==old['boot_id'],'new boot needs new baseline');procs=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();args=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();a=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
  if a['pgid'] in groups or a['sid'] in groups:need(a in allow['identities'],'historic group/session or changed occupant');collisions.append(a)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+args[:1]),'Julia active');procs.append(a)
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
need(not D.exists(),'new case only');D.mkdir(parents=True)
def put(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
h=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,verified_unrelated_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],master=BASE,diagnostic_head=git('rev-parse','HEAD',root=R));put('host-before.json',h);put('host-seed.json',h)
for n in ['src','test']:shutil.copytree(M/n,D/'baseline'/n)
for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']:shutil.copyfile(M/n,D/'baseline'/n)
put('baseline-tree.json',{str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()})
oldprot=json.loads((O/'protected-before.json').read_text());put('protected-before.json',{k:{p:sha(p) for p in v} for k,v in oldprot.items()})
keys=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME'];need(all(not os.environ.get(k) for k in keys),'environment override');put('environment.json',dict(inherited={k:os.environ[k] for k in keys+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}))

(D/'common.py').write_text((O/'common.py').read_text().replace("TARGET='8ceff4f1f7d295dcc9e656295b5553e28e7cbe9b'","TARGET='"+BASE+"'"))
shutil.copyfile(__file__,D/'bootstrap.py')
print('freshhost',len(groups),'groups/sessions; baseline',len(json.loads((D/'baseline-tree.json').read_text())),'files; noJulia')
