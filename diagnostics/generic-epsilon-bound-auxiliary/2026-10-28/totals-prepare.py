from pathlib import Path
import json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');p=D/'contract.json';c=json.loads(p.read_text());c['expected_assertions']=59053;c['correctness_assertions']=8897;p.write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
p=D/'audit.py';s=p.read_text();old="int(cols[0])>1000";assert s.count(old)==1;s=s.replace(old,"int(cols[0])==con['expected_assertions']");p.write_text(s)
shutil.copyfile(__file__,D/'totals-prepare.py')
