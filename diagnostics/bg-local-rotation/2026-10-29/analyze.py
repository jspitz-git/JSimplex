from pathlib import Path
import json,tomllib,hashlib,statistics,csv
D=Path(__file__).resolve().parent;d=tomllib.loads((D/'results-1.toml').read_text());run=D/'local-1';p=json.loads((run/'guard/process.json').read_text());sup=json.loads((run/'supervisor.json').read_text());post=json.loads((run/'postflight.json').read_text());pins=json.loads((D/'pins-2.json').read_text())
checks={'exit0':p['reason']=='exit0'and p['returncode']==0,'supervisor':sup['accepted'],'guardpins':p['pins_unchanged'],'99pins':len(pins['inventory'])==99 and all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256']for k,v in pins['inventory'].items()),'postflight':not post['conflicts'],'32cold':len(d['cold'])==32 and all(c['ok']and c['updates']==256 for c in d['cold']),'192windows':len(d['windows'])==192,'160measured':sum(not w['warm']for w in d['windows'])==160,'compile_zero':all(w['compile_seconds']==w['recompile_seconds']==0 for w in d['windows']if not w['warm'])}
summary=[]
for fixture in ['band','blocks','sparse','dense']:
 for backend in ['native','markowitz']:
  group=[c for c in d['cold']if(c['fixture'],c['backend'])==(fixture,backend)];checks[f'initial_{fixture}_{backend}']=len(group)==4 and len(set(c['initial_factor_hash']for c in group))==1
  for interval in [128,64]:
   for localized in [False,True]:
    key=(fixture,backend,interval,localized);c=next(c for c in group if c['interval']==interval and c['localized']==localized);ups=[x for x in c['trace']if x['event']=='update'];rs=[x for x in c['trace']if x['event']=='refactor'];ws=[w for w in d['windows']if(w['fixture'],w['backend'],w['interval'],w['localized'])==key and not w['warm']];orig=[w for w in d['windows']if(w['fixture'],w['backend'],w['interval'],w['localized'])==(fixture,backend,interval,False)and not w['warm']]
    checks['_'.join(map(str,key))]=len(ups)==256 and [x['step']for x in ups]==list(range(1,257))and len(rs)==256//interval-1 and len(ws)==5 and sorted(w['repetition']for w in ws)==list(range(1,6))and all(w['updates']==256 and w['refactors']==len(rs)for w in ws)
    checks['shape_'+'_'.join(map(str,key))]=all(x['triangular_upper']and x['finite_nonzero_diagonal']for x in ups)
    checks['no_invalid_endpoint_'+'_'.join(map(str,key))]=all(x['spike_last']>=x['leaving_position']for x in ups)
    ratios=[w['seconds']/next(b['seconds']for b in orig if b['repetition']==w['repetition'])for w in ws];med=lambda f:statistics.median(w[f]for w in ws)
    row=dict(fixture=fixture,backend=backend,interval=interval,localized=localized,seconds_median=med('seconds'),seconds_min=min(w['seconds']for w in ws),seconds_max=max(w['seconds']for w in ws),paired_median=statistics.median(ratios),paired_min=min(ratios),paired_max=max(ratios),bytes_median=med('bytes'),events_median=med('events'),retained_bytes_median=med('retained_bytes'),gc_seconds_total=sum(w['gc_seconds']for w in ws),u_peak=max(x['u_nonzero']for x in ups),u_final=ups[-1]['u_nonzero'],history_nonzero_final=ups[-1]['history_nonzero_coefficients'],history_records_final=ups[-1]['history_records'],history_nonzero_peak=max(x['history_nonzero_coefficients']for x in ups),storage_ratio_peak=max(x['storage_ratio_since_refactor']for x in ups),graph_peak=max(x.get('reachable_bytes',0)for x in c['trace']),span_median=statistics.median(x['spike_last']-x['leaving_position']for x in ups))
    for f in ['construct_seconds','ftran_seconds','btran_seconds','update_seconds','refactor_seconds','assembly_seconds']:row[f+'_median']=med(f)
    summary.append(row)
samples=[json.loads(x)for x in(run/'guard/resources.jsonl').read_text().splitlines()]
result=dict(accepted=all(checks.values()),checks=checks,summary=summary,process=dict(elapsed=p['elapsed_including_launch'],maxrss_kib=p['child_maxrss_kib'],min_available_kib=min(s['available_kib']for s in samples),swap_max=max(s['swap_used_kib']for s in samples)),raw_sha256=hashlib.sha256((D/'results-1.toml').read_bytes()).hexdigest())
with(D/'analysis-1.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
with(D/'summary.csv').open('x',newline='')as f:w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');w.writeheader();w.writerows(summary)
print('ACCEPTED',result['accepted'],'checks',len(checks),'process',result['process'])
print('fixture backend interval ratio range bytesratio eventsratio graphratio Upeak old->new historycoeff old->new')
for s in summary:
 if not s['localized']:continue
 b=next(x for x in summary if(x['fixture'],x['backend'],x['interval'],x['localized'])==(s['fixture'],s['backend'],s['interval'],False))
 print(s['fixture'],s['backend'],s['interval'],round(s['paired_median'],3),round(s['paired_min'],3),round(s['paired_max'],3),round(s['bytes_median']/b['bytes_median'],3),round(s['events_median']/b['events_median'],3),round(s['retained_bytes_median']/b['retained_bytes_median'],3),str(b['u_peak'])+'->'+str(s['u_peak']),str(b['history_nonzero_final'])+'->'+str(s['history_nonzero_final']))
if not result['accepted']:print('FALSE',[k for k,v in checks.items()if not v]);raise SystemExit(1)
