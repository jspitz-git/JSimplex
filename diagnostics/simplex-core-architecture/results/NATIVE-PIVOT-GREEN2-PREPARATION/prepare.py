"""One-shot offline GREEN-2 implementation. No stage or Julia execution."""
from pathlib import Path
import json,hashlib,os
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';F=D.parent/'NATIVE-PIVOT-OBSERVER-FIX';R=D.parents[3]
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def copy(src,n):
 with (D/n).open('xb') as f:f.write(src.read_bytes())
def save(n,z):put(n,json.dumps(z,indent=2)+'\n')
for n in ['guard.py','supervisor.py','exact.py','budget.json','loaded-paths.json']:copy(Q/n,n)
for n in ['test-support-fixed.jl','regression-reviewed.jl']:copy(F/n,n)
s=(F/'test-driver-fixed.jl').read_text()
s=s.replace('include(joinpath(@__DIR__,"test-support-fixed.jl"))','include(joinpath(@__DIR__,"test-support-fixed.jl"))\ninclude(joinpath(@__DIR__,"regression-reviewed.jl"))')
s=s.replace('root=RecordedTests.Capture("root")','root=RecordedTests.Capture("root")\n    regression=RecordedTests.Capture("regression")\n    helper_calls=Ref(0)')
s=s.replace('        Test.@with_testset root begin','''        raw["regression_counts_before"]=copy(NP.counts)
        Test.@with_testset regression begin
            DenseTokenRegression.run((format,v)->begin
                helper_calls[]+=1
                NP.dense_tokens(format,v)
            end,NP.scalar,NP.token)
        end
        raw["regression_counts_after"]=copy(NP.counts)
        Test.@with_testset root begin''')
s=s.replace('if phase=="red"\n            include(joinpath(@__DIR__,"..","NATIVE-PIVOT-QUALIFICATION","red-contract.jl"))\n        elseif phase=="green"','if phase=="green2"')
s=s.replace('raw["tests"]=RecordedTests.dictionary(root)','raw["tests"]=RecordedTests.dictionary(root)\n        raw["regression_tests"]=RecordedTests.dictionary(regression)\n        raw["regression_helper_calls"]=helper_calls[]')
s=s.replace('failed(root)==0 ? 0 : 1','failed(root)==0 && failed(regression)==0 ? 0 : 1')
put('test-driver.jl',s)
s=(Q/'common.py').read_text().replace("HEAD='8dc06f2b95ef74266cb4c7a7b05676a438c3be46'","HEAD='30b0b3402ef5d319c8faa0a78aca32ca3c354d22'")
s=s.replace("old=rd(PREV/'closure-final-host.json')","old=rd(Q/'host.json')").replace("rd(PREV/'closure-final-host.json')['boot_id']","rd(Q/'host.json')['boot_id']")
put('common.py',s)
s=(Q/'control_reviewed.py').read_text();start=s.index('PHASES=');end=s.index('def validate_environment():')
s=s[:start]+'''OLD=D.parent/'NATIVE-PIVOT-QUALIFICATION'
FIX=D.parent/'NATIVE-PIVOT-OBSERVER-FIX'
def config(phase):
 require(phase=='green2','Only new GREEN-2 is prepared')
 stage=R/'.superpowers/native-pivot-green2/green2'
 run=D/'runs/green2';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'test-driver.jl'),str(out),phase,str(stage)]
 return dict(phase=phase,seconds=60,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
'''+s[end:]
start=s.index('def predecessor(');end=s.index('def full_host(',start)
s=s[:start]+'''def validate_prerequisites(red,green):
 require(red.get('all_passed') is True and red.get('phase')=='red','Original RED not accepted')
 require(green.get('all_passed') is False and green.get('phase')=='green','Original failed GREEN must remain failed')
def predecessor(phase):
 config(phase)
 red=OLD/'runs/red';green=OLD/'runs/green'
 a=rd(red/'audit.json');g=rd(green/'audit.json');validate_prerequisites(a,g)
 verify_review(rd(red/'result-review.json'),red/'audit.json',list(a['sha256'])+[str(red/'audit.json')],'stage result','red')
 gr=rd(green/'result-review.json')
 require(gr['accepted'] is False and gr['diagnostic_accepted'] is True and gr['qualification_accepted'] is False,'Failed GREEN diagnostic review')
 require(set(gr['sha256'])==set(g['sha256'])|{str(green/'audit.json')} and gr['pins_sha256']==sha(green/'audit.json'),'Failed GREEN exact bindings')
 require(bindings(a) and bindings(g) and bindings(gr),'Original evidence changed')
 fp=FIX/'pins-reviewed.json';f=rd(fp)
 verify_review(rd(FIX/'review-final.json'),fp,list(f['sha256'])+[str(fp)],'offline observer correction')
 require(bindings(f),'Observer preparation changed')
 groups=rd(green/'posthost.json')['groups']
 require(not rd(green/'posthost.json')['matches'],'Original closure')
 files={red/'audit.json',red/'result-review.json',green/'audit.json',green/'result-review.json',green/'posthost.json',fp,FIX/'review-final.json'}
 files|={path(n) for z in [a,g,gr,f] for n in z['sha256']}
 return sorted(files),groups
'''+s[end:]
put('control.py',s)
s=(Q/'seal-reviewed.py').read_text().replace('from control_reviewed import *','from control import *').replace('preparation-pins-reviewed.json','preparation-pins.json')
put('seal.py',s)
s=(Q/'launch-reviewed.py').read_text().replace('from control_reviewed import *','from control import *').replace('from audit_reviewed import audit','from audit import audit')
put('launch.py',s)
s=(Q/'audit_reviewed.py').read_text().replace('from control_reviewed import *','from control import *').replace('from oracle import test_results,cost_results','from oracle import test_results')
s=s.replace(" if phase=='cost':names|={f'window-{i:03d}.toml' for i in range(1,89)}\n",'')
s=s.replace("result=cost_results(raw,[tomllib.loads((out/f'window-{i:03d}.toml').read_text()) for i in range(1,89)]) if phase=='cost' else test_results(raw,phase)","result=test_results(raw,phase)")
put('audit.py',s)
s=(Q/'oracle.py').read_text();s=s[:s.index('\ndef cost_results')]
a=s.index(" if phase=='red':");b=s.index(" budget=",a)
s=s[:a]+" require(phase=='green2' and raw['phase']==phase,'GREEN-2 phase')\n regression=regression_results(raw)\n"+s[b:]
s=s.replace("return dict(assertions=budget['green_assertions'],entry_counts=total", "return dict(regression=regression,assertions=budget['green_assertions'],entry_counts=total")
s+='''
def regression_results(raw):
 require(raw['phase']=='green2','Regression phase')
 root=raw['regression_tests'];groups=root['children']
 require(root['name']=='regression' and root['pass']==root['fail']==root['error']==root['broken']==0 and root['failures']==[],'Regression root')
 require(len(groups)==1,'Regression group count');g=groups[0]
 require(g['name']=='Dense diagnostic tokens preserve sparse inputs' and g['pass']==119 and g['fail']==g['error']==g['broken']==0 and g['failures']==[] and g['children']==[],'All 119 regression assertions')
 require(raw['regression_helper_calls']==16,'Regression helper budget')
 require(raw['regression_counts_before']==raw['regression_counts_after']=={},'Regression selected production calls')
 return dict(assertions=119,helper_calls=16,selected_production_calls=0,scope='Separate cold regression work; no runtime/native-internal zero-work claim')
'''
put('oracle.py',s)
save('environment.json',{k:os.environ.get(k) for k in json.loads((Q/'environment.json').read_text())})
save('regression-budget.json',dict(assertions=119,cases=12,helper_calls=16,old_expression_negative_calls=1,selected_production_calls=0,original_assertions=6858,total_assertions=6977,original_selected_entries=792,original_equations=324,public_solves=0))
# Save exact line-based delta to each canonical original; no generator rerun needed.
import difflib
pairs={'common.py':Q/'common.py','control.py':Q/'control_reviewed.py','seal.py':Q/'seal-reviewed.py','launch.py':Q/'launch-reviewed.py','audit.py':Q/'audit_reviewed.py','oracle.py':Q/'oracle.py','test-driver.jl':F/'test-driver-fixed.jl'}
put('changes.diff',''.join(''.join(difflib.unified_diff(p.read_text().splitlines(True),(D/n).read_text().splitlines(True),fromfile=str(p),tofile=str(D/n))) for n,p in pairs.items()))
save('source-map.json',dict(originals={n:str(p) for n,p in pairs.items()},byte_identical={n:str(Q/n) for n in ['guard.py','supervisor.py','exact.py','budget.json','loaded-paths.json']}|{n:str(F/n) for n in ['test-support-fixed.jl','regression-reviewed.jl']}))
print('New offline driver/control/audit prepared; seal/launch UNEXECUTED')
