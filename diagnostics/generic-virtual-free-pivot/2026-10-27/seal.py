from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');O=D.parents[1]/'generic-quality-local/2026-10-27';Q=O/'comparison-2';sys.path.insert(0,str(D));import common as c
for src,dst in [('/tmp/vfp-fixtures.jl','fixtures.jl'),('/tmp/vfp-driver.jl','driver.jl')]:shutil.copyfile(src,D/dst)
shutil.copytree(Q/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile(Q/'launch.py',D/'launch.py')
contract=json.loads((Q/'contract.json').read_text());contract['command']=[x.replace(str(Q),str(D)) for x in contract['command']];contract.update(cases=3328,measured_windows=59904);c.put('contract.json',contract)
s=(Q/'audit.py').read_text().replace(str(Q),str(D)).replace('Local quality whole-function comparison','Virtual free pivot whole-function comparison').replace('LOCAL_QUALITY_COMPARISON_COMPLETE cells=2172','VIRTUAL_FREE_PIVOT_COMPARISON_COMPLETE cells=3328')
a=s.index('expected=[]');b=s.index("fields=['seconds'")
s=s[:a]+'''expected=[]
for label,t in contexts:
 for n in [32,128]:
  for m in [4,16]:
   for scope in ['audit','virtual','virtual_transposed','pivot']:
    for density in ['sparse','dense']:
     for pattern in (['positive','negative','mixed','zero'] if t=='BigFloat' else ['mixed']):
      expected.append((label,t,n,scope,density,pattern,m,'C' if scope=='pivot' else 'A'))
 for n in [32,128]:
  for scope in ['enter_dantzig','enter_devex','partial_hit','partial_rebuild','summary']:
   for density in ['sparse','dense']:
    for pattern in (['positive','negative','mixed','bound'] if t=='BigFloat' else ['mixed']):expected.append((label,t,n,scope,density,pattern,4,'B'))
c.need(len(data['cells'])==len(expected)==contract['cases']==3328,'exact matrix length')
'''+s[b:]
s=s.replace("[key[0],key[2],*key[3:]]","[key[0],key[2],key[6],*key[3:6]]")
s=s.replace("['quality','quality_transposed']","['virtual','virtual_transposed']").replace('2172','3328')
s=s.replace("  by={w['arm']:w for w in pair};", "  if cell['scope']=='pivot':c.need(all(w['sink']==(3 if cell['pattern']=='zero' else 1) for w in pair),'complete pivot path')\n  if cell['scope'].startswith('enter_') or cell['scope'].startswith('partial_'):c.need(all(w['sink']>0 for w in pair),'nonempty entering path')\n  by={w['arm']:w for w in pair};")
s=s.replace(" r={k:cell[k] for k in names};", " route=cell['scope'] if cell['scope'] in ['partial_hit','partial_rebuild'] and cell['n']+cell['basis_rows']>128 else ('full_fallback' if cell['scope'] in ['partial_hit','partial_rebuild'] else 'none')\n c.need(cell['pool_route']==route,'actual partial scope declaration')\n r={k:cell[k] for k in names};")
s=s.replace("resources=[json.loads", "  c.need(len(v['route_checks'])==18 and all(validcost(x['before']) and validcost(x['after']) for x in v['route_checks']),'all route validation prep costs')\nresources=[json.loads")
(D/'audit.py').write_text(s)
shutil.copyfile(__file__,D/'seal.py')
paths={n for n in json.loads((Q/'pins.json').read_text())['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
paths.update(str(p) for root in [c.M/'src',c.M/'test',D/'baseline'] for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml'])
paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(O/'host-identity-allowance.json'));paths.add(str(c.R/'diagnostics/dual-finite-validity/terminal-primal-repair/green-2/output/process.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print(len(paths),'pins;noJulia')
