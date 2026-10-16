"""New one-shot source/inverse and predecessor check, no historical script execution."""
from control import *
import ast,copy
files,groups=predecessor('integration');cfg=config('integration');validate_environment();h=host();verify_host(h)
def funcs(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)}
a=funcs(DRIVER/'control.py');b=funcs(D/'control.py');names=set(a)-{'config','predecessor'}
old=rd(DRIVER/'config-preview.json');expected=copy.deepcopy(old)
expected.update(stage=cfg['stage'],run=cfg['run'],output=cfg['output'])
expected['command']=[x.replace(old['stage'],cfg['stage']).replace(old['output'],cfg['output']) for x in old['command']]
source_map=rd(D/'source-map.json');env=rd(D/'environment.json');previous=rd(DRIVER/'environment.json')
current_common=(D/'common.py').read_text().replace("PREV=Q.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'",'PREV=Q').replace(HEAD,'86e0397c882ff6628193cfa4c1d24a7c71ed7c3e')
checks=dict(predecessor=True,groups216=len(groups)==216 and not h['matches'],
 exact_copies=all(sha(D/n)==v['sha256']==sha(Path(v['source'])) for n,v in source_map['byte_identical'].items()),
 original_driver=cfg['command'][-4]==str(DRIVER/'driver.jl') and sha(DRIVER/'driver.jl')==source_map['driver_sha256'],
 unchanged_control_functions=all(a[n]==b[n] for n in names) and set(a)==set(b),
 exact_common_inverse=current_common==(DRIVER/'common.py').read_text(),
 exact_config=cfg==expected,environment_keys=set(env)==set(previous),
 environment_delta_only_path=[k for k in env if env[k]!=previous[k]]==['PATH'],
 path_only_first=env['PATH'].split(':')[1:]==previous['PATH'].split(':')[1:],
 source520=all(sha(R/n)==v for n,v in rd(DRIVER/'actual-baseline.json')['sha256'].items()),
 no_new_julia_text=not list(D.glob('*.jl')),no_stage=not Path(cfg['stage']).exists() and not Path(old['stage']).exists(),
 no_runs=not (D/'runs').exists() and not (DRIVER/'runs').exists(),
 offline17=rd(D/'offline-GREEN.json')['all_passed'] and len(rd(D/'offline-GREEN.json')['checks'])==17,
 preserved_red=rd(D/'offline-RED.json')['all_passed'] is False,
 before_bytes=sha(STATUS)==sha(D/'STATUS.md.before-environment') and sha(ROAD)==sha(D/'roadmap.md.before-environment'))
save(D/'config-preview.json',cfg)
maps=[]
for rec in ['closure.json','publication.json']:
 z=rd(DRIVER/rec)
 for name,preserved in [(STATUS,D/'STATUS.md.before-environment'),(ROAD,D/'roadmap.md.before-environment')]:
  key=str(name.relative_to(R));require(z['sha256'][key]==sha(preserved),'Preimage binding')
  maps.append(dict(record=str((DRIVER/rec).relative_to(R)),pointer=['sha256',key],preserved_path=str(preserved.relative_to(R)),sha256=sha(preserved)))
save(D/'continuation-mappings.json',dict(mappings=maps,scope='Only current driver-preparation closure/publication continuation paths; all older mappings preserved'))
save(D/'source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in sorted(set(files)|{D/n for n in ['common.py','control.py','environment.json','source-map.json','source-check.py']})},scope='Offline source and current read-time bindings only; no Julia/stage'))
require(all(checks.values()),'Source check failed; preserve');print(dict(checks=len(checks),predecessor_files=len(files),actual520=checks['source520']))
