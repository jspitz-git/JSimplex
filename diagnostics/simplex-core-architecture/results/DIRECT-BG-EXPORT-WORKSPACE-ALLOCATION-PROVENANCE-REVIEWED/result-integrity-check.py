"""Independent provenance saved-result integrity; no auditor or Julia rerun."""
from pathlib import Path
import json,sys,tomllib,re,math
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
import evidence as e
run=D/'runs/profile300';out=run/'output';checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
cfg=c.config('profile300');s=c.rd(run/'sealed.json');pins=c.rd(run/'launch-pins.json');a=c.rd(run/'audit.json')
c.validate_sources();c.validate_environment();c.preparation();c.predecessor('profile300');ck('current_sources_environment_predecessor',True)
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG export allocation provenance admission','profile300');ck('exact_admission',True)
ck('sealed_launch_hashes_resolutions',c.guard.pins_match(s) and c.guard.pins_match(pins))
ck('exact_config',s['config']==cfg==c.rd(run/'config.json'))
ck('launch_membership',set(pins['files'])==set(s['files'])|{str(run/n) for n in ('sealed.json','admission.json','prehost.json')} and pins['trees']==s['trees'])
ck('seal_launch_inventory_identity',all(pins['inventory'].get(n)==v for n,v in s['inventory'].items()))
ck('raw_pins',c.rd(out/'pins.json')==pins)
files=sorted(str(p) for p in run.rglob('*') if p.is_file())
ck('audit_membership_and_hashes',set(a['sha256'])==set(files)-{str(run/'audit.json')} and c.bindings(a))
ck('exact22_regular_outputs',{p.name for p in out.iterdir()}==e.expected_names() and len(list(out.iterdir()))==22 and all(p.is_file() and not p.is_symlink() for p in out.iterdir()))
rows,counts=e.output_checks(out,cfg)
ck('complete_saved_output_exact_residuals',rows==a['profiles'] and counts==a['counts']==dict(profiles=16,observed_vectors=768,completed_lifecycles=80,constructors=80,refactors=160,updates=640,FTRAN=1280,BTRAN=640))
ck('one_shot_success',a['all_passed'] is True and a['pure_timeout'] is False and a['error']=='')
p=c.rd(out/'process.json');cur=c.rd(out/'current.json');iv=c.rd(run/'invocation.json');sup=iv['supervisor']
ck('clean_exit',p['returncode']==sup['returncode']==0 and p['reason']=='exit0' and sup['accepted'] is True and p['pins_unchanged'] is True)
ck('no_timeout_kill_cleanup',all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in sup)
ck('elapsed_bound',all(type(t) in (int,float) and math.isfinite(t) and 0<t<=300 for t in (iv['elapsed_seconds'],sup['elapsed_seconds'])))
ck('identity_linkage',cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'])
ck('command_linkage',p['command']==cur['command']==iv['command']==cfg['command'])
ck('hash_linkage',p['pins_sha256']==cur['pins_sha256']==iv['pins_sha256']==c.sha(run/'launch-pins.json') and iv['review_sha256']==c.sha(run/'admission.json') and iv['reservation_sha256']==c.sha(run/'reservation.json'))
ck('reservation',c.rd(run/'reservation.json')==dict(one_attempt=True,phase='profile300',command=cfg['command'],pins_sha256=c.sha(run/'launch-pins.json'),review_sha256=c.sha(run/'admission.json'),max_seconds=300))
ck('guard_command',iv['guard_command']==c.guard_command(cfg,run/'launch-pins.json',iv['monotonic_start']) and Path(iv['python']).resolve()==Path(sys.executable).resolve())
hosts=[c.rd(run/n) for n in ('host.json','prehost.json','posthost.json')];groups=hosts[-1]['groups']
ck('saved_hosts_identity',all(c.host_safe(h) and all(h[k]==s[k] for k in ('head','master','boot_id')) for h in hosts))
ck('256_groups_sessions',len(groups)==256 and set(s['groups'])<=set(groups) and all(p[role][k] in groups for role in ('runner','child') for k in ('pgid','sid')))
ck('process_identity',all(p[role]['boot_id']==s['boot_id'] and p[role]['start_ticks']>0 and p[role]['command'] for role in ('runner','child')))
res=[json.loads(v) for v in (out/'resources.jsonl').read_text().splitlines()]
ck('resources',bool(res) and all(not c.guard.pressure(v) for v in res+[p['terminal_memory']]) and p['child_maxrss_kib']>0)
log=(out/'run.log').read_text()+'\n'+(run/'launcher.log').read_text()
ck('no_warning_worldage_fatal',not re.search(r'warning|world[ -]age|FATAL PROFILE:|ERROR:|Traceback',log,re.I))
profiles=[tomllib.loads((out/f'profile-{i}.toml').read_text()) for i in range(1,17)];summaries=[];outer_types=[]
for i,x in enumerate(profiles,1):
 records=x['allocations'];outer=[z for z in records if not any(frame.startswith('lifecycle | ') for frame in z['stack'].splitlines())]
 inside=[z for z in records if z not in outer]
 ck(f'unique_full_type_size_stack_{i}',len({(z['type'],z['size'],z['stack']) for z in records})==len(records))
 ck(f'profile_total_{i}',sum(z['count'] for z in records)==x['profile_count'] and sum(z['count']*z['size'] for z in records)==x['profile_bytes'])
 ck(f'observed_compile_zero_{i}',all(x[k]['compile_seconds']==x[k]['recompile_seconds']==0 for k in ('ordinary','profiled')))
 ck(f'outer_harness_frame_{i}',all('macro expansion | ./timing.jl:707' in z['stack'] and 'profile_once | ' in z['stack'] for z in outer))
 ck(f'outer_harness_count_{i}',sum(z['count'] for z in outer)==(14 if x['side']=='reference' else 0))
 ck(f'no_CoreBox_{i}',not any(z['type']=='Core.Box' for z in records))
 outer_types.append(dict(id=i,records=[dict(type=z['type'],size=z['size'],count=z['count']) for z in outer]))
 summaries.append(dict(id=i,fixture=x['fixture'],backend=x['backend'],side=x['side'],ordinary_events=x['ordinary']['events'],
  profiled_gc_events=x['profiled']['events'],total_profile_count=x['profile_count'],outer_timed_records=sum(z['count'] for z in outer),
  lifecycle_heap_count=sum(z['count'] for z in inside),gc_minus_lifecycle_heap=x['profiled']['events']-sum(z['count'] for z in inside)))
pairs=[]
for j in range(8):
 r,v=summaries[2*j:2*j+2];delta=v['profiled_gc_events']-r['profiled_gc_events']
 ck(f'paired_count_reconciliation_{j}',delta==v['lifecycle_heap_count']-r['lifecycle_heap_count'] and r['gc_minus_lifecycle_heap']==v['gc_minus_lifecycle_heap'])
 ck(f'native_residual_or_Markowitz_zero_{j}',r['gc_minus_lifecycle_heap']==([171,183,171,180][j//2] if r['backend']=='native' else 0))
 pairs.append(dict(fixture=r['fixture'],backend=r['backend'],profiled_gc_delta=delta,lifecycle_heap_delta=v['lifecycle_heap_count']-r['lifecycle_heap_count'],equal_side_residual=r['gc_minus_lifecycle_heap']))
ck('ordinary_dense96_native_anomaly_preserved',summaries[12]['ordinary_events']==2826 and summaries[12]['profiled_gc_events']==2785 and all(x['ordinary_events']==x['profiled_gc_events'] for i,x in enumerate(summaries) if i!=12))
ck('only_corrected_profile_attempt',{q.name for q in (D/'runs').iterdir()}=={'profile300'})
A=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE')
ck('initial_rejected_still_unattempted',{q.name for q in (A/'runs/profile300').iterdir()}=={'host.json','config.json','sealed.json'})
h=c.full_host(groups);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
save(D/'result-review-host.json',h)
ck('fresh256_clear',c.host_safe(h) and len(h['groups'])==256 and set(h['groups'])==set(groups))
ck('fresh_refs_boot_resources',all(h[k]==s[k] for k in ('head','master','boot_id')) and not c.guard.pressure(h['memory']))
ck('remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and h['master']+'\trefs/heads/master' in h['remote'])
ck('final_launch_pins',c.guard.pins_match(s) and c.guard.pins_match(pins))
result=dict(all_passed=all(checks.values()),checks=checks,check_count=len(checks),counts=counts,elapsed_seconds=iv['elapsed_seconds'],child_maxrss_kib=p['child_maxrss_kib'],
 resources=dict(samples=len(res),minimum_available_kib=min(x['available_kib'] for x in res+[p['terminal_memory']]),maximum_swap_kib=max(x['swap_used_kib'] for x in res+[p['terminal_memory']])),
 profile_summary=summaries,pair_reconciliation=pairs,outer_harness_records=outer_types,sha256={f:c.sha(f) for f in files},
 scope='Independent saved-result integrity and count-boundary reconciliation; causal site report review remains separate; no Julia or auditor rerun')
save(D/'result-integrity-check.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),counts=counts,groups=len(groups),pairs=pairs)))
