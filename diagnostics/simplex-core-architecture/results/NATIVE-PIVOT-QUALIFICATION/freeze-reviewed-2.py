"""New canonical offline manifest. Original842 manifest/review remain frozen."""
from common import *
require(rd(Q/'final-check-2.json')['all_passed'] is True,'Author checks')
original=rd(Q/'preparation-pins.json');require(bindings(original),'Original842 drift')
files={Path(n) for n in original['sha256']}|{p for p in Q.iterdir() if p.is_file()}
save(Q/'preparation-pins-reviewed.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Corrected offline package only; NO exact-stage admission or Julia execution.'))
print(dict(pins=len(files),julia_executed=False))
