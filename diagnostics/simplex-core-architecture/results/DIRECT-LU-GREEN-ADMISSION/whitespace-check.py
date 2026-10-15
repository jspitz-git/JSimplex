"""Separate exact exception for four byte-identical focused slices; execute once."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-ADMISSION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((D/'staging.json').read_text());spec=[('markowitz-fill.jl',25),('markowitz-sparse.jl',52),('markowitz-triangular.jl',36),('stability.jl',21)]
paths=[str((D/'focused'/n).relative_to(R)) for n,_ in spec]
expected=''.join(f'{p}:{line}: new blank line at EOF.\n' for p,(_,line) in zip(paths,spec))
r=subprocess.run(['git','diff','--cached','--check'],cwd=R,text=True,capture_output=True)
checks=dict(exact_four_warnings=r.returncode==2 and r.stdout==expected and r.stderr=='',four_frozen_copies=all((D/'focused'/n).read_bytes()==(A/'focused'/n).read_bytes() for n,_ in spec),four_current_source_slices=all((D/'focused'/v['output']).read_bytes()==(R/v['source']).read_bytes()[v['start_byte']:v['end_byte']] for v in s['focused'] if v['output'] in {n for n,_ in spec}))
clean=subprocess.run(['git','diff','--cached','--check','--','.',*[':(exclude)'+p for p in paths]],cwd=R,text=True,capture_output=True)
checks['everything_else_clean']=clean.returncode==0 and clean.stdout==clean.stderr==''
result=dict(all_passed=all(checks.values()),checks=checks,expected_stderr='',expected_stdout=expected,git_exit=2,scope='Only four unchanged exact source-slice EOF blank lines; no blanket whitespace waiver',sha256={str(p.relative_to(R)):sha(p) for p in [D/'whitespace-check.py',D/'publication.py',D/'staging.json',*[(D/'focused'/n) for n,_ in spec],*[(A/'focused'/n) for n,_ in spec]]})
with (D/'whitespace-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=checks)))
if not result['all_passed']:raise SystemExit('Unqualified whitespace difference')
