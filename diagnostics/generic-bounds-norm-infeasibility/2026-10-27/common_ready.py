from pathlib import Path
import json,hashlib,subprocess,os,datetime
os.environ['GIT_OPTIONAL_LOCKS']='0'
D=Path(__file__).resolve().parent;M=Path('/home/jspitz/JSimplex.jl');R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
TARGET='9d29b1f0aa21932217b03ca7b35dd91281baaae6'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(n):return json.loads((D/n).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def git(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a]).decode().strip()
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
def environment():
 found={k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}
 need(all(not os.environ.get(k) for k in OVERRIDES),'unreviewed environment override');return found
def unchanged():
 c=read('contract-ready.json');need(git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET,'master refs')
 need(git(['rev-parse','HEAD'],R)==read('host-before.json')['diagnostic_head'],'diagnostic ref')
 need(not git(['diff','--name-only','HEAD','--','src','test','Project.toml']),'production drift')
 need(environment()==read('environment.json')['inherited'],'inherited environment changed')
 pins=read('pins-ready.json')
 for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin changed '+n)
 for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership '+tree)
 protected=read('protected-before.json')
 for n,v in {**protected['files'],**protected['indexes']}.items():need(sha(n)==v,'protected file/index changed '+n)
def host(extra=()):
 old=read('host-seed.json');groups=set(old['groups'])|set(extra);procs=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   st=(p/'stat').read_text().rsplit(')',1)[1].split();a=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3])
   if pgid in groups or sid in groups:
    allowance=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json')
    need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed unrelated identity evidence')
    permitted=json.loads(allowance.read_text())['identities']
    actual=dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    need(actual in permitted,'historical group/session or changed unrelated process')
   need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+a[:1]),'Julia active')
   procs.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a))
  except (FileNotFoundError,ProcessLookupError):pass
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==old['boot_id'],'reboot')
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory')
 return dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
