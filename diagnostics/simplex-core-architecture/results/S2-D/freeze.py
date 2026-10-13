from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D';C=D.parent/'S2-C'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def put(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
groups=json.loads((C/'pre-continuation-host.json').read_text())['groups'];hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in groups or int(v[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):hits.append({'pid':p.name,'pgid':v[2],'sid':v[3],'start_ticks':v[19],'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
refs={n:subprocess.check_output(['git','rev-parse',n],text=True).strip() for n in ['HEAD','master']};assert refs=={'HEAD':'fdd4f5c67fdf1b0cdba3de85f5dcaaa887fa2f15','master':'d02416c108f06fcd41d58e0a1980b70a51fef9ef'};assert not hits
user=json.loads((C/'pre-continuation-host.json').read_text())['user'];assert all(sha(Path(p))==v['sha256'] for p,v in user.items())
put('host-before.json',{'refs':refs,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':groups,'matches':hits,'user':user,'no_Julia':True})
paths={R/p for p in subprocess.check_output(['git','ls-files','src','test','.github'],text=True).splitlines()}
paths|={p for p in D.rglob('*') if p.is_file()};paths|={Path(p) for p in user}
paths|={R/'Project.toml',R/'docs/superpowers/plans/2026-10-13-price-audit-values-admission.md'}
paths|={p for p in C.iterdir() if p.is_file()}
old=json.loads((D.parent/'S5-AA/green/pins.json').read_text())['inventory']
paths|={Path(p) for p in old if '/.julia/juliaup/' in p or p.endswith('/basis-chain-cost/julia.sh') or p.endswith('/basis-memory/reproduce/julia.sh')}
root=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia')
paths|={root/'base/loading.jl',root/'base/abstractarray.jl',root/'stdlib/v1.13/Test/src/Test.jl'}
required={str(p):sha(p) for p in sorted(paths)};put('required-paths.json',required)
paths.add(D/'required-paths.json')
inv={str(p):{'resolved':str(p.resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
put('admission-pins.json',{'files':sorted(inv),'trees':[],'inputs':[],'inventory':inv,'created':time.time(),'scope':'read-time admission preparation pins; NOT launch pins or allowance'})
print('Frozen',len(inv),'pins; no Julia / launcher execution.')
