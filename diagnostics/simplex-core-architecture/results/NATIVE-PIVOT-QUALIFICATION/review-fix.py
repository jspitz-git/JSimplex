"""One separate offline fix for rejected Test API binding; originals preserved."""
from common import *
require((Q/'review.json').is_file() and rd(Q/'review.json')['accepted'] is False,'Preserve initial rejected review first')
require(bindings(rd(Q/'preparation-pins.json')),'Original package changed')
s=(Q/'test-driver.jl').read_text();old=s
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl');api=runtime.read_text()
red='Test.push_testset(root)' in old and 'Test.pop_testset()' in old and 'function push_testset' not in api and 'function pop_testset' not in api
require(red,'R1 source RED')
s=s.replace('root=RecordedTests.Capture("root");Test.push_testset(root)','root=RecordedTests.Capture("root")')
s=s.replace('        if phase=="red"','        Test.@with_testset root begin\n        if phase=="red"')
s=s.replace('        raw["complete"]=true','        end # scoped Test1.13 context restored even on error\n        raw["complete"]=true')
s=s.replace('        Test.pop_testset();raw["tests"]=RecordedTests.dictionary(root)','        raw["tests"]=RecordedTests.dictionary(root)')
with (Q/'test-driver-reviewed.jl').open('x') as f:f.write(s)
updates={
 'control_reviewed.py':('control.py', [('test-driver.jl','test-driver-reviewed.jl')]),
 'seal-reviewed.py':('seal.py',[('from control import *','from control_reviewed import *'),('preparation-pins.json','preparation-pins-reviewed.json'),("D/'review.json'","D/'review-final.json'")]),
 'launch-reviewed.py':('launch.py',[('from control import *','from control_reviewed import *'),('from audit import audit','from audit_reviewed import audit')]),
 'audit_reviewed.py':('audit.py',[('from control import *','from control_reviewed import *')]),
 'continue-reviewed.py':('continue.py',[('from control import *','from control_reviewed import *'),('preparation-pins.json','preparation-pins-reviewed.json'),("D/'review.json'","D/'review-final.json'")]),
 'closure-reviewed.py':('closure.py',[('from control import *','from control_reviewed import *'),('preparation-pins.json','preparation-pins-reviewed.json'),("D/'review.json'","D/'review-final.json'")]),
 'ADMISSION-reviewed.md':('ADMISSION.md',[('`seal.py PHASE`','`seal-reviewed.py PHASE`'),('`launch.py PHASE`','`launch-reviewed.py PHASE`'),('control.config','control_reviewed.config'),('preparation-pins.json','preparation-pins-reviewed.json')]),
 'REPORT-final.md':('REPORT.md',[('ADMISSION.md','ADMISSION-reviewed.md'),('independent review record','independent review-final.json record')])}
for target,(source,replacements) in updates.items():
 text=(Q/source).read_text()
 for a,b in replacements:require(a in text,'Replacement absent '+a);text=text.replace(a,b)
 with (Q/target).open('x') as f:f.write(text)
with (Q/'REPORT-final.md').open('a') as f:f.write('\nInitial offline review REJECTED R1: removed Test.push_testset/pop_testset API in pinned Julia1.13. Separate test-driver-reviewed.jl uses installed Test.@with_testset scoped context inside try/finally. Original driver,842pins and rejected review remain frozen. Canonical tools: seal-reviewed.py, launch-reviewed.py, audit_reviewed.py and control_reviewed.py. No Julia execution or runtime acceptance. Exact final offline review binds preparation-pins-reviewed.json.\n')
checks=dict(source_red=red,scoped_macro_exists='macro with_testset(ts, expr)' in api,green_no_removed_api='Test.push_testset' not in s and 'Test.pop_testset' not in s,one_scoped_context=s.count('Test.@with_testset root begin')==1,raw_in_finally='finally\n        raw["tests"]' in s,unchanged_test_sources=all(sha(Q/n)==v['sha256'] for n,v in rd(Q/'test-inverse.json').items()),original842=bindings(rd(Q/'preparation-pins.json')),initial_review_rejected=rd(Q/'review.json')['accepted'] is False)
save(Q/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in [Path(__file__),runtime,Q/'test-driver-reviewed.jl',Q/'review.json',Q/'preparation-pins.json']+[Q/n for n in updates]},scope='Offline source RED/GREEN only; no Julia execution'))
require(all(checks.values()),'Correction failed');print(dict(checks=len(checks),all_passed=True))
