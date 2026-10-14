from pathlib import Path
import hashlib,json,time
D=Path(__file__).resolve().parent;R=D.parents[3];B=D.parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((B/'MA-V/pins.json').read_text());paths=set(old['inventory'])
# Current continuation bytes are preserved separately, not future mutable launch inputs.
cont={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')};paths-=cont
paths|={str(p) for root in old['trees'] for p in Path(root).rglob('*') if p.is_file()}
paths|={str(p) for p in D.iterdir() if p.is_file()}
paths|={str(B/'MA-W'/n) for n in ('review.json','review.md','evidence.json','closure.json','publication.json')}
paths.add(str(R/'docs/superpowers/plans/2026-10-14-ma-denselu-complete-qualification.md'))
paths=sorted(paths);inventory={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=sha(p)) for p in paths}
save('required-paths.json',paths);save('pins.json',dict(files=paths,trees=old['trees'],inventory=inventory,inputs=[],created=time.time(),scope='MA-X NEW prospective immutable admission; no launch, no retroactive pins; current continuation excluded and beforecopies included'))
checks=dict(unique=len(set(paths))==len(paths),complete=set(paths)==set(inventory),no_live_cont=not cont.intersection(paths),fresh=all(sha(p)==v['sha256'] for p,v in inventory.items()))
save('freeze.json',dict(all_passed=all(checks.values()),checks=checks,file_count=len(paths),tree_count=len(old['trees']),listed_bytes=sum(Path(p).stat().st_size for p in paths),sha256={str(D/n):sha(D/n) for n in ('freeze.py','pins.json','required-paths.json')}))
if not all(checks.values()):raise SystemExit(1)
print('frozen',len(paths),'files',len(old['trees']),'trees')
