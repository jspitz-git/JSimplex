"""New fail-closed MA-P RHS auditor. Import is pure; no old audit imported."""
from pathlib import Path
import json,tomllib,hashlib,math,statistics,sys
D=Path(__file__).resolve().parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bindings_match(bindings):
 return bool(bindings) and all(Path(p).is_file() and sha(p)==v for p,v in bindings.items())

def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0

def validate_raw(raw,index):
 fixtures=read(D/'fixtures.json');cases=[f for f in fixtures if f['cost']]
 checks={'header':raw.get('index')==index and raw.get('errors')==[] and raw.get('ambient_restored') is True and finite(raw.get('load_seconds'))}
 costs=raw.get('costs',[])
 checks['exact64_ids']=len(costs)==64 and [c['id'] for c in costs]==[f['id'] for f in cases]
 checks.update(windows=True,compile_zero=True,preservation=True,outputs=True)
 for ci,(c,f) in enumerate(zip(costs,cases),1):
  expected=16*(1+f['n'])
  checks['preservation'] &= c.get('preserved') is True
  first=c.get('first',[])
  checks['outputs'] &= c.get('expected')==expected and len(first)==2 and [x['side'] for x in first]==['reference','candidate'] and all(finite(x['seconds']) for x in first)
  ws=c.get('windows',[]);checks['windows'] &= len(ws)==20
  for pos,w in enumerate(ws):
   pair=pos//2+1;order=pos%2+1;firstref=(index+ci+pair)%2==0
   side=('reference' if firstref else 'candidate') if order==1 else ('candidate' if firstref else 'reference')
   checks['windows'] &= w.get('pair')==pair and w.get('order')==order and w.get('side')==side and w.get('phase')==('warm' if pair<=3 else 'measured') and all(finite(w.get(k)) for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds')) and w['seconds']>0 and type(w['bytes'])==int and type(w['events'])==int
   checks['outputs'] &= w.get('checksum')==expected
   if pair>3:checks['compile_zero'] &= w.get('compile_seconds')==0 and w.get('recompile_seconds')==0
 records=raw.get('checks',[])
 if index==1:
  normal={'reference_oracle','candidate_oracle','reference_preservation','candidate_preservation','input_owners','retained_outputs','zero_identity','equal_sharing','precision','roundreject'}
  micro={'represented','detached_scratch','input_preserved'}
  ids=[f['id'] for f in fixtures]+['scratch-Rational{BigInt}-true','scratch-Rational{BigInt}-false','scratch-BigFloat-true','scratch-BigFloat-false','negative-snapshot']
  checks['correctness']=len(records)==117 and [r.get('id') for r in records]==ids and all(set(r.get('flags',{}))==(normal if i<112 else micro if i<116 else {'mutation_detected'}) and all(v is True for v in r['flags'].values()) for i,r in enumerate(records))
 else:checks['no_extra_correctness']=records==[]
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
  raw=tomllib.loads((out/'raw.toml').read_text())
  checks.update(validate_raw(raw,index))
  checks['loaded_paths_pinned']=bool(raw.get('loaded_paths')) and all(str(Path(p).resolve()) in {v['resolved'] for v in pins['inventory'].values()} for p in raw['loaded_paths'].values())
 except Exception as e:error=repr(e);checks['complete_schema']=False
 return dict(all_passed=all(checks.values()) and bool(checks),checks=checks,error=error,sha256={str(p):sha(p) for p in out.rglob('*') if p.is_file()})

def aggregate(raws):
 rows=[]
 for ci in range(64):
  ratios=[];processes=[];target='-general' in raws[0]['costs'][ci]['id'] or '-equal' in raws[0]['costs'][ci]['id']
  for raw in raws:
   c=raw['costs'][ci];ws=[w for w in c['windows'] if w['phase']=='measured'];ref=[w for w in ws if w['side']=='reference'];cand=[w for w in ws if w['side']=='candidate']
   r=[b['seconds']/a['seconds'] for a,b in zip(ref,cand)];ratios+=r
   pr=dict(ratio=statistics.median(r),reference_bytes=statistics.median(w['bytes'] for w in ref),candidate_bytes=statistics.median(w['bytes'] for w in cand),reference_events=statistics.median(w['events'] for w in ref),candidate_events=statistics.median(w['events'] for w in cand))
   pr['pass']=pr['ratio']<1 and pr['candidate_bytes']<pr['reference_bytes'] and pr['candidate_events']<pr['reference_events']
   processes.append(pr)
  med=statistics.median(ratios);wins=sum(r<1 for r in ratios)
  rows.append(dict(id=raws[0]['costs'][ci]['id'],target=target,median_ratio=med,min_ratio=min(ratios),max_ratio=max(ratios),mad=statistics.median(abs(r-med) for r in ratios),faster_pairs=wins,processes=processes,accepted=all(p['pass'] for p in processes) and med<=.95 and wins>=18))
 return rows

def main():
 if sys.argv[1:]!=['aggregate']:raise ValueError('aggregate only')
 stages=[read(D/f'audit-{i}.json') for i in (1,2,3)]
 if not all(s['all_passed'] and bindings_match(s['sha256']) for s in stages):raise ValueError('incomplete qualification or evidence drift')
 if not all(stage(i)['all_passed'] for i in (1,2,3)):raise ValueError('fresh stage validation failed')
 raws=[tomllib.loads((D/f'run-{i}/raw.toml').read_text()) for i in (1,2,3)];rows=aggregate(raws)
 record=dict(qualification_pass=True,accepted=all(r['accepted'] for r in rows),cases=rows,total_windows=3840,total_timed_calls=61440,measured_windows=2688,warm_windows=1152,gc_windows=sum(w['gc_seconds']>0 for r in raws for c in r['costs'] for w in c['windows']),sha256={str(p):sha(p) for i in (1,2,3) for p in (D/f'run-{i}/raw.toml',D/f'audit-{i}.json')})
 with (D/'aggregate.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print('accepted',record['accepted'],'passing',sum(r['accepted'] for r in rows),'of64')
if __name__=='__main__':main()
