"""Complete the new unexecuted cost stage after preserved root-end selector failure."""
from pathlib import Path
import sys
D=Path(__file__).resolve().parent;R=D.parents[3];G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION');O=D.with_name('DIRECT-BG-SPLIT-COST-PREPARATION')
sys.path.insert(0,str(G));import control as g
sys.path.insert(0,str(D));from clone_source import clone_sources
base=Path(g.rd(G/'stages.json')['green']['path']);stage=R/'.superpowers/sdd/2026-10-18-direct-bg-export-workspace/task3-cost-stage'
clones,edits,header=clone_sources(g.C)
p=stage/'src/JSimplex.jl';s=p.read_text();g.require(s==(base/'src/JSimplex.jl').read_text() and s.endswith('\nend\n'),'Exact untouched root seed')
(D/'root.before-completion.jl').open('x').write(s)
addition=''.join('include("_bgxp_'+n+'.jl")\n' for n in clones)
p.write_text(s[:-len('end\n')]+addition+'end\n')
for name,t in clones.items():g.require((D/('probe-'+name+'.jl')).read_text()==t==(stage/'src'/('_bgxp_'+name+'.jl')).read_text(),'Existing clone identity')
g.save(D/'probe-inverse.json',dict(rename=[['_BGXBuildOwner','_BGXPBuildOwner'],['BGExport','BGProbeExport'],['_bgx_','_bgxp_']],edits=edits,header=header,stage_addition=addition,seed=str(base),scope='Untimed clones only; explicit seam counts, not complete native backend work'))
g.save(D/'stages.json',{'cost':dict(path=str(stage),sha256={str(p.relative_to(stage)):g.sha(p) for p in sorted(stage.rglob('*')) if p.is_file()})})
reused={n:dict(path=str(G/n),sha256=g.sha(G/n)) for n in ('guard.py','supervisor.py','seal.py','baseline.json','runtime-inputs-complete.json','environment.json')}
reused.update({n:dict(path=str(O/n),sha256=g.sha(O/n)) for n in ('inputs.json','inputs.toml','analysis.py')});g.save(D/'reused-files.json',reused)
g.save(D/'authorization.json',dict(user_request='Prosím dokonči testování a měření kandidáta autonomně.',scope='Accepted Task3 cost: independent preparation+concrete admission before each process; fixed design stop gates; no production integration',initial_seconds=300,only_pure_timeout_separate_seconds=600))
print('Completed83-file source-bound cost stage; no Julia/seal/reservation')
