from pathlib import Path
import json,hashlib,subprocess,os
Q=Path(__file__).resolve().parent;R=Q.parents[3];P=Q.parent/'NATIVE-PIVOT-PRODUCTION-INTEGRATION-PREPARATION';N=Q.parent/'NATIVE-PIVOT-INTEGRATION-180-PREPARATION'
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,o):
 with (Q/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
c=json.loads((Q/'production-commit.json').read_text());W=Path(c['worktree'])
for n in ['guard.py','supervisor.py']:
 with (Q/n).open('xb') as f:f.write((N/n).read_bytes())
for n in ['master-driver.jl','recorder.jl']:
 with (Q/n).open('xb') as f:f.write((P/n).read_bytes())
save('copied-sources.json',{str(Q/n):dict(source=str(src/n),sha256=sha(src/n)) for src,names in [(N,['guard.py','supervisor.py']),(P,['master-driver.jl','recorder.jl'])] for n in names})
for n in ['Manifest.toml','LocalPreferences.toml']:
 src=R/n;old=R/'.superpowers/native-pivot-integration-180/integration'/n
 need(sha(src)==sha(old),'Prior environment differs '+n)
 with (W/n).open('xb') as f:f.write(src.read_bytes())
save('environment-files.json',{str(W/n):dict(source=str(R/n),sha256=sha(R/n)) for n in ['Manifest.toml','LocalPreferences.toml']})
keys=['HOME','PATH','JULIA_LOAD_PATH','JULIA_PROJECT','JULIA_DEPOT_PATH','JULIA_CPU_TARGET','JULIA_BINDIR','LD_LIBRARY_PATH','LD_PRELOAD']
save('environment.json',{k:os.environ.get(k) for k in keys})
old=json.loads((N/'runs/integration/launch-pins.json').read_text());external={n:v for n,v in old['inventory'].items() if not n.startswith(str(R)+'/')}
for n,v in external.items():need(sha(Path(n))==v['sha256'] and str(Path(n).resolve())==v['resolved'],'Runtime drift '+n)
save('runtime-inputs.json',dict(provenance=str(N/'runs/integration/launch-pins.json'),scope='606 external runtime/library/wrapper paths reused and freshly hashed; no cache validity/import closure claim',inventory=external))
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=W).decode().split('\0')[:-1]
save('production-tree.json',dict(commit=c['commit'],sha256={n:sha(W/n) for n in tracked},git_blobs={n:subprocess.check_output(['git','rev-parse',c['commit']+':'+n],cwd=W,text=True).strip() for n in tracked}))
save('loaded-paths.json',dict(json.loads((N/'loaded-paths.json').read_text()),JSimplex=str(W/'src/JSimplex.jl')))
save('expected-tests.json',dict(groups=[['options_and_copy_intent',4946],['backend_owned_policy',35],['private_spare_copy_and_failure',1568],['precision_and_factory_dispatch',245],['Native pivot policy public integration',48],['Native pivot policy private recovery',114]],public_children=[[m+' / '+p,6] for m in ['pfi','forrest_tomlin','suhl_suhl','bartels_golub'] for p in ['default','threshold_one']],assertions=6956))
print('Copied4 immutable programs, environment2 untracked files, runtime',len(external),'tracked production',len(tracked))
