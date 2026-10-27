from pathlib import Path
import sys,json,re
sys.dont_write_bytecode=True
O=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');D=O/'GREEN-run';sys.path.insert(0,str(D));import common as c
load=lambda n:json.loads((D/n).read_text())
co=load('contract.json');p=load('output/process.json');s=load('supervisor.json');done=load('completed.json');res=load('reservation.json');audit=load('audit.json');gate=load('output/gate.json');permit=load('output/permit.json');current=load('output/current.json');inv=load('invocation.json');pins=load('pins.json')
for review in [D/'admission.json',O/'production-review.json',O/'publication-preparation-reviewed.json',O/'finalization-preparation-review.json']:
 r=json.loads(review.read_text());assert r['accepted'] and not r['findings']
 for name,h in r['bindings'].items():assert c.sha(name)==h,(review,name)
for name,h in audit['bindings'].items():assert c.sha(name)==h
assert co['arm']=='GREEN' and co['expected_exit']==co['expected_failures']==0 and len(co['files'])==len(set(co['files']))==51
assert p['command']==co['command']==inv['Julia_command']==gate['command']==permit['command']==current['command']
assert p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] and s['accepted'] and s['returncode']==0
assert all(s[x] is False for x in ['soft_timeout','hard_timeout','abnormal_cleanup_attempted','child_cleanup_attempted','child_kill','guard_kill','guard_term']) and 'cleanup_error' not in s
assert p['runner']==s['guard_identity']==s['guard_initial_identity']==gate['parent']==current['runner']
assert p['child']==gate['identity']==current['child'] and gate['parent_death_signal']==9
assert gate['current_sha256']==permit['current_sha256']==c.sha(D/'output/current.json') and gate['permit_sha256']==c.sha(D/'output/permit.json')
assert p['pins_sha256']==c.sha(D/'pins.json')==c.sha(D/'output/pins.json')==res['pins_sha256']
assert res['admission_sha256']==c.sha(D/'admission.json')
assert res['attempt']==1 and res['guard_deadline']==res['started_monotonic']+2992==inv['guard_deadline']
assert res['outer_deadline']==res['started_monotonic']+3000==inv['outer_deadline']
assert done['accepted'] and done['pins_unchanged'] and done['limit_seconds']==3000
assert 0<p['elapsed_including_launch']<=s['elapsed_seconds']<=done['elapsed_shared_seconds']<3000
log=(D/'output/run.log').read_text()
assert re.findall(r'^BNI_SOURCE (.*)$',log,re.M)==[str(O/'GREEN/src/JSimplex.jl')]
assert re.findall(r'^INCLUDING (.*)$',log,re.M)==co['files']
assert re.findall(r'^Test Summary:.*\|(.+)$',log,re.M)==['   Pass   Total      Time']
rows=re.findall(r'^Bounds norm infeasibility GREEN\s*\|\s*(\d+)\s+(\d+)\s+(\S+)\s*$',log,re.M);assert len(rows)==1 and rows[0][:2]==('314009','314009')
assert re.findall(r'^BNI_COMPLETED (.*)$',log,re.M)==['GREEN']
assert all(x not in log for x in ['Error During Test','Test Failed at '])
assert not re.search(r'^ERROR:',log,re.M)
assert len(re.findall(r'^\[ Info: Restarting simplex .*NUMERICAL_ERROR:',log,re.M))==12
resources=[json.loads(x) for x in (D/'output/resources.jsonl').read_text().splitlines()]
assert len(resources)==1755 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources)
assert all(a['elapsed']<b['elapsed'] for a,b in zip(resources,resources[1:]))
assert resources[0]['elapsed']<1 and resources[-1]['elapsed']<=p['elapsed_including_launch']
assert min(x['available_kib'] for x in resources)==audit['minimum_available_kib']==19171180
assert max(x['swap_used_kib'] for x in resources)==audit['maximum_swap_kib']==0
assert p['terminal_memory']['available_kib']>=6*1024**2 and p['terminal_memory']['swap_used_kib']==0
assert p['child_maxrss_kib']==audit['child_maxrss_kib']==3732620
assert audit['accepted'] and audit['passed']==audit['total']==314009 and audit['expected_failures']==0 and audit['samples']==len(resources)
assert audit['elapsed_shared_seconds']==done['elapsed_shared_seconds']
source=json.loads((O/'source-inverse.json').read_text());assert len(source['names'])==4
assert source['whole_stage']=={str(f.relative_to(O/'GREEN')):c.sha(f) for f in (O/'GREEN').rglob('*') if f.is_file()}
for name,h in source['candidate_sha256'].items():assert c.sha(O/'GREEN'/name)==h
c.unchanged();extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];host=c.host(extra);assert len(host['groups'])==647
c.put('independent-result-host.json',host)
with (D/'independent-result-review.py').open('x') as f:f.write(Path(__file__).read_text())
report='''# Independent GREEN result review

Accepted the exact candidate's 314,009/314,009 ordinary assertions in all 51 ordered whole test files, with exit0 and no failure/error/broken/skip column. All ten permanent whole-call allocation gates now pass following the independently preserved original-source RED of 15,911 passes and ten expected failures. Actual commit review, local integration and fresh actual-MASTER qualification remain required.

This reviewer independently parsed the raw ordinary Test summary and source/completion markers, checked every ordered include, all admission/production/preparation bindings, all 1,312 current resolved launch pins and complete source/test tree memberships, and the exact complete staged tree plus four candidate hashes. No source, test, threshold, existing evidence, or Git state changed. The old post-exit auditor was read but not rerun; no Julia was executed.

Runner/child/session identities, start ticks, boot IDs, commands, entry current/permit hash links, parent-death signal9, copied pins and reservation/admission hashes agree. Supervisor and child completed normally with no timeout, kill or cleanup path. Inclusive shared elapsed is 1,757.683262880004 seconds within the admitted 3,000-second ceiling. All 1,755 monotonic resource samples plus terminal resources meet the RAM/swap limits: minimum available RAM 19,171,180 KiB, maximum swap0, child max RSS 3,732,620 KiB. These are test-process observations, not a solver retained-memory or native-free result. Fresh closure over 647 historical groups AND sessions/boot/start ticks/commands found no Julia, with only the exact existing unrelated-WSL allowance; protected files/indexes/refs/environment remained intact.

A/B/C numerical and ownership conclusions remain those of PRODUCTION-REVIEW.md. No unnecessary added production scan, solve, copy, conversion, invariant pass or persistent numerical cache was found. A's per-row readiness branch and six additional method bodies remain acknowledged costs. Qualified whole-function measurements support lower allocation bytes/events on the affected paths; this broad correctness run does not establish a speedup. Original loader and comparison failures remain failed; qualified raw 1,632-cell/29,376-window evidence and separate 15,881-assertion correctness qualification are unchanged. Broader full suite, x64, native-retention and other recorded coverage remain open.
'''
with (D/'RESULT-REVIEW.md').open('x') as f:f.write(report)
paths=[D/n for n in ['admission.json','contract.json','pins.json','tests.jl','launch.py','common.py','audit.py','audit.json','audit-host.json','completed.json','supervisor.json','reservation.json','invocation.json','output/process.json','output/gate.json','output/permit.json','output/current.json','output/pins.json','output/resources.jsonl','output/run.log','RESULT-REVIEW.md','independent-result-host.json','independent-result-review.py']]+[O/'production-review.json',O/'source-inverse.json']
c.put('result-review.json',dict(accepted=True,findings=[],passed=314009,total=314009,expected_failures=0,files=51,pins=len(pins['inventory']),groups=len(host['groups']),elapsed_shared_seconds=done['elapsed_shared_seconds'],samples=len(resources),Julia_executed=False,Git_mutated=False,bindings={str(x):c.sha(x) for x in paths},scope='exact GREEN result accepted; actual commit and fresh MASTER still required'))
print('accepted independent GREEN 314009/314009; 51 files; 1312 pins; 647 groups; no Julia')
