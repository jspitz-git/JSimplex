from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-U-PLAN';D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
spec=R/'docs/superpowers/specs/2026-10-16-direct-bg-dynamic-upper.md';plan=R/'docs/superpowers/plans/2026-10-16-direct-bg-dynamic-upper.md';close=E/'close.py'
for p,n in [(spec,'spec.md.before-review'),(plan,'plan.md.before-review'),(close,'close.py.before-review')]:
 with (E/n).open('xb') as f:f.write(p.read_bytes())
s=spec.read_text();p=plan.read_text();c=close.read_text()
red={'q_aware_builder_missing':'iterate stable column_id=1:n through column_position' not in s,'old_full_inventory_call_present':'validate_sources();' in c}
if not all(red.values()):raise RuntimeError('Unexpected original state')
s=s.replace('Rows and columns have stable physical identities1:n.','Rows have stable physical identities1:n. Stable column IDs are ORIGINAL BASIS positions, exactly the exported permutation q[j] for logical CSC column j; they are not renumbered to j. Initialize column_order=copy(q), column_position=invperm(q), and identity row maps. Validate q as a dimension-matching permutation before publication; invalid q is rejected. These two owned column maps are already in the eight-vector ledger, not additional maps.')
s=s.replace('Fill slots in CSC column order; append row lists in increasing stable column identity and column lists in logical row order.','Pass exported q unchanged to `_bg_slots(U,q)`; iterate stable column_id=1:n through column_position (inverse q), selecting CSC column j=column_position[column_id]. Within that column visit stored rows in ascending logical row order. Append its slots to the column list keyed by column_id, and to the row lists in ascending column_id. This q-aware build preserves reference elimination order for nonidentity q while logical materialization through column_order reproduces the original CSC U. Do not change arithmetic order by assigning stable IDs from CSC order. Computing inverse q and maps is O(n).')
s=s.replace('initialize identity arena;','initialize identity arena with identity q;')
p=p.replace('_bg_slots(U::SparseMatrixCSC{Float64,Int})::BGSlotUpper','_bg_slots(U::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGSlotUpper')
p=p.replace('No solve here.','Repeat with q=[3,1,2]: column_order=q, column_position=[2,3,1], each row list sorted by original basis ID, column lists keyed by q[j], and logical materialization identical to input. Row1 stable IDs must be[1,2,3], not CSC visit order[3,1,2]. Reject duplicate/out-of-range/wrong-length q before publication. No solve here.')
p=p.replace('inverse transforms restore bit patterns.','inverse transforms restore bit patterns. Repeat swaps/rotations under q=[3,1,2] and verify both logical order and stable-ID row order.')
p=p.replace('Import identity arena on genuine exporter fallback.','Pass the exact exported q into the q-aware builder, without renumbering basis IDs; import identity arena with identity q on genuine exporter fallback.')
p=p.replace('Add focused n0/1/3/4 sequences','Include explicit nonidentity-q construction/update/copy/refactor cases and compare the stable-column-ID arithmetic trace against packed direct BG; a nonidentity permutation cannot be assumed from random fixtures. Add focused n0/1/3/4 sequences')
c=c.replace('from control import full_host,validate_sources,rd,sha,save,require,bindings','from control import full_host,rd,sha,save,require,bindings,git,W,MASTER')
c=c.replace("validate_sources();require(bindings(rd(E/'source-pins.json')),'Readtime source drift')", "require(bindings(rd(E/'source-pins.json')) and bindings(rd(E/'helper-pins.json')),'Bounded readtime/helper drift')\nrequire(git('rev-parse','HEAD')=='47ec2fc41fa3d21df9569e64a3b5a3e4ec7fa184','Diagnostic ref drift')\nrequire(git('rev-parse','master')==MASTER and git('rev-parse','HEAD',cwd=W)==MASTER,'Master refs drift')\nrequire(MASTER+'\\trefs/heads/master' in git('ls-remote','origin','refs/heads/master'),'Remote master drift')\nfor root in (R,W):\n require(not git('diff','HEAD','--name-only','--','src','test','.github','Project.toml',cwd=root),'Tracked source/test/CI/project drift')\n# No runtime inventory or environment requalification: planning uses 15 selected readtime pins only.")
c=c.replace('source_runtime_unchanged=True','selected15_sources_and_helpers_unchanged=True')
spec.write_text(s);plan.write_text(p);close.write_text(c)
save(E/'helper-pins.json',dict(scope='New planning closure helper readtime pins only; no runtime inventory',sha256={str(D/n):sha(D/n) for n in ['control.py','guard.py','host.json']}))
green={'q_builder': 'iterate stable column_id=1:n through column_position' in s,'q_maps':'column_order=copy(q), column_position=invperm(q)' in s,'q_interface':'q::Vector{Int}' in p,'q_fixture':'q=[3,1,2]' in p,'q_lifecycle':'nonidentity-q construction/update/copy/refactor' in p,'no_old_inventory':'validate_sources' not in c,'bounded_checks':'selected15_sources_and_helpers_unchanged' in c,'old_author_preserved':(E/'self-review.json').exists()}
if not all(green.values()):raise RuntimeError(green)
save(E/'review-fix.json',dict(all_passed=True,red=red,green=green,scope='Offline document amendment only; no Julia or implementation',sha256={str(x):sha(x) for x in [spec,plan,close,E/'helper-pins.json',E/'spec.md.before-review',E/'plan.md.before-review',E/'close.py.before-review']}))
print('Offline amendment RED2/GREEN8 PASS')
