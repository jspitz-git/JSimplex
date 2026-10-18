from pathlib import Path
import json,re,hashlib
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-COST-PREPARATION');R=E.parents[3];C=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,t):Path(p).write_text(t)
# Complete pre-check drafts; these versions have not yet been audited or reviewed.
i=json.loads((E/'probe-inverse.json').read_text());i['renames']['_bgu_check']='_probe_bgu_check'
i['allocator']['new']=i['allocator']['new'].replace('n*sizeof(T)','n*Base.elsize(Vector{T})')
p=E/'probe-upper.jl';write(p,p.read_text().replace('n*sizeof(T)','n*Base.elsize(Vector{T})'))
p=E/'probe-oracles.jl';t=p.read_text();first=t.index('function _bgu_check');second=t.index('function _bgu_check',first+1);t=t[:second]+t[second:].replace('_bgu_check','_probe_bgu_check');write(p,t)
p=E/'probe.jl';write(p,p.read_text().replace('sizeof(eltype(a))','Base.elsize(typeof(a))'))
write(E/'probe-inverse.json',json.dumps(i,indent=2)+'\n')
s=json.loads((E/'stages.json').read_text());stage=Path(s['cost']['path'])
for n in ['probe-upper.jl','probe-oracles.jl']:write(stage/'src'/n,(E/n).read_text());s['cost']['sha256']['src/'+n]=sha(stage/'src'/n)
write(E/'stages.json',json.dumps(s,indent=2)+'\n')
p=E/'evidence.py';t=p.read_text().replace("BASE|{'raw.toml'}","BASE|{'raw.toml','growth.toml'}")
t=t.replace("fixtures=rd(D/'inputs.json')['fixtures'];results=[];visited=set();cell=0;finished=0;windows=0", "fixtures=rd(D/'inputs.json')['fixtures'];results=[];visited=set();cell=0;finished=0;windows=0\n if 'growth.toml' in names:\n  growth_ok(tomllib.loads((out/'growth.toml').read_text()));visited.add('growth.toml')\n else:require(not any(n.startswith('started-') for n in names),'Cells before growth probe')")
# Include probes in precise residual counts, including partial checkpoints.
t=t.replace("windows=0\n if 'growth.toml'", "windows=0;probes=0\n if 'growth.toml'")
t=t.replace("probe_ok(pr,f,matrices);visited.add(probe)","probe_ok(pr,f,matrices);visited.add(probe);probes+=1")
t=t.replace('exact_residuals=24*windows','exact_residuals=24*windows+72*probes')
t=t.replace("['FATAL COST:','ERROR:','TEST FAILURE:','Traceback','Measured compilation; stop']","['FATAL COST:','ERROR:','TEST FAILURE:','Traceback','Measured compilation; stop','WARNING:','Warning:','world age']")
write(p,t)
with (E/'draft-completion.py').open('x') as f:f.write(Path(__file__).read_text())
