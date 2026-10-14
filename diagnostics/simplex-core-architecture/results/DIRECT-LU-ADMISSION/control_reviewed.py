"""Read-only helpers and fail-closed gates. No launch on import."""
from pathlib import Path
import hashlib,json,subprocess,time,tomllib
D=Path(__file__).resolve().parent;R=D.parents[3]
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
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
    for p in Path('/proc').glob('[0-9]*'):
        try:
            f=(p/'stat').read_text().rsplit(')',1)[1].split()
            if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):
                matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
        except (FileNotFoundError,ProcessLookupError):pass
    return dict(time=time.time(),boot_id=boot,groups=sorted(set(groups)),matches=matches,head=git('rev-parse','HEAD'),master=git('rev-parse','master'))
def phase_config(phase):
    req(phase in ('red','green'),'Unknown phase')
    c=rd(D/'config.json')['phases'][phase]
    req(c['seconds']==(30 if phase=='red' else 90),'Time limit changed')
    req(c['expected_exit']==(1 if phase=='red' else 0),'Exit contract changed')
    req(c['output']==str(D/(phase+'-run')),'Output path changed')
    return c
def validate_review(review,pin_path,required):
    req(review.get('accepted') is True and review.get('findings')==[], 'Review not accepted')
    req(review.get('pins_sha256')==sha(pin_path),'Review pins mismatch')
    bindings=review.get('sha256',{})
    req(set(bindings)==set(required),'Exact required review membership')
    req(all(bindings[n]==sha(n) for n in required),'Required review bindings changed')
def raw_ok(raw,phase,config):
    expected=config['groups'];rows=raw.get('groups',[])
    return (raw.get('phase')==phase and raw.get('completed') is True and raw.get('all_expected') is True and raw.get('fatal')==''
        and raw.get('loaded_path')==str(Path(config['project'])/'src/JSimplex.jl')
        and len(rows)==len(expected) and all(r.get('name')==e['name'] and [r.get(k) for k in ('pass','fail','error','broken')]==e['counts'] and r.get('expected')==e['counts'] and r.get('counts_match') is True for r,e in zip(rows,expected)))
