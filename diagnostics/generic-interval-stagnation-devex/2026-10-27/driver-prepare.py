from pathlib import Path
import shutil,json,sys
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');O=D.parents[1]/'generic-stagnation-unit-seed/2026-10-27';sys.path.insert(0,str(D));import common as c
shutil.copyfile('/tmp/isd-fixtures.jl',D/'fixtures.jl')
s=(O/'comparison-2/driver-reviewed.jl').read_text().replace('("Reference","A","B","C","BC")','("Reference","A","B","C")').replace('fixtures-reviewed.jl','fixtures.jl').replace('include(joinpath(@__DIR__,"extra-tests-reviewed.jl"))\n','').replace('include(joinpath(@__DIR__,"boundary-tests.jl"))\n','').replace('correctness(T);extra_correctness(T);boundary_correctness(T)','correctness(T);boundary_correctness(T)')
a=s.index(' for n in (32,128),');b=s.index('\nend\ntry',a)
s=s[:a]+''' for (n,m) in ((16,8),(64,16)),density in (:sparse,:dense),shape in (T===BigFloat ? (:positive,:negative,:mixed) : (:mixed,))
  for scope in (:rows,:feasible,:reduced,:witness);onecell(T,label,n,m,scope,density,shape,:A);end
  for scope in (:new,:cold,:rebase);onecell(T,label,n,m,scope,density,shape,:B);end
  for scope in (:devex_shared,:devex_solve);onecell(T,label,n,m,scope,density,shape,:C);end
 end
 for shape in (T===BigFloat ? (:positive,:negative,:mixed) : (:mixed,));onecell(T,label,16,8,:leaving,:sparse,shape,:C);end
'''+s[b:]
s=s.replace('Stagnation unit seed whole-function comparison','Interval setup Devex whole-function comparison').replace('STAGNATION_UNIT_SEED_COMPARISON_COMPLETE','INTERVAL_SETUP_DEVEX_COMPARISON_COMPLETE');(D/'driver.jl').write_text(s)
shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
s=(O/'comparison-2/launch-reviewed.py').read_text().replace('common_reviewed','common').replace('contract-reviewed.json','contract.json').replace('pins-reviewed.json','pins.json');(D/'launch.py').write_text(s)
co=c.read('../generic-stagnation-unit-seed/2026-10-27/contract-reviewed.json') if False else json.loads((O/'comparison-2/contract-reviewed.json').read_text());co['command']=[x.replace(str(O/'comparison-2/driver-reviewed.jl'),str(D/'driver.jl')).replace(str(O/'comparison-2/output'),str(D/'output')) for x in co['command']];co.update(cases=1813,measured_windows=32634);c.put('contract.json',co)
# Standalone post-exit auditor adapted from the accepted schema; all new exact grid is frozen below.
s=(O/'comparison-2/audit-reviewed.py').read_text().replace('common_reviewed','common').replace('contract-reviewed.json','contract.json').replace('pins-reviewed.json','pins.json').replace('audit-reviewed.py','audit.py').replace('Stagnation unit seed whole-function comparison','Interval setup Devex whole-function comparison').replace('STAGNATION_UNIT_SEED_COMPARISON_COMPLETE cells=3415','INTERVAL_SETUP_DEVEX_COMPARISON_COMPLETE cells=1813')
a=s.index('for label,t in contexts:');b=s.index("c.need(len(data['cells'])",a)
s=s[:a]+'''for label,t in contexts:
 for n,rows_count in [(16,8),(64,16)]:
  for density in ['sparse','dense']:
   for shape in (['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):
    for scope in ['rows','feasible','reduced','witness']:expected.append((label,t,n,rows_count,scope,density,shape,'A'))
    for scope in ['new','cold','rebase']:expected.append((label,t,n,rows_count,scope,density,shape,'B'))
    for scope in ['devex_shared','devex_solve']:expected.append((label,t,n,rows_count,scope,density,shape,'C'))
 for shape in (['positive','negative','mixed'] if t=='BigFloat' else ['mixed']):expected.append((label,t,16,8,'leaving','sparse',shape,'C'))
'''+s[b:]
s=s.replace('==3415','==1813').replace('==3415+38','==1813+38')
s=s.replace("(7 if cell['scope']=='values' else 1)","(2*cell['rows'] if cell['scope']=='rows' else 2*(cell['n']+cell['rows']) if cell['scope']=='reduced' else 1)")
(D/'audit.py').write_text(s)
(D/'SERIALIZATION.md').write_text('Ordinary Test and plain finally TOML. Raw typed column arrays retain all32634 windows and preparation costs; cold/warm/reset/fixture/validation/GC separately recorded. No custom recorder/manual Test stack. All outputs consumed; import/process init only bounded inclusive.\n')
shutil.copyfile(__file__,D/'driver-prepare.py');print('1813 planned cells/32634 windows, driver and auditor prepared; noJulia')
