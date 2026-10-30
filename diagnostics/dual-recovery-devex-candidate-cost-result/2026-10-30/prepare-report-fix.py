from pathlib import Path
import ast,json,hashlib,subprocess
T=Path('/tmp/devex-candidate-cost-run-20261030');D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-candidate-cost-result/2026-10-30');old=(T/'write-report.py').read_text();lines=old.splitlines(keepends=True)
if not lines[10].endswith('|"\n'):raise RuntimeError('unexpected initial line')
new=''.join([*lines[:10],lines[10][:-1]+')\n',*lines[11:]])
checks={}
try:ast.parse(old);checks['initial_source_rejected_syntax']=False
except SyntaxError as e:checks['initial_source_rejected_syntax']=e.lineno==11 and 'never closed' in e.msg;initial_error=dict(type='SyntaxError',line=e.lineno,message=e.msg,source_line=e.text,scope='new AST check of preserved source; initial execution failure captured in tool output')
checks['single_closing_parenthesis_only']=new==old.replace(lines[10],lines[10][:-1]+')\n',1) and len(new)==len(old)+1
ast.parse(new);checks['corrected_source_AST_accepted']=True
if not all(checks.values()):raise RuntimeError(str(checks))
with (T/'write-report-2.py').open('x') as f:f.write(new)
for n in ('write-report.py','write-report-2.py','prepare-report-fix.py'):
 with (D/n).open('xb') as f:f.write((T/n).read_bytes())
with (D/'report-writer-fix.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,initial_execution_exit=1,initial_error=initial_error,change='one closing parenthesis on row append; no data, math, auditor or numerical process change',bindings={str(T/n):hashlib.sha256((T/n).read_bytes()).hexdigest() for n in ('write-report.py','write-report-2.py','prepare-report-fix.py')}),f,indent=2);f.write('\n')
p=subprocess.run(['/usr/bin/python3','-B',str(T/'write-report-2.py')],capture_output=True,text=True)
with (D/'report-writer-2.log').open('x') as f:f.write(p.stdout+p.stderr)
print(p.stdout+p.stderr);raise SystemExit(p.returncode)
