from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common_ready as c
p=c.read('output/process.json');c.need(p['returncode']==1 and p['pins_unchanged'],'failedloaderpreserved');log=(D/'output/run.log').read_text();c.need('invalid method definition' in log and 'JSimplex._primal_nonnegative_step' in log and 'CONTEXT ' not in log and not(D/'output/results.toml').exists(),'loadfailurebeforetests')
c.unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];h=c.host(extra);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);c.put('failed-load-host.json',h)
Q=D/'comparison-2';Q.mkdir()
def put(n,v):
 with (Q/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
for arm in ['Reference','A','B','C']:
 s=(D/(arm+'.jl')).read_text();c.need(s.count('_primal_nonnegative_step,')==1,'exactimportentry');(Q/(arm+'.jl')).write_text(s.replace('_primal_nonnegative_step,','',1))
for old,new in [('fixtures.jl','fixtures.jl'),('extra-tests-ready.jl','extra-tests.jl')]:shutil.copyfile(D/old,Q/new)
(Q/'driver.jl').write_text((D/'driver-ready.jl').read_text().replace('extra-tests-ready.jl','extra-tests.jl'))
(Q/'common.py').write_text((D/'common_ready.py').read_text().replace('contract-ready.json','contract.json').replace('pins-ready.json','pins.json'))
(Q/'launch.py').write_text((D/'launch-ready.py').read_text().replace('common_ready','common').replace('contract-ready.json','contract.json').replace('pins-ready.json','pins.json').replace('admission-ready.json','admission.json'))
shutil.copytree(D/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'))
for n in ['environment.json','protected-before.json']:shutil.copyfile(D/n,Q/n)
put('host-before.json',h);put('host-seed.json',h)
co=c.read('contract-ready.json');co['command']=[x.replace(str(D/'driver-ready.jl'),str(Q/'driver.jl')).replace(str(D/'output/results.toml'),str(Q/'output/results.toml')) for x in co['command']];put('contract.json',co)
put('load-fix.json',dict(accepted_source_fix=True,failed_attempt=dict(process=c.sha(D/'output/process.json'),log=c.sha(D/'output/run.log'),no_context_tests_or_measurement=True),only_change='remove using-import of already copied short-form private helper; retain owned exact baseline definition in each fragment',candidate_algorithms_unchanged=True,reference_and_allcandidate_inverse={arm:dict(old=c.sha(D/(arm+'.jl')),new=c.sha(Q/(arm+'.jl'))) for arm in ['Reference','A','B','C']}))
shutil.copyfile(__file__,Q/'prepare.py');paths=set(c.read('pins-ready.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.is_relative_to(D/'baseline'))
put('pins.json',dict(files=sorted(paths),trees=c.read('pins-ready.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import importlib.util
sp=importlib.util.spec_from_file_location('newcommon',Q/'common.py');cc=importlib.util.module_from_spec(sp);sp.loader.exec_module(cc);cc.unchanged();cc.put('author-host.json',cc.host());print('comparison-2',len(paths),'pins; fresh',len(h['groups']),'groups; noJulia')
