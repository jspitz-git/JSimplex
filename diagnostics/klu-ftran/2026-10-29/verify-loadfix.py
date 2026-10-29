from pathlib import Path
import json,tomllib,hashlib,statistics,csv,math,re,sys
D=Path(__file__).resolve().parent
checks=[]
def require(ok,msg):
 if not ok:raise ValueError(msg)
 checks.append(msg)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
r=tomllib.loads((D/'results-2.toml').read_text());p=json.loads((D/'comparison-2/guard/process.json').read_text());post=json.loads((D/'comparison-2/postflight.json').read_text());sup=json.loads((D/'comparison-2/supervisor.json').read_text())
require(r['completed'] is True and p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] and sup['accepted'] and not post['conflicts'],'guard result and host closure')
pins=json.loads((D/'launch-pins-2.json').read_text())
require(all(str(Path(k).resolve())==v['resolved'] and sha(k)==v['sha256'] for k,v in pins['inventory'].items()),'all immutable launch bindings')
log=(D/'comparison-2/guard/run.log').read_text();require('Error During Test' not in log and 'Test Failed' not in log and 'Fixed-base graph-local FTRAN' in log,'ordinary Test no failures')
cs=r['cases'];require(len(cs)==12 and sum(c['queries'] for c in cs)==489,'12 cases 489 actual/control queries')
require({c['id'] for c in cs}=={f'{h}-B{a}' for h in ['runtime-30000','runtime-40000','fast0507-1000'] for a in [0,80,160]}|{'coupled256-forced','dense256-native-only','irreducible256-native-only'},'exact case names')
rows=[];total=0
for c in cs:
 require(c['max_scaled_residual']<=c['tolerance']==min(1e-10,128*c['n']*2**-52) and c['max_native_relative_difference']<=1e-6,f"numeric bounds {c['id']}")
 require(len(c['enclosures'])==3 and all(q['residual_upper']<=q['allowed_lower'] for q in c['enclosures']),f"directed enclosure {c['id']}")
 require(sum(c['qualification_routes'])==2*c['queries'],f"two cold cycles {c['id']}")
 require(len(c['samples'])==15,f"sample count {c['id']}")
 for arm in ['native','full','local']:
  ss=sorted([s for s in c['samples'] if s['arm']==arm],key=lambda s:s['round'])
  require([s['round'] for s in ss]==list(range(1,6)) and all(s['calls']==8*c['queries'] and sum(s['paths'])==s['calls'] for s in ss),f"whole call counts {c['id']}/{arm}")
  require(all(s['compile_seconds']==s['recompile_seconds']==0 and math.isfinite(s['seconds']) and s['seconds']>0 and math.isfinite(s['checksum']) and s['bytes']>=0 and s['events']>=0 for s in ss),f"compiled measured fields {c['id']}/{arm}")
  for s in ss:rows.append(dict(case=c['id'],**s))
  total+=sum(s['calls'] for s in ss)
 require(c['candidate_memory']['owned_export_and_scratch_payload_bytes']>=c['reference_memory']['owned_export_and_scratch_payload_bytes'],f"extra retained payload explicit {c['id']}")
require(total==58680,'exact measured calls58680')
summary=[]
for c in cs:
 by={a:sorted([s for s in c['samples'] if s['arm']==a],key=lambda s:s['round']) for a in ['native','full','local']}
 base=by['native'];entry={'case':c['id'],'graph_eligible':c['candidate_memory']['graph_eligible'],'cold_routes':c['qualification_routes'],'zero_sign_differences':c['zero_sign_differences']}
 for arm in by:
  ss=by[arm];rat=[s['seconds']/b['seconds'] for s,b in zip(ss,base)]
  entry[arm]={'paired_ratio_median':statistics.median(rat),'ratio_min':min(rat),'ratio_max':max(rat),'median_us_per_call':statistics.median(s['seconds']/s['calls']*1e6 for s in ss),'bytes_per_batch':sorted(set(s['bytes'] for s in ss)),'events_per_batch':sorted(set(s['events'] for s in ss)),'gc_seconds':sum(s['gc_seconds'] for s in ss),'paths':ss[0]['paths'],'average_processed_blocks':ss[0]['processed_blocks']/ss[0]['calls'],'average_processed_weight':ss[0]['processed_weight']/ss[0]['calls']}
 entry['local_full_ratio_median']=statistics.median(s['seconds']/b['seconds'] for s,b in zip(by['local'],by['full']))
 entry['reference_memory']=c['reference_memory'];entry['candidate_memory']=c['candidate_memory']
 entry['warm_setup']=[s for s in r['preparation'] if s['case']==c['id'] and s['stage']=='warm-factor-and-private-context']
 summary.append(entry)
with (D/'samples-2.csv').open('x',newline='') as f:
 fields=['case','arm','round','seconds','bytes','events','calls','gc_seconds','compile_seconds','recompile_seconds','processed_blocks','processed_weight','checksum','paths'];w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
out={'accepted':True,'checks':checks,'launch_bindings':len(pins['inventory']),'measured_calls':total,'summary':summary,'guard_wall_seconds':p.get('elapsed_seconds'),'scope':'fixed-base entering-column FTRAN; no production integration or end-to-end solver speedup'}
(D/'analysis-2.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'accepted':True,'checks':len(checks),'cases':len(cs),'calls':total}))
