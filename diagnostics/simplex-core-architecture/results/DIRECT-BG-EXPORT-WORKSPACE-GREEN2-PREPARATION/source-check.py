"""New offline inverse and failclosed tests. Synthetic raw is NOT numerical evidence."""
from pathlib import Path
import sys,json,copy
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
from oracle import test_results
O=c.O;R=c.R;F=R/'diagnostics/direct-bg-export-workspace-harness-fix/reproduce';checks={}
def ck(v,n):checks[n]=bool(v)
def rejects(f):
 try:f();return False
 except (ValueError,RuntimeError,KeyError):return True
inv=c.rd(D/'inverse.json');old=Path(inv['original']).read_text();new=Path(inv['amended']).read_text()
ck(new.count(inv['after'])==1 and new.replace(inv['after'],inv['before'])==old,'whole_test_inverse_one_init')
ck(new.count('@test')==old.count('@test') and c.rd(D/'expected-tests.json')==c.rd(O/'expected-tests.json'),'unchanged_predicates_counts')
ck((F/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve()==(c.C/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve(),'relative_fixture_identical')
for name in inv['copied_controls']:ck((D/name).read_bytes()==(O/name).read_bytes(),'byteexact_'+name)
s=(O/'driver.jl').read_text()
for a,b in inv['driver_replacements']:s=s.replace(a,b)
ck((D/'driver.jl').read_text()==s,'driver_only_test_path_and_unique_phase')
ck((D/'stages.json').read_bytes()==(O/'stages.json').read_bytes(),'same_stage_candidate')
ck(c.config('green2-300')['seconds']==300 and c.config('green2-600')['seconds']==600,'bounded_phases')
for phase in ('green300','red300','green2','cost1-300','green2-301'):
 ck(rejects(lambda:c.config(phase)),'reject_unprepared_'+phase)
f,g=c.predecessor('green2-300');ck(bool(f) and len(g)==250,'accepted_RED_and_failed_GREEN_preserved')
# Synthetic all-pass raw exercises only pure Python parser, never claims a test pass.
expected=c.rd(D/'expected-tests.json')['green'];loaded=c.loaded_for(c.config('green2-300'))
raw=dict(phase='green2-300',complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0},failures=[],children=[dict(name=e[0],**dict(zip(('pass','fail','error','broken'),e[1:])),failures=[],children=[]) for e in expected['groups']]))
ck(test_results(raw,expected,loaded,'green2-300')['assertions']==7935,'synthetic_exact7935')
for name,mut in [('wrongphase',lambda v:v.update(phase='green300')),('incomplete',lambda v:v.update(complete=False)),('fatal',lambda v:v.update(fatal='x')),('wrongloaded',lambda v:v['loaded'].update(JSimplex='x')),('threads',lambda v:v.update(threads=2)),('missinggroup',lambda v:v['tests']['children'].pop()),('changedpass',lambda v:v['tests']['children'][3].update({'pass':55})),('testerror',lambda v:v['tests']['children'][3].update({'pass':55,'error':1,'failures':['x']}))]:
 v=copy.deepcopy(raw);mut(v);ck(rejects(lambda:test_results(v,expected,loaded,'green2-300')),'reject_'+name)
for p in D.glob('*.py'):compile(p.read_text(),str(p),'exec')
ck(True,'new_Python_syntax_only')
ck(not (D/'runs').exists(),'no_seal_reservation_launch')
paths=sorted([p for p in D.iterdir() if p.is_file()]+[F/'import-tests.jl'])
v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):c.sha(p) for p in paths},scope='Offline source inverse and synthetic Python refusal checks only; no Julia or numerical claim')
c.save(D/'source-check.json',v);print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),failed=[n for n,b in checks.items() if not b])));c.require(v['all_passed'],'Preserve failed offline check')
