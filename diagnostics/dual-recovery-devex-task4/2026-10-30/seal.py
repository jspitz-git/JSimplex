"""Prepare exactly one immutable phase seal. Never launches Julia."""
import sys
from pathlib import Path
import common as C

def main(phase):
 C.phase_ok(phase);used,previous=C.previous(phase);h=C.host()
 pub=C.read(C.D/'publication.json');C.require(pub['accepted'],'preparation not published')
 paths=[C.W/p for p in pub['expected_names']]
 C.require(all(C.git('hash-object',str(p))==C.git('rev-parse','HEAD:'+str(p.relative_to(C.W))) for p in paths),'prepared artifacts not exact committed bytes')
 runtime=Path(C.JULIA).parents[1]
 paths += [Path(sys.executable),Path(C.JULIA),runtime/'lib/libjulia.so.1.13.0',runtime/'lib/julia/sys.so',runtime/'lib/julia/libjulia-internal.so.1.13.0',runtime/'share/julia/base/timing.jl']
 for depot in C.DEPOTS.split(':'):C.require(Path(depot).is_dir(),'missing configured depot '+depot)
 paths=sorted(set(p.absolute() for p in paths));files=[str(p) for p in paths]
 inventory={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=C.sha(p)) for p in paths}
 out=C.RUN/phase;out.mkdir(parents=True,exist_ok=False)
 C.fresh(out/'pins.json',dict(files=files,trees=[],inventory=inventory,inputs=[],scope='exact files/readtime/runtime command; not cache confinement or hidden loader proof'))
 seal=dict(phase=phase,head=h['refs']['HEAD'],master=C.MASTER,command=C.command(phase),environment=C.environment(phase),expected_exit=1 if phase=='red' else 0,pins_sha256=C.sha(out/'pins.json'),shared_total_seconds=1800,used_seconds=used,previous=previous,preflight=h)
 C.fresh(out/'seal.json',seal)
 print('SEALED ONLY',phase,'independent numerical admission still required',C.sha(out/'seal.json'))
if __name__=='__main__':
 C.require(len(sys.argv)==2,'one phase required');main(sys.argv[1])
