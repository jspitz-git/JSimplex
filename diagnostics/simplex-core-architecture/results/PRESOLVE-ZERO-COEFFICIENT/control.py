from pathlib import Path
import hashlib,json,subprocess,time,math,tomllib,statistics
D=Path(__file__).resolve().parent; R=D.parents[3]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def req(v,msg):
 if not v:raise ValueError(msg)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def host(groups):
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   f=(p/'stat').read_text().rsplit(')',1)[1].split()
   if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
    matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
  except (FileNotFoundError,ProcessLookupError):pass
 return dict(time=time.time(),boot_id=boot,groups=sorted(set(groups)),matches=matches,head=git('rev-parse','HEAD'),master=git('rev-parse','master'))
def validate_review(review,pins_sha,required):
 req(review.get('accepted') is True and review.get('findings')==[], 'review not accepted')
 req(review.get('pins_sha256')==pins_sha,'review pins')
 bindings=review.get('sha256',{})
 req(all(bindings.get(str(p))==sha(p) for p in required),'review required bindings')
def metric_ok(w):
 return all(isinstance(w[k],(int,float)) and not isinstance(w[k],bool) and math.isfinite(w[k]) and w[k]>=0 for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'))
