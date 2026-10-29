from pathlib import Path
import sys,tomllib,json,statistics,csv,hashlib
D=Path(sys.argv[1]);data=tomllib.loads((D/'results-1.toml').read_text());checks={}
cs={c['id']:c for c in data.get('cases',[])};q=data.get('qualification',[]);samples=data.get('samples',[])
checks['completed']=data.get('completed') is True
checks['cases_12']=len(cs)==12
checks['cold_24']=len(q)==24 and len({(r['case'],r['arm']) for r in q})==24
checks['all_cold_pass']=all(r['passed'] for r in q)
checks['measured_120_warm_48']=sum(r['measured'] for r in samples)==120 and sum(not r['measured'] for r in samples)==48
checks['literal_call_counts']=data['counts']==dict(builds=196,forward=8522,transpose=4272)
checks['all_residuals']=all(all(0<=v<=cs[r['case']]['tolerance'] for v in r['residuals']) for r in [*q,*samples])
checks['all_directed']=all(e['passed'] and e['residual_upper']<=e['allowed_lower'] for r in q for e in r['directed'])
checks['known_points']=all(all(v<=1e-6 for v in r['known_point_error']) for r in q)
checks['growth_storage']=all(r['metadata']['growth']<=1e8 and sum(r['metadata'][k] for k in ['L_nnz','U_nnz','coupling_nnz'])<=5_000_000 for r in q)
checks['input_alias_refused']=all(r['metadata']['input_values_independent'] for r in q)
checks['compilezero']=all(r[k]['compile_seconds']==r[k]['recompile_seconds']==0 for r in samples if r['measured'] for k in ['factor','ftran','btran'])
checks['positive_native_reports']=all(0<r['metadata']['native_current_bytes']<=r['metadata']['native_peak_bytes'] for r in q)
checks['KLU_controls']=all(r['metadata']['control']==dict(tol=1.,btf=1,ordering=0,scale=1,maxwork=10.) for r in q if r['arm'].startswith('KLU'))
controls={r['case']:r['metadata'] for r in q if r['arm'].startswith('KLU')}
checks['irreducible_controls']=all(controls.get(k,{}).get('blocks')==1 and controls[k]['max_block']==256 and controls[k]['coupling_nnz']==0 for k in ['irreducible-sparse256','irreducible-dense256'])
checks['coupled_control']=controls.get('coupled-blocks256',{}).get('blocks')==32 and controls['coupled-blocks256']['coupling_nnz']>0
allrecords={};arms=['UMFPACK-one','KLU-BTF-AMD-one']
for r in samples:
 if r['measured']:allrecords.setdefault((r['case'],r['arm']),[]).append(r)
checks['rounds']=all(len(allrecords.get((c,a),[]))==5 and sorted(r['round'] for r in allrecords[c,a])==[3,4,5,6,7] for c in cs for a in arms)
checks['stable_outputs']=all(len({r['output_hash'] for r in v})==1 for v in allrecords.values())
process=json.loads((D/'comparison-1/guard/process.json').read_text());post=json.loads((D/'comparison-1/postflight.json').read_text())
checks['guard']=process['reason']=='exit0' and process['returncode']==0 and process['pins_unchanged'] and not post['conflicts']
pins=json.loads((D/'launch-pins.json').read_text());checks['launch_pins_unchanged']=all(str(Path(p).resolve())==h['resolved'] and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h['sha256'] for p,h in pins['inventory'].items())
summary=[];ratios=[]
for case,c in cs.items():
 for arm in arms:
  rr=allrecords.get((case,arm),[]);meta=next(r['metadata'] for r in q if r['case']==case and r['arm']==arm)
  row=dict(case=case,arm=arm,n=c['n'],nnz=c['nnz'],blocks=controls[case]['blocks'],max_block=controls[case]['max_block'],native_current=meta['native_current_bytes'],native_peak=meta['native_peak_bytes'],graph=meta['julia_graph_bytes'],L_nnz=meta['L_nnz'],U_nnz=meta['U_nnz'],F_nnz=meta['coupling_nnz'],growth=meta['growth'])
  for stage,div in [('factor',1),('ftran',64),('btran',32)]:
   for measure in ['seconds','bytes','events','gc_seconds']:
    row[stage+'_'+measure]=statistics.median(r[stage][measure]/div for r in rr) if rr else float('nan')
  summary.append(row)
 if allrecords.get((case,arms[0])) and allrecords.get((case,arms[1])):
  a={r['round']:r for r in allrecords[case,arms[0]]};b={r['round']:r for r in allrecords[case,arms[1]]}
  out=dict(case=case)
  for stage in ['factor','ftran','btran']:
   r=[b[i][stage]['seconds']/a[i][stage]['seconds'] for i in sorted(a)];m=statistics.median(r)
   out[stage]=dict(median=m,min=min(r),max=max(r),mad=statistics.median(abs(x-m) for x in r))
  ratios.append(out)
with (D/'summary.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
result=dict(scope='offline analysis; not retroactive launch pin',checks=checks,passed=all(checks.values()),counts=data['counts'],ratios=ratios,GC_seconds=sum(r[k]['gc_seconds'] for r in samples if r['measured'] for k in ['factor','ftran','btran']))
(D/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(not result['passed'])
