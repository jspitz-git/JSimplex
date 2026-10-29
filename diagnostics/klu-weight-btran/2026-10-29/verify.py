from pathlib import Path
import json,tomllib,hashlib,statistics,csv,math,sys
D=Path(__file__).resolve().parent
checks=[]
def need(v,m):
 if not v:raise ValueError(m)
 checks.append(m)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def integer(x):return type(x)is int
def number(x):return type(x)in(int,float)and math.isfinite(x)
def stats(s,label):
 need(all(number(s[k])and s[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'])and s['seconds']>0,label+' finite stats')
 need(integer(s['bytes'])and integer(s['events']),label+' strict allocation types')
 need(s['compile_seconds']==s['recompile_seconds']==0,label+' no measured compilation')
def inverse():
 source=(D/'consumer-source.txt').read_text();whole=(D/'consumer.jl').read_text();i=whole.index('function original_weights!');j=whole.index('function weights!')
 original=whole[i:j][:-1].replace('original_weights!','_rebuild_recovery_weights!').replace('JSimplex.','')
 need(original==source,'byte exact original consumer inverse')
 subset=whole[j:].replace('function weights!(trial::JSimplex.SimplexWorkspace{T},rows,stop,mode::Val) where T','function _rebuild_recovery_weights!(trial::JSimplex.SimplexWorkspace{T},stop) where T').replace('for row in rows','for row in 1:m')
 subset=subset.replace('        unit_btran!(direction,trial.factorization.ctx,rhs,row,mode)','        fill!(rhs,zero(T))\n        rhs[row] = one(T)\n        JSimplex.transpose_solve!(direction,trial.factorization,rhs)').replace('JSimplex.','')
 need(subset==source,'byte exact subset producer consumer inverse')
 need(sha(D/'ftran.jl')==sha(D.parents[1]/'klu-ftran/2026-10-29/candidate-loadfix.jl'),'byte exact accepted forward loadfix copy')
 return source
# Path above D.parents[1] is diagnostics, checked deliberately.
if len(sys.argv)>1 and sys.argv[1]=='inverse':
 inverse();print(json.dumps({'accepted':True,'inverse_checks':len(checks)}));raise SystemExit
inverse()
r=tomllib.loads((D/'results-1.toml').read_text());p=json.loads((D/'comparison-1/guard/process.json').read_text());post=json.loads((D/'comparison-1/postflight.json').read_text());sup=json.loads((D/'comparison-1/supervisor.json').read_text())
need(r['completed']is True and p['reason']=='exit0'and p['returncode']==0 and p['pins_unchanged']is True and sup['accepted']is True and not post['conflicts'],'guard completed and full host closure')
pins=json.loads((D/'launch-pins.json').read_text())
need(all(str(Path(k).resolve())==v['resolved']and sha(k)==v['sha256']for k,v in pins['inventory'].items()),'every launch pin unchanged')
log=(D/'comparison-1/guard/run.log').read_text();need('Shared KLU unit transpose and weight handling' in log and 'Test Failed'not in log and 'Error During Test'not in log,'ordinary Test output without failures')
cs=r['cases'];names={f'{h}-B{a}'for h in ['runtime-30000','runtime-40000','fast0507-1000']for a in [0,80,160]}|{'coupled64-forced','dense64-native-only','irreducible64-native-only'}
need(len(cs)==12 and {c['id']for c in cs}==names and sum(c['sample_rows']for c in cs)==1344,'exact12 cases and1344 unit positions')
records=[];summary=[];wholecalls=kernelcalls=inclusivecalls=0
for c in cs:
 name=c['id'];n=c['n'];count=min(n,128);expected=[1+(i*(n-1))//(count-1)for i in range(count)]
 need(c['rows']==expected and c['sample_rows']==count and len(set(expected))==count,name+' exact uniform original-row schedule')
 need((n==28453 if name.startswith('runtime')else n==484 if name.startswith('fast')else n==64),name+' dimensions')
 need(c['max_scaled_residual']<=c['tolerance']==min(1e-10,128*n*2**-52)and c['max_native_relative_difference']<=1e-6,name+' residual and reference bounds')
 need(c['direct_UMFPACK_checks']==3 and integer(c['signed_zero_differences'])and c['signed_zero_differences']>=0,name+' independent reference and zero signs')
 weights=c['cold_weights'];need(len(weights)==3 and all(len(v)==count and all(number(x)and x>=1e-4 for x in v)for v in weights),name+' complete finite positive floored cold weights')
 need(all(abs(x-y)<=max(1e-12,1e-6*max(abs(x),abs(y)))for v in weights[1:]for x,y in zip(weights[0],v)),name+' cold scalar weight comparison')
 need(len(c['cold_stops'])==3 and len(set(c['cold_stops']))==1 and c['cold_stops'][0]>=count,name+' original stop ordering counts')
 need(c['policy']['max_refinements']==3 and c['policy']['solve_refinement']is False and c['policy']['hypersparse']is False and c['policy']['adaptive_refactor']is False,name+' native legacy policy unchanged')
 bycategory={}
 for category,rounds in [('samples',5),('kernel_samples',5),('inclusive_samples',3)]:
  ss=c[category];need(len(ss)==3*rounds,name+'/'+category+' sample count');by={}
  for arm in ['native','full','local']:
   arr=sorted([s for s in ss if s['arm']==arm],key=lambda s:s['round']);need([s['round']for s in arr]==list(range(1,rounds+1)),name+'/'+category+'/'+arm+' rounds')
   for s in arr:
    label=name+'/'+category+'/'+arm+'/'+str(s['round']);stats(s,label)
    need(integer(s['unit_calls'])and s['unit_calls']==count and len(s['paths'])==7 and all(integer(x)and x>=0 for x in s['paths']),label+' strict unit/path counts')
    if category=='kernel_samples':need(sum(s['paths'])==count and number(s['checksum']),label+' kernel output and routes')
    else:need(integer(s['generic_correction_calls'])and sum(s['paths'])==count+s['generic_correction_calls']and s['paths'][2]==s['generic_correction_calls']and integer(s['stop_calls'])and s['stop_calls']>=count,label+' complete correction and stop counts')
    records.append(dict(case=name,category=category,**s))
   by[arm]=arr
  bycategory[category]=by
  calls=sum(s['unit_calls']for s in ss)
  if category=='samples':wholecalls+=calls
  elif category=='kernel_samples':kernelcalls+=calls
  else:inclusivecalls+=calls
 out=dict(case=name,n=n,rows=count,graph_eligible=c['memory']['local']['graph_eligible'],signed_zero_differences=c['signed_zero_differences'],memory=c['memory'])
 for category,by in bycategory.items():
  out[category]={}
  for arm,arr in by.items():
   ratios=[s['seconds']/ref['seconds']for s,ref in zip(arr,by['native'])]
   out[category][arm]=dict(paired_ratio_median=statistics.median(ratios),ratio_min=min(ratios),ratio_max=max(ratios),median_ms=statistics.median(s['seconds']*1e3 for s in arr),bytes=sorted({s['bytes']for s in arr}),events=sorted({s['events']for s in arr}),gc_seconds=sum(s['gc_seconds']for s in arr),paths=arr[0]['paths'])
 summary.append(out)
need((wholecalls,kernelcalls,inclusivecalls)==(20160,20160,12096),'all three categories exact measured solve counts')
setup=r['setup'];need(len(setup)==108,'exact108 setup records');setupsummary=[]
for c in cs:
 name=c['id'];by={}
 for arm in ['native-staged','shared-staged','original-FTRAN-unsplit']:
  arr=sorted([s for s in setup if s['case']==name and s['arm']==arm],key=lambda s:s['round']);need([s['round']for s in arr]==[1,2,3],name+'/'+arm+' exact setup rounds')
  for s in arr:
   stats(s,name+'/'+arm+'/setup')
   for stage,v in s['stages'].items():stats(v,name+'/'+arm+'/'+stage)
   if arm=='original-FTRAN-unsplit':need(not s['stages'],name+' unsplit original control')
   else:
    required={'factor','scratch','reverse'}|({'extraction','metadata'}if arm=='shared-staged'and c['memory']['local']['graph_eligible']else set())
    need(set(s['stages'])==required,name+'/'+arm+' exact stages')
    need(sum(v['seconds']for v in s['stages'].values())<=s['seconds']*(1+1e-8)+1e-6,name+'/'+arm+' stage sum inside total')
  by[arm]=dict(median_ms=statistics.median(s['seconds']*1e3 for s in arr),bytes=sorted({s['bytes']for s in arr}),events=sorted({s['events']for s in arr}),stage_medians={stage:dict(ms=statistics.median(s['stages'][stage]['seconds']*1e3 for s in arr),bytes=sorted({s['stages'][stage]['bytes']for s in arr}),events=sorted({s['stages'][stage]['events']for s in arr}))for stage in arr[0]['stages']})
 setupsummary.append(dict(case=name,arms=by))
profile=tomllib.loads((D/'allocation-profile.toml').read_text());need({q['arm']for q in profile['profiles']}=={'original-FTRAN-unsplit','shared-staged'}and len(profile['profiles'])==2,'both setup allocation profiles')
for q in profile['profiles']:
 need(q['sample_rate']==0.01 and integer(q['sampled_events'])and q['sampled_events']>=0 and sum(g['sampled_events']for g in q['groups'])==q['sampled_events']and sum(g['sampled_bytes']for g in q['groups'])==q['sampled_bytes'],'profile recorded sample counts and bytes '+q['arm'])
with(D/'samples.csv').open('x',newline='')as f:
 fields=sorted({k for s in records for k in s});writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(records)
out=dict(accepted=True,checks=checks,launch_bindings=len(pins['inventory']),cases=12,unit_positions=1344,measured_whole_unit_calls=wholecalls,measured_kernel_unit_calls=kernelcalls,measured_inclusive_unit_calls=inclusivecalls,summary=summary,setup=setupsummary,profile=[dict(arm=q['arm'],sampled_events=q['sampled_events'],top_groups=q['groups'][:8])for q in profile['profiles']],scope='sampled algebraic complete weight handling; not full n-row rebuild or original LP trajectory')
(D/'analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(accepted=True,checks=len(checks),cases=12,whole_calls=wholecalls,kernel_calls=kernelcalls,inclusive_calls=inclusivecalls)))
