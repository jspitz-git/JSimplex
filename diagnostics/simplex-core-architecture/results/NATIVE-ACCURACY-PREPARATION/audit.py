"""One-shot diagnostic audit. Residual failures are evidence, never cost acceptance."""
from evidence import *
def audit(phase):
 cfg=phase_config(phase);checks={};result={};error=''
 try:checks,result=phase_checks(phase)
 except Exception as e:error=repr(e);checks=dict(complete=False)
 paths=set(phase_paths(phase,cfg))|{p for p in Path(cfg['output']).rglob('*') if p.is_file()}
 record=dict(all_passed=bool(checks) and all(checks.values()),checks=checks,error=error,result=result,cost_qualified=result.get("interpretable_cost",False),
 scope='Bounded diagnostic evidence only; accuracy and cost reported separately; no retry, cost2 or production promotion',sha256={str(p):sha(p) for p in sorted(paths) if p.is_file()})
 save(Q/(phase+'-audit.json'),record);return record
if __name__=='__main__':
 import sys
 req(audit(sys.argv[1])['all_passed'],'Diagnostic integrity failed; preserve and stop')
