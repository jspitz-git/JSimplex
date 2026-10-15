"""Preserve tested draft sources, then bind fresh-stage continuation and cwd."""
from common import *
changes={'seal.py':("files=sorted(set(pins['files'])", "files=sorted({str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}|set(pins['files'])"),'launch.py':('validate_environment();phase_config','os.chdir(R);validate_environment();phase_config')}
mappings={}
for name,(old,new) in changes.items():
 p=F/name;before=F/(name+'.before-preparation-fix');req(not before.exists() and p.read_text().count(old)==1,'Unique source edit');before.write_bytes(p.read_bytes());p.write_text(p.read_text().replace(old,new));mappings[str(p)]={'old_sha256':sha(before),'preserved':str(before),'new_sha256':sha(p)}
checks=dict(seal_binds_live_continuation="str(R/'diagnostics/simplex-core-architecture/STATUS.md')" in (F/'seal.py').read_text(),seal_binds_roadmap="str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')" in (F/'seal.py').read_text(),launcher_cwd='os.chdir(R);validate_environment()' in (F/'launch.py').read_text(),preserved_offline_bindings=all(rd(F/'offline-tests.json')['sha256'][n]==v['old_sha256'] for n,v in mappings.items()))
save(F/'preparation-fix.json',dict(all_passed=all(checks.values()),checks=checks,mappings=mappings,sha256={str(p):sha(p) for p in [Path(__file__),F/'seal.py',F/'launch.py',F/'seal.py.before-preparation-fix',F/'launch.py.before-preparation-fix']}));req(all(checks.values()),'Fix failure')
