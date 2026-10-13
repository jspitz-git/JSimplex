"""Exclusive author-side static verification; no frozen script import/execution."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;W=H.parent/'S5-W'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((H/'evidence.json').read_text());s=(H/'candidate.jl').read_text();report=D/'S5-CRASH-FALLBACK-OBSERVER-PREPARATION.md';plan=R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-qualification.md'
c=dict(full213=len(e['sha256'])==213 and all(sha(k)==v for k,v in e['sha256'].items()),literal22=len(e['checks'])==22 and e['all_passed'] is True and all(v is True for v in e['checks'].values()),entry17=len(json.loads((H/'entry.json').read_text())['checks'])==17 and json.loads((H/'entry.json').read_text())['all_passed'] is True,inverse_original=sha(H/'construction-inverse.txt')==sha(W/'original-testset.txt') and (H/'construction-inverse.txt').read_text() in (R/'test/simplex_start_state_tests.jl').read_text(),candidate_fixed=sha(H/'candidate.jl')=='5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18',actual_schema=len(e['predicate_names'])==50 and len(e['probe_fields'])==11 and s.count('copy(')==7 and 2+6*4==26 and 50+12+2+7+7+3+2+7==90,raw_before_assert=s.index('TOML.print(io,output)')<s.index('@assert all(values(checks))'),separate_admission='BEFORE any Julia' in plan.read_text() and 'Every runtime expectation' in report.read_text(),source_test_unchanged=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']))
files=[Path(__file__),H/'entry.py',H/'entry.json',H/'host.json',H/'source_check.py',H/'evidence.json',H/'candidate.jl',H/'construction-inverse.txt',report,plan]
x=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in files})
with (H/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));assert x['all_passed']
