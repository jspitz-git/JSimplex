"""Supplement saved first-cost evidence only; never reruns Julia or the admitted auditor."""
from pathlib import Path
import sys,json,tomllib
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION';sys.path.insert(0,str(D))
import control_reviewed as c
run=D/'runs/cost1-300';out=run/'output';checks={}
def check(n,v):
 checks[n]=bool(v);c.require(v,n)
a=c.rd(run/'audit.json');check('original_audit_integrity_numerics_compile_pass',a.get('all_passed') is True and a.get('pure_timeout') is False and a['phase']=='cost1-300')
check('original_audit_evidence_unchanged',c.bindings(a))
c.preparation();c.validate_environment();c.validate_sources();c.predecessor('cost1-300');check('preparation_sources_runtime_green_lineage',True)
s=c.rd(run/'sealed.json');check('sealed_launch_inputs_unchanged',c.guard.pins_match(s) and c.guard.pins_match(c.rd(run/'launch-pins.json')))
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'dynamic BG matched cost admission','cost1-300');check('exact_admission',True)
raw=tomllib.loads((out/'raw.toml').read_text());check('complete_counts_threads_paths',raw==dict(phase='cost1-300',loaded=c.loaded_for(c.config('cost1-300')),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1))
check('audit_counts',a['counts']==dict(cells=8,windows=160,exact_residuals=3840) and len(a['cells'])==8)
windows=[tomllib.loads(p.read_text()) for p in out.glob('window-*.toml')];check('warm_measured_windows',len(windows)==160 and sum(w['measured'] for w in windows)==112)
check('measured_compile_zero',all(w['compile_seconds']==w['recompile_seconds']==0 for w in windows if w['measured']))
p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');check('exit_zero',p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True and inv['supervisor']['accepted'] is True)
check('inclusive300_limit',0<=inv['elapsed_seconds']<=300)
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];check('resource_guard_and_terminal',bool(resources) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
h=c.full_host(c.rd(run/'posthost.json')['groups']);check('fresh_groups_sessions_nojulia',not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']))
check('first_attempt_only',{x.name for x in (D/'runs').iterdir()}=={'cost1-300'})
check('no_second_process_selection',a['selection']==[] and a['manager_backend']==[])
summary=[]
for cell in a['cells']:
 st=cell['statistics'];states=cell['probe']['states']
 summary.append(dict(fixture=cell['fixture'],backend=cell['backend'],time_ratio=st['seconds']['paired_ratio']['median'],time_ratio_range=[st['seconds']['paired_ratio'][k] for k in ['minimum','maximum']],time_ratio_mad=st['seconds']['paired_ratio']['mad'],reference_seconds=st['seconds']['reference']['median'],candidate_seconds=st['seconds']['candidate']['median'],faster_pairs=st['faster_pairs'],bytes=[st['bytes'][side]['median'] for side in ['reference','candidate']],events=[st['events'][side]['median'] for side in ['reference','candidate']],final_graph=[st['retained_bytes'][side]['median'] for side in ['reference','candidate']],max_checkpoint_graph_ratio=max(z['graphs'][1]/z['graphs'][0] for z in states),gates={k:st[k] for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']},probe_counters=cell['probe']['counts'],max_capacity=max(z['capacity'] for z in states),max_live=max(z['live'] for z in states),max_arena_payload=max(z['requested_payload_bytes'] for z in states),nested_seconds=st['nested_seconds']))
viable=c.first_process_viable(a,c.rd(D/'inputs.json')['fixtures'])
check('second_process_gate_consistent',viable==all(all(z['gates'].values()) and z['faster_pairs']>=3 for z in summary))
log=(out/'run.log').read_text();warnings=[x for x in log.splitlines() if x.startswith('WARNING:')]
c.save(E/'posthost.json',h)
files=sorted([x for x in run.rglob('*') if x.is_file()]+[E/'postcheck.py',E/'posthost.json',E/'authorization.json',E/'entry.json'])
c.save(E/'postcheck.json',dict(all_passed=True,checks=checks,summary=dict(cells=summary,first_process_viable=viable,exit=0,elapsed_seconds=inv['elapsed_seconds'],resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),terminal_memory=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'],warnings=warnings,warm_windows=48,measured_windows=112,timed_exact_residuals=3840,probe_exact_residuals=576,measured_nonzero_gc_windows=sum(w['gc_seconds']>0 for w in windows if w['measured']),scope='First process only; integrity PASS is not cost acceptance, source API ledger not observed full native work; no native peak/public solver speedup proof'),sha256={str(x):c.sha(x) for x in files}))
print('Supplement PASS',len(checks),'first_process_viable',viable)
print(json.dumps(summary,indent=2))
if __name__=='__main__':pass
