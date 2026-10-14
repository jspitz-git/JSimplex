from pathlib import Path
import json,re,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
new=set(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=R,text=True).splitlines())-{'Manifest.toml','LocalPreferences.toml'}
report='diagnostics/simplex-core-architecture/MA-DENSELU-COMPLETE-QUALIFICATION.md'
prefixes=('diagnostics/simplex-core-architecture/results/MA-X/','diagnostics/simplex-core-architecture/results/MA-Y/')
if not all(n==report or n.startswith(prefixes) for n in new):raise SystemExit('unexpected new path')
names=sorted(new|{str((D/n).relative_to(R)) for n in ('closure.json','publication.json','publication.py','publication-names.json')}|{'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'})
with (D/'publication-names.json').open('x') as f:json.dump(names,f,indent=2);f.write('\n')
s=(D.with_name('MA-X')/'publication.py').read_text().replace("results/MA-X'","results/MA-Y'")
s=re.sub(r'^NAMES = .*$',lambda _: 'NAMES = '+repr(names),s,flags=re.M)
s=s.replace('MA-X offline concrete driver/admission preparation only; no Julia or numerical run','MA-Y diagnostic closure of rejected complete qualification; three processes, no retry or production promotion')
with (D/'publication.py').open('x') as f:f.write(s)
print('fixed publication names',len(names))
