"""Future one-shot GREEN2 seal. No Julia; main is NOT run during preparation."""
import sys
from pathlib import Path
import common as C
def main():
 C.require(not C.OUT.exists(),'GREEN2 already sealed/reserved')
 h=C.host();fixture=C.fixtures()
 paths=C.required_paths()
 for folder in (C.ORIGINAL,C.OLD_RED,C.OLD_GREEN,C.FIX,C.D):
  for rel in C.read(folder/'publication.json')['expected_names']:
   C.require(C.git('hash-object',str(C.W/rel))==C.git('rev-parse','HEAD:'+rel),'uncommitted/changed preparation '+rel)
 for depot in C.DEPOTS.split(':'):C.require(Path(depot).is_dir(),'missing configured depot '+depot)
 used,previous=C.prior();C.require(C.TOTAL-used>20,'shared cleanup budget exhausted')
 pins=dict(files=paths,trees=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=C.sha(n)) for n in paths},inputs=C.expected_inputs(),scope='exact published/runtime files and BOTH fixture inputs; not loader/cache/native proof')
 C.check_inventory(pins,paths,C.expected_inputs())
 C.OUT.mkdir(parents=True,exist_ok=False)
 C.fresh(C.OUT/'pins.json',pins)
 C.fresh(C.OUT/'seal.json',dict(phase='green2',guard_python=str(Path(sys.executable).absolute()),head=h['refs']['HEAD'],master=C.MASTER,command=C.command(),environment=C.environment(),expected_exit=0,pins_sha256=C.sha(C.OUT/'pins.json'),shared_total_seconds=1800,used_seconds=used,previous=previous,remaining_seconds=1800-used,preflight=h,fixture_audit=fixture))
 print('SEALED ONLY GREEN2; fresh independent numerical admission still required',C.sha(C.OUT/'seal.json'))
if __name__=='__main__':
 C.require(len(sys.argv)==1,'no phase override');main()
