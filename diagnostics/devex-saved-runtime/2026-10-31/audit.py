import json,math,re,tomllib,traceback
from pathlib import Path
import common as C
def main():
 checks={};error=None
 def check(name,v):checks[name]=bool(v);C.require(bool(v),name)
 try:
  c=C.read(C.D/'contract.json');p=C.read(C.R/'guard/process.json');s=C.read(C.R/'supervisor.json');done=C.read(C.R/'completion.json')
  check('guard_exit0_and_pins',p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] is True)
  check('supervisor_clean',s['accepted'] is True and all(s.get(k) is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted')))
  check('budget',0<done['elapsed_inclusive_seconds']<=1800)
  check('immutable_pins',C.pins_ok());check('postflight',not C.read(C.R/'postflight.json')['conflicts'])
  text=(C.R/'guard/run.log').read_text();matches=re.findall(r'^Saved runtime basis Devex recovery\s*\|\s*(\d+)\s+(\d+)\s+[^\n]+$',text,re.M)
  check('ordinary_Test_summary',len(matches)==1 and int(matches[0][0])==int(matches[0][1]) and int(matches[0][0])>0)
  result=tomllib.loads((C.R/'results/completion.toml').read_text());check('complete_six_zero_iterations',result['completed'] is True and result['cases']==6 and result['iterations']==0)
  expected={name+'.toml' for name in c['cases']}|{'completion.toml'};check('exact_result_membership',{p.name for p in (C.R/'results').iterdir()}==expected)
  for name in c['cases']:
   v=tomllib.loads((C.R/'results'/f'{name}.toml').read_text());check(name+'_adopted',v['published'] is True and v['pricing']=='devex' and v['iterations']==0 and v['failed_weight_row']>=1)
   check(name+'_commit_events',all(v['events'][key]==1 for key in ('repair','pricing_devex','pricing_weight_rejected')))
   check(name+'_policy_unchanged',v['policy']['solve_tolerance']==2**-44 and v['policy']['max_refinements']==3 and v['policy']['solve_refinement'] is False and v['policy']['adaptive_refactor'] is False and v['policy']['hypersparse'] is False)
   check(name+'_direct_strict_refuses',len(v['direct_strict'])==7 and all(r['accepted'] is False for r in v['direct_strict']))
   check(name+'_all_pairs',len(v['trials'])==14 and {(r['round'],r['algorithm']) for r in v['trials']}=={(round,a) for round in range(1,8) for a in ('dual','unspecified')})
   check(name+'_outcomes',all(r['returned_trial']==(r['algorithm']=='dual') for r in v['trials']))
   check(name+'_finite_costs',all(type(r[k]) in (float,int) and math.isfinite(r[k]) and r[k]>=0 for r in v['trials'] for k in ('seconds','bytes','events','compile_seconds','recompile_seconds','gc_seconds')))
   check(name+'_measured_compile0',all(r['compile_seconds']==r['recompile_seconds']==0 for r in v['trials'] if r['round']>2))
   check(name+'_case_marker',text.count('CASE_COMPLETE '+name+' published=true iterations=0')==1)
  check('resources',all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in [json.loads(line) for line in (C.R/'guard/resources.jsonl').read_text().splitlines()]))
 except Exception:error=traceback.format_exc()
 accepted=error is None and bool(checks) and all(checks.values());C.fresh(C.R/'audit.json',dict(accepted=accepted,checks=checks,error=error));return accepted
if __name__=='__main__':raise SystemExit(0 if main() else 1)
