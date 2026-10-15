"""Bounded independent correction check. Read-only inputs; no Julia/stage/old checker."""
from pathlib import Path
import json,hashlib,ast,sys
Q=Path(__file__).resolve().parent;R=Q.parents[3]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bindings(z):return all(sha(n)==h for n,h in z['sha256'].items())
checks={}
a=rd(Q/'preparation-pins.json');p=Q/'preparation-pins-reviewed.json';b=rd(p)
assert len(a['sha256'])==842 and len(b['sha256'])==872 and bindings(a) and bindings(b)
assert all(b['sha256'][n]==h for n,h in a['sha256'].items());checks['all_872_hashes_original_842_unchanged']=True
old=rd(Q/'review.json');assert old['accepted'] is False and [f['id'] for f in old['findings']]==['R1']
assert set(old['sha256'])==set(a['sha256'])|{str(Q/'preparation-pins.json')} and bindings(old)
checks['rejected_review_exact_843_preserved']=True
s=(Q/'test-driver.jl').read_text()
edits=[('root=RecordedTests.Capture("root");Test.push_testset(root)','root=RecordedTests.Capture("root")'),('        if phase=="red"','        Test.@with_testset root begin\n        if phase=="red"'),('        raw["complete"]=true','        end # scoped Test1.13 context restored even on error\n        raw["complete"]=true'),('        Test.pop_testset();raw["tests"]=RecordedTests.dictionary(root)','        raw["tests"]=RecordedTests.dictionary(root)')]
for x,y in edits:assert s.count(x)==1;s=s.replace(x,y)
assert s==(Q/'test-driver-reviewed.jl').read_text();checks['exact_four_edit_driver_correction']=True
api=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl').read_text()
assert 'macro with_testset(ts, expr)' in api and '@with(CURRENT_TESTSET =>' in api
assert 'get_testset_depth() == 0 ? DefaultTestSet : typeof(get_testset())' in api
assert 'Test.push_testset' not in s and 'Test.pop_testset' not in s
assert s.index('    try\n')<s.index('Test.@with_testset root begin')<s.index('end # scoped Test1.13')<s.index('    catch e\n')<s.index('    finally\n')<s.index('TOML.print')<s.index('    exit(')
checks['pinned_scoped_api_and_outer_raw_finally']=True
updates={
'control_reviewed.py':('control.py',[('test-driver.jl','test-driver-reviewed.jl')]),
'seal-reviewed.py':('seal.py',[('from control import *','from control_reviewed import *'),('preparation-pins.json','preparation-pins-reviewed.json'),("D/'review.json'","D/'review-final.json'")]),
'launch-reviewed.py':('launch.py',[('from control import *','from control_reviewed import *'),('from audit import audit','from audit_reviewed import audit')]),
'audit_reviewed.py':('audit.py',[('from control import *','from control_reviewed import *')]),
'continue-reviewed.py':('continue.py',[('from control import *','from control_reviewed import *'),('preparation-pins.json','preparation-pins-reviewed.json'),("D/'review.json'","D/'review-final.json'")]),
'closure-reviewed.py':('closure.py',[('from control import *','from control_reviewed import *'),('preparation-pins.json','preparation-pins-reviewed.json'),("D/'review.json'","D/'review-final.json'")])}
for dest,(src,repls) in updates.items():
 text=(Q/src).read_text()
 for x,y in repls:assert x in text;text=text.replace(x,y)
 assert text==(Q/dest).read_text()
checks['exact_control_admission_audit_publication_routing_deltas']=True
for n,c in [('review-fix.json',8),('final-check-2.json',15)]:
 z=rd(Q/n);assert z['all_passed'] is True and len(z['checks'])==c and all(v is True for v in z['checks'].values()) and bindings(z)
z=rd(Q/'oracle-regression.json');assert z['all_passed'] is True and len(z['refusals'])==20 and z['positive_known_C_false_P_true'] is True and bindings(z)
checks['author_fix_oracle_final_check_bindings']=True
failure=rd(Q/'final-check-failures.json');assert len(failure['failures'])==2
for f in failure['failures']:assert f['exit_code']==1 and sha(Q/f['script'])==f['source_sha256']
assert not (Q/'final-check.json').exists() and not (Q/'freeze-reviewed.json').exists()
assert "['all_passed']" in (Q/'final-check.py').read_text() and "final-check-2.json" in (Q/'freeze-reviewed-2.py').read_text()
checks['two_offline_failures_preserved']=True
m=rd(Q/'reviewer-continuation-map.json');z=rd(Q/'reviewer-check.json')
assert m['record']==str(Q/'reviewer-check.json') and m['key']==str(Q/'continuation-text.md')
assert m['preserved_path']==str(Q/'continuation-text.md.before-review')
assert m['sha256_original']==z['sha256'][m['key']]==sha(m['preserved_path'])=='dfe47a9bbdd8907b26686f61565f798ffb6a50eb7d890c143d8bf409e8d6597d'
assert bindings(m)
mapped=[]
for n,h in z['sha256'].items():
 if sha(n)!=h:assert n==m['key'] and h==m['sha256_original'];mapped.append(n)
assert mapped==[m['key']];checks['single_exact_continuation_preservation_mapping']=True
for f in Q.glob('*.py'):ast.parse(f.read_text(),filename=str(f))
checks['python_syntax']=True
# Definitions-only configuration reads. No seal/launcher/auditor import or calls.
sys.path.insert(0,str(Q))
import control_reviewed as c
for phase,cap,exitcode,driver in [('red',30,1,'test-driver-reviewed.jl'),('green',60,0,'test-driver-reviewed.jl'),('cost',45,0,'cost-driver.jl')]:
 cfg=c.config(phase);assert cfg['seconds']==cap and cfg['expected_exit']==exitcode and cfg['command'][-4]==str(Q/driver)
 gc=c.guard_command(cfg,Q/'synthetic-never-created.json',100.)
 assert gc[gc.index('--seconds')+1]==str(cap-8) and gc[gc.index('--deadline')+1]==str(float(100+cap-8))
checks['canonical_driver_caps_and_guard_offsets']=True
required=set(b['sha256'])|{str(p)}
synthetic=dict(accepted=True,findings=[],scope='offline preparation',pins_sha256=sha(p),sha256={**b['sha256'],str(p):sha(p)})
c.verify_review(synthetic,p,required,'offline preparation')
refusals=[]
for label,value in [('old rejected review',old),('old accepted membership',dict(old,accepted=True,findings=[])),('wrong scope',dict(synthetic,scope='exact-stage admission')),('omitted manifest',dict(synthetic,sha256=b['sha256']))]:
 try:c.verify_review(value,p,required,'offline preparation')
 except RuntimeError:refusals.append(label)
 else:raise AssertionError('accepted '+label)
assert len(refusals)==4;checks['exact_873_review_gate_refusals']=True
budget=rd(Q/'budget.json');assert budget['green_assertions']==6858 and sum(budget['main'].values())==722 and sum(budget['neighbors'].values())==70
assert budget['cost']==dict(construction=88,refactor=176,forward=2816,transpose=1408,windows=88,fresh_native_source=176,private_lu_source=88)
assert 8*19*2+10*2==324;checks['unchanged_previously_derived_budgets']=True
assert not (Q/'runs').exists() and not (R/'.superpowers/native-pivot-qualification').exists();checks['no_stage_or_run']=True
record=dict(all_passed=all(checks.values()),checks=checks,refusals=refusals,resolved=['R1'],scope='Independent bounded offline correction review; no Julia or runtime admission',sha256={str(x):sha(x) for x in [Path(__file__),p,Q/'test-driver-reviewed.jl',Q/'review-fix.json',Q/'reviewer-continuation-map.json',Q/'final-check-2.json',Q/'final-check-failures.json']})
with (Q/'reviewer-check-final.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),all_passed=record['all_passed'],synthetic_refusals=len(refusals),pins=872,required_review_bindings=873,pins_sha256=sha(p))))
