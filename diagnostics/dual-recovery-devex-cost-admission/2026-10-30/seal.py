"""Future immutable seal for one cost phase; main unexecuted in preparation."""
import sys
from pathlib import Path
import common as C
def main(phase):
 C.phase_ok(phase);r=C.out(phase);C.require(not r.exists(),'phase already sealed')
 h=C.host();C.driver_ready();used,facts=C.prior(phase);C.require(1800-used>20,'no cleanup/shared budget')
 paths=C.required_paths(phase)
 for folder in (C.ORIGINAL,C.OLD_RED,C.OLD_GREEN,C.FIX,C.GREEN2_PREP,C.GREEN2_RESULT,C.D):
  for rel in C.read(folder/'publication.json')['expected_names']:
   C.require(C.git('hash-object',str(C.W/rel))==C.git('rev-parse','HEAD:'+rel),'uncommitted preparation '+rel)
 for depot in C.DEPOTS.split(':'):C.require(Path(depot).is_dir(),'missing depot '+depot)
 pins=dict(files=paths,trees=[],inputs=[],inventory={p:dict(resolved=str(Path(p).resolve(strict=True)),sha256=C.sha(p)) for p in paths},scope='exact published/runtime/phase-evidence files; fixed inline matrices; not loader/native proof')
 C.check_inventory(pins,paths)
 r.mkdir(parents=True,exist_ok=False);C.fresh(r/'pins.json',pins)
 C.fresh(r/'seal.json',dict(phase=phase,guard_python=str(Path(sys.executable).absolute()),head=h['refs']['HEAD'],master=C.MASTER,command=C.command(phase),environment=C.environment(phase),expected_exit=0,pins_sha256=C.sha(r/'pins.json'),shared_total_seconds=1800,used_seconds=used,remaining_seconds=1800-used,previous=facts,preflight=h))
 print('SEALED ONLY',phase,'fresh independent numerical admission still required',C.sha(r/'seal.json'))
if __name__=='__main__':
 C.require(len(sys.argv)==2,'phase required');main(sys.argv[1])
