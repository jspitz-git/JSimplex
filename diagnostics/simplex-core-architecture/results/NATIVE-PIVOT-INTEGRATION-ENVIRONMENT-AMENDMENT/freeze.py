"""One-shot read-time amendment inventory; no stage or numerical admission."""
from control import *
files,groups=predecessor('integration');files=set(files)
validate_environment();verify_host(host())
files|={p for p in D.iterdir() if p.is_file()}
files-={STATUS,ROAD};files.add(D/'required-paths.json')
save(D/'required-paths.json',dict(paths=sorted(map(str,files)),scope='Exact required preparation membership, no launch admission'))
save(D/'preparation-pins.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Fresh read-time environment amendment preparation, no Julia or launch pins'))
print(dict(pins=len(files),environment_exact=True))
