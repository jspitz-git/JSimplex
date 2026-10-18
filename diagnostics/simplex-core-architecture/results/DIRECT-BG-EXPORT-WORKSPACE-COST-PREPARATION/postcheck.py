"""New saved-result author check; no Julia or admitted auditor rerun."""
from pathlib import Path
import sys,json,tomllib,statistics,math,re
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
r=D/'runs/cost1-300';o=r/'output';a=c.rd(r/'audit.json');s=c.rd(r/'sealed.json');ad=c.rd(r/'admission.json');iv=c.rd(r/'invocation.json');p=c.rd(o/'process.json');checks={}
def ck(v,n):checks[n]=bool(v)
ck(a['all_passed'] is True and a['pure_timeout'] is False and a['error']=='','correctness_integrity_audit')
raw=tomllib.loads((o/'raw.toml').read_text());ck(raw['completed'] and not raw['fatal'] and raw['cells']==8 and raw['windows']==160 and raw['phase']=='cost1-300','complete_raw_schedule')
ck(raw['threads']==raw['blas_threads']==1 and raw['loaded']==c.loaded_for(c.config('cost1-300')),'actual_loaded_paths_threads')
ck(a['counts']==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576),'output_counts')
ck(len(list(o.iterdir()))==199 and len(list(o.glob('window-*.toml')))==160,'exact_output_count')
rows=[tomllib.loads(f.read_text()) for f in o.glob('window-*.toml')];all_measured=[x for x in rows if x['pair']>=4]
ck(len(all_measured)==112 and all(x['compile_seconds']==x['recompile_seconds']==0 for x in all_measured),'112_compile_zero_measured_windows')
summary=[]
for i,cell in enumerate(a['cells'],1):
 st=cell['statistics'];rs=[tomllib.loads((o/f'window-{i}-{k}.toml').read_text()) for k in range(1,21)];pairs=[{x['side']:x for x in rs if x['pair']==k} for k in range(4,11)]
 ratios=[z['candidate']['seconds']/z['reference']['seconds'] for z in pairs]
 ck(statistics.median(ratios)==st['seconds']['paired_ratio']['median'] and sum(x<1 for x in ratios)==st['faster_pairs'],f'cell{i}_independent_paired_time')
 for key in ('bytes','events','retained_bytes'):
  ck(all(statistics.median([z[side][key] for z in pairs])==st[key][side]['median'] for side in ('reference','candidate')),f'cell{i}_{key}_medians')
 ck(all(z['candidate']['outputs']==z['reference']['outputs'] and z['candidate']['modes']==z['reference']['modes'] for z in pairs),f'cell{i}_paired_bits_modes')
 ck(st['time_median_gate']==(statistics.median(ratios)<=.95) and st['allocation_gate']==all(st[k]['candidate']['median']<=st[k]['reference']['median'] for k in ('bytes','events')),f'cell{i}_cost_predicates')
 ck(st['memory_gate'] and st['probe_memory_gate'] and all(10*z['candidate']['retained_bytes']<=11*z['reference']['retained_bytes'] for z in pairs),f'cell{i}_memory')
 summary.append(dict(fixture=cell['fixture'],backend=cell['backend'],paired_time_ratio=statistics.median(ratios),bytes_change=st['bytes']['candidate']['median']-st['bytes']['reference']['median'],events_change=st['events']['candidate']['median']-st['events']['reference']['median'],retained_ratio=st['retained_bytes']['candidate']['median']/st['retained_bytes']['reference']['median'],time_gate=st['time_median_gate'],allocation_gate=st['allocation_gate'],faster_pairs=st['faster_pairs']))
from analysis import first_process_viable
ck(not first_process_viable(a,c.rd(D/'inputs.json')['fixtures']) and sum(x['time_gate'] for x in summary)==2 and sum(not x['allocation_gate'] for x in summary)==3,'fixed_design_STOP_no_second_process')
ck(set(x.name for x in (D/'runs').iterdir())=={'cost1-300'},'only_one_cost_attempt')
ck(p['returncode']==0 and p['reason']=='exit0' and iv['supervisor']['accepted'] and iv['supervisor']['returncode']==0 and not iv['supervisor']['hard_timeout'] and 0<iv['elapsed_seconds']<=300,'exit_limit_supervisor')
pins=c.rd(r/'launch-pins.json');ck(all(Path(n).resolve(strict=True)==Path(v['resolved']) and c.sha(n)==v['sha256'] for n,v in pins['inventory'].items()),'all_launch_hashes_and_resolutions')
ck(c.bindings(ad) and c.bindings(ad,'evidence_sha256'),'admission_bindings')
log=(o/'run.log').read_text()+'\n'+(r/'launcher.log').read_text();ck(not re.search(r'warning|world[ -]age|FATAL COST:|ERROR:|Traceback',log,re.I),'no_warning_error')
res=[json.loads(x) for x in (o/'resources.jsonl').read_text().splitlines()];ck(bool(res) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in res+[p['terminal_memory']]),'resource_samples_terminal')
groups=c.rd(r/'posthost.json')['groups'];h=c.full_host(groups);c.save(D/'postcheck-host.json',h)
ck(c.host_safe(h) and h['boot_id']==s['boot_id'] and set(groups)<=set(h['groups']),'fresh_all_groups_sessions_no_Julia')
ck(h['head']==s['head'] and h['master']==c.MASTER,'refs_unchanged')
files=sorted(x for x in r.rglob('*') if x.is_file())+[Path(__file__),D/'postcheck-host.json']
out=dict(all_passed=all(checks.values()),checks=checks,sha256={str(f):c.sha(f) for f in files},summary=summary,resources=dict(samples=len(res),minimum_available_kib=min(x['available_kib'] for x in res),maximum_swap_kib=max(x['swap_used_kib'] for x in res),elapsed_seconds=iv['elapsed_seconds'],child_maxrss_kib=p['child_maxrss_kib']),scope='Correctness accepted; fixed design performance rejected; no second process or production integration')
c.save(D/'postcheck.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),resources=out['resources'],failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Postcheck failed; preserve')
