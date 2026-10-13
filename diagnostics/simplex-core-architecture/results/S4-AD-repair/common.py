from pathlib import Path
import hashlib,json,subprocess,sys,os,time,math
D=Path(__file__).resolve().parent;R=D.parents[3];P=Path('/home/jspitz/JSimplex.jl');AC=D.parent/'S4-AC'
def require(x,m):
 if not x:raise ValueError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):
 p=Path(p);q=p.with_name(p.name+'.pending')
 with q.open('x') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.link(q,p);q.unlink()
def refs():return {str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (R,P)}
def host(groups):
 matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rindex(')')+2:].split();comm=(p/'comm').read_text().strip()
   if int(f[2]) in groups or int(f[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches)
def pins_ok(pins):
 try:return pins['trees']==[] and pins['inputs']==[] and set(pins['files'])==set(pins['inventory']) and all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items())
 except (KeyError,TypeError,OSError):return False
def guard_command(s,c):return [sys.executable,str(D/'guard.py'),'run',str(s/'pins.json'),c['output'],'--seconds','120','--',*c['command']]
def pressure_ok(m):return type(m['available_kib']) is int and m['available_kib']>=6*1024**2 and type(m['swap_used_kib']) is int and 0<=m['swap_used_kib']<=1024**2
