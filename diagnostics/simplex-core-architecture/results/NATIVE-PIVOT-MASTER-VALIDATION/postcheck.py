"""New post-exit supplement; not a launch pin and never re-executes the auditor."""
from pathlib import Path
import sys,math,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'NATIVE-PIVOT-MASTER-READINESS';sys.path.insert(0,str(D))
from control import *
from oracle import test_results
phase=sys.argv[1];run=D/'runs'/phase;out=run/'output';a=rd(run/'audit.json');cfg=config(phase)
require(a['all_passed'] is True and a['pure_timeout'] is False,'Not a successful audited attempt')
preparation();validate_environment();validate_production();s=rd(run/'sealed.json');pins=rd(run/'launch-pins.json')
verify_review(rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'actual-master exact-stage admission',phase)
require(guard.pins_match(s) and guard.pins_match(pins),'Immutable run inputs')
require(bindings(a),'Original auditor bindings')
raw=tomllib.loads((out/'raw.toml').read_text());result=test_results(raw,rd(D/'expected-tests.json'),rd(D/'loaded-paths.json'))
p=rd(out/'process.json');post=rd(run/'posthost.json');h=full_host(post['groups']);require(not h['matches'],'Processes remain')
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];memory=guard.memory();require(not guard.pressure(memory),'Current memory')
main=Path('/home/jspitz/JSimplex.jl');integration=rd(E/'integration.json')
require(all(sha(main/n)==v for n,v in integration['user_sha256'].items()),'User bytes drift')
require(all(git('hash-object','--',n,cwd=main)==v for n,v in integration['git_blobs'].items()),'Actual main bytes drift')
checks=dict(audit_pass=True,readiness_scope=True,actual_stage_admission=True,immutable_seal_and_launch=True,audit_original_bindings=True,exact_assertions=result['assertions']==6956,actual_master_identity=True,user_files_preserved=True,all_groups_sessions_absent=True,current_resources=True)
files=sorted([q for q in run.rglob('*') if q.is_file()]+[Path(__file__),E/'integration.json'])
save(E/(phase+'-postcheck.json'),dict(all_passed=all(checks.values()),checks=checks,host=h,result=result,resource_summary=dict(samples=len(resources),min_available_kib=min(z['available_kib'] for z in resources),max_swap_kib=max(z['swap_used_kib'] for z in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'],inclusive_elapsed_seconds=rd(run/'invocation.json')['elapsed_seconds'],timing_scope='Inclusive guard/test run, not benchmark'),sha256={str(q):sha(q) for q in files},scope='Post-exit supplement, not launch admission'))
print('Master postcheck',len(checks),'PASS',result['assertions'],'assertions',len(resources),'resource samples')
