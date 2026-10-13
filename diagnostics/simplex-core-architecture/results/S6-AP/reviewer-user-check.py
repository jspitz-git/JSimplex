"""Fresh exclusive offline supplement check; never execute/import existing evidence scripts."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();H=R/'diagnostics/simplex-core-architecture/results/S6-AP';pins={};sizes={}
def sha(p):
 p=Path(p);key=str(p)
 if key not in pins:
  h=hashlib.sha256();n=0
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
  pins[key]=h.hexdigest();sizes[key]=n
 return pins[key]
def readj(p):sha(p);return json.loads(Path(p).read_text())
a=readj(H/'user-linkage.json');maps=readj(H/'user-reply-before-texts.json')['mappings'];first=readj(H/'reviewer-check.json')
bad=[p for p,v in a['sha256'].items() if sha(p)!=v]
old_report=H/'S6-TEST-MPS-FAILURE-PROVENANCE.md.before-user-reply';old_plan=H/'2026-10-13-test-mps-original-run-linkage.md.before-user-reply'
report=R/'diagnostics/simplex-core-architecture/S6-TEST-MPS-FAILURE-PROVENANCE.md';plan=R/'docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md'
rt=report.read_text();pt=' '.join(plan.read_text().split());ut=(H/'user-clarification.txt').read_text()
original=readj(H/'independent.json');supp=readj(H/'independent-supplement.json')
protected=['src','test','Project.toml','.github','.vscode']
prod_diff=subprocess.check_output(['git','diff','HEAD','--name-only','--',*protected],text=True).strip()
refs={k:subprocess.check_output(['git','rev-parse',k],text=True).strip() for k in ['HEAD','master']}
checks={
 'new_author_9_checks_8_bindings':a['all_passed'] is True and len(a['checks'])==9 and all(a['checks'].values()) and len(a['sha256'])==8 and not bad,
 'all_3_preservation_mappings':len(maps)==3 and all(sha(x['preserved'])==x['sha256'] for x in maps),
 'old_report_plan_match_first_review':sha(old_report)=='0ee580015b7b8ecadbf8f54e94f3f09cc25b11ac3c4bf7a00d579611fd03bf3d' and sha(old_plan)=='c0e95eef6eefc053c3083a0672016dd4c4f500d6a8b9af52b9dfc8c79a2074cd',
 'initial_review_and_check_unchanged':sha(H/'review.md')==sha(H/'review.md.before-user-reply')=='d8297ce814de042f8cc96fb4961bfb9a20083ea1410f623f11c35ec4d45b746a' and sha(H/'reviewer-check.json')=='adc8b147c5e01927f3c50103b59bcab941dbff1b0f2ce1a4d313f6bc93c0dee5',
 'old_record_exact_suffix':rt.split('## Initial record before that clarification\n\n',1)[1]==old_report.read_text().split('\n\n',1)[1],
 'original_false_and_supplement_unchanged':sha(H/'independent.json')==first['sha256'][str(H/'independent.json')] and sha(H/'independent-supplement.json')==first['sha256'][str(H/'independent-supplement.json')] and original['all_passed'] is False and original['checks']['no_new_execution_admission'] is False and supp['all_passed'] is True,
 'user_reported_active_branch_settings':all(t in ut for t in ['filename = "test.mps"','reader_native = true','basis_update=:huangfu_hall','basis_refactorization=:native','refactorization_interval=320','algorithm=:dual','simplex_strategy=:legacy','pricing=:steepest_edge','time_limit=Inf','iteration_limit=1_000_000','relax_integrality=true']) and 'not an original script-file byte capture' in ut,
 'bounded_current_missing_paths':not Path('/mnt/c/tmp/test.mps').exists() and not Path('/mnt/c/tmp/capture-failure.jl').exists(),
 'report_source_witness_and_runtime_limits':all(t in rt for t in ['not a captured runtime configuration','Approximate time cannot select a commit','No original point/basis/dual witness was supplied','Defaults for options not','The inactive else branch']),
 'conditional_new_evidence_without_repeat':all(t in pt for t in ['Do not ask for this script again','Continue only when genuinely new original source/runtime metadata, input hash, or already stored point/basis/dual certificate input is available.','no equivalent search without new information.','User-reported settings are not runtime observations.']),
 'no_new_numerical_allowance':all(t in pt for t in ['SOURCE/EVIDENCE ONLY: no Julia/query/parser/import/compile/native/numerical call','old script/auditor rerun or new numerical allowance.','neither this plan nor the supplied old command authorizes one.']),
 'local_refs_and_no_production_changes':refs=={'HEAD':'393067527dc04eb817c6af75347770b69a1905ee','master':'d02416c108f06fcd41d58e0a1980b70a51fef9ef'} and not prod_diff
}
sha(Path(__file__).resolve())
out=dict(scope='Narrow user-clarification review; old 1977-file verification reused without rerun. No old scripts imported/executed; no Julia/model parse/compile/native/numerical execution.',checks=checks,all_passed=all(checks.values()),mismatches=bad,refs=refs,production_diff=prod_diff,sha256=pins,physical_files_hashed=len(pins),physical_bytes_hashed=sum(sizes.values()),hash_buffer_bytes=1048576)
with (H/'reviewer-user-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='sha256'}))
