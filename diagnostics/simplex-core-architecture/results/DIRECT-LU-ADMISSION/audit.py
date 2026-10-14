"""One-shot fail-closed result audit; never treats missing raw/logs as success."""
from control import *
import guard

def audit(phase):
    cfg=phase_config(phase);out=Path(cfg['output']);checks={};error=''
    try:
        inv=rd(D/(phase+'-invocation.json'));post=rd(D/(phase+'-posthost.json'));p=rd(out/'process.json')
        pins_path=D/(phase+'-launch-pins.json');pins=rd(pins_path);s=inv['supervisor'];expected=cfg['expected_exit'];raw=tomllib.loads((out/'raw.toml').read_text())
        resources=[json.loads(line) for line in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
        checks.update(no_processes=post['matches']==[],bounded=inv['elapsed_seconds']<=cfg['seconds'] and s['elapsed_seconds']<=cfg['seconds'] and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,
            exit=p['returncode']==expected and p['reason']=='exit'+str(expected) and s['returncode']==(0 if expected==0 else 1),
            pins=p['pins_unchanged'] is True and guard.pins_match(pins) and rd(out/'pins.json')==pins,
            command=p['command']==cfg['command']==inv['command'] and p['pins_sha256']==sha(pins_path)==inv['pins_sha256'],
            resources=all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources),
            raw=raw_ok(raw,phase,cfg),logs=(out/'run.log').is_file() and (D/(phase+'-launcher.log')).is_file(),
            reservation=rd(D/(phase+'-reservation.json'))==dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pins_path),review_sha256=sha(D/(phase+'-admission.json')),max_seconds=cfg['seconds']))
        checks['progress']=all(tomllib.loads((out/f'group-{i+1}.toml').read_text())==row for i,row in enumerate(raw['groups']))
        checks['totals']=all(raw['total_'+k]==sum(row[k] for row in raw['groups']) for k in ('pass','fail','error','broken'))
    except Exception as e:error=repr(e);checks['complete_records']=False
    result=dict(all_passed=bool(checks) and all(checks.values()),checks=checks,error=error,scope='Expected contract RED only' if phase=='red' else 'Correctness only; no cost/speedup/public solver claim',sha256={str(q):sha(q) for q in out.rglob('*') if q.is_file()})
    save(D/(phase+'-audit.json'),result);return result
if __name__=='__main__':
    import sys
    req(audit(sys.argv[1])['all_passed'],'Audit rejected')
