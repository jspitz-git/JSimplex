"""Exclusive preparation for each distinct stage; never launches Julia."""
from common import *
WORKSPACE=[('Repeated Markowitz construction reuses private workspace',12),('Markowitz pivot ties do not depend on retained dictionary capacity',56),('Markowitz workspace resets clear dimension and failure history',224),('Retained Markowitz capacity after smaller bases',8),('Markowitz initial counts reuse active row length queries',24)]
MARKOWITZ=[('Markowitz sparse elimination and dense core',62),('Markowitz fill pivots and permutations',8),('Rejected singleton rows are reconsidered',2),('Equal-fill pivots preserve magnitude preference',1),('Markowitz pivoting avoids extreme fill overflow',1),('Markowitz threshold respects stored BigFloat precision',2),('Triangular updates accumulate over a Markowitz base',144),('Markowitz backend retains sparse storage and solve buffers',7),('Dense Markowitz input avoids a sparse staging copy',1),('Markowitz refactorization is selectable for every basis update',80)]
CACHE=[('Markowitz caches raw maxima once per pivot search',50),('Markowitz maximum cache retains stored BigFloat precision',36),('Markowitz maximum storage survives workspace shrink',4)]
def freeze(stage):
 synthetic=read(D/'synthetic.json');require(synthetic['all_passed'] is True and all(v is True for v in synthetic['checks'].values()),'synthetic preparation gates')
 s=D/stage;require(not s.exists(),'stage exists');root=P if stage=='master' else R
 if stage=='red':
  groups=read(D/'host.json')['groups'];require((R/'src/markowitz_factorization.jl').read_bytes()==(D/'source.before-S4-AD.jl').read_bytes() and (R/'test/markowitz_workspace_reuse_allocation_tests.jl').read_bytes()==(D/'test.before-S4-AD.jl').read_bytes(),'RED baseline')
  files=[str(AC/'test-append.jl')];expected={files[0]:[dict(name=WORKSPACE[-1][0],counts=[20,4,0,0])]};previous=[]
 else:
  prior=D/('red' if stage=='green' else 'green');audit=read(prior/'audit.json');require(audit['all_passed'] is True and all(v is True for v in audit['checks'].values()),'prior audit')
  require(all(sha(p)==h for field in ('sha256','portable_sha256') for p,h in audit[field].items()),'prior raw bindings')
  groups=audit['host']['groups'];previous=[p for p in prior.rglob('*') if p.is_file()]
  require((root/'src/markowitz_factorization.jl').read_bytes()==(AC/'candidate-source.jl').read_bytes() and (root/'test/markowitz_workspace_reuse_allocation_tests.jl').read_bytes()==(AC/'candidate-test.jl').read_bytes(),'exact candidate actual source/test')
  if stage=='master':
   rv=read(prior/'result-review.json');require(rv['accepted'] is True and rv['unresolved_findings']==[] and all(v is True for v in rv['checks'].values()),'GREEN result acceptance');require(all(sha(p)==h for p,h in rv['sha256'].items()),'GREEN result bindings')
  specs=[('markowitz_workspace_reuse_allocation_tests.jl',WORKSPACE)]
  if stage=='green':specs += [('markowitz_tests.jl',MARKOWITZ),('runtime_markowitz_cache_tests.jl',CACHE)]
  files=[str(root/'test'/n) for n,_ in specs];expected={str(root/'test'/n):[dict(name=k,counts=[v,0,0,0]) for k,v in rows] for n,rows in specs}
 require(len(groups)=={'red':34,'green':36,'master':38}[stage],'group lineage');h=host(groups);require(not h['matches'],'host');s.mkdir()
 out=R/'.superpowers/simplex-core-architecture/S4-AD'/stage;require(not out.exists(),'output exists')
 wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
 command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(root),str(D/'driver.jl'),str(s/'driver-config.toml')]
 c=dict(stage=stage,root=str(root),output=str(out),command=command,files=files,expected=expected,groups=groups,refs=refs(),expected_child_exit=1 if stage=='red' else 0,expected_guard_exit=1 if stage=='red' else 0)
 dump(s/'config.json',c);dump(s/'host.json',h)
 lines=[f'{k} = {json.dumps(v)}' for k,v in dict(stage=stage,root=str(root),output=str(out),files=files,source_sha256=sha(root/'src/markowitz_factorization.jl')).items()]
 lines += ['','[file_hashes]',*[json.dumps(p)+' = '+json.dumps(sha(p)) for p in files]]
 with (s/'driver-config.toml').open('x') as f:f.write('\n'.join(lines)+'\n')
 old=read(D.parent/'S4-AB/launch-pins.json')['inventory'];paths={Path(p) for p in old if not Path(p).is_relative_to(R)}
 paths|={p for n in ('src','test','.github') for p in (root/n).rglob('*') if p.is_file()}
 paths|={root/n for n in ('Project.toml','Manifest.toml','LocalPreferences.toml')}
 paths|={D/n for n in ('driver.jl','guard.py','common.py','oracle.py','run_stage_reviewed.py','freeze_stage_reviewed.py','schedule.json','synthetic.json','host.json','source.before-S4-AD.jl','test.before-S4-AD.jl','STATUS.md.before-S4-AD','roadmap.md.before-S4-AD','continuation-map.json')}
 paths|={D/n for n in ('schedule.before-count-fix.json','preparation-failure.json','synthetic-reviewed.py','run_stage.py','freeze_stage.py')}
 paths|={p for p in (D/'red-preparation-failed').iterdir() if p.is_file()}
 paths|={s/n for n in ('config.json','driver-config.toml','host.json')};paths|=set(map(Path,files));paths|=set(previous)
 paths|={AC/n for n in ('candidate-source.jl','candidate-test.jl','test-append.jl','original-test.jl','review.md','review.json','closure.json','publication.json')}
 paths|={R/'docs/superpowers/plans/2026-10-13-markowitz-row-count-integration.md',Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl')}
 pins=dict(files=sorted(map(str,paths)),trees=[],inputs=[],inventory={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)},created=time.time())
 dump(s/'pins.json',pins);print(json.dumps(dict(stage=stage,pins=len(paths),pins_sha256=sha(s/'pins.json'),expected_assertions=sum(sum(e['counts']) for v in expected.values() for e in v))),flush=True)
if __name__=='__main__':
 require(len(sys.argv)==2 and sys.argv[1] in ('red','green','master'),'stage');freeze(sys.argv[1])
