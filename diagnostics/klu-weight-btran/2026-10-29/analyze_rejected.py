from pathlib import Path
import json,tomllib,hashlib,statistics,collections,re,csv,math
D=Path(__file__).resolve().parent;checks=[]
def need(v,m):
 if not v:raise ValueError(m)
 checks.append(m)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def stats(s,m):
 need(type(s['bytes'])is int and type(s['events'])is int and all(type(s[k])in(int,float)and math.isfinite(s[k])and s[k]>=0 for k in ['seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'])and s['seconds']>0,m+' observed fields')
 need(s['compile_seconds']==s['recompile_seconds']==0,m+' measured compilation zero')
r=tomllib.loads((D/'results-2.toml').read_text());proc=json.loads((D/'comparison-2/guard/process.json').read_text());post=json.loads((D/'comparison-2/postflight.json').read_text());sup=json.loads((D/'comparison-2/supervisor.json').read_text());pins=json.loads((D/'launch-pins-2.json').read_text())
need(proc['reason']=='exit1'and proc['returncode']==1 and sup['accepted']is False and proc['pins_unchanged']is True,'failed qualification guard is preserved')
need(not post['conflicts']and len(post['checked_groups'])==723,'full723 group/session closure')
need(r['completed']is True,'raw driver reached final serialization; not numerical acceptance')
for manifest in ['source-pins.json','launch-pins.json','launch-pins-2.json']:
 inv=json.loads((D/manifest).read_text())['inventory'];need(all(str(Path(k).resolve())==v['resolved']and sha(k)==v['sha256']for k,v in inv.items()),'all unchanged '+manifest+' hashes')
strict=json.loads((D/'strict-auditor-rejection.json').read_text());need(strict['returncode']==1 and 'guard completed and full host closure'in strict['stderr'],'complete acceptance auditor remains rejected')
log=(D/'comparison-2/guard/run.log').read_text();hist=collections.Counter()
for entry in log.split('Test Failed at ')[1:]:
 expr=re.search(r'Expression: (.*)',entry.split('Stacktrace:')[0]);need(expr is not None,'every failure has ordinary Test expression');hist[expr.group(1)]+=1
need(hist=={'weights!(trial, rows, stopper, mode)':18,'t.value':126,'t.value.ok':72,'coldstops[1] == coldstops[2] == coldstops[3]':1},'all217 failures exactly classified')
need('13816   217  14033'in log and '0 errored'in log,'ordinary Test13816pass217fail0error')
cs=r['cases'];expectednames={f'{h}-B{a}'for h in ['runtime-30000','runtime-40000','fast0507-1000']for a in [0,80,160]}|{'coupled64-forced','dense64-native-only','irreducible64-native-only'}
need(len(cs)==12 and {c['id']for c in cs}==expectednames and sum(c['sample_rows']for c in cs)==1344,'complete fixed case/row set')
summary=[];records=[];kernels=validwhole=invalidwhole=validinclusive=invalidinclusive=0
for c in cs:
 name=c['id'];n=c['n'];rows=c['sample_rows'];need(c['rows']==[1+(i*(n-1))//(rows-1)for i in range(rows)]and rows==min(n,128),name+' exact uniform row positions')
 need(c['max_scaled_residual']<=c['tolerance']==min(1e-10,128*n*2**-52) and c['max_native_relative_difference']<=1e-6 and c['direct_UMFPACK_checks']==3,name+' complete kernel cold oracles')
 need(c['policy']['max_refinements']==3 and c['policy']['solve_refinement']is False and c['policy']['adaptive_refactor']is False and c['policy']['hypersparse']is False,name+' unchanged native legacy policy')
 bad=name.startswith('runtime');actualcold=[sum(v)-v[2]for v in c['cold_paths']]
 need(actualcold==([1]*3 if bad else [rows]*3),name+' actual cold completed unit calls')
 if bad:need(all(all(x==1.0 for x in v)for v in c['cold_weights']),name+' initial ones are not published weight evidence')
 item=dict(case=name,n=n,requested_rows=rows,whole_handler_qualified=not bad,first_rejected_row_position=(1 if bad else None),cold_paths=c['cold_paths'],cold_stop_calls=c['cold_stops'],max_scaled_residual=c['max_scaled_residual'],max_relative_difference=c['max_native_relative_difference'],signed_zero_differences=c['signed_zero_differences'],memory=c['memory'])
 for category,rounds in [('kernel_samples',5),('samples',5),('inclusive_samples',3)]:
  raw=c[category];need(len(raw)==rounds*3,name+'/'+category+' observed sample count');by={}
  for arm in ['native','full','local']:
   ss=sorted([s for s in raw if s['arm']==arm],key=lambda s:s['round']);need([s['round']for s in ss]==list(range(1,rounds+1)),name+'/'+category+'/'+arm+' rounds')
   for s in ss:
    stats(s,name+'/'+category+'/'+arm);need(s['unit_calls']==rows and len(s['paths'])==7 and all(type(x)is int and x>=0 for x in s['paths']),name+'/'+category+' count types')
    if category=='kernel_samples':
     need(sum(s['paths'])==rows and math.isfinite(s['checksum']),name+' all kernel calls completed');actual=rows;valid=True;kernels+=rows
    else:
     need(s['generic_correction_calls']==s['paths'][2]and s['stop_calls']>=1,name+' correction/native route accounting')
     actual=sum(s['paths'])-s['generic_correction_calls'];need(actual==(1 if bad else rows),name+' actual handler workload vs requested');valid=not bad
     if category=='samples':
      if valid:validwhole+=actual
      else:invalidwhole+=1
     else:
      if valid:validinclusive+=actual
      else:invalidinclusive+=1
    records.append(dict(case=name,category=category,valid_complete=valid,requested_unit_calls=rows,actual_unit_calls=actual,**{k:v for k,v in s.items()if k!='unit_calls'}))
   by[arm]=ss
  if category=='kernel_samples'or not bad:
   item[category]={}
   for arm,ss in by.items():
    ratios=[s['seconds']/b['seconds']for s,b in zip(ss,by['native'])]
    item[category][arm]=dict(paired_ratio_median=statistics.median(ratios),ratio_min=min(ratios),ratio_max=max(ratios),median_ms=statistics.median(s['seconds']*1000 for s in ss),bytes=sorted({s['bytes']for s in ss}),events=sorted({s['events']for s in ss}),gc_seconds=sum(s['gc_seconds']for s in ss),paths=ss[0]['paths'])
  else:item[category]={'excluded':'native/full/local all returned false after first unit; never a128-row weight measurement'}
 summary.append(item)
need((kernels,validwhole,invalidwhole,validinclusive,invalidinclusive)==(20160,8640,90,5184,54),'actual complete kernel and partial-handler totals')
setup=r['setup'];need(len(setup)==108,'all108 setup windows retained');prep=[]
for c in cs:
 name=c['id'];by={}
 for arm in ['native-staged','shared-staged','original-FTRAN-unsplit']:
  ss=sorted([s for s in setup if s['case']==name and s['arm']==arm],key=lambda s:s['round']);need([s['round']for s in ss]==[1,2,3],name+'/'+arm+' setup rounds')
  for s in ss:
   stats(s,name+'/'+arm+'/setup')
   expected=set()if arm=='original-FTRAN-unsplit'else {'factor','scratch','reverse'}|({'extraction','metadata'}if arm=='shared-staged'and c['memory']['local']['graph_eligible']else set())
   need(set(s['stages'])==expected,name+'/'+arm+' stage keys')
   for key,v in s['stages'].items():stats(v,name+'/'+arm+'/'+key)
   need(sum(v['seconds']for v in s['stages'].values())<=s['seconds']*(1+1e-8)+1e-6,name+'/'+arm+' staged work inside total')
  by[arm]=dict(median_ms=statistics.median(s['seconds']*1000 for s in ss),bytes=sorted({s['bytes']for s in ss}),events=sorted({s['events']for s in ss}),stage_medians={k:dict(ms=statistics.median(s['stages'][k]['seconds']*1000 for s in ss),bytes=sorted({s['stages'][k]['bytes']for s in ss}),events=sorted({s['stages'][k]['events']for s in ss}))for k in ss[0]['stages']})
 ratios=[s['seconds']/o['seconds']for s,o in zip(sorted([s for s in setup if s['case']==name and s['arm']=='shared-staged'],key=lambda s:s['round']),sorted([s for s in setup if s['case']==name and s['arm']=='original-FTRAN-unsplit'],key=lambda s:s['round']))]
 prep.append(dict(case=name,arms=by,shared_over_unsplit_paired_median=statistics.median(ratios)))
profiles=tomllib.loads((D/'allocation-profile.toml').read_text())['profiles'];need(len(profiles)==2 and {p['arm']for p in profiles}=={'original-FTRAN-unsplit','shared-staged'},'both allocation profiles')
for p in profiles:
 need(p['sample_rate']==.01 and p['sampled_events']==sum(g['sampled_events']for g in p['groups'])and p['sampled_bytes']==sum(g['sampled_bytes']for g in p['groups']),'sample accounting '+p['arm'])
original=next(p for p in profiles if p['arm']=='original-FTRAN-unsplit');loop_samples=sum(g['sampled_events']for g in original['groups']if any(g['first_diagnostic_frame'].endswith('ftran.jl:'+str(k))for k in (37,39,40)))
with(D/'diagnostic-samples.csv').open('x',newline='')as f:
 fields=sorted({k for s in records for k in s});w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(records)
out=dict(diagnostic_accepted=True,whole_experiment_accepted=False,tests_passed=13816,tests_failed=217,failures=dict(hist),checks=checks,launch_bindings=134,complete_measured_kernel_calls=kernels,complete_measured_handler_calls=validwhole,rejected_whole_windows=invalidwhole,complete_measured_inclusive_calls=validinclusive,rejected_inclusive_windows=invalidinclusive,summary=summary,setup=prep,profile_original_loop_sample_events=loop_samples,profile_original_sample_events=original['sampled_events'],profile=profiles,scope='diagnostic classification of rejected run; no original gate waived, no rerun, no runtime whole-handler speed ratio')
(D/'diagnostic-analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'diagnostic_accepted':True,'whole_experiment_accepted':False,'checks':len(checks),'kernel_calls':kernels,'rejected_whole_windows':invalidwhole,'rejected_inclusive_windows':invalidinclusive,'loop_samples':loop_samples,'total_samples':original['sampled_events']}))
