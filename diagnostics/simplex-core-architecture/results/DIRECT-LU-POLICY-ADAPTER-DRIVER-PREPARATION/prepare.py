"""One-shot offline stage/runtime preparation; never invokes Julia or old scripts."""
from pathlib import Path
import json,hashlib,os,sys,shutil,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];A=D.parent/'DIRECT-LU-POLICY-ADAPTER-PREPARATION';OLD=D.parent/'NATIVE-PIVOT-MASTER-READINESS';L=R/'.superpowers/sdd/2026-10-16-direct-lu-policy-adapters';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
for n in ['guard.py','supervisor.py','recorder.jl']:(D/n).write_bytes((OLD/n).read_bytes())
sys.path.insert(0,str(D));import guard
save(D/'reused-helpers.json',{n:dict(source=str(OLD/n),sha256=sha(D/n),byte_identical=True) for n in ['guard.py','supervisor.py','recorder.jl']})
stages={}
for mode,prior in [('red','red'),('green','candidate')]:
 src=L/(prior+'-overlay');m=json.loads((A/(prior+'-overlay.json')).read_text());out=L/'driver-stages'/mode
 need(not out.exists(),'Stage exists');need(set(m['overlay_sha256'])=={str(p.relative_to(src)) for p in src.rglob('*') if p.is_file() and p.name!='overlay.json'},'Source membership')
 need(all(sha(src/n)==h for n,h in m['overlay_sha256'].items()),'Accepted source drift')
 out.mkdir(parents=True)
 for n in m['overlay_sha256']:
  p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((src/n).read_bytes())
 for n in ['Manifest.toml','LocalPreferences.toml']:(out/n).write_bytes((W/n).read_bytes())
 stages[mode]=dict(path=str(out),master=m['master'],sha256={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},source_manifest=str(A/(prior+'-overlay.json')))
save(D/'stages.json',stages)
envkeys=['HOME','PATH','JULIA_LOAD_PATH','JULIA_PROJECT','JULIA_DEPOT_PATH','JULIA_CPU_TARGET','JULIA_BINDIR','LD_LIBRARY_PATH','LD_PRELOAD']
save(D/'environment.json',{k:os.environ.get(k) for k in envkeys})
prior=json.loads((OLD/'runtime-inputs.json').read_text());paths=sorted(set(prior['inventory'])|{sys.executable,str(Path(sys.executable).resolve())})
current=guard.inventory(paths,[])
need(all(current[n]==h for n,h in prior['inventory'].items()),'Runtime drift from accepted master; stop for review')
save(D/'runtime-inputs.json',dict(scope='Fresh readtime runtime/wrapper/library pins, not launch admission or cache closure',inventory=current,provenance=str(OLD/'runtime-inputs.json')))
loaded=json.loads((OLD/'loaded-paths.json').read_text());loaded.pop('JSimplex')
for module in ['Test','PrecompileTools']:
 candidates=[p for p in paths if p.endswith('/'+module+'.jl') and '/src/' in p]
 need(len(candidates)==1,'Module path '+module);loaded[module]=candidates[0]
save(D/'loaded-paths.json',loaded)
save(D/'preparation-source.json',dict(script_sha256=sha(__file__),stage_files={k:len(v['sha256']) for k,v in stages.items()},runtime_files=len(current),julia_executed=False))
print('Prepared red/green ordinary stages and fresh runtime pins; Julia not executed',len(current))
