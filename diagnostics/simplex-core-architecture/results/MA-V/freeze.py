from pathlib import Path
import hashlib,json,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-V';S=D.with_name('MA-S-2');U=D.with_name('MA-U')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((S/'pins.json').read_text());paths=set(old['inventory'])
# Fresh hashes for every runtime/dependency path, not a retroactive old launch pin.
paths|={str(p) for root in old['trees'] for p in Path(root).rglob('*') if p.is_file()}
local=['driver.jl','micro-batch.jl','tests-recorded.jl','guard-tests-recorded.jl','launcher.py','guard.py','supervisor.py','audit.py','schedule.json','commands.json','admission.md','work-ledger.md','source-check.json','source-check.py','review-fix-map.json','offline-tests-complete.json','offline-tests.py','supervisor-tests-final.json','supervisor-tests.py','entry.json','host.json','continuation-map.json','freeze.py']
paths|={str(D/n) for n in local}
paths|={str(U/n) for n in ['candidate.jl','reference.jl','instrumented.jl','fixtures.toml','tests.jl','guard-tests.jl','source-green.json','review.json','closure.json','publication.json']}
paths|={str(R/p) for p in ['diagnostics/simplex-core-architecture/MA-ROUNDING-GUARD-ADMISSION.md','diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','docs/superpowers/plans/2026-10-14-ma-rounding-guard.md','docs/superpowers/specs/2026-10-14-ma-rounding-guard-design.md']}
paths=sorted(paths);inventory={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=sha(p)) for p in paths}
save('required-paths.json',paths);save('pins.json',dict(files=paths,trees=old['trees'],inventory=inventory,inputs=[],created=time.time(),scope='MA-V prospective admission inventory; no new launch or retroactive old pins'))
save('freeze.json',dict(all_passed=True,file_count=len(paths),listed_bytes=sum(Path(p).stat().st_size for p in paths),sha256={str(D/n):sha(D/n) for n in ['freeze.py','pins.json','required-paths.json']}))
print('fresh files',len(paths))
