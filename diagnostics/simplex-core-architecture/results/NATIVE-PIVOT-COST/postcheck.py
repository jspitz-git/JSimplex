"""One-shot post-exit evidence checks and descriptive summary; no rerun."""
from pathlib import Path
import sys,json,tomllib,statistics,struct
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-COST-PREPARATION';R=D.parents[3];RUN=Q/'runs/cost';sys.path.insert(0,str(Q))
from control import rd,sha,save,require,bindings,full_host,validate_stage,config,git
import guard
checks={};a=rd(RUN/'audit.json');r=a['result'];inv=rd(RUN/'invocation.json');proc=rd(RUN/'output/process.json');sealed=rd(RUN/'sealed.json');pins=rd(RUN/'launch-pins.json')
checks['audit']=a['all_passed'] is True and a['error']=='' and bindings(a)
checks['sealed_pins']=guard.pins_match(sealed);checks['launch_pins']=guard.pins_match(pins)
checks['exit']=proc['returncode']==0 and inv['supervisor']['accepted'] is True and inv['elapsed_seconds']<=45
h=full_host(rd(RUN/'posthost.json')['groups']);save(D/'posthost.json',h);checks['groups']=not h['matches'] and len(h['groups'])==216
raw=tomllib.loads((RUN/'output/raw.toml').read_text());ws=[tomllib.loads((RUN/f'output/window-{i:03d}.toml').read_text()) for i in range(1,89)]
checks['counts']=raw['counts']==dict(construction=88,refactor=176,forward=2816,transpose=1408) and raw['windows']==88
checks['inputs']=raw['complete'] is True and raw['inputs_unchanged'] is True and raw['fatal']==''
checks['schedule']=[w['schedule'] for w in ws]==rd(Q/'inputs.json')['schedule']
measured=[w for w in ws if not w['schedule']['warm']];regions=['construction','refactor_fresh','refactor_spare','solve','total'];metrics=[w[k] for w in measured for k in regions]
checks['compile']=len(metrics)==320 and all(v['compile_time']==v['recompile_time']==0 for v in metrics)
checks['threshold_accuracy']=r['accuracy']=={'C':False,'P':True} and len(r['residuals'])==4224
checks['savedC']=r['unexplained_C_mismatch'] is False and all(m['matches_all_saved'] for m in r['saved_C_comparison'])
checks['solve_allocations']=all(w['solve']['bytes']==w['solve']['events']==0 for w in measured)
checks['stage75']=len(validate_stage(config('cost')))==75
checks['old_failed']=rd(Q.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green/audit.json')['all_passed'] is False
checks['no_other_run']={p.name for p in (Q/'runs').iterdir()}=={'cost'}
checks['actual_unchanged']=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce')
resources=[json.loads(s) for s in (RUN/'output/resources.jsonl').read_text().splitlines()]
checks['resources']=all(z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2 for z in resources+[proc['terminal_memory']])
byid={w['schedule']['id']:w for w in ws};accuracy={}
for v in r['residuals']:
 s=byid[v['window']]['schedule'];key=s['fixture']+':'+s['arm'];z=accuracy.setdefault(key,dict(total=0,passed=0,nonzero=0,max_ratio=0.))
 z['total']+=1;z['passed']+=int(v['passed']);z['nonzero']+=int(v['max_residual']!='0');z['max_ratio']=max(z['max_ratio'],v['ratio'])
comparisons={};outliers=[]
for key,z in r['paired_cost'].items():
 C=z['C'];P=z['P'];ratios=[P[str(i)]['seconds']/C[str(i)]['seconds'] for i in range(4,12)]
 med=statistics.median(ratios);stat=dict(median=med,minimum=min(ratios),maximum=max(ratios),mad=statistics.median(abs(x-med) for x in ratios))
 require(stat==z['summary'] and ratios==z['ratios'],'Saved statistics mismatch')
 comparisons[key]=dict(summary=stat,ratios=ratios,Cmedian_us=statistics.median(v['seconds'] for v in C.values())*1e6,Pmedian_us=statistics.median(v['seconds'] for v in P.values())*1e6)
 for metric in ['bytes','events']:
  diffs=[P[str(i)][metric]-C[str(i)][metric] for i in range(4,12)]
  comparisons[key][metric]=dict(Cmedian=statistics.median(v[metric] for v in C.values()),Pmedian=statistics.median(v[metric] for v in P.values()),paired_differences=diffs,minimum_delta=min(diffs),maximum_delta=max(diffs))
 for i,ratio in zip(range(4,12),ratios):
  if ratio>2 or ratio<.5:outliers.append(dict(series=key,round=i,ratio=ratio,C=C[str(i)],P=P[str(i)],scope='Descriptive ratio flag only, never exclusion'))
def num(t):return struct.unpack('>d',bytes.fromhex(t))[0]
factors={k:{**{n:v[n] for n in ['lnz','unz','graph_bytes','strategy','spare_W','spare_Wi']},'unit_bytes':num(v['info'][3]),'numeric_units':num(v['info'][40]),'peak_units':num(v['info'][41])} for k,v in r['factors'].items()}
summary=dict(accuracy=accuracy,comparisons=comparisons,ratio_flags=outliers,factors=factors,measured_regions=320,measured_gc_nonzero=[dict(schedule=w['schedule'],region=k,metrics=w[k]) for w in measured for k in regions if w[k]['gctime']!=0],inclusive_seconds=inv['elapsed_seconds'],resources=dict(samples=len(resources),min_available_kib=min(z['available_kib'] for z in resources),max_swap_kib=max(z['swap_used_kib'] for z in resources),terminal=proc['terminal_memory'],child_maxrss_kib=proc['child_maxrss_kib']),pins=dict(seal=len(sealed['files']),launch=len(pins['files']),audit=len(a['sha256'])),diagnostic_graph_bytes=raw['diagnostic_graph_bytes'])
save(D/'summary.json',summary)
files=[D/'postcheck.py',D/'posthost.json',D/'summary.json',RUN/'audit.json',RUN/'output/raw.toml',RUN/'output/process.json',RUN/'invocation.json',RUN/'sealed.json',RUN/'launch-pins.json',Q/'inputs.json']
save(D/'postcheck.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in files},scope='Post-exit supplemental checks, not launch pins or a numerical rerun'))
require(all(checks.values()),'Postcheck failed: preserve');print(json.dumps(dict(checks=len(checks),accuracy=accuracy,gc_nonzero=len(summary['measured_gc_nonzero']),ratio_flags=outliers,resources=summary['resources'],pins=summary['pins'],factors=factors),indent=2))
