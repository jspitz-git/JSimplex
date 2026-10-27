from pathlib import Path
import json,shutil,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27');Q=D/'MASTER-run'
shutil.copyfile(__file__,D/'prepare-master-time.py')
for n in ['contract.json','launch.py','audit.py','pins.json']:shutil.copyfile(Q/n,Q/(n+'.before-time'))
for n in ['launch.py','audit.py']:
 p=Q/n;s=p.read_text();assert '1800' in s and '1792' in s;s=s.replace('1800','2400').replace('1792','2392');compile(s,str(p),'exec');p.write_text(s)
p=Q/'contract.json';j=json.loads(p.read_text());assert j['shared_limit_seconds']==1800 and j['guard_limit_seconds']==1792;j['shared_limit_seconds']=2400;j['guard_limit_seconds']=2392;p.write_text(json.dumps(j,indent=2)+'\n')
j=json.loads((Q/'pins.json').read_text())
for p in [Q/'launch.py',Q/'audit.py',Q/'contract.json',D/'MASTER-TIME-ADDENDUM.md',D/'prepare-master-time.py']:
 j['files']=sorted(set(j['files'])|{str(p)});j['inventory'][str(p)]=dict(resolved=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(Q/'pins.json').write_text(json.dumps(j,indent=2,sort_keys=True)+'\n');shutil.copyfile(__file__,D/'prepare-master-time.py');print('MASTER cap2400seconds,exacttests/inputs/guards unchanged;notlaunched')
