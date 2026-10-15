"""Synthetic complete schema and numerical-oracle tests. No solver execution."""
from control import *
import analysis as a,copy,tempfile,tomllib,guard,evidence
checks={}
def check(n,v):req(v,n);checks[n]=True
def refuses(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,IndexError,FileExistsError,FileNotFoundError,tomllib.TOMLDecodeError):checks[n]=True;return
 raise ValueError('Accepted invalid '+n)
def mutate(o,p,v):
 o=copy.deepcopy(o);q=o
 for k in p[:-1]:q=q[k]
 q[p[-1]]=v;return o
T=a.token;base=[T(0)]*20;base[3]=T(.1);base[15]=T(.001)
def control(arm):
 v=list(base);v[3]=T(1 if arm=='P' else .1);v[7]=T(2 if arm=='R' else 0);return v
def state(arm,n):return dict(native_owned=True,native_match=True,control_private=True,control_equal=True,control=control(arm),strategy=1.,sym_pivot=T(.001),Wi=n,W=n*(5 if arm=='R' else 1))
def factor(arm,n):
 info=[T(0)]*90;info[18]=T(1);info[3]=T(16)
 return dict(n=n,status=0,nzd=n,do_recip=0,control=control(arm),info=info,graph_bytes=100,lnz=n,unz=n,L=dict(format='csr',ptr=list(range(1,n+2)),indices=list(range(1,n+1)),values=[T(1)]*n),U=dict(format='csc',ptr=list(range(1,n+2)),indices=list(range(1,n+1)),values=[T(1)]*n),p=list(range(1,n+1)),q=list(range(1,n+1)),Rs=[T(1)]*n)
data=rd(D/'inputs.json');raw=dict(completed=True,inputs_unchanged=True,fatal='',counts=a.COUNTS,threads=1,blas_threads=1,index_bits=64,stdlib_paths=rd(D/'stdlib-paths.json'))
lives={}
for arm in 'CPR':
 v={k:state(arm,32) for k in ('initial','first','second','fresh','finalF','finalS')};v.update({k:True for k in ('poisoned_private','copy_contract','independent_T','independent_V','preserved','singular')});v.update(arm=arm,cause='LinearAlgebra.SingularException',status=1,outputs=[[T(0)]*32 for _ in range(14)],info=[[T(0)]*4 for _ in range(14)]);lives[arm]=v
windows=[];timing=dict(seconds=1.,bytes=0,events=0,gctime=0.,compile_time=0.,recompile_time=0.)
for spec in data['schedule']:
 n=next(f['matrix']['n'] for f in data['fixtures'] if f['name']==spec['fixture']);arm=spec['arm'];v=dict(schedule=spec,construction=timing,solve=timing,before=state(arm,n),after=state(arm,n),outputs=[[T(0)]*n for _ in range(48)],info=[[T(0)]*4 for _ in range(48)])
 if spec['round']==11:v['factor']=factor(arm,n)
 windows.append(v)
def run(rr=raw,ll=lives,ww=windows):return a.analyze(rr,ll,ww,data,[T(0)]*96)
r=run();check('6378_false_accuracy_preserved',len(r['residuals'])==6378 and r['diagnostic_integrity'] and not any(r['accuracy'].values()) and not any(r['remedy_eligible'].values()))
check('all_samples_and12factors',len(r['cost'])==24 and len(r['factors'])==12 and r['interpretable_cost'])
for name,p,v in [('input_changed',['inputs_unchanged'],False),('incomplete',['completed'],False),('fatal',['fatal'],'error'),('budget',['counts','ftran'],4246)]:refuses(name,lambda p=p,v=v:run(rr=mutate(raw,p,v)))
for name,p,v in [('missing_output',[0,'outputs'],[]),('wrong_stage',[0,'schedule','id'],2),('alias',[0,'before','native_owned'],False),('workspace',[0,'before','W'],0),('control',[0,'before','control',15],T(1)),('strategy',[0,'before','strategy'],0),('missing_info',[0,'info'],[]),('refinement_bounds',[0,'info',0],[T(0),T(0),T(3),T(1)])]:refuses(name,lambda p=p,v=v:run(ww=mutate(windows,p,v)))
refuses('copy_ownership',lambda:run(ll=mutate(lives,['C','copy_contract'],False)))
refuses('bad_exception',lambda:run(ll=mutate(lives,['C','cause'],'ErrorException')))
w=copy.deepcopy(windows);i=next(i for i,v in enumerate(w) if not v['schedule']['warm']);w[i]['solve']=dict(timing,compile_time=.1);check('compile_data_preserved_cost_rejected',run(ww=w)['interpretable_cost'] is False)
# Exact orientation/permutation identity on a deliberately nonsymmetric matrix.
m=dict(n=2,colptr=[1,3,5],rowval=[1,2,1,2],nzval=list(map(T,[4,2,2,4])))
f=factor('C',2);f.update(lnz=3,unz=3,p=[2,1],q=[2,1],Rs=list(map(T,[2,4])))
f['L']=dict(format='csr',ptr=[1,2,4],indices=[1,1,2],values=list(map(T,[1,1,1])))
f['U']=dict(format='csc',ptr=[1,2,4],indices=[1,1,2],values=list(map(T,[1,.5,1.5])))
check('division_orientation',a.factor_report(f,m,'C',base)['factor_identity_exact'])
g=copy.deepcopy(f);g['do_recip']=1;g['Rs']=list(map(T,[.5,.25]));check('multiplication_orientation',a.factor_report(g,m,'C',base)['factor_identity_exact'])
for name,p,v in [('duplicate_perm',['p'],[1,1]),('zero_scale',['Rs'],[T(0),T(1)]),('zero_upper',['U','values'],list(map(T,[1,.5,0]))),('nonunit_lower',['L','values'],list(map(T,[2,1,1]))),('reciprocal_flag',['do_recip'],2)]:refuses(name,lambda p=p,v=v:a.factor_report(mutate(f,p,v),m,'C',base))
mt=dict(n=2,colptr=[1,3,4],rowval=[1,2,2],nzval=list(map(T,[1,2,3])));check('transpose_rhs_pairing',a.residual(mt,list(map(T,[1,2])),list(map(T,[5,6])),True)['passed'])
with tempfile.TemporaryDirectory(prefix='accuracy-offline-') as tmp:
 p=Path(tmp)/'reservation.json';save(p,{'one_attempt':True});refuses('reused_reservation',lambda:save(p,{}))
 f=Path(tmp)/'pin';f.write_text('a');pins=dict(files=[str(f)],trees=[],inventory=guard.inventory([str(f)],[]));check('fresh_pin',guard.pins_match(pins));f.write_text('b');check('changed_pin_refused',not guard.pins_match(pins))
 refuses('missing_raw',lambda:(Path(tmp)/'absent').read_text());refuses('truncated_raw',lambda:tomllib.loads('a = ['))
check('exact141outputnames',len(evidence.output_names())==len(set(evidence.output_names()))==141)
save(D/'schema-tests.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in [Path(__file__),D/'analysis.py',D/'evidence.py',D/'inputs.json']},scope='Synthetic offline data only; no Julia parsing/native operation'))
print(len(checks),'PASS')
