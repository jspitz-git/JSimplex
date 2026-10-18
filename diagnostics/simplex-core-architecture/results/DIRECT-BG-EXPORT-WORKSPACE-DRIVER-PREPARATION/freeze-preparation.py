"""One-shot exact offline preparation inventory, not a numerical seal."""
from control import *
PREP_NAMES=['ADMISSION.md', 'ASSERTION-INVENTORY.md', 'WORK-MEMORY.md', 'audit.py', 'author.py', 'authorization.json', 'baseline.json', 'control-lineage.json', 'control.py', 'driver.jl', 'entry.json', 'environment.json', 'expected-tests.json', 'expected-tests.toml', 'freeze-preparation.py', 'guard.py', 'host.json', 'launch.py', 'loaded-paths.json', 'offline-tests.json', 'offline-tests.py', 'oracle.py', 'prepare.py', 'recorder.jl', 'red.jl', 'runtime-inputs-complete.json', 'seal.py', 'source-check.json', 'source-check.py', 'stages.json', 'supervisor.py']
def main():
 require({p.name for p in D.iterdir() if p.is_file()}==set(PREP_NAMES),'Exact authored preparation membership')
 require(not (D/'runs').exists(),'No phase activity')
 require(rd(D/'source-check.json')['all_passed'] and rd(D/'offline-tests.json')['all_passed'],'Author checks')
 require(bindings(rd(D/'source-check.json')),'Checked bytes')
 names=[D/n for n in PREP_NAMES]+[D/'required-paths.json']
 names += [Path(n) for n in rd(D/'entry.json')['sha256']]
 names += [Path(v['source']) for v in rd(D/'control-lineage.json').values()]
 names += [Path(n) for n in rd(D/'runtime-inputs-complete.json')['inventory']]
 names += [Path(v['path'])/n for v in rd(D/'stages.json').values() for n in v['sha256']]
 names += [root/n for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]]
 names=sorted(set(names))
 save(D/'required-paths.json',dict(scope='Exact offline preparation inputs; excludes future independent review/closure/publication and all run outputs',paths=[str(p) for p in names]))
 save(D/'preparation-pins.json',dict(scope='Offline preparation, NOT numerical admission or launch',sha256={str(p):sha(p) for p in names}))
 print('Preparation manifest',len(names),'files; no phase seal')
if __name__=='__main__':main()
