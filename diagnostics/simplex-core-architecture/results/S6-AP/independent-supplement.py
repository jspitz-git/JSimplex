"""Exclusive correction of a literal text assertion; preserve original false result."""
from pathlib import Path
import json,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;p=R/'docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md';d=json.loads((H/'independent.json').read_text());t=' '.join(p.read_text().split())
c={'original_false_preserved':d['all_passed'] is False and d['checks']['no_new_execution_admission'] is False,'other_three_original_checks_pass':all(v for k,v in d['checks'].items() if k!='no_new_execution_admission'),'actual_prohibition_text':'SOURCE/EVIDENCE ONLY: no Julia/query/parser/import/compile/native/numerical call' in t and 'old script/auditor rerun or new numerical allowance.' in t,'conditional_new_evidence_only':'Continue only when genuinely new original-run evidence or user clarification is available.' in t}
pins={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [p,H/'independent.json',H/'independent.py',Path(__file__)]}
with (H/'independent-supplement.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=pins,reason='Original checker demanded literal no new numerical allowance; the plan expresses no ... old script/auditor rerun or new numerical allowance. Plan is unchanged.'),f,indent=2);f.write('\n')
print(c);assert all(c.values())
