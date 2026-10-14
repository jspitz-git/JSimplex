"""Read-only exact phase evidence validation. No subprocesses or audit writes."""
from control_reviewed import *
import guard
CONTROL_SUFFIXES=('seal-host.json','sealed-pins.json','admission.json','prehost.json','launch-pins.json','reservation.json','launcher.log','invocation.json','posthost.json')
def phase_paths(phase,cfg):
    out=Path(cfg['output'])
    names=['pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml']
    names += [f'{prefix}-{i+1}.toml' for i in range(len(cfg['groups'])) for prefix in ('started','group')]
    return sorted([D/(phase+'-'+n) for n in CONTROL_SUFFIXES]+[out/n for n in names])
def phase_checks(phase):
    cfg=phase_config(phase);out=Path(cfg['output']);paths=phase_paths(phase,cfg)
    req(all(p.is_file() for p in paths),'Missing phase evidence')
    expected_out={p for p in paths if p.parent==out}
    req({p for p in out.rglob('*') if p.is_file()}==expected_out,'Unexpected output membership')
    inv=rd(D/(phase+'-invocation.json'));post=rd(D/(phase+'-posthost.json'));p=rd(out/'process.json')
    pins_path=D/(phase+'-launch-pins.json');pins=rd(pins_path);s=inv['supervisor'];expected=cfg['expected_exit']
    raw=tomllib.loads((out/'raw.toml').read_text())
    resources=[json.loads(line) for line in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
    sealed_path=D/(phase+'-sealed-pins.json');sealed=rd(sealed_path);review_path=D/(phase+'-admission.json')
    validate_review(rd(review_path),sealed_path,sealed['files']+[str(sealed_path)])
    req(sealed['phase']==phase,'Wrong sealed phase')
    req(set(pins['files'])==set(sealed['files'])|{str(sealed_path),str(review_path)} and pins['trees']==sealed['trees'],'Launch/seal membership')
    req(all(pins['inventory'].get(n)==v for n,v in sealed['inventory'].items()),'Launch/seal inventory drift')
    reservation_path=D/(phase+'-reservation.json')
    current=rd(out/'current.json');pre=rd(D/(phase+'-prehost.json'));sealhost=rd(D/(phase+'-seal-host.json'))
    checks=dict(complete_records=True,review=True,
        host=not pre['matches'] and not sealhost['matches'] and all(pre[k]==sealhost[k]==sealed[k] for k in ('head','master','boot_id')),
        no_processes=post['matches']==[] and all(post[k]==pre[k] for k in ('head','master','boot_id')),
        identities=current['runner']==p['runner']==s['guard_identity'] and current['child']==p['child'] and all(p[k][field] in post['groups'] for k in ('runner','child') for field in ('pgid','sid')),
        bounded=inv['elapsed_seconds']<=cfg['seconds'] and s['elapsed_seconds']<=cfg['seconds'] and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,
        exit=p['returncode']==expected and p['reason']=='exit'+str(expected) and s['returncode']==(0 if expected==0 else 1),
        pins=p['pins_unchanged'] is True and guard.pins_match(pins) and rd(out/'pins.json')==pins,
        command=p['command']==current['command']==cfg['command']==inv['command'] and p['pins_sha256']==current['pins_sha256']==sha(pins_path)==inv['pins_sha256'],
        resources=all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources),
        raw=raw_ok(raw,phase,cfg),
        reservation=rd(reservation_path)==dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pins_path),review_sha256=sha(review_path),max_seconds=cfg['seconds']),
        invocation=inv['review_sha256']==sha(review_path) and inv['reservation_sha256']==sha(reservation_path))
    checks['progress']=all(tomllib.loads((out/f'group-{i+1}.toml').read_text())==row and tomllib.loads((out/f'started-{i+1}.toml').read_text())==dict(name=e['name'],expected=e['counts']) for i,(row,e) in enumerate(zip(raw['groups'],cfg['groups']))) and len(raw['groups'])==len(cfg['groups'])
    checks['totals']=all(raw['total_'+k]==sum(row[k] for row in raw['groups']) for k in ('pass','fail','error','broken'))
    return checks

def validate_predecessor():
    cfg=phase_config('red');paths=phase_paths('red',cfg);audit_path=D/'red-audit.json';audit=rd(audit_path)
    req(audit.get('all_passed') is True and audit.get('error')=='','RED audit not accepted')
    bindings=audit.get('sha256',{})
    req(set(bindings)=={str(p) for p in paths},'Exact complete RED audit membership')
    req(all(p.is_file() and bindings[str(p)]==sha(p) for p in paths),'RED evidence missing or changed')
    actual={p for p in D.glob('red-*') if p.is_file()}|{p for p in Path(cfg['output']).rglob('*') if p.is_file()}
    req(actual==set(paths)|{audit_path},'Unexpected RED artifact membership')
    checks=phase_checks('red')
    req(audit.get('checks')==checks and all(checks.values()),'RED evidence no longer satisfies contract')
    return paths+[audit_path]
