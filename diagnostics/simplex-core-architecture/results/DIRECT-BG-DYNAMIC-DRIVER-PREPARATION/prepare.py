"""One-shot offline Task3 stage/runtime preparation; no Julia or old executable."""
from pathlib import Path
import json,hashlib,os,sys,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.parent/'DIRECT-BG-DYNAMIC-ADAPTER-PREPARATION';OLD=D.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';DR=D.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION';L=R/'.superpowers/sdd/2026-10-16-direct-bg-dynamic-upper';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def need(v,m):
 if not v:raise RuntimeError(m)
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
helpers={}
for n,src in [('guard.py',OLD/'guard.py'),('supervisor.py',OLD/'supervisor.py'),('recorder.jl',DR/'recorder.jl')]:
 with (D/n).open('xb') as f:f.write(src.read_bytes())
 helpers[n]=dict(source=str(src),sha256=sha(src),byte_identical=True)
save(D/'reused-helpers.json',helpers)
sys.path.insert(0,str(D));import guard
stages={}
for mode,m in [('red',rd(OLD/'stages.json')['cost']),('green',rd(P/'overlay-reviewed.json'))]:
 src=Path(m['path']);baseline=m['sha256'];out=L/'task3-driver-stages'/mode
 need(len(baseline)==(75 if mode=='red' else 81),'Source count')
 need(set(baseline)=={str(p.relative_to(src)) for p in src.rglob('*') if p.is_file()},'Source membership')
 need(not src.is_symlink() and not any(p.is_symlink() for p in src.rglob('*')),'Source symlink')
 need(all(sha(src/n)==h for n,h in baseline.items()),'Frozen source drift')
 need(not out.exists(),'Existing stage');out.mkdir(parents=True)
 for n in baseline:
  p=out/n;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write((src/n).read_bytes())
 for n in ['Manifest.toml','LocalPreferences.toml']:need((out/n).read_bytes()==(W/n).read_bytes(),'Accepted stage environment drift '+n)
 stages[mode]=dict(path=str(out),master='26e2291745999f485a74f643298ca997d65c7205',sha256={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},source=str(src),baseline_sha256=baseline)
save(D/'stages.json',stages)
keys=['HOME','PATH','JULIA_LOAD_PATH','JULIA_PROJECT','JULIA_DEPOT_PATH','JULIA_CPU_TARGET','JULIA_BINDIR','LD_LIBRARY_PATH','LD_PRELOAD']
save(D/'environment.json',{k:os.environ.get(k) for k in keys})
prior=rd(OLD/'runtime-inputs-complete.json');paths=sorted(set(prior['inventory'])|{sys.executable,str(Path(sys.executable).resolve())})
current=guard.inventory(paths,[]);need(all(current[n]==v for n,v in prior['inventory'].items()),'Runtime drift from accepted source; stop for review')
save(D/'runtime-inputs-complete.json',dict(scope='Fresh readtime runtime/wrapper/library/source pins; not launch/cache/loader proof',inventory=current,provenance=str(OLD/'runtime-inputs-complete.json')))
loaded=rd(DR/'loaded-paths.json');loaded.pop('JSimplex',None)
need(all(str(Path(p).resolve())==p and p in current for p in loaded.values()),'Loaded input membership')
save(D/'loaded-paths.json',loaded)
baseline={}
for label,root in [('diagnostic',R),('production',W)]:
 names=subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines()
 baseline[label]={n:sha(root/n) for n in names}
save(D/'baseline.json',baseline)
save(D/'preparation-source.json',dict(script_sha256=sha(__file__),stage_counts={k:len(v['sha256']) for k,v in stages.items()},runtime_files=len(current),julia_executed=False))
print('Prepared RED75/GREEN81 ordinary stages;',len(current),'fresh runtime files; no Julia')
