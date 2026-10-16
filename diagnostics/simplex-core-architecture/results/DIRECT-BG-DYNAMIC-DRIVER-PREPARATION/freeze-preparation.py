"""One-shot OFFLINE inventory creation, never a phase seal."""
from control import *
def main():
 require(not (D/'runs').exists(),'No phase activity')
 require(rd(D/'source-check.json')['all_passed'] and rd(D/'offline-tests.json')['all_passed'],'Author checks')
 require(bindings(rd(D/'source-check.json')),'Author checked bytes')
 # Explicit scope includes all prepared files; reviewer-owned evidence is separately bound by final review.
 names=[p for p in D.iterdir() if p.is_file() and not p.name.startswith('reviewer-') and p.name not in ('review.json','review.md','required-paths.json','preparation-pins.json')]
 names += list(C.rglob('*'))
 names=[p for p in names if p.is_file()]
 names += [Path(n) for n in rd(D/'entry.json')['sha256']]
 names += [Path(v['source']) for v in rd(D/'reused-helpers.json').values()]
 names += [Path(n) for n in rd(D/'runtime-inputs-complete.json')['inventory']]
 names += [Path(v['path'])/n for v in rd(D/'stages.json').values() for n in v['sha256']]
 names += [root/n for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]]
 names=sorted(set(names+[D/'required-paths.json']))
 save(D/'required-paths.json',dict(scope='Exact preparation inputs; excludes future review/closure/publication and all run outputs',paths=[str(p) for p in names]))
 save(D/'preparation-pins.json',dict(scope='Offline preparation, not numerical admission or launch',sha256={str(p):sha(p) for p in names}))
 print('Preparation manifest',len(names),'files; no phase seal')
if __name__=='__main__':main()
