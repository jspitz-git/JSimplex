"""Create separate Task3 candidate-only harness/stage; no Julia or operational launch."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION');G=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER');C=R/'diagnostics/direct-bg-export-specialized/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def save(n,v):put(n,json.dumps(v,indent=2)+'\n')
def rename(s):return s.replace('_BGXBuildOwner','_BGXSBuildOwner').replace('BGExport','BGSpecializedExport').replace('_bgx_','_bgxs_').replace('_BGXPBuildOwner','_BGXSPBuildOwner').replace('BGProbeExport','BGSpecializedProbeExport').replace('_bgxp_','_bgxsp_')
reused={}
for n in ['guard.py','supervisor.py','baseline.json','environment.json','runtime-inputs-complete.json']:
 put(n,(G/n).read_text());reused[n]=dict(path=str(G/n),sha256=sha(G/n))
for n in ['inputs.json','inputs.toml','analysis.py']:
 put(n,(O/n).read_text());reused[n]=dict(path=str(O/n),sha256=sha(O/n))
for n in ['cost.jl','probe.jl','clone_source.py']:
 put(n,rename((O/n).read_text()))
# Transform accepted full-source inversion generator to specialized namespace; no old script executes.
sys.path.insert(0,str(D));from clone_source import clone_sources
clones,edits,header=clone_sources(C)
seed=Path(json.loads((G/'stages.json').read_text())['green']['path']);stage=R/'.superpowers/sdd/2026-10-19-direct-bg-export-specialization/task3-cost-stage';stage.mkdir(parents=True,exist_ok=False)
seedhash=json.loads((G/'stages.json').read_text())['green']['sha256']
for n,h in seedhash.items():
 if sha(seed/n)!=h:raise RuntimeError('Seed drift')
 p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((seed/n).read_bytes())
for name,s in clones.items():put('probe-'+name+'.jl',s);(stage/'src'/('_bgxsp_'+name+'.jl')).write_text(s)
p=stage/'src/JSimplex.jl';s=p.read_text()
if not s.endswith('\nend\n'):raise RuntimeError('Root end changed')
addition=''.join('include("_bgxsp_'+n+'.jl")\n' for n in clones);p.write_text(s[:-len('end\n')]+addition+'end\n')
save('probe-inverse.json',dict(edits=edits,header=header,stage_addition=addition,seed=str(seed),rename=[['_BGXSBuildOwner','_BGXSPBuildOwner'],['BGSpecializedExport','BGSpecializedProbeExport'],['_bgxs_','_bgxsp_']],scope='Full-file inverse to specialized candidate; untimed probes only'))
save('stages.json',{'cost':dict(path=str(stage),sha256={str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()})})
loaded=json.loads((G/'loaded-paths.json').read_text());loaded.pop('Test',None);save('loaded-paths.json',loaded);save('reused-files.json',reused)
# Retain old cost output contract and arithmetic; descriptive strings kept for exact inverse.
put('evidence.py',(O/'evidence.py').read_text())
for n in ['outer.py','seal.py','launch.py','post-return.py']:
 put(n,(G/n).read_text().replace('BG specialization GC exact-stage admission','BG specialized export cost admission'))
save('source-transform.json',dict(source=str(O),namespace_only=['cost.jl','probe.jl','clone_source.py'],byte_exact=['inputs.json','inputs.toml','analysis.py','evidence.py'],seed_files=len(seedhash),stage_files=len(list(stage.rglob('*.jl'))),scope='Frozen Task3 whole-lifecycle capture; no explicit GC added, unlike separate Task2 amendment'))
print('Prepared separate source-inverse clones and 87-file stage; no Julia.')
