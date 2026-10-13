"""Exclusive offline RED/GREEN admission binding correction tests."""
from common_reviewed import *
import copy,subprocess
refs={str(R):'a650c0e16f2423fcfc26abcad13f1ecb3f8e408f',str(M):'35a6a9f4bb61e204b0c61ec9effe96cd9d2de3ab'}
def fixture(stage):
 b=dict(accepted=True,unresolved_findings=[],stage=stage,root=str(root(stage)),refs=refs,candidate_sha256=EXPECTED,sha256={k:'0'*64 for k in stage_required(stage)})
 b['sha256'][str(root(stage)/REL)]=EXPECTED;return b
base=fixture('green');known=dict(base['sha256']);master=fixture('master');known.update(master['sha256'])
def valid(b,stage):return stage_record_valid(b,stage,hashfn=lambda k:known.get(k),refs=refs)
red=dict(empty_binding_previously_accepted=all([]),missing_master_linkage_previously_accepted=all([]))
c={'valid_green_synthetic':valid(base,'green'),'valid_master_binding_synthetic':valid(master,'master')}
cases=[]
for name,stage,change in [('empty_binding','green',lambda b:b.__setitem__('sha256',{})),('wrong_stage','green',lambda b:b.__setitem__('stage','master')),('wrong_root','green',lambda b:b.__setitem__('root',str(M))),('wrong_refs','green',lambda b:b.__setitem__('refs',{})),('unresolved','green',lambda b:b.__setitem__('unresolved_findings',['P2'])),('wrong_candidate','green',lambda b:b.__setitem__('candidate_sha256',OLD)),('missing_master_review','master',lambda b:b['sha256'].pop(str(H/'green/review.md'))),('missing_master_post','master',lambda b:b['sha256'].pop(str(H/'green/postcheck.json'))),('changed_hash','green',lambda b:b['sha256'].__setitem__(str(H/'driver.jl'),'1'*64))]:
 b=copy.deepcopy(base if stage=='green' else master);change(b);c[name]=not valid(b,stage);cases.append(dict(name=name,rejected=c[name]))
f=H/'reviewed-failure-cases';f.mkdir()
for name,contents in [('missing',None),('malformed','{'),('incomplete','{}')]:
 d=f/name;d.mkdir()
 if contents is not None:(d/'process.json').write_text(contents)
 dest=f/(name+'-audit.json');cmd=[sys.executable,str(H/'audit-reviewed.py'),'green',str(d),str(dest)];p=subprocess.run(cmd,capture_output=True,text=True);dump(f/(name+'-process.json'),dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));x=read(dest);c['durable_'+name]=p.returncode==1 and x['all_passed'] is False and x['checks']=={'readable_valid_complete_inputs':False}
source={n:(H/n).read_text() for n in ('common_reviewed.py','launcher-reviewed.py','audit-reviewed.py')}
c.update(run_enforces_stage_and_launch='launch_accepted(stage)' in source['launcher-reviewed.py'],audit_enforces_stage_and_launch="stage_launch_bindings=launch_accepted(stage)['accepted'] is True" in source['audit-reviewed.py'],freeze_enforces_stage='stage_accepted(stage)' in source['launcher-reviewed.py'],master_checks_green='post[\'all_passed\'] is True' in source['common_reviewed.py'])
result=dict(red=red,checks=c,all_passed=all(c.values()),cases=cases,scope='Synthetic metadata/hash-reader cases and new auditor refusals only; no Julia, actual test edit or numerical retry.',sha256={str(H/n):sha(H/n) for n in ('common_reviewed.py','launcher-reviewed.py','audit-reviewed.py','review_fix.py','reviewed_failure_tests.py')})
dump(H/'reviewed-failure-tests.json',result);print(json.dumps(c));assert result['all_passed']
