"""Fresh read-only host preflight for offline GREEN admission; execute once."""
from pathlib import Path
import json,subprocess,time
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
previous=json.loads((D.parent/'DIRECT-LU-TEST-REPAIR/host.json').read_text())
groups=previous['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
    try:
        f=(p/'stat').read_text().rsplit(')',1)[1].split()
        if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
            matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
    except (FileNotFoundError,ProcessLookupError):pass
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
result=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),branch=git('branch','--show-current'))
with (D/'host.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
if matches or len(groups)!=200 or result['head']!='ac2a94f40e8c815f48683adce67820e5ec6b8d62' or result['master']!='6f68e24e8ddac42b948da8fcc2d636c010751194' or result['branch']!='codex/simplex-core-architecture':raise SystemExit('Host preflight refused')
print(json.dumps(dict(groups=len(groups),matches=matches,head=result['head'],master=result['master'],boot_id=boot)))
