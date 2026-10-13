from pathlib import Path
import json,hashlib,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def put(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((D/'admission-pins.json').read_text())['inventory']
if not all(sha(Path(p))==v['sha256'] for p,v in old.items()):raise SystemExit('old pins changed')
paths={Path(p) for p in old}|{p for p in D.rglob('*') if p.is_file()}|{R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION.md'}
required={str(p):sha(p) for p in sorted(paths)};put('required-paths-reviewed.json',required)
paths.add(D/'required-paths-reviewed.json')
inv={str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
put('admission-pins-reviewed.json',{'files':sorted(inv),'trees':[],'inputs':[],'inventory':inv,'created':time.time(),'scope':'corrected read-time OFFLINE admission only, NOT launch pins or allowance'})
put('review-fix-author.json',{'checks':{'all_original780_unchanged':len(old)==780,'fix5_pass':json.loads((D/'review-fix.json').read_text())['all_passed'],'synthetic32_pass':len(json.loads((D/'review-fix-tests.json').read_text())['checks'])==32 and json.loads((D/'review-fix-tests.json').read_text())['all_passed'],'full_reviewed_inventory':all(sha(Path(p))==v['sha256'] for p,v in inv.items()),'no_allowance':not (D/'allowance.json').exists()},'sha256':{str(D/n):sha(D/n) for n in ['freeze-reviewed.py','admission-pins-reviewed.json','required-paths-reviewed.json','review-fix.json','review-fix-tests.json']},'pins':len(inv)})
print('Reviewed inventory',len(inv),'synthetic checks',len(json.loads((D/'review-fix-tests.json').read_text())['checks']))
if not all(json.loads((D/'review-fix-author.json').read_text())['checks'].values()):raise SystemExit(1)
