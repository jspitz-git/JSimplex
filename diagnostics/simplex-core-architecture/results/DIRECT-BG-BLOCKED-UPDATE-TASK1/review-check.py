from pathlib import Path
import hashlib,json
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
q=root/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK1'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
initial=json.loads((q/'review-initial.json').read_text())
changed={}
for name in ['panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json']:
    key='diagnostics/direct-bg-blocked-update/reproduce/'+name
    changed[name]={'recorded':initial['sha256'][key], 'before_review':h(q/(name+'.before-review')), 'current':h(root/key)}
unchanged={p:h(root/p)==v for p,v in initial['sha256'].items() if not p.startswith('diagnostics/direct-bg-blocked-update/reproduce/')}
source_map=json.loads((root/'diagnostics/direct-bg-blocked-update/reproduce/source-map.json').read_text())
deps={p:h(root/p)==v for p,v in source_map['dependencies'].items()}
testsfirst=json.loads((q/'tests-first.json').read_text()); fixfirst=json.loads((q/'review-tests-first.json').read_text())
r={'initial_deliverable_bindings':changed,'initial_unchanged_bindings':unchanged,'source_map_dependencies':deps,'initial_report_hash_valid':h(q/'review-initial.md')==initial['report_sha256'],'original_tests_first_valid':h(q/'panel-tests.first.jl')==testsfirst['tests_sha256'],'fix_tests_first_current_valid':h(root/'diagnostics/direct-bg-blocked-update/reproduce/panel-tests.jl')==fixfirst['tests_sha256'],'fix_candidate_before_valid':h(q/'panel.jl.before-review')==fixfirst['candidate_before_probe_sha256'],'script_sha256':h(Path(__file__))}
with (q/'review-binding-check.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
