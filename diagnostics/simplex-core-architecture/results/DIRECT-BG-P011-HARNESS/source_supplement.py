"""Correct one author expectation without rerunning the preserved source checker."""
from pathlib import Path
import json,hashlib
import control as c
D=Path(__file__).resolve().parent;v=c.rd(D/'source-check.json');cmd=c.config('p011-300')['command'];driver=str(c.PROBE/'driver.jl');i=cmd.index(driver)
checks=dict(original_only_two_args_false=[k for k,x in v['checks'].items() if x is not True]==['two_args'],
 actual_command_length=len(cmd)==11,exact_two_driver_arguments=cmd[i+1:]==[c.config('p011-300')['payload'],c.config('p011-300')['stage']],
 old_failure_preserved=v['all_passed'] is False,unchanged_subject=all(c.sha(p)==h for p,h in v['sha256'].items()))
c.save(D/'source-supplement.json',dict(all_passed=all(checks.values()),checks=checks,command=cmd,sha256={str(D/n):c.sha(D/n) for n in ['source_check.py','source-check.json','source_supplement.py','control.py']},explanation='Original check expected total command length12; actual11 has exactly two driver arguments. No control/driver change or rerun.'))
if not all(checks.values()):raise RuntimeError(checks)
print(json.dumps(dict(all_passed=True,checks=len(checks))))
