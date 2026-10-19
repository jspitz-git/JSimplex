"""Exclusive diagnostic-only receipt; standard library, no subprocess or imported checks."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800-HARNESS');R=D.parents[3];RUN=D/'runs/red1800';O=D/'outers/red1800'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
c=rd(E/'independent-result-check.json');assert c['all_passed'] is True and c['qualification_accepted'] is False and c['count']==15221
assert sha(E/'independent-result-check.py')==c['checker_sha256']
raw={str(p):sha(p) for root in [RUN,O] for p in sorted(root.rglob('*')) if p.is_file()}
assert raw==c['sha256'] and len(raw)==48 and not (RUN/'result-review.json').exists()
a=rd(RUN/'audit.json');assert a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Exact payload membership')"
assert sha(E/'outer.log')=='42f70b133c9a6a56ee1ade2112ca0b242c22e378e71d8c7f83287752e005d65b'
for n in ['independent-result-check.py','independent-result-check.json','independent-result-review.md','independent-result-publication.py']:
 text=(E/n).read_text();assert text.endswith('\n') and not text.endswith('\n\n') and all(line==line.rstrip() for line in text.splitlines())
# Verify local symbolic refs without Git subprocess or network access.
gd=Path((R/'.git').read_text().strip().removeprefix('gitdir: '));common=(gd/(gd/'commondir').read_text().strip()).resolve()
head=(gd/'HEAD').read_text().strip();assert head=='ref: refs/heads/codex/simplex-core-architecture'
assert (common/head.removeprefix('ref: ')).read_text().strip()=='cc9d35dc3e2c526bcae8b752ca2ea43dad9a5212'
assert (common/'refs/heads/master').read_text().strip()=='26e2291745999f485a74f643298ca997d65c7205'
save(E/'independent-result-publication.json',dict(all_passed=True,qualification_accepted=False,raw_files=48,sha256=raw,checker_sha256=sha(E/'independent-result-check.py'),checker_result_sha256=sha(E/'independent-result-check.json'),review_sha256=sha(E/'independent-result-review.md'),scope='Final independent raw and review binding verification; diagnostic only'))
files=[p for p in E.iterdir() if p.is_file() and p.name!='result-review.json']
files += [D/n for n in ['ADMISSION.md','MEMORY-WORK.md','independent-review.md','control.py','audit.py','oracle.py','driver.jl','guard.py','supervisor.py','numerical-tests.jl','lifecycle-tests.jl','panel-tests.jl','schedule.json','assertion-sites.json','copied-files.json','control-transform.json']]
files += [R/'AGENTS.md',R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md',R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md']
evidence={str(p):sha(p) for p in sorted(files)}
save(E/'result-review.json',dict(accepted=True,qualification_accepted=False,findings=[],scope='BG blocked typed RED1800 OOM diagnostic',phase='red1800',sha256=raw,evidence_sha256=evidence))
print(json.dumps(dict(accepted=True,qualification_accepted=False,raw_bindings=len(raw),evidence_bindings=len(evidence),receipt_sha256=sha(E/'result-review.json'))))
