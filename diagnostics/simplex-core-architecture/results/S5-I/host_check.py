"""Fresh host-only absence snapshot. Each label is exclusive; never probes Julia."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
I=Path(__file__).resolve().parent;R=I.parents[3];label=sys.argv[1]
assert label in ('before-green-edit','before-green-launch','before-master-edit','before-master-launch','after-master')
groups={49081,49084,23249,23257}
for p in (R/'.superpowers/simplex-core-architecture/S5-I').glob('*/process.json'):
 x=json.loads(p.read_text());groups.update(x[k]['pgid'] for k in ('runner','child') if k in x)
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text();f=stat[stat.rindex(')')+2:].split()
  if int(f[2]) in groups or (p/'comm').read_text().strip()=='julia':matches.append({'pid':int(p.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'boot_id':boot,'command':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
users=json.loads((I/'host-before.json').read_text())['user_hashes']
x={'boot_id':boot,'groups':sorted(groups),'matches':matches,'time_ns':time.time_ns(),'users_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in users.items()),'refs':subprocess.check_output(['git','rev-parse','HEAD','master'],cwd=R,text=True)}
with (I/(label+'.json')).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));assert not matches and x['users_unchanged']
