"""One-shot offline preparation closure; no Julia or launch entrypoints."""
from control import *
def main():
 prepared=preparation();validate_environment();validate_stage_binding();validate_probe()
 h=rd(D/'host-closure.json')
 checks={
 'accepted_independent_preparation':rd(D/'review.json')['accepted'] is True and rd(D/'review.json')['launch_admitted'] is False,
 'source18':rd(D/'source-check.json')['all_passed'] is True and len(rd(D/'source-check.json')['checks'])==18 and bindings(rd(D/'source-check.json')),
 'extended1298':rd(D/'tests-extended.json')['all_passed'] is True and rd(D/'tests-extended.json')['count']==1298,
 'independent2950':rd(D/'independent-check.json')['all_passed'] is True and rd(D/'independent-check.json')['count']==2950 and bindings(rd(D/'independent-check.json')),
 'dict_fix3':rd(D/'dict-fix.json')['all_passed'] is True and bindings(rd(D/'dict-fix.json')),
 'fresh_host_277':host_safe(h) and len(h['groups'])==277 and h['head']==ENTRY,
 'master_unchanged':git('rev-parse','master')==MASTER,
 'tracked_index_clean':not git('diff','--name-only') and not git('diff','--cached','--name-only'),
 'no_launch':not (D/'runs').exists() and not (D/'outers').exists(),
 'ledger_snapshot':(R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md').read_bytes()==(D/'progress.md.after-zero-harness').read_bytes(),
 }
 # Only initial oracle was revised after the initial1104 checks.
 initial=rd(D/'tests.json');checks['initial1104_preserved']=initial['all_passed'] is True and initial['count']==1104 and all(sha(D/(n+'.initial' if n=='oracle.py' else n))==v for n,v in initial['sha256'].items())
 checks['extended_bindings']=all(sha(D/n)==v for n,v in rd(D/'tests-extended.json')['sha256'].items())
 paths=sorted(p for p in D.iterdir() if p.is_file())
 record=dict(all_passed=all(checks.values()),checks=checks,julia_invoked=False,sha256={str(p):sha(p) for p in paths})
 save(D/'closure.json',record);require(record['all_passed'],'Closure failed')
 print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(paths))))
if __name__=='__main__':main()
