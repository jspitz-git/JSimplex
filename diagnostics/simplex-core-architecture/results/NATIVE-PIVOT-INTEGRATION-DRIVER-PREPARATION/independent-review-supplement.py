"""Resolve reviewer-context check without editing pins or permitting a launch."""
from pathlib import Path
import json,sys,hashlib
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control
rd=lambda p:json.loads(p.read_text())
a=rd(D/'independent-review-checks.json');e=rd(D/'independent-review-environment.json')['differences'];checks={}
checks['initial_only_environment']=a['failed']==['environment exact'] and len(a['checks'])==4172
checks['only_worker_PATH_prefix']=set(e)=={'PATH'} and e['PATH']['expected'].split(':')[1:]==e['PATH']['observed'].split(':')[1:] and all('/.codex/tmp/arg0/codex-arg0' in e['PATH'][k].split(':')[0] for k in ['expected','observed'])
try:control.validate_environment()
except RuntimeError as ex:checks['current_context_refused']=str(ex)=='Loading environment changed'
else:checks['current_context_refused']=False
checks['all_noncontext_checks_pass']=all(v for k,v in a['checks'].items() if k!='environment exact')
checks['no_stage_or_runs']=not Path(control.config('integration')['stage']).exists() and not (D/'runs').exists()
T=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl');t=T.read_text()
checks['Test113_scoped_recorder_contract']=all(x in t for x in ['macro with_testset(ts, expr)','CURRENT_TESTSET => $(esc(ts))','typeof(get_testset())','ret = finish(ts)','record(ts, Error(:nontest_error'])
with (D/'independent-review-supplement.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,resolution='Offline preparation accepted; current worker environment is refused for launch. No environment or pin rewrite; exact-stage review remains mandatory.',source_sha256={str(T):hashlib.sha256(T.read_bytes()).hexdigest()}),f,indent=2);f.write('\n')
with (D/'review-initial.json').open('x') as f:json.dump(dict(accepted=False,scope='offline preparation',findings=['Initial reviewer current-environment equality check failed; only worker temporary PATH prefix differs. Pending scope/refusal resolution.'],evidence='independent-review-checks.json',preserved=True),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),all_passed=all(checks.values()))))
if not all(checks.values()):sys.exit(1)
