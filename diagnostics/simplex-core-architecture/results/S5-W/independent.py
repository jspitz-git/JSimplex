"""Exclusive independent author-side offline checks, no prior script import."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;e=json.loads((H/'evidence.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
s=(R/'src/simplex_start.jl').read_text();j=(R/'src/simplex.jl').read_text();d=(R/'src/simplex_diagnostics.jl').read_text();block=(H/'original-testset.txt').read_text();report=D/'S5-CRASH-FALLBACK-OBSERVER-ORACLE.md';plan=R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-preparation.md'
c=dict(full189=len(e['sha256'])==189 and all(sha(k)==v for k,v in e['sha256'].items()),source19=len(e['checks'])==19 and e['all_passed'] is True and all(e['checks'].values()),entry14=len(json.loads((H/'entry.json').read_text())['checks'])==14 and json.loads((H/'entry.json').read_text())['all_passed'] is True,original6=block in (R/'test/simplex_start_state_tests.jl').read_text() and block.count('@test ')==6,conditional_order=s.index('_invalidate_basis_checkpoints!(trial)')<s.index('        final_violation =') and d.index('    record_event!(d, reason)')<d.index('            d.observer(reason, state)'),copies7_entries26=2+6*4==26 and 'Seven owned vector containers, 26 copied entries' in report.read_text(),timing_native_limits='kernel_timing::Bool=false' in d and 'policy.solve_refinement || return true' in (R/'src/simplex_recovery.jl').read_text(),no_source_test_change=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml']))
files=[Path(__file__),H/'prepare.py',H/'entry.json',H/'host.json',H/'evidence.json',H/'original-testset.txt',report,plan]
x=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in files})
with (H/'independent.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));assert x['all_passed']
