"""New saved-result summary; never reruns an auditor or numerical process."""
from pathlib import Path
import sys,json,tomllib
Q=Path(__file__).resolve().parent;P=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-COST');sys.path.insert(0,str(P));import control as c
from analysis import first_process_viable
run=P/'runs/cost1-300';out=run/'output';outer=P/'outers/cost1-300';checks={}
def ck(n,v):checks[n]=bool(v)
a=c.rd(run/'audit.json');p=c.rd(out/'process.json');inv=c.rd(run/'invocation.json');cl=c.rd(run/'outer-closure.json');outcome=c.rd(outer/'outer-outcome.json');seal=c.rd(run/'sealed.json');launch=c.rd(run/'launch-pins.json')
ck('seal_launch_pins',c.guard.pins_match(seal) and c.guard.pins_match(launch))
ck('saved_audit_bindings',c.bindings(a));ck('external_closure',cl['all_passed'] is True and c.host_safe(cl['host']) and c.bindings(cl))
ck('outer_identity',outcome['identity']==seal['outer_identity']==cl['outer_identity'])
ck('preparation_publication_preserved',c.bindings(c.rd(P/'publication.json')))
ck('refs_unchanged',c.git('rev-parse','HEAD')=='e149671cd2c9560ae2a91b80614d36799b845240' and c.git('rev-parse','master')==c.MASTER)
ck('one_attempt',c.rd(run/'reservation.json')['one_attempt'] is True and (run/'reservation.json').is_file())
ck('no_second_or_longer_phase',not any((P/'runs'/n).exists() for n in ['cost2-300','cost1-600','cost2-600']))
files=sorted(out.glob('*.toml'));windows=sorted(out.glob('window-*.toml'));rows=[tomllib.loads(f.read_text()) for f in windows];resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
raw=tomllib.loads((out/'raw.toml').read_text()) if (out/'raw.toml').exists() else None
viable=first_process_viable(a,c.rd(P/'inputs.json')['fixtures'])
cells=[]
for z in a.get('cells',[]):
 st=z['statistics'];cells.append(dict(fixture=z['fixture'],backend=z['backend'],policy=z['policy'],time_ratio=st['seconds']['paired_ratio']['median'],time_range=[st['seconds']['paired_ratio'][k] for k in ['minimum','maximum']],time_mad=st['seconds']['paired_ratio']['mad'],reference_seconds=st['seconds']['reference']['median'],candidate_seconds=st['seconds']['candidate']['median'],bytes=[st['bytes'][s]['median'] for s in ['reference','candidate']],events=[st['events'][s]['median'] for s in ['reference','candidate']],retained_bytes=[st['retained_bytes'][s]['median'] for s in ['reference','candidate']],time_gate=st['time_median_gate'],allocation_gate=st['allocation_gate'],memory_gate=st['memory_gate'],probe_memory_gate=st['probe_memory_gate'],faster_pairs=st['faster_pairs'],coexistence_graph_peak=z['coexistence_graph_peak'],probe_counts=z['probe_counts']))
record=dict(all_passed=all(checks.values()),checks=checks,audit_all_passed=a.get('all_passed'),pure_timeout=a.get('pure_timeout'),audit_error=a.get('error'),first_process_viable=viable,process_returncode=p.get('returncode'),process_reason=p.get('reason'),outer_returncode=outcome.get('returncode'),windows=len(rows),measured_windows=sum(r['measured'] for r in rows),saved_window_outputs=sum(len(r['outputs']) for r in rows),raw=raw,cells=cells,counts=a.get('counts'),guard_elapsed=p.get('elapsed_including_launch'),supervisor_elapsed=inv['supervisor']['elapsed_seconds'],outer_elapsed=outcome.get('elapsed_with_checks_seconds'),child_maxrss_kib=p.get('child_maxrss_kib'),resource_samples=len(resources),minimum_available_kib=min(z['available_kib'] for z in resources),maximum_swap_kib=max(z['swap_used_kib'] for z in resources),terminal_memory=p.get('terminal_memory'),observed_compile=[r['compile_seconds'] for r in rows if r['measured']],observed_recompile=[r['recompile_seconds'] for r in rows if r['measured']],observed_gc=[r['gc_seconds'] for r in rows if r['measured']],scope='Post-exit supplemental evidence, not a launch pin; no auditor rerun; diagnostic integrity separate from all-eight cost acceptance; graph/RSS are not native allocations or native retention',sha256={str(f):c.sha(f) for f in [Q/'postcheck.py',run/'audit.json',out/'process.json',run/'invocation.json',run/'outer-closure.json',outer/'outer-outcome.json']+files})
c.save(Q/'postcheck.json',record)
print(json.dumps({k:record[k] for k in ['all_passed','audit_all_passed','pure_timeout','audit_error','first_process_viable','process_returncode','windows','measured_windows','counts','supervisor_elapsed','cells']}))
c.require(record['all_passed'],'Postcheck integrity failed; preserve and stop')
