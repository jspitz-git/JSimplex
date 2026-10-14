from pathlib import Path
import json,tomllib,statistics,hashlib
D=Path(__file__).resolve().parent
raws=[tomllib.loads((D/f'run-{i}/raw.toml').read_text()) for i in (1,2,3)]
agg=json.loads((D/'aggregate.json').read_text());fixtures=tomllib.loads((D.parent/'MA-R/fixtures.toml').read_text())['cost_cases'];rows=[]
for ci,f in enumerate(fixtures):
 pairs=[];per=[];allr=[];allc=[]
 for r in raws:
  windows=r['costs'][ci]['windows'];rw=[w for w in windows if w['phase']=='measured' and w['side']=='reference'];cw=[w for w in windows if w['phase']=='measured' and w['side']=='candidate']
  ratios=[c['seconds']/rr['seconds'] for rr,c in zip(rw,cw)];pairs.extend(ratios);allr.extend(rw);allc.extend(cw)
  rt=statistics.median(w['seconds']/4 for w in rw);ct=statistics.median(w['seconds']/4 for w in cw);rb=statistics.median(w['bytes'] for w in rw);cb=statistics.median(w['bytes'] for w in cw);re=statistics.median(w['events'] for w in rw);ce=statistics.median(w['events'] for w in cw)
  gates=dict(time=statistics.median(ratios)<1,bytes=cb<rb,events=ce<re) if f['eligible'] else dict(time=ct-rt<=max(.1*rt,.4e-6),bytes=cb<=rb,events=ce<=re)
  per.append(dict(reference_seconds_per_call=rt,candidate_seconds_per_call=ct,paired_median=statistics.median(ratios),reference_bytes_per_window=rb,candidate_bytes_per_window=cb,reference_events_per_window=re,candidate_events_per_window=ce,gates=gates))
 rt=statistics.median(w['seconds']/4 for w in allr);ct=statistics.median(w['seconds']/4 for w in allc);median=statistics.median(pairs);wins=sum(x<1 for x in pairs)
 pooled=(median<=.95 and wins>=15) if f['eligible'] else ct-rt<=max(.05*rt,.2e-6)
 accepted=pooled and all(all(p['gates'].values()) for p in per)
 rows.append(dict(id=f['id'],target=f['eligible'],median_ratio=median,pooled_time_pass=pooled,pooled_reference_seconds_per_call=rt,pooled_candidate_seconds_per_call=ct,faster_pairs=wins,accepted=accepted,processes=per))
checks={'52cases':len(rows)==52,'36targets':sum(r['target'] for r in rows)==36,'all_aggregate_decisions':all(r['accepted']==a['accepted'] and r['median_ratio']==a['median_ratio'] and r['faster_pairs']==a['faster_pairs'] for r,a in zip(rows,agg['cases'])),'48accepted':sum(r['accepted'] for r in rows)==48,'all36targets_pass':all(r['accepted'] for r in rows if r['target']),'12controls_pass':sum(r['accepted'] for r in rows if not r['target'])==12,'all_control_times_pass':all(r['pooled_time_pass'] and all(p['gates']['time'] for p in r['processes']) for r in rows if not r['target']),'correctness4329':raws[0]['counts']['qualification']==dict(pass_=4329) if False else raws[0]['counts']['qualification']=={'pass':4329,'fail':0,'error':0,'broken':0},'smoke16':raws[0]['counts']['smoke']=={'pass':16,'fail':0,'error':0,'broken':0},'160cases162calls':len(raws[0]['correctness'])==160 and sum(x['calls_per_side'] for x in raws[0]['correctness'])==162,'no_extra_correctness':all(r['correctness']==[] and r['counts']=={} and r['red']=={} for r in raws[1:]),'raw_no_errors':all(r['errors']==[] and r['ambient_restored'] is True for r in raws)}
ws=[w for r in raws for c in r['costs'] for w in c['windows']];measured=[w for w in ws if w['phase']=='measured']
checks.update(windows3120=len(ws)==3120,measured2184=len(measured)==2184,costcalls12480=sum(w['calls'] for w in ws)==12480,compilezero=all(w['compile_seconds']==0 and w['recompile_seconds']==0 for w in measured))
targets=[r for r in rows if r['target']];ratios=[r['median_ratio'] for r in targets];br=[p['candidate_bytes_per_window']/p['reference_bytes_per_window'] for r in targets for p in r['processes']];er=[p['candidate_events_per_window']/p['reference_events_per_window'] for r in targets for p in r['processes']]
paths=[D/'result-analysis.py',D/'aggregate.json',D.parent/'MA-R/fixtures.toml']+[D/f'run-{i}/raw.toml' for i in (1,2,3)]
o=dict(all_passed=all(checks.values()),qualification_accepted=False,checks=checks,cases=rows,target_paired_median_range=[min(ratios),max(ratios)],target_bytes_ratio_range=[min(br),max(br)],target_events_ratio_range=[min(er),max(er)],gc_windows=len([w for w in ws if w['gc_seconds']>0]),measured_gc_windows=len([w for w in measured if w['gc_seconds']>0]),sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
with (D/'result-analysis.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in o.items() if k not in ('cases','sha256')}))
if not o['all_passed']:raise SystemExit(1)
