"""New one-shot post-exit supplement; never reruns the numerical auditor."""
from pathlib import Path
import json,sys,hashlib
Q=Path(__file__).resolve().parent;E=Q.parent/'DIRECT-BG-BLOCK-COST-PREPARATION';R=Q.parents[3]
sys.path.insert(0,str(E));import control as c
run=E/'runs/cost1-300';a=c.rd(run/'audit.json');p=c.rd(run/'output/process.json');checks={}
def ok(v,k):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
ok(a['all_passed'] is True and a['pure_timeout'] is False,'integrity_audit_accepted')
ok(a['counts']==dict(cells=8,windows=160,exact_residuals=4416),'exact_completed_budget')
ok(p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True,'normal_exit')
ok(c.guard.pins_match(c.rd(run/'sealed.json')) and c.guard.pins_match(c.rd(run/'launch-pins.json')),'all_actual_inputs_unchanged')
ok(c.bindings(a),'original_audit_evidence_unchanged')
ok(not c.first_process_viable(a,c.rd(E/'inputs.json')['fixtures']),'first_cost_gates_reject_second_process')
ok({x.name for x in (E/'runs').iterdir()}=={'cost1-300'},'one_attempt_only')
resources=[json.loads(x) for x in (run/'output/resources.jsonl').read_text().splitlines()]
ok(resources and all(not c.guard.pressure(x) for x in resources+[p['terminal_memory']]),'resource_guards')
h=c.full_host(c.rd(run/'posthost.json')['groups']);c.save(Q/'posthost.json',h)
ok(not h['matches'] and len(h['groups'])==240,'fresh_all_groups_AND_sessions_no_Julia')
ok(h['head']=='ffa005e219b2eb4b8f119a24f6c9953214cac8b9' and h['master']==c.MASTER,'unchanged_refs')
ok(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'no_tracked_changes')
rows=[]
for cell in a['cells']:
 s=cell['statistics'];states=cell['probe']['states'];i,worst=max(enumerate(states),key=lambda z:z[1]['graphs'][1]/z[1]['graphs'][0]);rows.append(dict(fixture=cell['fixture'],backend=cell['backend'],time_ratio=s['seconds']['paired_ratio']['median'],time_ratio_range=[s['seconds']['paired_ratio'][k] for k in ['minimum','maximum']],time_ratio_mad=s['seconds']['paired_ratio']['mad'],bytes=[s['bytes'][x]['median'] for x in ['reference','candidate']],events=[s['events'][x]['median'] for x in ['reference','candidate']],final_graph=[s['retained_bytes'][x]['median'] for x in ['reference','candidate']],worst_checkpoint=dict(index=i,step=worst['step'],refactored=worst['refactored'],graphs=worst['graphs'][:2],ratio=worst['graphs'][1]/worst['graphs'][0]),faster_pairs=s['faster_pairs'],gates={k:s[k] for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']}))
files=[run/'audit.json',run/'output/process.json',run/'invocation.json',run/'posthost.json',run/'output/resources.jsonl',Q/'posthost.json',Path(__file__).resolve()]
c.save(Q/'postcheck.json',dict(all_passed=True,checks=checks,rows=rows,resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_kib=max(x['swap_used_kib'] for x in resources),maxrss_kib=p['child_maxrss_kib'],inclusive_seconds=c.rd(run/'invocation.json')['elapsed_seconds'],sha256={str(p):c.sha(p) for p in files},scope='Integrity accepted; fixed design cost rejected; no second process or production acceptance'))
print('Postcheck PASS',len(checks),'checks')
