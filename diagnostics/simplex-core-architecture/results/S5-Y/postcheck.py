"""Exclusive independent postexit check, no auditor rerun or Julia."""
from pathlib import Path
import json,hashlib,subprocess,tomllib,time
R=Path.cwd();H=Path(__file__).resolve().parent;B=R/'.superpowers/simplex-core-architecture/S5-Y/qualification-1';X=H.parent/'S5-X';M=Path('/home/jspitz/JSimplex.jl')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
a=read(H/'audit.json');pin=read(H/'pins.json');p=read(B/'process.json');raw=tomllib.loads((B/'raw.toml').read_text());resources=[json.loads(x) for x in (B/'resources.jsonl').read_text().splitlines()]
portable=H/'portable';portable.mkdir()
for name,digest in a['raw_sha256'].items():
 assert sha(B/name)==digest
 with (portable/name).open('xb') as f:f.write((B/name).read_bytes())
G=set(a['groups']['groups']);matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  s=(q/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if int(v[2]) in G or (q/'comm').read_text().strip()=='julia':matches.append(dict(pid=int(q.name),pgid=int(v[2]),start_ticks=int(v[19]),command=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
c=dict(audit23=len(a['checks'])==23 and a['all_passed'] is True and all(v is True for v in a['checks'].values()),full1347=len(pin['inventory'])==1347 and all(sha(k)==v['sha256'] and str(Path(k).resolve(strict=True))==v['resolved'] for k,v in pin['inventory'].items()),admission1344=len(read(H/'admission-pins.json')['inventory'])==1344 and all(sha(k)==v['sha256'] for k,v in read(H/'admission-pins.json')['inventory'].items()),raw6=len(a['raw_sha256'])==6 and all(sha(B/k)==sha(portable/k)==v for k,v in a['raw_sha256'].items()),invocation3=len(a['invocation_sha256'])==3 and all(sha(k)==v for k,v in a['invocation_sha256'].items()),literal50=len(raw['checks'])==50 and all(v is True for v in raw['checks'].values()),work_and_events=raw['fallback_record']==raw['after_record']==dict(iterations=2,refactorizations=2,crash_pivot=2,refactor_other=1,crash_fallback=1,crash_accepted=0,callbacks=6),candidate_source=sha(X/'candidate.jl')=='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18' and (X/'candidate.jl').read_text().count('JSimplex._crash_workspace(')==1 and (X/'candidate.jl').read_text().count('JSimplex.initialize_workspace(')==1,refs_and_source=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines()==['f45899f3b06c819943498f9906c8ffefca31c15a','2b546e946ddb7fdb6c0092df9cc19f566e301aa2'] and not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']),user6=all(sha(k)==v for k,v in read(H/'host.json')['user_hashes'].items()),full22groups_noJulia=len(G)==22 and not matches)
files=[Path(__file__),H/'audit.json',H/'pins.json',H/'admission-pins.json',H/'acceptance.json',H/'launch-binding.json',X/'candidate.jl',H/'schema.json']
x=dict(checks=c,all_passed=all(c.values()),sha256={str(f):sha(f) for f in files},groups=sorted(G),matches=matches,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),resource_samples=len(resources),minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_kib=max(x['swap_used_kib'] for x in resources),elapsed_including_launch=p['elapsed_including_launch'],time_ns=time.time_ns())
dump(H/'postcheck.json',x);print(json.dumps(x));assert x['all_passed']
