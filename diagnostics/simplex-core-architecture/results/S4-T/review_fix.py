from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-T';p=D/'S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT.md';s=p.read_text();sha=lambda b:hashlib.sha256(b).hexdigest()
old='Installed PrecompileTools1.3.4 runs BOTH workload bodies when output generation OR\nverbose[] is true.'
new='Installed PrecompileTools1.3.4 gates BOTH workload bodies by\n`(generating_output && workload_enabled(module)) || verbose[]`. workload_enabled first\nchecks the enabled preference constant, then the module precompile_workload preference\n(with the installed catch/default behavior). Output generation alone is not sufficient.'
red=dict(missing_enabled_preference_guard=old in s and new not in s)
assert all(red.values());before=sha(p.read_bytes());saved=E/'report-before-workload-guard.md'
with saved.open('x') as f:f.write(s)
s=s.replace(old,new);p.write_text(s)
checks=dict(exact_guard_stated=new in s,old_sufficient_condition_removed=old not in s,old_hash_preserved=sha(saved.read_bytes())==before,launch_still_unsupported='launch_supported\nis false' in s)
obj=dict(red=red,checks=checks,before={str(p):dict(sha256=before,preserved=str(saved))},after={str(p):sha(p.read_bytes())},scope='ONE offline documentation fix for reviewer Minor; original604 inventory binds before text; no prior script or numerical rerun')
with (E/'review-fix.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(obj));assert all(checks.values())
