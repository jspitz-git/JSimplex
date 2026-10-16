"""One-shot preparation inventory only. No stage, seal or numerical launch."""
from common import *
from control import predecessor
files,groups=predecessor('integration');files=set(files)
QOLD=Q.parent/'NATIVE-PIVOT-QUALIFICATION';runtime=rd(QOLD/'runtime-pins.json')['sha256']
for n,h in runtime.items():require(sha(path(n))==h,'Runtime/source drift '+n)
files|={path(n) for n in runtime}|{QOLD/'runtime-pins.json'}
files|={Path(e['source']) for e in rd(Q/'overlay-manifest.json')['candidate']}
files|={R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md'}
files|={R/n for n in rd(Q/'actual-baseline.json')['sha256']}
files|={p for p in Q.iterdir() if p.is_file()}
files-={STATUS,ROAD};files.add(Q/'required-paths.json')
save(Q/'required-paths.json',dict(paths=sorted(map(str,files)),scope='Exact preparation input membership including this list; not launch admission'))
save(Q/'preparation-pins.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Fresh read-time preparation pins only; all Julia UNEXECUTED'))
print(dict(files=len(files),runtime=len(runtime),all_read=True))
