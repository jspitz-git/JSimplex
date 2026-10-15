"""Read-only helpers; single future diagnostic, no launch on import."""
from pathlib import Path
import hashlib,json,subprocess,time,tomllib,sys,os
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/"NATIVE-ACCURACY-QUALIFICATION"
def req(value,message):
 if not value:raise ValueError(message)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(path):return json.loads(Path(path).read_text())
def save(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def host(groups):
 from common import host as scan
 original=scan();missing=set(groups)-set(original['groups'])
 for p in Path('/proc').glob('[0-9]*'):
  try:
   z=(p/'stat').read_text().rsplit(')',1)[1].split()
   if int(z[2]) in missing or int(z[3]) in missing:
    original['matches'].append(dict(pid=int(p.name),pgid=int(z[2]),sid=int(z[3]),start_ticks=int(z[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=original['boot_id']))
  except (FileNotFoundError,ProcessLookupError):pass
 original['groups']=sorted(set(groups)|set(original['groups']));return original
ENV_KEYS=('HOME','PATH','JULIA_LOAD_PATH','JULIA_PROJECT','JULIA_DEPOT_PATH','JULIA_CPU_TARGET','JULIA_BINDIR','LD_LIBRARY_PATH','LD_PRELOAD')
def environment():return {k:os.environ.get(k) for k in ENV_KEYS}
def validate_environment():req(environment()==rd(D/'environment.json'),'Loading environment changed')
def expected_config(phase):
 req(phase=='accuracy','Only one diagnostic process')
 project=str(R);output=str(Q/'accuracy-run')
 wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
 inputs=str(D/'inputs.toml')
 command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+project,str(D/'driver.jl'),output,inputs]
 return dict(seconds=45,expected_exit=0,project=project,output=output,command=command)
def phase_config(phase):
 cfg=rd(D/'config.json');req(set(cfg)=={'accuracy'},'Exact one phase')
 expected=expected_config(phase);req(cfg[phase]==expected,'Command/budget drift');return expected
def validate_review(review,pin_path,required):
 req(review.get('accepted') is True and review.get('findings')==[],'Review not accepted')
 req(review.get('pins_sha256')==sha(pin_path),'Review pins mismatch')
 b=review.get('sha256',{});req(len(required)==len(set(required)) and set(b)==set(required),'Exact review membership')
 req(all(b[n]==sha(n) for n in required),'Review hashes changed')
def guard_command(cfg,pin_path,started):
 return [sys.executable,'-B',str(D/'guard.py'),'run',str(pin_path),cfg['output'],'--seconds','39','--deadline',str(started+39),'--',*cfg['command']]
