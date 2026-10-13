from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
# Preserve initial controls before a prospective completeness gate is added.
for n in ('auditor.py','launcher-reviewed.py'):
 with (D/(n+'.before-grid')).open('xb') as f:f.write((D/n).read_bytes())
p=D/'auditor.py';p.write_text(p.read_text()+'''

def complete_grid(pairs):
 require(set(pairs)==set(range(1,11)), 'incomplete pair grid')
 for pair in range(1,11):
  require(set(pairs[pair])=={'reference','candidate'}, 'incomplete side grid')
  paired(pairs[pair]['reference'],pairs[pair]['candidate'])
 return True
''')
p=D/'launcher-reviewed.py';p.write_text(p.read_text().replace('from auditor import validate,paired','from auditor import validate,paired,complete_grid').replace("  require(refs()==a['refs'] and inventory_ok", "  complete_grid(raw_pairs)\n  require(refs()==a['refs'] and inventory_ok"))
