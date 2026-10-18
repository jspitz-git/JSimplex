"""Fresh independent R1 amendment checks; never replay prior checkers or launch."""
from pathlib import Path
import hashlib,json,sys,ast,tempfile
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-workspace/reproduce'
sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import guard
checks={};readtime={}
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 value=h.hexdigest();readtime[str(p)]=value;return value
def rd(p):return json.loads(Path(p).read_text())
def ck(name,v):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
mapping={str(D/n):str(D/(n+'.before-R1')) for n in ['required-paths.json','preparation-pins.json','review.json','review.md']}
fix=rd(D/'review-fix.json');ck('exact_four_before_mappings',fix['before_mapping']==mapping)
oldpins=rd(D/'preparation-pins.json.before-R1');newpins=rd(D/'preparation-pins.json');oldreview=rd(D/'review.json.before-R1')
ck('original_rejection_exact_hash',sha(D/'review.json.before-R1')=='3828dbd68a52e2850dbebe29f6575f4fe83ca70a3c6a2f75b5a06c5343740127')
ck('original_review_text_exact_hash',sha(D/'review.md.before-R1')=='998dcf3fff9c0deea18c27250a2af1c30a2ac1eaf1296a60917a7526571b7f34')
ck('original_manifest_exact_hash',sha(D/'preparation-pins.json.before-R1')=='254dc44d7893023521bca933610d97fbf954757c18fc8ca41ac74dd009714036')
ck('old_1858_bindings_preserved',len(oldpins['sha256'])==1858 and all(sha(mapping.get(p,p))==h for p,h in oldpins['sha256'].items()))
ck('old_1859_review_bindings_preserved',len(oldreview['sha256'])==1859 and all(sha(mapping.get(p,p))==h for p,h in oldreview['sha256'].items()))
ck('old_review_evidence_preserved',len(oldreview['evidence_sha256'])==6 and all(sha(mapping.get(p,p))==h for p,h in oldreview['evidence_sha256'].items()))
ck('all_1870_current_bindings_match',len(newpins['sha256'])==1870 and all(sha(p)==h for p,h in newpins['sha256'].items()))
ck('new_required_membership_exact',set(newpins['sha256'])==set(rd(D/'required-paths.json')['paths']))
ck('old_required_membership_exact',set(oldpins['sha256'])==set(rd(D/'required-paths.json.before-R1')['paths']))
fixture=(C/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve();expected='835b6e4241705b4c7a6a2625c904999ffe30e90ec99c937d257cbe2a2c289517'
extra=['review-fix.py','review-fix.json','AMENDMENT.md','required-paths.json.before-R1','preparation-pins.json.before-R1','review.json.before-R1','review.md.before-R1','independent-review-check.py','independent-review-check-initial-error.json','independent-review-check-v2.py','independent-review-check-v2.json']
ck('only_12_additive_paths',set(newpins['sha256'])-set(oldpins['sha256'])=={str(fixture)}|{str(D/n) for n in extra})
ck('no_original_path_dropped',set(oldpins['sha256'])<=set(newpins['sha256']))
ck('only_original_required_manifest_changes',{p for p,h in oldpins['sha256'].items() if sha(p)!=h}=={str(D/'required-paths.json')})
ck('old_review_only_two_manifest_changes', {p for p,h in oldreview['sha256'].items() if sha(p)!=h}=={str(D/'required-paths.json'),str(D/'preparation-pins.json')})
ck('fixture_exact_hash',sha(fixture)==newpins['sha256'][str(fixture)]==expected)
for task in ['TASK1','TASK2']:
 review=rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-'+task)/'final-review.json')
 ck(task+'_accepted_fixture_continuity',review['accepted'] is True and review['readtime_sha256'][str(fixture)]==expected)
ck('literal_include_resolves_exact_fixture','include("../../direct-lu-policy-adapters/reproduce/fixtures.jl")' in (C/'import-tests.jl').read_text())
ck('fixture_no_transitive_include','include(' not in fixture.read_text())
ck('amendment_author_bindings',all(sha(p)==h for p,h in fix['sha256'].items()))
ck('old_v2_readtime_preserved',all(sha(mapping.get(p,p))==h for p,h in rd(D/'independent-review-check-v2.json')['sha256'].items()))
ck('old_author_check_bindings_preserved',all(sha(mapping.get(p,p))==h for p,h in rd(D/'source-check.json')['sha256'].items()))
ck('prior_findings_not_erased',oldreview['accepted'] is False and len(oldreview['findings'])==1 and oldreview['findings'][0]['id']=='R1')
# Follow source-level membership propagation; no phase seal or review gate invoked.
control=(D/'control.py').read_text();seal=(D/'seal.py').read_text();launch=(D/'launch.py').read_text()
ck('preparation_propagates_all_pin_paths',"return sorted(set(j['sha256'])|{str(m),str(v)})" in control)
ck('seal_keeps_preparation_files',"files=preparation()" in seal and 'files=sorted(set(files+' in seal and 'inventory=guard.inventory(files,trees)' in seal)
ck('launch_keeps_all_sealed_files',"files=sorted(set(sealed['files'])|" in launch and "inventory=guard.inventory(files,sealed['trees'])" in launch)
with tempfile.TemporaryDirectory(prefix='bgx-amendment-review-') as td:
 p=Path(td)/'fixture.jl';p.write_text('fixed fixture')
 inventory=guard.inventory([str(p)],[]);bindings=dict(files=[str(p)],trees=[],inventory=inventory)
 ck('additive_file_pin_valid',guard.pins_match(bindings));p.write_text('different fixture')
 ck('additive_file_content_drift_refused',not guard.pins_match(bindings));p.unlink()
 ck('additive_file_missing_refused',not guard.pins_match(bindings))
ck('no_phase_activity',not (D/'runs').exists())
ast.parse((D/'review-fix.py').read_text());ck('amendment_Python_syntax_only',True)
sha(D/'preparation-pins.json');sha(Path(__file__))
result=dict(all_checks_passed=all(checks.values()),checks=checks,old_bindings_verified=1858,old_review_bindings_verified=1859,current_bindings_verified=1870,before_mapping=mapping,sha256=readtime,resolved_findings=['R1'],scope='Fresh independent offline amendment verification; no Julia, old checker, seal, reservation or launch')
with (D/'amendment-independent-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),all_passed=result['all_checks_passed'],current1870=True,old1858=True,oldreview1859=True)))
