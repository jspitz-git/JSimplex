"""New author rehash; no historical executable imports or reruns."""
from pathlib import Path
import hashlib,json
R=Path.cwd();H=Path(__file__).resolve().parent;pins={}
def sh(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 pins[str(p)]=h.hexdigest();return pins[str(p)]
c={}
for n,count in [('entry.json',15),('provenance.json',17)]:
 d=json.loads((H/n).read_text());c[n]=d['all_passed'] is True and len(d['checks'])==count and all(d['checks'].values()) and all(sh(p)==v for p,v in d['sha256'].items());sh(H/n)
report=R/'diagnostics/simplex-core-architecture/S6-TEST-MPS-FAILURE-PROVENANCE.md';plan=R/'docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md'
c['source_and_history_scope']=all(t in report.read_text() for t in ['conditional','runtime.mps','not a unique model identity','(!exhausted || !eligible_at_cutoff)','not peak/live memory'])
c['no_new_execution_admission']='no new numerical allowance' in plan.read_text() and 'Continue only when genuinely new' in plan.read_text()
for p in [report,plan,H/'read-failure.md',Path(__file__)]:sh(p)
with (H/'independent.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=pins),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,pins=len(pins))));assert all(c.values())
