from pathlib import Path
import hashlib,json,re,statistics,subprocess,tomllib
root=Path(__file__).resolve().parents[3]
raw=root/'.superpowers/pfi-direct-packing';out=root/'diagnostics/pfi-direct-packing/results';out.mkdir(exist_ok=True)
records=json.loads((raw/'validation.json').read_text());assert len(records)==9 and all(r['returncode']==0 for r in records)
processes=[]
for r in records:
 p=json.loads((raw/r['job']/'process.json').read_text());assert p['returncode']==0 and p['sources_unchanged'];processes.append(dict(job=r['job'],**p))
p=json.loads((raw/'production-kernel-O2'/'process.json').read_text())
assert p['returncode']==0 and p['sources_unchanged']
processes.append(dict(job='production-kernel-O2',**p))
rows=[]
for case in ('fast','medium','runtime'):
 docs={arm:tomllib.loads((raw/f'{case}-{arm}'/'results.toml').read_text()) for arm in ('baseline','candidate')}
 for arm,d in docs.items():
  for rel,digest in d['source_hashes'].items():
   content=subprocess.check_output(['git','show','43bb7a0:'+rel],cwd=root) if arm=='baseline' else (root/rel).read_bytes()
   assert hashlib.sha256(content).hexdigest()==digest,(case,arm,rel)
  (out/f'{case}-{arm}.toml').write_bytes((raw/f'{case}-{arm}'/'results.toml').read_bytes())
 assert len(docs['baseline']['cases'])==len(docs['candidate']['cases'])
 for a,b in zip(docs['baseline']['cases'],docs['candidate']['cases']):
  assert a.keys()==b.keys()
  assert {k:v for k,v in a.items() if k!='seconds_instrumented'}=={k:v for k,v in b.items() if k!='seconds_instrumented'},case
  assert hashlib.sha256(Path(a['input']).read_bytes()).hexdigest()==a['input_sha256']
  if a['status']=='OPTIMAL':assert a['original_feasible'] and b['original_feasible']
  rows.append(dict(case=case,algorithm=a['algorithm'],status=a['status'],iterations=a['iterations'],refactorizations=a['refactorizations'],baseline_seconds=a['seconds_instrumented'],candidate_seconds=b['seconds_instrumented'],identical=True))
logs=[];counts={}
for name in ('targeted','semantic'):
 s=(raw/name/'run.log').read_text();assert 'Test Failed' not in s and 'Error During Test' not in s
 counts[name]=sum(int(m[0]) for m in re.findall(r'\|\s+(\d+)\s+(\d+)\s+(?:[\dm.]+s)',s))
 lines=s.splitlines();logs.append(name+'\n'+'\n'.join(l for i,l in enumerate(lines) if l.startswith('Test Summary:') or (i and lines[i-1].startswith('Test Summary:'))))
(out/'test-summaries.txt').write_text('\n\n'.join(logs)+'\n')
for name in ('production-kernel','production-kernel-O2'):
 p=raw/name/'results.toml'
 if not p.exists():continue
 d=tomllib.loads(p.read_text());assert len(d['cases'])==24
 assert all(statistics.median(c['old_bytes'])==statistics.median(c['new_bytes']) for c in d['cases'])
 (out/(name+'.toml')).write_bytes(p.read_bytes())
 report={k:(min(v),max(v)) for k in ('sparse','dense') if (v:=[c['ratio'] for c in d['cases'] if c['density']==k])};print(name,report)
summary=dict(baseline='43bb7a0',assertions=counts,paired_cases=rows,processes=processes)
(out/'validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(assertions=counts,paired_cases=rows),indent=2))
