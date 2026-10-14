"""New fail-closed MA-M auditor. Import is pure; no old audit imported."""
from pathlib import Path
import json,tomllib,hashlib,math,statistics,sys
D=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0

def validate_raw(raw,index,red=None,green=None):
 checks={};fixtures=read(D.parent/'MA-L/fixtures.json'); fixtures=fixtures['fixtures'] if isinstance(fixtures,dict) else fixtures
 cases=[f for f in fixtures if f['cost']]
 checks['header']=raw.get('index')==index and raw.get('errors')==[] and raw.get('ambient_restored') is True and raw.get('trace_cleared') is True
 checks['elapsed_fields']=all(finite(raw.get(k)) for k in ('load_seconds','qualification_seconds','first_calls_seconds','cost_body_seconds'))
 costs=raw.get('costs',[])
 checks['exact76_ids']=len(costs)==76 and [c['id'] for c in costs]==[f['id'] for f in cases]
 checks['windows']=True;checks['compile_zero']=True;checks['preservation']=True;checks['outputs']=True
 for ci,(c,f) in enumerate(zip(costs,cases),1):
  checks['preservation'] &= c.get('preservation_checks')==22 and c.get('class')==f['cost'] and c.get('expected') is f['expected']
  first=c.get('first',[])
  checks['outputs'] &= len(first)==2 and [x['side'] for x in first]==['reference','candidate'] and all(x['result'] is f['expected'] and finite(x['seconds']) for x in first)
  ws=c.get('windows',[]);checks['windows'] &= len(ws)==20
  for pos,w in enumerate(ws):
   pair=pos//2+1;order=pos%2+1;firstref=(index+ci+pair)%2==0
   side=('reference' if firstref else 'candidate') if order==1 else ('candidate' if firstref else 'reference')
   checks['windows'] &= w.get('pair')==pair and w.get('order')==order and w.get('side')==side and w.get('phase')==('warm' if pair<=3 else 'measured') and all(finite(w.get(k)) for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')) and w['seconds']>0 and type(w['bytes'])==int and type(w['events'])==int
   checks['outputs'] &= w.get('true_count')==128*int(f['expected'])
   if pair>3:checks['compile_zero'] &= w.get('compile_seconds')==0 and w.get('recompile_seconds')==0
 if index==1:
  rr=[] if red is None else red.get('records',[]);gr=[] if green is None else green.get('records',[])
  checks['red']=len(rr)==10 and sum(x['type']=='Pass' for x in rr)==8 and sum(x['type']=='Fail' for x in rr)==2 and all(x['type']=='Pass' or (x['type']=='Fail' and x['expression']=='MAL_TRACE[].scratch == 1') for x in rr)
  checks['green']=len(gr)==3787 and all(x['type']=='Pass' for x in gr)
 return checks

def stage(index):
 out=D/f'run-{index}';checks={};error=None
 try:
  invocation=read(D/f'invocation-{index}.json');res=read(D/f'reservation-{index}.json');proc=read(out/'process.json');pins=read(D/'pins.json');cmd=read(D/'commands.json')[str(index)]
  checks['process']=proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True and invocation['returncode']==0
  checks['command']=proc['command']==cmd and proc['cwd']==str(D.parents[3]) and res['command']==cmd and invocation['command'][-len(cmd):]==cmd
  checks['links']=invocation['reservation_sha256']==sha(D/f'reservation-{index}.json') and res['pins_sha256']==sha(D/'pins.json')==proc['pins_sha256'] and res['review_sha256']==sha(D/'admission-review.json') and res['host_sha256']==sha(D/f'prelaunch-{index}.json')
  checks['hard_cap']=finite(invocation['elapsed_seconds']) and invocation['elapsed_seconds']<=120 and proc['elapsed_including_launch']<=114
  checks['pins']=read(out/'pins.json')==pins and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
  samples=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]+[proc['terminal_memory']]
  checks['memory']=len(samples)>=2 and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples)
  raw=tomllib.loads((out/'raw.toml').read_text());red=tomllib.loads((out/'red.toml').read_text()) if index==1 else None;green=tomllib.loads((out/'green.toml').read_text()) if index==1 else None
  checks.update(validate_raw(raw,index,red,green))
 except Exception as e:error=repr(e);checks['complete_schema']=False
 return dict(all_passed=all(checks.values()) and bool(checks),checks=checks,error=error,sha256={str(p):sha(p) for p in out.rglob('*') if p.is_file()})

def aggregate(raws):
 rows=[]
 for ci in range(76):
  ratios=[];processes=[];target=raws[0]['costs'][ci]['class']=='target'
  for raw in raws:
   c=raw['costs'][ci];ws=[w for w in c['windows'] if w['phase']=='measured'];ref=[w for w in ws if w['side']=='reference'];cand=[w for w in ws if w['side']=='candidate']
   r=[b['seconds']/a['seconds'] for a,b in zip(ref,cand)];ratios+=r
   pr=dict(ratio=statistics.median(r),reference_bytes=statistics.median(w['bytes'] for w in ref),candidate_bytes=statistics.median(w['bytes'] for w in cand),reference_events=statistics.median(w['events'] for w in ref),candidate_events=statistics.median(w['events'] for w in cand))
   pr['pass']=(pr['ratio']<1 and pr['candidate_bytes']<pr['reference_bytes'] and pr['candidate_events']<pr['reference_events']) if target else (pr['ratio']<=1.02 and pr['candidate_bytes']<=pr['reference_bytes'] and pr['candidate_events']<=pr['reference_events'])
   processes.append(pr)
  med=statistics.median(ratios);wins=sum(r<1 for r in ratios)
  rows.append(dict(id=raws[0]['costs'][ci]['id'],target=target,median_ratio=med,min_ratio=min(ratios),max_ratio=max(ratios),mad=statistics.median(abs(r-med) for r in ratios),faster_pairs=wins,processes=processes,accepted=all(p['pass'] for p in processes) and (med<=.95 and wins>=18 if target else med<=1)))
 return rows

def main():
 if sys.argv[1:]!=['aggregate']:raise ValueError('aggregate only')
 stages=[read(D/f'audit-{i}.json') for i in (1,2,3)]
 if not all(s['all_passed'] for s in stages):raise ValueError('incomplete qualification')
 raws=[tomllib.loads((D/f'run-{i}/raw.toml').read_text()) for i in (1,2,3)];rows=aggregate(raws)
 record=dict(qualification_pass=True,accepted=all(r['accepted'] for r in rows),cases=rows,total_windows=4560,total_timed_calls=583680,measured_windows=3192,warm_windows=1368,gc_windows=sum(w['gc_seconds']>0 for r in raws for c in r['costs'] for w in c['windows']),sha256={str(p):sha(p) for i in (1,2,3) for p in (D/f'run-{i}/raw.toml',D/f'audit-{i}.json')})
 with (D/'aggregate.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print('accepted',record['accepted'],'passing',sum(r['accepted'] for r in rows),'of76')
if __name__=='__main__':main()
