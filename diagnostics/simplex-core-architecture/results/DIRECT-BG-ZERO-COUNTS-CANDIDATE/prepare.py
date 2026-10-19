"""One-shot offline candidate preparation; no Julia parsing or execution."""
from pathlib import Path
import hashlib,json
import source_contract as s
E=Path(__file__).resolve().parent;R=E.parents[3];original=R/'diagnostics/direct-bg-blocked-update/reproduce/panel.jl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
text=original.read_text();anchor='struct BGNoCounts end\n'
if text.count(anchor)!=1:raise RuntimeError('Constant insertion anchor')
text=text.replace(anchor,s.INSERT+anchor,1)
for old,new in s.REPLACEMENTS:
 if text.count(old)!=1:raise RuntimeError('Unique replacement')
 text=text.replace(old,new,1)
if s.inverse(text).encode()!=original.read_bytes():raise RuntimeError('Inverse mismatch')
with (E/'panel.jl').open('x') as f:f.write(text)
checks=s.checks(text);checks['byte_exact_inverse']=s.inverse(text).encode()==original.read_bytes()
checks['tests_preceded_candidate']=json.loads((E/'structural-red.json').read_text())['expected_red'] is True
checks['no_mutable_singleton']='BGPanelCounts() = BGPanelCounts(_BGB_ZERO_COUNTS)' in text and text.count('mutable struct BGPanelCounts')==1
checks['unchanged_mutation_methods']=text[text.index('@inline bump!'):text.index('counts(::BGNoCounts)')]==original.read_text()[original.read_text().index('@inline bump!'):original.read_text().index('counts(::BGNoCounts)')]
paths=sorted(p for p in original.parent.rglob('*') if p.is_file())
paths += [R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl',E/'panel.jl',E/'zero-counts-tests.jl',E/'source_contract.py',E/'structural-red.json',Path(__file__).resolve()]
record={'all_passed':all(checks.values()),'checks':checks,'sha256':{str(p):sha(p) for p in paths},'scope':'Offline source contract only; candidate/tests unparsed and unexecuted in Julia'}
with (E/'source-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':record['all_passed'],'checks':len(checks),'hashes':len(paths),'candidate_sha256':sha(E/'panel.jl')}))
if not record['all_passed']:raise SystemExit(1)
