"""New source-only Task3 cost preparation after accepted GREEN2. No Julia."""
from pathlib import Path
import sys,json,shutil
D=Path(__file__).resolve().parent;R=D.parents[3];G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION');O=D.with_name('DIRECT-BG-SPLIT-COST-PREPARATION')
sys.path.insert(0,str(G));import control as g
h=g.full_host(g.rd(G/'runs/green2-300/posthost.json')['groups']);h.update(memory=g.guard.memory(),status=g.git('status','--porcelain'),remote=g.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
g.require(g.host_safe(h) and not g.guard.pressure(h['memory']) and not g.git('diff','--name-only','HEAD') and not g.git('diff','--cached','--name-only'),'Host/refs')
g.preparation();g.validate_sources();g.result_review('green2-300','BG export workspace GREEN2 result','result-review.json');g.require(g.rd(G/'runs/green2-300/audit.json')['all_passed'],'GREEN2')
g.save(D/'host.json',h)
# New controls are byte-exact copies except the documented cost scope string.
reused={}
for n in ('guard.py','supervisor.py','seal.py','baseline.json','runtime-inputs-complete.json','environment.json'):
 (D/n).open('xb').write((G/n).read_bytes());reused[n]=dict(path=str(G/n),sha256=g.sha(G/n))
for n in ('inputs.json','inputs.toml','analysis.py'):
 (D/n).open('xb').write((O/n).read_bytes());reused[n]=dict(path=str(O/n),sha256=g.sha(O/n))
s=(G/'launch.py').read_text().replace('BG export workspace exact-stage admission','BG export workspace cost admission');(D/'launch.py').open('x').write(s)
s=(O/'audit.py').read_text().replace('split BG matched cost admission','BG export workspace cost admission').replace("all(not h['matches'] for h in [pre,hs,post])","all(host_safe(h) for h in [pre,hs,post])")
(D/'audit.py').open('x').write(s)
loaded=g.rd(G/'loaded-paths.json');loaded.pop('Test',None);g.save(D/'loaded-paths.json',loaded)
# Build a new stage from exact accepted GREEN2 candidate stage; no old stage mutation.
base=Path(g.rd(G/'stages.json')['green']['path']);stage=R/'.superpowers/sdd/2026-10-18-direct-bg-export-workspace/task3-cost-stage';stage.mkdir(parents=True,exist_ok=False)
for n,h0 in g.rd(G/'stages.json')['green']['sha256'].items():
 p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);g.require(g.sha(base/n)==h0,'Stage seed');p.open('xb').write((base/n).read_bytes())
sys.path.insert(0,str(D));from clone_source import clone_sources
clones,edits,header=clone_sources(g.C)
for name,s in clones.items():
 (D/('probe-'+name+'.jl')).open('x').write(s);(stage/'src'/('_bgxp_'+name+'.jl')).open('x').write(s)
p=stage/'src/JSimplex.jl';s=p.read_text();g.require(s.endswith('end # module JSimplex\n'),'Root end')
addition=''.join('include("_bgxp_'+n+'.jl")\n' for n in clones)
p.write_text(s[:-len('end # module JSimplex\n')]+addition+'end # module JSimplex\n')
g.save(D/'probe-inverse.json',dict(rename=[['_BGXBuildOwner','_BGXPBuildOwner'],['BGExport','BGProbeExport'],['_bgx_','_bgxp_']],edits=edits,header=header,stage_addition=addition,seed=str(base),scope='Untimed clones only; counters at explicit seams, not complete native backend work'))
g.save(D/'stages.json',{'cost':dict(path=str(stage),sha256={str(p.relative_to(stage)):g.sha(p) for p in sorted(stage.rglob('*')) if p.is_file()})})
g.save(D/'reused-files.json',reused)
g.save(D/'authorization.json',dict(user_request='Prosím dokonči testování a měření kandidáta autonomně.',scope='Accepted Task3 cost: independent preparation+concrete admission before each process; fixed design stop gates; no production integration',initial_seconds=300,only_pure_timeout_separate_seconds=600))
print('New83-file cost stage and independent probe clones prepared; no Julia/seal/reservation')
