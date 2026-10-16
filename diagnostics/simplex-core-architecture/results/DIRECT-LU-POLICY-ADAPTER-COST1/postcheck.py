"""Saved first-process evidence summary only; no auditor or numerical rerun."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';sys.path.insert(0,str(D))
from control import rd,save,sha,full_host
run=D/'runs/cost1-300';out=run/'output';a=rd(run/'audit.json');p=rd(out/'process.json');inv=rd(run/'invocation.json')
h=full_host(rd(run/'posthost.json')['groups']);save(E/'postcheck-host.json',h)
raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
checks=dict(audit_accepted=a['all_passed'] is True and a['pure_timeout'] is False,exit0=p['returncode']==0 and p['reason']=='exit0' and inv['supervisor']['returncode']==0,pins_unchanged=p['pins_unchanged'] is True,limit300=0<inv['elapsed_seconds']<=300,no_live_groups_sessions_Julia=not h['matches'],no_second_or_retry=not any((D/'runs'/n).exists() for n in ['cost1-600','cost2-300','cost2-600']),full24cells=len(a.get('cells',[]))==24,output558=len(list(out.iterdir()))==558,raw_complete=raw is not None and raw.get('completed') is True)
summary=[]
for c in a.get('cells',[]):
 s=c['statistics'];summary.append({k:c[k] for k in ['fixture','manager','backend','policy']}|dict(paired_time=s['seconds']['paired_ratio'],faster_pairs=s['faster_pairs'],time_gate=s['time_median_gate'],allocation_gate=s['allocation_gate'],memory_gate=s['memory_gate'],reference_bytes=s['bytes']['reference']['median'],candidate_bytes=s['bytes']['candidate']['median'],reference_events=s['events']['reference']['median'],candidate_events=s['events']['candidate']['median'],reference_memory=s['retained_bytes']['reference']['median'],candidate_memory=s['retained_bytes']['candidate']['median']))
files=sorted(q for q in run.rglob('*') if q.is_file())+[Path(__file__)]
record=dict(all_passed=all(checks.values()),checks=checks,audit_error=a.get('error'),counts=a.get('counts'),summary=summary,elapsed=inv['elapsed_seconds'],resources=dict(samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_used_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=p['child_maxrss_kib'],terminal=p['terminal_memory']),sha256={str(q):sha(q) for q in files},scope='Saved first-process description; full numerical acceptance from admitted audit and independent review; no two-process performance selection')
save(E/'postcheck.json',record);print(json.dumps({k:v for k,v in record.items() if k!='sha256'},indent=2))
