"""One-shot timeout preservation check. No numerical or original auditor rerun."""
from pathlib import Path
import sys,json
K=Path(__file__).resolve().parent;R=K.parents[3];E=K.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT';sys.path.insert(0,str(E))
from control import *
run=E/'runs/integration';out=run/'output';p=rd(out/'process.json');inv=rd(run/'invocation.json');audit=rd(run/'audit.json');pins=rd(run/'launch-pins.json');sealed=rd(run/'sealed.json');admission=rd(run/'admission.json');sup=inv['supervisor'];cur=rd(out/'current.json')
h=full_host(rd(run/'posthost.json')['groups']);save(K/'timeout-host.json',h)
resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]
checks=dict(no_survivors=not h['matches'],groups218=len(h['groups'])==218,
 refs_boot=all(h[x]==sealed[x] for x in ['head','master','boot_id']),
 group_closure=all(p[role][x] in h['groups'] for role in ['runner','child'] for x in ['pgid','sid']),
 process_identity=cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],
 identity_boot_start=all(p[role]['boot_id']==sealed['boot_id'] and p[role]['start_ticks']>0 and p[role]['command'] for role in ['runner','child']),
 timeout=p['reason']=='wall_time' and p['returncode']==-9 and sup['accepted'] is False,
 outer_limit=0<=inv['elapsed_seconds']<=60 and 0<=sup['elapsed_seconds']<=60,
 command=p['command']==cur['command']==inv['command']==sealed['config']['command'],
 guard_command=inv['guard_command']==guard_command(sealed['config'],run/'launch-pins.json',inv['monotonic_start']),
 invocation_bindings=inv['pins_sha256']==sha(run/'launch-pins.json')==p['pins_sha256'] and inv['review_sha256']==sha(run/'admission.json') and inv['reservation_sha256']==sha(run/'reservation.json'),
 exact_reservation=rd(run/'reservation.json')==dict(one_attempt=True,phase='integration',command=sealed['config']['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=60),
 output5={x.name for x in out.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log'},
 no_raw=not (out/'raw.toml').exists(),
 audit_false=audit['all_passed'] is False and audit['error']=="RuntimeError('Exact output membership')" and audit['result']=={},
 audit_bindings=bindings(audit),admission_bindings=bindings(admission),
 launch_pins=all(sha(Path(n))==z['sha256'] and str(Path(n).resolve())==z['resolved'] for n,z in pins['inventory'].items()),
 seal_pins=all(sha(Path(n))==z['sha256'] and str(Path(n).resolve())==z['resolved'] for n,z in sealed['inventory'].items()),
 pin_link=rd(out/'pins.json')==pins and p['pins_unchanged'] is True,
 memory=bool(resources) and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources+[p['terminal_memory']]),
 actual520=all(sha(R/n)==s for n,s in rd(E/'actual-baseline.json')['sha256'].items()),
 before_texts=sha(STATUS)==sha(K/'STATUS.md.before-integration-run') and sha(ROAD)==sha(K/'roadmap.md.before-integration-run'))
log=(out/'run.log').read_text(errors='replace')
summary=dict(qualification_accepted=False,attempt_consumed=True,reason=p['reason'],child_returncode=p['returncode'],inclusive_seconds=inv['elapsed_seconds'],guard_elapsed=p['elapsed_including_launch'],resident_highwater_kib=p['child_maxrss_kib'],resource_samples=len(resources),min_available_kib=min(v['available_kib'] for v in resources),max_swap_kib=max(v['swap_used_kib'] for v in resources),terminal_memory=p['terminal_memory'],supervisor=sup,raw_absent=True,assertion_results='UNKNOWN; no completed raw',selected_work_counts='UNKNOWN; no completed raw',interruption_stack_has_llvm='libLLVM' in log and 'jl_compile' in log,interruption_stack_public_case='public_case at ' in log,scope='Stack location at interruption only, not full timing attribution or proof of a solver/numerical defect',groups=len(h['groups']),launch_pins=len(pins['inventory']),seal_pins=len(sealed['inventory']))
save(K/'timeout-postcheck.json',dict(all_passed=all(checks.values()),checks=checks,summary=summary,sha256={str(p):sha(p) for p in [run/'audit.json',run/'admission.json',run/'invocation.json',run/'posthost.json',out/'process.json',out/'run.log',out/'resources.jsonl',K/'timeout-host.json',K/'timeout-postcheck.py']},scope='Integrity/cleanup only; numerical qualification remains FAILED/CONSUMED'))
require(all(checks.values()),'Timeout preservation check failed; preserve');print(dict(checks=len(checks),**{k:summary[k] for k in ['qualification_accepted','inclusive_seconds','resident_highwater_kib','resource_samples','min_available_kib','max_swap_kib','groups','launch_pins']}))
