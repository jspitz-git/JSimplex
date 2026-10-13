"""Exclusive offline refusal test using exact corrected invocation block; no Julia."""
from common_reviewed import *
import subprocess,sys,textwrap
text=(H/'launcher-reviewed.py').read_text();block=text.split(' invocation=dict(')[1].split('\nelse:raise ValueError(mode)')[0];block=textwrap.dedent(' invocation=dict('+block)
scratch=H/'synthetic-refusal';scratch.mkdir();scope=dict(H=scratch,G=G,O=scratch/'never-created',pins=scratch/'missing-pins.json',sys=sys,time=time,subprocess=subprocess,command=lambda:[],absent=absent,dump=dump,R=R)
try:exec(compile(block,'exact-corrected-invocation-block','exec'),scope)
except SystemExit as e:code=e.code
record=read(scratch/'guard-invocation.json');log=(scratch/'guard-output.log').read_text()
checks={'pre_output_refusal_exit1':code==1 and record['returncode']==1,'refusal_log_preserved':bool(log) and 'missing-pins.json' in log,'no_guard_output_directory':not (scratch/'never-created').exists(),'exact_corrected_block':"dump(H/'guard-invocation.json',invocation)" in block,'elapsed_auditor_gate':"process['elapsed_including_launch']<=120" in (H/'audit-reviewed.py').read_text()}
dump(H/'correction-checks.json',dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in [H/'correction_checks.py',scratch/'guard-invocation.json',scratch/'guard-output.log']},scope='Exact corrected invocation block with deliberately missing manifest; no child created, no Julia.'));assert all(checks.values())
