"""New supplemental post-exit verification and descriptive cost statistics; no Julia."""
from pathlib import Path
import json,tomllib,hashlib,statistics,subprocess,time
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D';O=R/'.superpowers/simplex-core-architecture/S2-D/qualification-1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,o):
 with Path(p).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
pins=read(D/'launch-pins.json');audit=read(D/'audit.json');process=read(O/'process.json');host=read(E/'host-before.json');groups=set(host['groups'])|{process[k]['pgid'] for k in ['runner','child']};hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):hits.append({'pid':int(p.name),'pgid':int(v[2]),'sid':int(v[3]),'start_ticks':int(v[19]),'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
portable=E/'qualification-1';portable.mkdir()
rawpairs={}
for p in sorted(O.rglob('*')):
 if p.is_file():
  dest=portable/p.relative_to(O);dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(p.read_bytes())
  rawpairs[str(p)]={'portable':str(dest),'sha256':sha(p),'portable_sha256':sha(dest)}
resources=[json.loads(l) for l in (O/'resources.jsonl').read_text().splitlines()]
rows=[];all_samples=[]
spec=tomllib.loads((D/'fixtures.toml').read_text())
for fixture in spec['fixtures']:
 a=tomllib.loads((O/'raw'/(fixture['id']+'.toml')).read_text());s=a['samples'];all_samples+=s
 measured=[t for t in s if t['measured']];by={(t['round'],t['side']):t for t in measured}
 ratios=[by[(r,'candidate')]['seconds']/by[(r,'reference')]['seconds'] for r in range(5,13)];median=statistics.median(ratios)
 sides={side:{'window_seconds_median':statistics.median(t['seconds'] for t in measured if t['side']==side),'window_seconds_range':[min(t['seconds'] for t in measured if t['side']==side),max(t['seconds'] for t in measured if t['side']==side)],'bytes':sorted(set(t['bytes'] for t in measured if t['side']==side)),'allocations':sorted(set(t['allocations'] for t in measured if t['side']==side)),'gc_seconds':sorted(set(t['gc_seconds'] for t in measured if t['side']==side))} for side in ['reference','candidate']}
 rows.append({'fixture':fixture['id'],'m':fixture['m'],'n':fixture['n'],'nnz':len(fixture['rowval']),'paired_candidate_reference_ratios':ratios,'paired_median':median,'paired_range':[min(ratios),max(ratios)],'paired_MAD':statistics.median(abs(x-median) for x in ratios),'side_median_ratio':sides['candidate']['window_seconds_median']/sides['reference']['window_seconds_median'],'sides':sides})
raw=tomllib.loads((O/'raw/regression.toml').read_text());inv=read(D/'invocation.json');res=read(D/'attempt-reserved.json')
checks={
 'full826_current_resolved':len(pins['inventory'])==826 and all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()),
 'raw16_portable_byteidentical':len(rawpairs)==16 and all(v['sha256']==v['portable_sha256'] for v in rawpairs.values()),
 'audit21_allpass':len(audit['checks'])==21 and audit['all_passed'] is True and all(audit['checks'].values()) and audit['error'] is None,
 'audit_raw16_bindings':len(audit['raw_sha256'])==16 and all(sha(p)==h for p,h in audit['raw_sha256'].items()),
 'audit_invocation3_bindings':len(audit['invocation_sha256'])==3 and all(sha(p)==h for p,h in audit['invocation_sha256'].items()),
 'exit0_resource_terminal':process['reason']=='exit0' and process['returncode']==0 and process['pins_unchanged'] is True and process['elapsed_including_launch']<=180 and process['terminal_memory']['available_kib']>=6*1024**2 and process['terminal_memory']['swap_used_kib']<=1024**2,
 'full28_groups_AND_sessions_noJulia':len(groups)==28 and not hits,
 '655_and_seven_children':raw['counts']==dict(pass_=655) if False else raw['counts']=={'pass':655,'fail':0,'error':0,'broken':0} and [x['counts']['pass'] for x in raw['children']]==[90,40,416,34,16,31,28],
 'all192_true_3072_calls':len(all_samples)==192 and all(t['ok'] is True and t['calls']==16 for t in all_samples) and sum(t['calls'] for t in all_samples)==3072,
 '64warm128measured_compilezero':sum(t['measured'] for t in all_samples)==128 and all(t['compile_seconds']==0 and t['recompile_seconds']==0 for t in all_samples if t['measured']),
 'user6_unchanged':len(host['user'])==6 and all(sha(p)==v['sha256'] for p,v in host['user'].items()),
 'refs_unchanged':all(subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip()==ref for p,ref in read(D/'allowance.json')['refs'].items()),
 'actual_source_test_env_CI_master_equal':not subprocess.check_output(['git','diff','--name-only','master','--','src','test','.github','Project.toml'],text=True).strip(),
 'one_bound_reservation':inv['reservation_sha256']==sha(D/'attempt-reserved.json') and res['allowance_sha256']==sha(D/'allowance.json') and res['pins_sha256']==sha(D/'launch-pins.json'),
}
put(E/'cost-summary.json',{'rows':rows,'window_calls':16,'measured_pairs_per_fixture':8,'warm_windows':64,'measured_windows':128,'resources':{'samples':len(resources),'min_available_kib':min(t['available_kib'] for t in resources),'max_swap_used_kib':max(t['swap_used_kib'] for t in resources),'terminal':process['terminal_memory'],'elapsed_including_launch':process['elapsed_including_launch']},'scope':'Descriptive single-process whole-audit windows; no universal/end-to-end speedup or native allocation/free interpretation. GC counters may include native allocations. Setup/import/regression are outside these windows.'})
paths=[E/'postcheck.py',E/'cost-summary.json',D/'audit.json',D/'launch-pins.json',D/'allowance.json',D/'numerical-review.md',E/'admission-review-check.json',E/'seal-review.json',E/'prelaunch-host.json']
put(E/'postcheck.json',{'checks':checks,'all_passed':all(checks.values()),'raw_pairs':rawpairs,'host':{'time_ns':time.time_ns(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':sorted(groups),'matches':hits},'sha256':{str(p):sha(p) for p in paths},'scope':'Supplemental post-exit script, not a launch pin. Frozen admitted auditor ran once separately.'})
print(json.dumps({'checks':checks,'rows':rows,'resources':read(E/'cost-summary.json')['resources']},indent=2))
if not all(checks.values()):raise SystemExit(1)
