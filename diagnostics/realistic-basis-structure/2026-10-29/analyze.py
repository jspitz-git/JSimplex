from pathlib import Path
import json,tomllib,hashlib,statistics,csv,sys
D=Path(__file__).resolve().parent;d=tomllib.loads((D/'results-1.toml').read_text());run=D/'realistic-1'
p=json.loads((run/'guard/process.json').read_text());sup=json.loads((run/'supervisor.json').read_text());post=json.loads((run/'postflight.json').read_text());pins=json.loads((D/'pins.json').read_text())
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
checks={'exit0':p['reason']=='exit0'and p['returncode']==0,'supervisor':sup['accepted'],'guard_pins':p['pins_unchanged'],'101pins':len(pins['inventory'])==101 and all(digest(k)==v['sha256']for k,v in pins['inventory'].items()),'postflight':not post['conflicts'],'4cases':len(d['cases'])==4,'12basisprofiles':sum(len(c['basis_profiles'])for c in d['cases'])==12,'32cold':len(d['cold'])==32 and all(c['ok']and c['updates']==160 for c in d['cold']),'192windows':len(d['windows'])==192,'160measured':sum(not w['warm']for w in d['windows'])==160,'compile_zero':all(w['compile_seconds']==w['recompile_seconds']==0 for w in d['windows']if not w['warm']),'320spikeprofiles':sum(len(c['spike_profiles'])for c in d['cold'])==320}
witness=json.loads((D/'witness-verification.json').read_text());checks['saved_witnesses']=witness['accepted'] and witness['raw_sha256']==digest(D/'results-1.toml')
summary=[]
for case in ['runtime-30000','runtime-40000','fast0507-1000']:
 backends=['native','markowitz']if case=='fast0507-1000'else['native']
 for backend in backends:
  group=[c for c in d['cold']if(c['case'],c['backend'])==(case,backend)]
  checks['initial_'+case+backend]=len(group)==8 and len(set(c['initial_factor_hash']for c in group))==1
  for c in group:
   key=(case,backend,c['mode'],c['interval']);ups=[r for r in c['trace']if r['event']=='update'];refs=[r for r in c['trace']if r['event']=='refactor'];ws=[w for w in d['windows']if(w['case'],w['backend'],w['mode'],w['interval'])==key and not w['warm']]
   checks['_'.join(map(str,key))]=len(ups)==10 and [r['step']for r in ups]==list(range(16,161,16))and len(refs)==(1 if c['interval']==80 else 0)and len(ws)==5 and sorted(w['repetition']for w in ws)==list(range(1,6))and all(w['updates']==160 and w['refactors']==len(refs)for w in ws)and all(r['triangular_upper']and r['factor_storage_count']<=5_000_000 for r in ups)
   modebase='BG'if c['mode']=='BG-local'else'SS'
   base=[w for w in d['windows']if(w['case'],w['backend'],w['mode'],w['interval'])==(case,backend,modebase,c['interval'])and not w['warm']]
   pair=[w['seconds']/next(b['seconds']for b in base if b['repetition']==w['repetition'])for w in ws];med=lambda f:statistics.median(w[f]for w in ws)
   graph=c['spike_profiles'];sizes=[g['profile']['largest_block']for g in graph];spans=[g['spike_last']-g['position']+1 for g in graph]
   row=dict(case=case,backend=backend,mode=c['mode'],interval=c['interval'],seconds_median=med('seconds'),seconds_min=min(w['seconds']for w in ws),seconds_max=max(w['seconds']for w in ws),relative_mode=modebase,paired_median=statistics.median(pair),paired_min=min(pair),paired_max=max(pair),bytes_median=med('bytes'),events_median=med('events'),retained_bytes_median=med('retained_bytes'),gc_seconds_total=sum(w['gc_seconds']for w in ws),u_peak_sampled=max(r['u_nonzero']for r in ups),u_final=ups[-1]['u_nonzero'],history_stored_peak_sampled=max(r['history_stored_coefficients']for r in ups),history_stored_final=ups[-1]['history_stored_coefficients'],factor_storage_peak_sampled=max(r['factor_storage_count']for r in ups),storage_ratio_peak_sampled=max(r['storage_ratio_since_refactor']for r in ups),largest_spike_block_median=statistics.median(sizes),largest_spike_block_max=max(sizes),rotation_span_median=statistics.median(spans),spike_profiled=10,spike_pure_permutation=sum(g['profile']['permutation_triangularizable']for g in graph),zero_spike_diagonal=sum(g['spike_diagonal_zero']for g in graph),graph_seconds_total=sum(g['seconds']for g in graph),graph_bytes_total=sum(g['bytes']for g in graph),normwise_residual_max=max(max(r['forward_residual'],r['transpose_residual'])for r in ups))
   for f in ['construct_seconds','ftran_seconds','btran_seconds','update_seconds','refactor_seconds','assembly_seconds']:row[f+'_median']=med(f)
   summary.append(row)
checks['16coldresets']=sum(c['refactors']for c in d['cold'])==16
checks['80measuredresets']=sum(w['refactors']for w in d['windows']if not w['warm'])==80
samples=[json.loads(x)for x in(run/'guard/resources.jsonl').read_text().splitlines()]
result={'accepted':all(checks.values()),'checks':checks,'summary':summary,'cases':d['cases'],'process':dict(elapsed=p['elapsed_including_launch'],maxrss_kib=p['child_maxrss_kib'],min_available_kib=min(s['available_kib']for s in samples),swap_max=max(s['swap_used_kib']for s in samples)),'witness_verified':witness['verified_witnesses'],'witness_omitted':len(witness['omitted_witnesses']),'raw_sha256':digest(D/'results-1.toml')}
with(D/'analysis-1.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
with(D/'summary.csv').open('x',newline='')as f:w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator='\n');w.writeheader();w.writerows(summary)
print('ACCEPTED',result['accepted'],'checks',len(checks),'process',result['process'])
print('BTF profiles case step n blocks singleton largest coupling')
for c in d['cases']:
 for v in c['basis_profiles']:
  x=v['profile'];print(c['id'],v['step'],x['dimension'],x['blocks'],x['singletons'],x['largest_block'],x['coupling_nnz'])
print('case backend mode interval whole_ms bytesKiB events graphKiB sampledUpeak historyEnd spikeBlockMedian rotationSpanMedian modeRatio')
for s in summary:print(s['case'],s['backend'],s['mode'],s['interval'],round(s['seconds_median']*1000,2),round(s['bytes_median']/1024,1),s['events_median'],round(s['retained_bytes_median']/1024,1),s['u_peak_sampled'],s['history_stored_final'],s['largest_spike_block_median'],s['rotation_span_median'],round(s['paired_median'],3))
if not result['accepted']:print('FALSE',[k for k,v in checks.items()if not v]);raise SystemExit(1)
