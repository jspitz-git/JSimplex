"""Exclusive source-only closure. Do not rerun after publication."""
import hashlib,json,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[4];o=Path(__file__).resolve().parent;d=r/'diagnostics/simplex-core-architecture'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
a=json.loads((o/'source-contract.json').read_text());i=json.loads((o/'independent.json').read_text());f=json.loads((o/'review-fix.json').read_text());h=json.loads((o/'host-after.json').read_text());b=json.loads((o/'host-before.json').read_text())
report='diagnostics/simplex-core-architecture/S3-DSE-CONSUMER-CONTRACT.md'
review=' '.join((d/'S3-DSE-CONSUMER-CONTRACT-REVIEW.md').read_text().split())
bound=all(sha(o/'report-before-review.md' if p==report else r/p)==v for p,v in i['sha256'].items())
c={'source_16_pass':a['all_passed'] and len(a['checks'])==16,'all53_pins_current':len(a['sha256'])==53 and all(sha(p)==v for p,v in a['sha256'].items()),'author9_pass':i['all_passed'] and len(i['checks'])==9,'author_bound_files_preserved':bound,'review_fix5_pass':f['all_passed'] and all(f['green'].values()) and all(sha(r/p)==v for p,v in f['sha256'].items()),'review_accepted':'Decision: ACCEPTED. No outstanding Critical, Important, or Minor findings.' in review,'host_groups_absent':not h['matches'] and h['boot_id']==b['boot_id'],'six_user_files':h['user_hashes']==b['user_hashes'] and all(sha(p)==v for p,v in h['user_hashes'].items()),'master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=r,text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298','source_test_ci_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=r).strip(),'continuation_no_launch':'No Julia launch authorization' in (d/'STATUS.md').read_text()}
paths=list(o.iterdir())+[d/'S3-DSE-CONSUMER-CONTRACT.md',d/'S3-DSE-CONSUMER-CONTRACT-REVIEW.md',d/'STATUS.md',r/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',r/'docs/superpowers/plans/2026-10-12-dse-mixed-route-qualification.md']
v={'checks':c,'all_passed':all(c.values()),'sha256':{str(p.relative_to(r)):sha(p) for p in paths if p.is_file()}}
with (o/'closure.json').open('x') as out:json.dump(v,out,indent=2);out.write('\n')
print(json.dumps({'checks':len(c),'all_passed':v['all_passed']}));raise SystemExit(0 if v['all_passed'] else 1)
