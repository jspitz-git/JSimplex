"""W-only publication closure; exclusive output. Execute before staging/publication."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[4];r=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=json.loads((r/'source-contract.json').read_text());i=json.loads((r/'independent.json').read_text());f=json.loads((r/'review-fix.json').read_text());h=json.loads((r/'host-after.json').read_text());before=json.loads((r/'host-before.json').read_text())
review=root/'diagnostics/simplex-core-architecture/S4-PUBLIC-CONTROLLER-ATTEMPT-CONTRACT-REVIEW.md'
reviewtext=' '.join(review.read_text().split())
checks={
 'source_checks_pass':a['all_passed'] and len(a['checks'])==22,
 'independent_eight_pass':i['all_passed'] and len(i['checks'])==8,
 'independent_bound_evidence_unchanged':all(sha(root/p)==v for p,v in i['bound_sha256'].items()),
 'review_correction_pass':f['all_passed'] and len(f['green'])==5 and all(f['red_expected_findings'].values()),
 'seven_correction_bound_files_unchanged':len(f['sha256'])==7 and all(sha(root/p)==v for p,v in f['sha256'].items()),
 'final_review_accepted':'final PASS for source/evidence-only publication' in reviewtext and 'No unresolved Critical, Important or Minor findings remain.' in reviewtext,
 'user_six_unchanged':all(sha(p)==v for p,v in before['user_hashes'].items()),
 'host_groups_absent_master_unchanged':not h['matches'] and h['boot_id']==before['boot_id'] and h['refs']==before['refs'],
 'source_test_CI_project_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml'],cwd=root,text=True),
 'continuation_source_only': 'S4-W source-only attempt ledger completed' in (root/'diagnostics/simplex-core-architecture/STATUS.md').read_text() and 'finite COMPLETE prospective public-route budget' in (root/'docs/superpowers/plans/2026-10-12-hh-postsolve-dual-work-contract.md').read_text()
}
paths=[p for p in r.iterdir() if p.is_file()]+[review,root/'diagnostics/simplex-core-architecture/S4-PUBLIC-CONTROLLER-ATTEMPT-CONTRACT.md',root/'diagnostics/simplex-core-architecture/STATUS.md',root/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',root/'docs/superpowers/plans/2026-10-12-hh-postsolve-dual-work-contract.md']
out={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p.relative_to(root)):sha(p) for p in paths},'scope':'Prepublication closure; source-only evidence, not numerical qualification. Original evidence and preserved before texts remain unchanged.'}
with (r/'closure.json').open('x') as g:json.dump(out,g,indent=2);g.write('\n')
print(json.dumps({'checks':checks,'all_passed':out['all_passed']}));raise SystemExit(0 if out['all_passed'] else 1)
