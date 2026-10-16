from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
checks=[]
def check(name,v):
    assert v,name
    checks.append(name)
stages=json.loads((D/'stages.json').read_text())
for phase,s in stages.items():
    p=Path(s['path'])
    check(phase+' exact stage membership',{str(f.relative_to(p)) for f in p.rglob('*') if f.is_file()}==set(s['sha256']))
    check(phase+' content hashes',all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in s['sha256'].items()))
# Independently counted from Julia source, not by importing preparation scripts.
slot=[4*8+3*2+4+4+1+3+1,3+2*2+50*2+16+16+1+4*2+6,5+3*5+4+7*4+3+1,2*(4*3+10)+3*3,12+1]
pair=10;solve=4+pair;replace=3*solve+3+pair
base=pair+2*solve+1+2+1+1+2+1+solve+2*(solve+1)+1
updated=8*replace+5+replace+2*(2+pair)+7*solve+solve
other=[2*(2*4+2*solve+3+7)+16+2+3+1+1,2*(2+3*replace+solve+1+2*solve+1+solve)+1+pair,5*(3+pair)+6+5+(4+pair)+(2*replace+2+2*solve)+3+2*3]
counts=slot+[14*base+10*updated]+other
expected=json.loads((D/'expected-tests.json').read_text())
check('independent assertion leaf derivation',counts==[g[1] for g in expected['green']['groups']])
check('independent total',sum(counts)==8776==expected['green']['assertions'])
check('red missing symbols',expected['red']['assertions']==8 and (D/'red.jl').read_text().count('@test isdefined')==8)
ledger=json.loads((D/'work-ledger.json').read_text())
lifecycle=dict(cases=14,cases_with_updates=10,backend_construction_attempts=14*(2+6)+10*4,singular_attempts=14,real_exports=14*(2+4)+10*4,throwing_exports=14,manager_constructors=14*2,refactor_attempts=14*6+10*4,manager_copies=10*2,forward_entries=14*8+10*(9*4+7*2+2),transpose_entries=14*2+10*9*2,replace_entries=10*9*2)
check('independent lifecycle API ledger',ledger['groups']['lifecycle']==lifecycle)
for key,total in ledger['totals'].items():
    if key in ('native_attempts','markowitz_attempts','valid_solve_entries','unit_metadata_entries','native_orientation_solve_upper_bound'):continue
    check('API group sum '+key,total==sum(g.get(key,0) for g in ledger['groups'].values()))
check('backend split',ledger['totals']['native_attempts']==76+2+8+24 and ledger['totals']['markowitz_attempts']==76+2+6)
check('solve total',ledger['totals']['valid_solve_entries']==698+238)
result=dict(scope='Independent offline source/count/hash checks only; no Julia or old script execution',passed=len(checks),checks=checks,assertion_leaves=counts,assertion_total=sum(counts),lifecycle=lifecycle)
(D/'reviewer-independent-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
