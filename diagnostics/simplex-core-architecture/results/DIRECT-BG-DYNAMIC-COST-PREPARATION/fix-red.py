"""New offline regression reproduction; no auditor/Julia/launcher execution."""
from pathlib import Path
import json
E=Path(__file__).resolve().parent
# Use a new synthetic prefix test program derived from the already saved test text;
# execute no old test executable and write a separate fixed-path RED result.
s=(E/'prefix-tests.py').read_text();start=s.index(" _,prefix=e.output_checks(out,cfg,partial=True);check('valid_partial_prefix'");stop=s.index(" p=out/'window-1-2.toml'",start)
s=s[:stop]+''' # Both individually valid modes and signed zero must be rejected before cell completion.
 for field,value in [('outputs',None),('modes',['direct']*3)]:
  p=out/'window-1-2.toml';before=p.read_text();d=e.tomllib.loads(before)
  if field=='outputs':d['outputs'][2][1]=token(-0.)
  else:d[field]=value
  p.write_text(toml(d))
  try:e.output_checks(out,cfg,partial=True)
  except (RuntimeError,ValueError,KeyError,TypeError):checks['partial_reject_'+field]=True
  else:checks['partial_reject_'+field]=False
  p.write_text(before)
checks['first_process_stop_gate']='first_process_viable' in (D/'control.py').read_text()
save(D/'fix-red.json',dict(all_passed=all(checks.values()),checks=checks,expected_missing=['partial_reject_outputs','partial_reject_modes','first_process_stop_gate'],scope='Synthetic prefix behavior and source stop-gate RED; no numerical execution'))
print('Expected RED', [k for k,v in checks.items() if not v])
'''
# This is deliberately saved before execution and never overwrites prior scripts/results.
with (E/'fix-red-generated.py').open('x') as f:f.write(s)
