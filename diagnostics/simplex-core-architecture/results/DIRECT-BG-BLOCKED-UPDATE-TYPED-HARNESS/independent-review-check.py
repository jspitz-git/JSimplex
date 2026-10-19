"""Independent OFFLINE preparation review. Standard library only; never invokes Julia or entrypoints."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,re,sys,tempfile
D=Path(sys.argv[1]).resolve();R=D.parents[3]
sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
checks=[]
def ck(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def reject(name,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,FileNotFoundError):checks.append(name);return
 raise AssertionError('accepted invalid '+name)
def load(name):
 spec=importlib.util.spec_from_file_location(name,D/(name+'.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
pins=rd(D/'preparation-pins.json')['sha256'];required=rd(D/'required-paths.json')['paths']
ck('581 exact unique required subjects',len(pins)==len(required)==len(set(required))==581 and set(pins)==set(required))
for n,h in pins.items():ck('pin '+n,Path(n).is_file() and not Path(n).is_symlink() and sha(n)==h)
for name,item in rd(D/'copied-files.json').items():ck('copy '+name,sha(D/name)==sha(item['source'])==item['sha256'])
f=rd(D/'fault-transform.json');s=(D/'panel-fault.jl').read_text()
for old,new in reversed(f['edits']):ck('unique inverse '+new,s.count(new)==1);s=s.replace(new,old,1)
ck('fault exact inverse',s.encode()==Path(f['source']).read_bytes() and sha(f['source'])==f['source_sha256'] and sha(D/'panel-fault.jl')==f['prepared_sha256'])
for n in ['runs','outers','reservation.json','release.json','sealed.json']:ck('absent '+n,not (D/n).exists())
q=rd(D/'qualification-bindings.json')
for n,h in q['sha256'].items():ck('qualification '+n,sha(n)==h)
for n in q['accepted_receipts']:
 v=rd(n);ck('accepted prior '+n,v.get('accepted') is True and v.get('findings')==[])
 for key in ['sha256','evidence_sha256']:
  for p,h in v.get(key,{}).items():ck('prior receipt binding '+p,sha(Path(p) if Path(p).is_absolute() else R/p)==h)
for name,st in rd(D/'stages.json').items():
 root=Path(st['path']);ck('stage membership',not root.is_symlink() and {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==set(st['sha256']))
 for p,h in st['sha256'].items():ck('stage '+p,not (root/p).is_symlink() and sha(root/p)==h)
for n in D.glob('*.py'):ast.parse(n.read_text());checks.append('Python syntax '+n.name)
site=rd(D/'assertion-sites.json');expected={f'P{i:03}' for i in range(1,103)}|{f'L{i:03}' for i in range(1,41)}|{f'N{i:03}' for i in range(1,27)}
ck('168 site universe',set(site)==expected)
for key,v in site.items():ck('site line '+key,(D/v['file']).read_text().splitlines()[v['line']-1].strip()==v['source'])
s=(D/'driver.jl').read_text();ck('includes before main',all(m.start()<s.index('function main()') for m in re.finditer(r'include\(',s)))
ck('unit finally then aggregate',s.index('save("unit-$index.toml"')<s.index('Unexpected unit failure') and s.index('save("raw.toml",raw)')<s.index('exit(valid'))
ck('no dispatch workaround',not any(t in s for t in ('invokelatest','@eval','eval(')))
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base');runtime=rd(D/'runtime-inputs-complete.json')['inventory']
for n in ('dict.jl','abstractdict.jl','timing.jl','experimental.jl'):
 p=base/n;v=runtime[str(p)];ck('Base bound '+n,str(p.resolve())==v['resolved'] and sha(p)==v['sha256'])
ck('generator widening source','promote_typejoin(V, typeof(v))' in (base/'abstractdict.jl').read_text())
ck('timed inline source','local val = @__tryfinally($(esc(ex))' in (base/'timing.jl').read_text() and 'without introducing the try scope' in (base/'timing.jl').read_text())
o=load('oracle');c=load('control');a=load('audit');S=rd(D/'schedule.json');loaded={'JSimplex':'synthetic-source-only'}
# Independent synthetic rows use zero ordinary scalar steps plus deliberate pure
# row events and both panel admission outcomes; these are schema fixtures, not
# claimed numerical executions.
pcounts={f'P{i:03}':1 for i in range(1,103)}
for lo,hi,n in [(1,1,5),(13,13,2),(15,15,4),(16,18,10),(19,20,5760),(21,26,10),(27,27,3),(34,45,4),(62,64,3),(66,66,2),(85,91,3)]:
 for i in range(lo,hi+1):pcounts[f'P{i:03}']=n
ck('panel count independent',sum(pcounts.values())==11768 and pcounts==o.panel_counts())
def node(name,n=0,fail=0,children=None):return dict(name=name,**{'pass':n-fail,'fail':fail,'error':0,'broken':0},children=children or [])
def trace(finished,p=0,pure=0):
 d={f'N{i:03}':p for i in range(1,4)};d['N004']=pure
 d.update({f'N{i:03}':finished for i in range(5,13)})
 return d
metric=dict(seconds=1.,bytes=1024,events=8,gc_seconds=0.,compile_seconds=.1,recompile_seconds=0.)
def fixture(phase):
 data={n:dict(metric) for n in o.PREPARATION};totals=[0,0,0,0]
 for i,name in enumerate(S['units'],1):
  events={};apis={};obs=[];children=[];fail=int(phase=='red300' and name in S['expected_red_units'])
  if i==1:
   sites=dict(pcounts)
   children=[node(n,k) for n,k in zip(['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses'],[31,11619,74,44])]
  elif i==2:
   sites={f'L{k:03}':1 for k in range(1,41)}
   for lo,hi,n in [(1,22,2),(31,32,2),(33,35,3)]:
    for k in range(lo,hi+1):sites[f'L{k:03}']=n
   sites.update(L025=1,L030=2);sites.update(trace(3,0,2))
   events=dict(finish=3,event_begin=3,event_finish=3,event_pure=1,pure_row=2,catch_overflow=1,catch_nonfinite=2)
   apis=dict(factory_candidate=2,factory_micro=12,FTRAN=13,BTRAN=2,replace=8,copy=6,refactor=8,eliminate=8,eliminate_fault=4)
   children=[node('blocked BG lifecycle and failure ownership',sum(sites.values()))]
  else:
   f=S['fixtures'][(i-3)//2];u=f['updates'];panels=f['minimum_panels'] if phase=='green300' else 0
   events=dict(finish=2*u,event_begin=2*u,event_finish=2*u,pure_row=2,event_pure=1)
   if phase=='green300':
    events.update(event_panel_begin=panels+1,event_panel_commit=panels,event_panel_reject=1,event_eligibility=panels+1,event_panel_pivot=8*panels+1,pivot=8*panels+1,event_scalar_suffix=1)
   sites=trace(2*u,8*panels+1 if phase=='green300' else 0,2)
   sites.update({f'N{k:03}':u for k in range(15,26)});sites.update(N013=1,N014=1,N021=2*u,N024=u if f['pivot_agreement'] else 0,N026=1)
   apis=dict(factory_reference=1,factory_candidate=1,FTRAN=6*u,BTRAN=2*u,replace_reference=u,replace_candidate=u)
   obs=[dict(panels=panels if k==0 else 0,rejections=int(k==0 and phase=='green300'),growth=4.,minpivot=1.) for k in range(u)]
  sites={k:v for k,v in sites.items() if v};n=sum(sites.values());totals[0]+=n-fail;totals[1]+=fail
  record=dict(sites=sites,events={k:v for k,v in events.items() if v},apis=apis,active='',failure_count=fail,failures=[dict(site='N026',kind='fail',detail='Test Failed\nExpression: sum(o.panels for o in observed) >= f["minimum_panels"]')] if fail else [])
  data[f'unit-{i}.toml']=dict(index=i,name=name,complete=True,fatal='',tests=node(name,0 if children else n,fail,children),records=record,observations=obs)
 data['raw.toml']=dict(phase=phase,complete=True,fatal='',units_completed=28,loaded=loaded,threads=1,blas_threads=1,totals=totals)
 return data
for phase in ('red300','green300'):
 p=fixture(phase);check=lambda x:o.validate(x,S,loaded,phase)
 ck(phase+' positive alternate event branches',check(p)['expected_failures']==(6 if phase=='red300' else 0))
 for n in sorted(p):
  bad=copy.deepcopy(p);del bad[n];reject(phase+' missing '+n,lambda:check(bad))
 for n in o.PREPARATION:
  for k in ('bytes','events'):
   bad=copy.deepcopy(p);bad[n][k]=1.;reject(phase+' fractional type '+n+k,lambda:check(bad))
  for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):
   for v in (-1,float('nan'),float('inf'),301,True):
    bad=copy.deepcopy(p);bad[n][k]=v;reject(phase+' cost '+n+k+str(v),lambda:check(bad))
 for i in range(1,29):
  key=f'unit-{i}.toml'
  for group in ('sites','apis','events'):
   for counter in p[key]['records'][group]:
    bad=copy.deepcopy(p);bad[key]['records'][group][counter]+=10000;reject(phase+key+group+counter,lambda:check(bad))
  bad=copy.deepcopy(p);bad[key]['complete']=False;reject(phase+key+' incomplete',lambda:check(bad))
 log=''
 for i in range(1,29):
  u=p[f'unit-{i}.toml'];log+=f"UNIT BEGIN {i} {u['name']}\n"
  for f in u['records']['failures']:log+='TEST FAILURE: N026 '+f['detail']+'\n'
  log+=f"UNIT END {i} {u['name']}\n"
 ck(phase+' exact log',not o.warning_log(log,p,phase))
 for extra in ['WARNING','world age','method overwrite','FATAL','ERROR:','Test Failed','TEST FAILURE: P011']:
  ck(phase+' rejected log '+extra,o.warning_log(log+extra,p,phase))
 ck(phase+' missing endpoint',o.warning_log(log.replace('UNIT END 28','lost END 28'),p,phase))
mem=dict(available_kib=8*1024**2,swap_used_kib=0)
ck('valid resources',a.resource_records([dict(mem,elapsed=0.)],mem,1.))
for v in [True,-1,293,float('nan'),float('inf')]:reject('bad resource elapsed '+str(v),lambda:a.resource_records([dict(mem,elapsed=v)],mem,1.))
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'pin';p.write_text('independent temporary fixture')
 receipt=dict(accepted=True,findings=[],scope='review fixture',pins_sha256=sha(p),sha256={str(p):sha(p)},phase='red300')
 c.verify_review(receipt,p,[str(p)],'review fixture','red300');checks.append('review receipt positive')
 for key,val in [('accepted',1),('findings',['x']),('scope','bad'),('pins_sha256','bad'),('sha256',{}),('phase','green300')]:
  bad=dict(receipt);bad[key]=val;reject('bad receipt '+key,lambda:c.verify_review(bad,p,[str(p)],'review fixture','red300'))
ck('no RED predecessor',c.predecessor('red300')==([],[]))
reject('GREEN predecessor absent',lambda:c.predecessor('green300'))
ck('286 history groups',len(set(rd(D/'historical-groups.json')['groups']))==286)
# Recheck all 581 subjects after pure-module/synthetic tests.
ck('final pins unchanged',all(sha(n)==h for n,h in pins.items()))
result=dict(all_passed=True,count=len(checks),checks=checks,pins_sha256=sha(D/'preparation-pins.json'),subjects=581,required_members=581,source_sites=168,payload_files=60,prior_qualification_bound=True,numerical_execution=False,scope='Independent Python/static source preparation verification; synthetic records are not numerical evidence',sha256={str(D/n):sha(D/n) for n in ('driver.jl','oracle.py','control.py','audit.py','schedule.json')},base_source_sha256={str(base/n):sha(base/n) for n in ('dict.jl','abstractdict.jl','timing.jl','experimental.jl')})
if len(sys.argv)>2 and sys.argv[2]=='--publish':
 for name,content in [('independent-review-check.py',Path(__file__).read_text()),('independent-review-check.json',json.dumps(result,indent=2)+'\n')]:
  with (D/name).open('x') as f:f.write(content)
else:
 with Path('/tmp/bg-independent-review-check.json').open('w') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','sha256','base_source_sha256']}))
