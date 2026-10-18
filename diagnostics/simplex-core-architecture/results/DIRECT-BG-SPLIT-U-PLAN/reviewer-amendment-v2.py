#!/usr/bin/env python3
"""One-shot bounded I1 amendment review; no original check execution."""
import difflib,hashlib,json,pathlib
R=pathlib.Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
Q=pathlib.Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
initial=json.loads((Q/'review-initial.json').read_text())
author=json.loads((Q/'author-check.json').read_text())
fix=json.loads((Q/'review-fix.json').read_text())
checks={};diffs={};bindings={}
for path,b in fix['bindings'].items():
    old=R/b['before_path'];new=R/path
    before,after=old.read_text(),new.read_text()
    checks[path+'_before_binding']=sha(old)==b['before_sha256']==initial['readtime_sha256'][path]==author['source_readtime_sha256'][str(new)]
    checks[path+'_after_binding']=sha(new)==b['after_sha256']
    edits=[op for op in difflib.SequenceMatcher(a=before.splitlines(keepends=True),b=after.splitlines(keepends=True)).get_opcodes() if op[0]!='equal']
    checks[path+'_single_paragraph_replacement']=len(edits)==1 and edits[0][0]=='replace' and edits[0][2]-edits[0][1]==1 and edits[0][4]-edits[0][3]==1
    diffs[path]=''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile=b['before_path'],tofile=path))
    bindings[path]={'before_path':b['before_path'],'before_sha256':sha(old),'after_sha256':sha(new)}
checks['unchanged_other_initial_read_bindings']=all(sha(R/p)==h for p,h in initial['readtime_sha256'].items() if p not in bindings)
checks['unchanged_initial_review_evidence']=all(sha(Q/p)==h for p,h in initial['evidence_sha256'].items())
spec=(R/'docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md').read_text()
plan=(R/'docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md').read_text()
checks['spec_logical_state_and_reserve_identity']=all(t in spec for t in ('Logical live values, row/column order, encoded handles, unique ownership and complete partition','Their original backing identities and physical positions need not survive; their consistency must survive.','separately from earlier committed numerical edits'))
checks['task1_specific_failure_composition']=all(t in plan for t in ('Include row reserve success followed by split allocation failure.','do not demand backing-identity rollback','repair reciprocal physical row positions'))
checks['both_keep_free_split_handle_contract']=all('free-split helper itself changes no active extent or row handle' in text for text in (spec,plan))
files=['review-initial.md','review-initial.json','reviewer-check-v1.py','reviewer-check-v1.json','reviewer-record-initial.py','author-check.json','host.json','spec.before-review.md','plan.before-review.md','review-fix.json','reviewer-amendment-v2.py']
out={'scope':'split free block BG plan','amendment_scope':'bounded I1 clarification only','all_passed':all(checks.values()),'checks':checks,'resolved':['I1'],'bindings':bindings,'exact_diff':diffs,'evidence_sha256':{p:sha(Q/p) for p in files},'no_original_check_rerun':True,'no_julia_or_candidate':True}
with (Q/'reviewer-amendment-v2.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':checks}))
assert out['all_passed']
