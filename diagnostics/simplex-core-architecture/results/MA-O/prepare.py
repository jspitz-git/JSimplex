from pathlib import Path
import hashlib,json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-O';N=D.parent/'MA-N'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
def save(p,v):write(p,(json.dumps(v,indent=2)+'\n').encode())
def require(ok,msg):
 if not ok:raise ValueError(msg)
write(D/'host.json',Path('/tmp/ma-o-host-mbk1n1xf.json').read_bytes())
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
write(D/'STATUS.md.before-MA-O',status.read_bytes());write(D/'roadmap.md.before-MA-O',road.read_bytes())
checks={};bindings={}
for name in ('review.json','publication-amendment-review.json','publication-gate-review.json','closure.json','closure-final.json','publication-final.json'):
 v=read(N/name);checks[name]=(v.get('accepted',v.get('all_passed')) is True and not v.get('findings',[]) and all(v['checks'].values()) and all(sha(Path(p) if Path(p).is_absolute() else R/p)==h for p,h in v['sha256'].items()));bindings[str(N/name)]=sha(N/name)
checks['initial_publication_failure_preserved']=read(N/'publication.json')['all_passed'] is False
mapping={str(status):str(D/'STATUS.md.before-MA-O'),str(road):str(D/'roadmap.md.before-MA-O')};current=[]
for name in ('continuation-map.json','closure.json','closure-final.json','publication.json','publication-final.json'):
 for p,h in read(N/name)['sha256'].items():
  a=str(Path(p) if Path(p).is_absolute() else R/p)
  if a in mapping:current.append(dict(record=name,path=a,preserved=mapping[a],sha256=h,match=sha(mapping[a])==h))
checks['ten_current_continuation_bindings']=len(current)==10 and all(v['match'] for v in current)
copyfiles=('driver.jl','audit.py','launcher.py','guard.py','env/Project.toml','env/Manifest.toml')
for name in copyfiles:write(D/name,(N/name).read_bytes())
checks['six_exact_source_environment_copies']=all((D/n).read_bytes()==(N/n).read_bytes() for n in copyfiles)
commands=read(N/'commands.json')
for i,cmd in commands.items():
 require(cmd[-3]==str(N/'driver.jl') and cmd[-2]==i and cmd[-1]==str(N/f'run-{i}'),'oldcommand')
 cmd[-3]=str(D/'driver.jl');cmd[-1]=str(D/f'run-{i}')
save(D/'commands.json',commands)
checks['commands_only_driver_output_paths']=all(a[:-3]==b[:-3] and a[-2]==b[-2] for a,b in zip(commands.values(),read(N/'commands.json').values()))
bindings.update({str(D/n):sha(D/n) for n in (*copyfiles,'commands.json','host.json','STATUS.md.before-MA-O','roadmap.md.before-MA-O')})
save(D/'entry.json',dict(all_passed=all(checks.values()),checks=checks,current_binding_maps=current,sha256=bindings))
require(all(checks.values()),'entry checks failed')
print(json.dumps(checks,indent=2))
