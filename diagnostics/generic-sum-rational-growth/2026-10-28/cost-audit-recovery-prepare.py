from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28')
p=D/'audit-qualified-complete.py';s=p.read_text()
prefix='''import os
# Record this new postexit observer's identity without granting any exception.
observation_stat=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
observation=dict(pid=os.getpid(),ppid=os.getppid(),pgid=int(observation_stat[2]),sid=int(observation_stat[3]),start_ticks=int(observation_stat[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=[x.decode(errors='replace') for x in Path('/proc/self/cmdline').read_bytes().split(b'\\0') if x])
put('qualified-audit-invoker.json',observation)
'''
s=s.replace('import tomllib,re,statistics as stats,math\n','import tomllib,re,statistics as stats,math\n'+prefix)
s=s.replace("'audit-qualified-complete.py'","'audit-qualified-recovery.py'")
s=s.replace("'correctness-qualification/result-review.json']","'correctness-qualification/result-review.json','qualified-audit-invoker.json']")
compile(s,str(D/'audit-qualified-recovery.py'),'exec');(D/'audit-qualified-recovery.py').write_text(s)
(D/'cost-audit-host-rejection.json').write_text(json.dumps(dict(original_auditor=str(p),original_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),executed_once=True,accepted_output_written=False,stopped_at='host(extra) strict historical group/session occupancy check after unchanged() and all raw windows/preparation validation',exception='RuntimeError: historical group/session or changed unrelated process',failed_occupant_not_captured=True,subsequent_readonly_observation={'boot_id':'781795f4-f7af-4c3b-9ce9-45c7cae76ecb','self':153646,'parent':153645,'groups':653,'collisions':[]},occupant_cause='unknown; transient observer PID reuse is a hypothesis only',Julia_or_measurement_rerun=False,new_recovery_sha256=hashlib.sha256(s.encode()).hexdigest(),new_host_policy='unchanged exact full653groups ANDsessions; no new allowance or PID exception'),indent=2)+'\n')
(D/'cost-audit-recovery-prepare.py').write_text(Path(__file__).read_text());print('separate postexit observer prepared; identical strict gates/no identity allowance')
