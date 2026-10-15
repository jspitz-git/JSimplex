"""Future one-shot result publication; missing/changed evidence fails closed."""
from control import *
from evidence import phase_checks,phase_paths

def audit(phase):
    cfg=phase_config(phase);out=Path(cfg['output']);error=''
    try:checks=phase_checks(phase)
    except Exception as e:error=repr(e);checks=dict(complete_records=False)
    # Partial failed evidence is preserved too; success needs the exact required set.
    paths=set(phase_paths(phase,cfg))|{p for p in out.rglob('*') if p.is_file()}
    result=dict(all_passed=bool(checks) and all(checks.values()),checks=checks,error=error,
        scope='Expected contract RED only' if phase=='red' else 'Correctness only; no cost/speedup/public solver claim',
        sha256={str(p):sha(p) for p in sorted(paths) if p.is_file()})
    save(D/(phase+'-audit.json'),result);return result
if __name__=='__main__':
    import sys
    req(audit(sys.argv[1])['all_passed'],'Audit rejected')
