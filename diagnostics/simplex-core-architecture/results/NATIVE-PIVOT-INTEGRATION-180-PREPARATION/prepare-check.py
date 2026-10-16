"""New offline checks and explicit read-time inventory; no Julia or stage."""
from control import *
import ast
checks={}
def check(n,v):
 checks[n]=bool(v);require(v,n)
def refuses(f):
 try:f();return False
 except Exception:return True
cfg=config('integration');check('seconds180',cfg['seconds']==180)
check('inner172',guard_command(cfg,Path('/tmp/pins'),10)[6:10]==['--seconds','172','--deadline','182'])
check('original_driver',cfg['command'][-4]==str(DRIVER/'driver.jl'))
check('unchanged_flags',cfg['command'][2:6]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G'])
check('wrong_phase_refused',refuses(lambda:config('cost')))
validate_environment();baseline=dict(os.environ)
try:
 for k in rd(D/'environment.json'):
  os.environ[k]='__wrong__';check('environment_refusal_'+k,refuses(validate_environment));os.environ.clear();os.environ.update(baseline)
finally:os.environ.clear();os.environ.update(baseline)
check('no_attempt',not (D/'runs').exists() and not Path(cfg['stage']).exists())
source=rd(D/'source-map.json');E=D.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT'
check('eight_exact_copies',all(sha(D/n)==h==sha(E/n) for n,h in source['byte_identical'].items()) and len(source['byte_identical'])==8)
check('common_exact_delta',(D/'common.py').read_text()==(E/'common.py').read_text().replace('5fd40966abc84be5bb88a789853273b41f754717',HEAD))
for p in D.glob('*.py'):ast.parse(p.read_text())
check('python_source_parse',True)
extra,groups=predecessor('integration');h=full_host(groups);verify_host(h);save(D/'prepare-host.json',h);check('groups218',len(h['groups'])==218)
base=rd(E/'actual-baseline.json');check('actual520',len(base['sha256'])==520 and bindings(base))
check('frozen_tests',all(sha(e['source'])==e['sha256'] for e in rd(DRIVER/'overlay-manifest.json')['candidate']))
check('same_solver_deadline','time_limit=5.0, iteration_limit=100' in (DRIVER/'observed-tests.jl').read_text())
check('same_assertions','All162 assertions are unchanged' in (DRIVER/'REPORT.md').read_text())
A=D.parent/'NATIVE-PIVOT-INTEGRATION-COMPILE-ANALYSIS'
extra += [E/n for n in source['byte_identical']]+[E/'control.py',E/'common.py',E/'actual-baseline.json']
extra += list(A.iterdir())
rt=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
extra += [rt/'share/julia/base/loading.jl',rt/'share/doc/julia/html/en/manual/command-line-interface.html',Path('/home/jspitz/.julia/packages/PrecompileTools/QUxvR/src/workloads.jl')]
save(D/'prepare-checks.json',dict(all_passed=all(checks.values()),checks=checks,scope='Offline read-time validation and synthetic process-local environment refusal; no Julia/stage'))
files=sorted(set(extra)|{p for p in D.iterdir() if p.is_file()})
require(all(p.is_file() for p in files),'Input file')
save(D/'required-paths.json',dict(paths=sorted([str(p) for p in files]+[str(D/'required-paths.json')])))
files.append(D/'required-paths.json')
save(D/'preparation-pins.json',dict(sha256={str(p):sha(p) for p in files},scope='New read-time preparation inventory; original launch manifests unchanged'))
print(dict(checks=len(checks),pins=len(files),no_Julia=True))
