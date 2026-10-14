from pathlib import Path
import json,hashlib,time
E=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((E/'pins.json').read_text());review=json.loads((E/'admission-review.json').read_text())
if not all(sha(p)==s for p,s in review['sha256'].items()):raise SystemExit('Initial reviewed bytes drift')
add=['audit_reviewed.py','launcher-reviewed.py','offline-tests-reviewed.py','offline-tests-reviewed.json','admission-reviewed.md','review-fix.py','review-fix-red.json','prepare-pins-reviewed.py','admission-review.md','admission-review.json','pins.json','required-paths.json','preparation-check.json','source-check.py','source-check.json']
files=sorted(set(old['files'])|{str(E/n) for n in add})
inv={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=sha(p)) for p in files}
if any(inv[p]!=v for p,v in old['inventory'].items()):raise SystemExit('Original inventory drift')
save(E/'required-paths-reviewed.json',files)
save(E/'pins-reviewed.json',dict(files=files,trees=old['trees'],inventory=inv,inputs=[]))
checks={'original4247_unchanged':len(old['inventory'])==4247 and all(inv[p]==v for p,v in old['inventory'].items()),'initial16review_bindings_unchanged':len(review['sha256'])==16 and all(sha(p)==s for p,s in review['sha256'].items()),'review_rejected_preserved':review['accepted'] is False and len(review['findings'])==2,'new65tests':len(json.loads((E/'offline-tests-reviewed.json').read_text())['checks'])==65 and json.loads((E/'offline-tests-reviewed.json').read_text())['all_passed'] is True,'no_launch_or_seal':not any((E/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3'])}
save(E/'review-fix-check.json',dict(checks=checks,all_passed=all(checks.values()),pin_count=len(files),readtime=time.time(),sha256={str(E/n):sha(E/n) for n in add+['pins-reviewed.json','required-paths-reviewed.json']}))
print(json.dumps(dict(checks=checks,pins=len(files))))
if not all(checks.values()):raise SystemExit(1)
