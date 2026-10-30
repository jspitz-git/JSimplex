import sys,ast
from pathlib import Path
import common as C
C.require(not C.R.exists(),'master verification already sealed');h=C.host();C.require(C.prior_time()==1108.3747013349202,'actual prior time');c=C.read(C.D/'contract.json');s=C.read(C.D/'integration.json');C.require(c['previous_seconds']==1108.3747013349202 and c['remaining_seconds']==691.6252986650798 and c['previous_seconds']+c['remaining_seconds']==1800,'shared time reset')
C.require(C.git(C.W,'diff-tree','--no-commit-id','--name-only','-r',s['production_commit']).splitlines()==C.read(C.D/'production-commit.json')['names'],'production11files')
for n,v in s['payload_sha256'].items():C.require(C.sha(C.M/n)==C.sha(C.P/'prepared'/n)==v,'integrated payload changed')
for p in C.D.rglob('*.py'):ast.parse(p.read_text())
for n in c['known_fixtures']:C.require(Path(n).is_file() and C.sha(n)==C.read(C.P/'source-check.json')['bindings'][str(C.W/Path(n).relative_to(C.M))],'fixture missing/changed')
files=C.paths();pins=dict(files=files,trees=[],inputs=c['known_fixtures'],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=C.sha(n)) for n in files});C.verify_pins(pins);C.R.mkdir(parents=True,exist_ok=False);C.fresh(C.R/'pins.json',pins);C.fresh(C.R/'seal.json',dict(head=c['diagnostic_head'],production_commit=c['production_commit'],command=c['command'],environment=c['environment'],guard_python=str(Path(sys.executable).absolute()),pins_sha256=C.sha(C.R/'pins.json'),previous_seconds=c['previous_seconds'],remaining_seconds=c['remaining_seconds'],preflight=h));print('SEALED MASTER ONLY',len(files),C.sha(C.R/'seal.json'))
