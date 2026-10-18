"""Independent saved-result checks; no auditor, old checker or Julia rerun."""
from pathlib import Path
import json,sys,tomllib,statistics,math,re,time
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
import evidence as e
import analysis as a
run=D/'runs/cost1-300';out=run/'output';checks={}
def ck(name,value):
    checks[name]=bool(value)
    if not value:raise AssertionError(name)
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def toml(p):return tomllib.loads(p.read_text())
cfg=c.config('cost1-300');sealed=c.rd(run/'sealed.json');pins=c.rd(run/'launch-pins.json');audit=c.rd(run/'audit.json')
c.validate_environment();c.validate_sources();c.preparation();c.predecessor('cost1-300')
ck('source_environment_predecessor',True)
ck('seal_config',sealed['config']==cfg==c.rd(run/'config.json'))
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',sealed['files']+[str(run/'sealed.json')],'BG export workspace cost admission','cost1-300')
ck('exact_admission',True)
ck('seal_and_launch_pins',c.guard.pins_match(sealed) and c.guard.pins_match(pins))
ck('launch_file_membership',set(pins['files'])==set(sealed['files'])|{str(run/n) for n in ('sealed.json','admission.json','prehost.json')} and pins['trees']==sealed['trees'])
ck('seal_launch_same_inventory',all(pins['inventory'].get(k)==v for k,v in sealed['inventory'].items()))
ck('raw_pins',c.rd(out/'pins.json')==pins)
actual_run={str(p) for p in run.rglob('*') if p.is_file()}
ck('audit_exact_preexisting_membership',set(audit['sha256'])==actual_run-{str(run/'audit.json')})
ck('audit_all_hashes',c.bindings(audit))
ck('exact_199_output_files',len(list(out.iterdir()))==199 and {p.name for p in out.iterdir()}==e.expected_names())
# Pure saved-output functions are used; audit.py and its one-shot writer are never called.
cells,counts=e.output_checks(out,cfg)
ck('all_saved_outputs_exact_residuals',cells==audit['cells'] and counts==audit['counts']==dict(cells=8,windows=160,window_outputs=3840,probe_outputs=576))
ck('audit_correctness_not_performance',audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']=='' and audit['selection']==audit['manager_backend']==[])
proc=c.rd(out/'process.json');cur=c.rd(out/'current.json');inv=c.rd(run/'invocation.json');sup=inv['supervisor'];reservation=c.rd(run/'reservation.json')
ck('successful_exit',proc['returncode']==sup['returncode']==0 and proc['reason']=='exit0' and sup['accepted'] is True and proc['pins_unchanged'] is True)
ck('no_timeout_or_cleanup',all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in sup)
ck('inclusive_300_seconds',all(type(t) in (int,float) and math.isfinite(t) and 0<=t<=300 for t in (inv['elapsed_seconds'],sup['elapsed_seconds'])))
ck('identity_linkage',cur['runner']==proc['runner']==sup['guard_identity'] and cur['child']==proc['child'])
ck('command_linkage',proc['command']==cur['command']==inv['command']==cfg['command'])
ck('pin_review_reservation_hashes',proc['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==c.sha(run/'launch-pins.json') and inv['review_sha256']==c.sha(run/'admission.json') and inv['reservation_sha256']==c.sha(run/'reservation.json'))
ck('reservation_exact',reservation==dict(one_attempt=True,phase='cost1-300',command=cfg['command'],pins_sha256=c.sha(run/'launch-pins.json'),review_sha256=c.sha(run/'admission.json'),max_seconds=300))
ck('guard_command',inv['guard_command']==c.guard_command(cfg,run/'launch-pins.json',inv['monotonic_start']) and Path(inv['python']).resolve()==Path(sys.executable).resolve())
hosts=[c.rd(run/n) for n in ('host.json','prehost.json','posthost.json')]
ck('saved_hosts_safe',all(c.host_safe(h) for h in hosts))
ck('saved_host_refs_boot',all(all(h[k]==sealed[k] for k in ('head','master','boot_id')) for h in hosts))
groups=hosts[-1]['groups']
ck('254_group_session_closure',len(groups)==254 and set(sealed['groups'])<=set(groups) and all(proc[role][k] in groups for role in ('runner','child') for k in ('pgid','sid')))
ck('process_start_identity',all(proc[role]['boot_id']==sealed['boot_id'] and proc[role]['start_ticks']>0 and proc[role]['command'] for role in ('runner','child')))
resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]
ck('resource_samples',bool(resources) and all(not c.guard.pressure(x) for x in resources+[proc['terminal_memory']]) and proc['child_maxrss_kib']>0)
log=(out/'run.log').read_text()+'\n'+(run/'launcher.log').read_text()
ck('no_warning_worldage_fatal',not re.search(r'warning|world[ -]age|FATAL COST:|ERROR:|Traceback',log,re.I))
summaries=[];all_rows=[];graph_ratios=[]
def stats(v):
    med=statistics.median(v)
    return dict(median=med,mad=statistics.median(abs(x-med) for x in v),minimum=min(v),maximum=max(v),values=v)
for i,cell in enumerate(cells,1):
 rows=[toml(out/f'window-{i}-{w}.toml') for w in range(1,21)];all_rows+=rows
 pairs=[{r['side']:r for r in rows if r['pair']==pair} for pair in range(4,11)]
 st=cell['statistics']
 for metric in ('seconds','bytes','events','retained_bytes','gc_seconds','compile_seconds','recompile_seconds'):
  rv=[p['reference'][metric] for p in pairs];cv=[p['candidate'][metric] for p in pairs]
  ck(f'stats_{i}_{metric}',st[metric]['reference']==stats(rv) and st[metric]['candidate']==stats(cv) and (not all(rv) or st[metric]['paired_ratio']==stats([y/x for x,y in zip(rv,cv)])))
 for phase in range(6):
  ck(f'nested_stats_{i}_{phase}',all(st['nested_seconds'][phase][side]==stats([p[side]['nested_seconds'][phase] for p in pairs]) for side in ('reference','candidate')))
 probe=toml(out/f'probe-{i}.toml')
 for state in probe['states']:
  graph_ratios.extend(g/state['graphs'][0] for g in state['graphs'][1:])
 ck(f'probe_counter_{i}',probe['counts']['triangle_checks']==probe['counts']['permutation_checks']==6 and probe['counts']['normalized_stores']==probe['counts']['index_stores'] and probe['counts']['raw_stores']==probe['counts']['fallback_stores']==0)
 summaries.append(dict(fixture=cell['fixture'],backend=cell['backend'],paired_time_median=st['seconds']['paired_ratio']['median'],
  paired_time_mad=st['seconds']['paired_ratio']['mad'],time_range=[st['seconds']['paired_ratio']['minimum'],st['seconds']['paired_ratio']['maximum']],
  bytes_delta=st['bytes']['candidate']['median']-st['bytes']['reference']['median'],events_delta=st['events']['candidate']['median']-st['events']['reference']['median'],
  faster_pairs=st['faster_pairs'],time_pass=st['time_median_gate'],allocation_pass=st['allocation_gate'],memory_pass=st['memory_gate'],
  final_graph_ratio=st['retained_bytes']['paired_ratio']['median'],cache_charge_peak=probe['cache_charge_peak'],coexistence_graph_peak=probe['coexistence_graph_peak']))
measured=[r for r in all_rows if r['measured']];warm=[r for r in all_rows if not r['measured']]
ck('112_measured_48_warm',len(measured)==112 and len(warm)==48)
ck('measured_compile_recompile_zero',all(r['compile_seconds']==r['recompile_seconds']==0 for r in measured))
ck('stop_all_eight_failed',not a.first_process_viable(audit,c.rd(D/'inputs.json')['fixtures']))
ck('six_time_three_allocation_failures',sum(not x['time_pass'] for x in summaries)==6 and sum(not x['allocation_pass'] for x in summaries)==3 and all(x['memory_pass'] for x in summaries))
ck('sparse96_markowitz_one_faster',summaries[5]['faster_pairs']==1)
ck('no_other_run',{p.name for p in (D/'runs').iterdir()}=={'cost1-300'})
h=c.full_host(groups);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
save(D/'cost1-result-host.json',h)
ck('fresh_all254_clear',c.host_safe(h) and set(h['groups'])==set(groups) and len(h['groups'])==254)
ck('fresh_refs_boot_resources',all(h[k]==sealed[k] for k in ('head','master','boot_id')) and not c.guard.pressure(h['memory']))
ck('fresh_remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and h['master']+'\trefs/heads/master' in h['remote'])
ck('final_pins_unchanged',c.guard.pins_match(sealed) and c.guard.pins_match(pins))
result=dict(all_passed=all(checks.values()),checks=checks,check_count=len(checks),correctness_accepted=True,performance_accepted=False,second_process_allowed=False,
 counts=counts,summary=summaries,max_probe_graph_ratio=max(graph_ratios),
 elapsed_seconds=inv['elapsed_seconds'],child_maxrss_kib=proc['child_maxrss_kib'],
 min_available_kib=min(x['available_kib'] for x in resources+[proc['terminal_memory']]),max_swap_kib=max(x['swap_used_kib'] for x in resources+[proc['terminal_memory']]),
 measured_gc_windows=[dict(cell=1+i//20,pair=r['pair'],side=r['side'],seconds=r['seconds'],gc_seconds=r['gc_seconds']) for i,r in enumerate(all_rows) if r['measured'] and r['gc_seconds']>0],
 warm_compile_seconds=sum(r['compile_seconds'] for r in warm),warm_recompile_seconds=sum(r['recompile_seconds'] for r in warm),
 scope='Independent saved-result verification only; no audit script, old checker or Julia execution',
 sha256={p:c.sha(p) for p in sorted(actual_run)})
save(D/'cost1-result-check.json',result)
print(json.dumps({k:result[k] for k in ('all_passed','check_count','counts','performance_accepted','second_process_allowed','max_probe_graph_ratio','measured_gc_windows')}))
