from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((Q/'reviewer-final-check.json').read_text());checks={}
checks['only_prior_failure_was_announced_ledger_binding']=[k for k,v in prior['checks'].items() if not v]==['corrected_binding']
oldledger=Q/'adapter-work-memory.md.before-cold-budget';newledger=C/'adapter-work-memory.md'
paragraph='''The cold scalar reference creates one ephemeral BGPanelFactor per update (256
wrappers across both backends), with workspace=nothing; it is not the future
timed reference route. Test-set objects, returned NamedTuples and vectors are
additional cold allocations, not included in the candidate scratch cap.
'''
checks['ledger_only_additive_budget_paragraph']=newledger.read_text().count(paragraph)==1 and newledger.read_text().replace(paragraph,'',1)==oldledger.read_text()
ledgerkey=str(newledger.relative_to(R))
checks['all_prior_reviewed_candidate_bytes_accounted']=all(sha(oldledger if p==ledgerkey else R/p)==h for p,h in prior['sha256'].items())
fix=json.loads((Q/'review-fix.json').read_text())
fixresolution={str(newledger):str(oldledger)}
checks['fix_receipt_exact_named_binding']=all(sha(Path(fixresolution.get(p,p)))==h for p,h in fix['sha256'].items())
first=json.loads((Q/'review-first.json').read_text());firstresolution=prior['initial_binding_resolution']
checks['initial_receipt_exact_named_binding']=all(sha(R/firstresolution.get(p,p))==h for p,h in first['sha256'].items())
checks['distinct_ledger_history_versions']=firstresolution[ledgerkey]==str((Q/'adapter-work-memory.md.before-review').relative_to(R)) and sha(oldledger)!=sha(Q/'adapter-work-memory.md.before-review')
o=json.loads((C/'overlay-manifest.json').read_text());stage=Path(o['stage'])
checks['final_original_source_pins']=all(sha(R/p)==h for p,h in o['original_sha256'].items())
checks['final_staged_source_pins']=all(sha(stage/p)==h for p,h in o['stage_sha256'].items())
files=[p for p in C.iterdir() if p.is_file()]+[Q/'REPORT.md',Q/'reviewer-final-check.py',Q/'reviewer-final-check.json',Q/'reviewer-final-binding.py',Q/'review-fix.py',Q/'review-fix.json',Q/'cold-budget-note.txt',oldledger]
out=dict(all_passed=all(checks.values()),scope='New final binding resolution after additive cold-budget ledger note; source-only, no Julia',checks=checks,initial_binding_resolution=firstresolution,fix_binding_resolution=fixresolution,sha256={str(p.relative_to(R)):sha(p) for p in files})
with (Q/'reviewer-final-binding.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':checks},indent=2))
