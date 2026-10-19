from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER'
def edit(n,a,b):
 p=P/n;s=p.read_text()
 if s.count(a)!=1:raise ValueError((n,a,s.count(a)))
 p.write_text(s.replace(a,b))
edit('outer.py','One explicit RED300 invocation','One explicit RED/GREEN GC invocation')
# Prepare exact required launch input membership independent of self-reported seal lists.
p=P/'control.py';s=p.read_text();s+='''
def seal_files(cfg,prepared,extra):
 run=Path(cfg['run'])
 return sorted(set(prepared+list(rd(D/'runtime-inputs-complete.json')['inventory'])+[str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]]+[str(Path(cfg['stage'])/n) for n in rd(D/'stages.json')[cfg['mode']]['sha256']]+extra+[str(run/'host.json'),str(run/'config.json'),str(outer_dir(cfg['phase'])/'outer-ready.json')]))
def verify_seal(cfg,sealed):
 prepared=preparation();extra,_=predecessor(cfg['phase'])
 require(sealed['files']==seal_files(cfg,prepared,extra),'Exact seal membership')
 require(sealed['trees']==[cfg['stage'],str(C)] and sealed['inputs']==[],'Exact sealed trees')
 require(sealed['inventory']==guard.inventory(sealed['files'],sealed['trees']),'Exact sealed inventory')
''';p.write_text(s)
p=P/'seal.py';s=p.read_text();a=s.index(' files=sorted(set(');b=s.index('\n # All production',a);s=s[:a]+" files=seal_files(cfg,files,extra)"+s[b:];p.write_text(s)
edit('launch.py',"verify_outer_invocation(phase,sealed,live=True)","verify_seal(cfg,sealed)\n verify_outer_invocation(phase,sealed,live=True)")
edit('audit.py',"verify_outer_invocation(phase,s)","verify_seal(cfg,s)\n verify_outer_invocation(phase,s)")
# Preserve external closure inputs in predecessor even though outer files are outside run directory.
edit('control.py',"return f,sorted(set(g)|set(closure['host']['groups']))","require(closure['outer_identity']==rd(run/'sealed.json')['outer_identity'],'RED outer mismatch')\n outcome=rd(outer_dir(red)/'outer-outcome.json')\n require(outcome['launched'] is True and outcome['returncode']==0 and outcome['error']=='','RED outer did not finish successfully')\n return sorted(set(f)|set(closure['sha256'])),sorted(set(g)|set(closure['host']['groups']))")
(P/'finalize-source.py').write_text(Path(__file__).read_text())
