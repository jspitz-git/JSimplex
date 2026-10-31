from pathlib import Path
import sys,json,tomllib,hashlib,subprocess
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import common as C
sys.path.insert(0,str(D/'guard'));import guard_reviewed as G
C.require(not (D/'seal.json').exists() and not (D/'pins.json').exists() and not C.R.exists(),'already sealed/attempted')
C.fresh(D/'preparation-host.json',C.host());files={str(p) for p in D.rglob('*') if p.is_file()};files.update(str(C.M/n) for n in C.git(C.M,'ls-files','src').splitlines());files.update(str(C.M/n) for n in ('Project.toml','Manifest.toml','LocalPreferences.toml','.vscode/settings.json'))
old=C.W/'diagnostics/klu-weight-btran/2026-10-29';files.update(str(old/n) for n in ('inputs.toml','results-2.toml','REPORT.md','consumer.jl','analyze_rejected.py'))
inputs=[]
for item in tomllib.loads((old/'inputs.toml').read_text())['cases']:
 if item['id'].startswith('runtime-'):
  C.require(C.sha(item['path'])==item['sha256'],'old tape changed');inputs.append(item['path']);files.add(item['path'])
c=C.read(D/'contract.json');j=Path(c['command'][0]);root=j.parents[1]
files.update(str(p) for p in (j,root/'lib/libjulia.so.1.13.0',root/'lib/julia/sys.so',root/'lib/julia/libjulia-internal.so.1.13.0',root/'share/julia/base/timing.jl',Path(sys.executable).absolute()))
for name in ('libumfpack.so.6.3.5','libamd.so.3.3.3','libcolamd.so.3.3.4','libsuitesparseconfig.so.7.10.1','libopenblas64_.so','libblastrampoline.so.5'):
 p=root/'lib/julia'/name
 if p.exists():files.add(str(p))
files=sorted(files);pins=dict(files=files,trees=[],inventory=G.inventory(files,[]),inputs=inputs,created=__import__('time').time());C.fresh(D/'pins.json',pins)
C.fresh(D/'seal.json',dict(master=c['master'],diagnostic=c['diagnostic'],command=c['command'],environment=c['environment'],pins_sha256=C.sha(D/'pins.json'),file_count=len(files),limit_seconds=1800,maximum_processes=1,scope='six exact saved runtime bases, production strict versus explicit dual recovery; no LP solve'))
print(json.dumps(dict(sealed=True,files=len(files),seal_sha256=C.sha(D/'seal.json'))))
