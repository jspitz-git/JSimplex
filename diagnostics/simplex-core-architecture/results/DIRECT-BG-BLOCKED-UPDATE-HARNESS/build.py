from pathlib import Path
import json,hashlib,re,os,sys,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');B=R/'diagnostics/simplex-core-architecture/results';H=B/'DIRECT-BG-BLOCKED-UPDATE-HARNESS';C=R/'diagnostics/direct-bg-blocked-update/reproduce';G=B/'DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER';Q=B/'DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,s):
 with (H/n).open('x') as f:f.write(s)
def js(n,j):write(n,json.dumps(j,indent=2)+'\n')
def rep(s,a,b):
 if s.count(a)!=1:raise ValueError((a,s.count(a)))
 return s.replace(a,b)
write('build.py',Path(__file__).read_text())
# Exact reusable guard/supervisor, no execution.
copies={}
for name in ['guard.py','supervisor.py','loaded-paths.json']:
 p=G/name;write(name,p.read_text());copies[name]={'source':str(p),'sha256':sha(p)}
js('copied-files.json',copies)
js('environment.json',{k:os.environ.get(k) for k in json.loads((G/'environment.json').read_text())})
m=json.loads((C/'overlay-manifest.json').read_text());stage={'path':m['stage'],'sha256':m['stage_sha256']};js('stages.json',{'red':stage,'green':stage})
roots={'diagnostic':R,'production':Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')}
js('baseline.json',{k:{n:sha(root/n) for n in subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines()} for k,root in roots.items()})
# Only definition imports; never invoke guard/main.
sys.path.insert(0,str(H));import guard
runtime=json.loads((G/'runtime-inputs-complete.json').read_text());js('runtime-inputs-complete.json',{'scope':'Fresh readtime bindings only; no runtime/loader capture','inventory':guard.inventory(list(runtime['inventory']),[])})
for name in ['outer.py','seal.py','launch.py','post-return.py']:
 s=(G/name).read_text().replace('BG specialization GC','BG blocked U').replace('BG specialization','BG blocked U').replace('redgc300','red300').replace('greengc300','green300');write(name,s)
s=(G/'control.py').read_text().replace('diagnostics/direct-bg-export-specialized/reproduce','diagnostics/direct-bg-blocked-update/reproduce').replace("ENTRY='ff248544e8f89cc05aecff64806bf60d8b2bd9cf'","ENTRY='1a824ea2d6478ba5ecbd3afc8ffbe83207bf2fd8'").replace('redgc300','red300').replace('greengc300','green300').replace('BG specialization GC','BG blocked U')
a=s.index('def preparation():');b=s.index('def result_review(',a)
s=s[:a]+'''def preparation():
 m=D/'preparation-pins.json';j=rd(m)
 require(bindings(j) and set(j['sha256'])==set(rd(D/'required-paths.json')['paths']),'Preparation drift/membership')
 verify_review(rd(D/'review.json'),m,list(j['sha256'])+[str(m)],'BG blocked U driver preparation')
 q=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2');v=rd(q/'review.json')
 require(v.get('accepted') is True and v.get('findings')==[] and bindings(v),'Task2 review drift')
 require(rd(D/'review.json').get('launch_admitted') is False,'Offline review is not admission')
 for name,item in rd(D/'copied-files.json').items():
  require(sha(D/name)==sha(item['source'])==item['sha256'],'Copied control drift')
 return sorted(set(j['sha256'])|{str(m),str(D/'review.json')}|set(rd(D/'review.json').get('evidence_sha256',{})))
''' +s[b:];write('control.py',s)
# Preserve original test bytes: separate clones, literal inverse substitutions only.
sites={};transforms={}
for name,prefix in [('panel-tests.jl','P'),('numerical-tests.jl','N'),('lifecycle-tests.jl','L')]:
 original=(C/name).read_text();s=original;changes=[];idx=0
 def macros(match):
  global idx
  idx+=1;sid=f'{prefix}{idx:03d}';kind=match.group(0);line=original.count('\n',0,match.start())+1
  sites[sid]={'file':name,'line':line,'kind':kind,'source_line':original.splitlines()[line-1]}
  return ('@checkthrows' if kind=='@test_throws' else '@check')+' "'+sid+'"'
 s=re.sub(r'@test_throws\b|@test\b',macros,s)
 changes.append({'kind':'macros','sites':[k for k in sites if k.startswith(prefix)]})
 first='using Test';s=rep(s,first,'using ..HarnessRecords: @check, @checkthrows\nimport ..HarnessRecords\n'+first)
 # Cold API accounting at call sites, before dispatch including expected throws.
 for call,label in [('J.forward_solve!','FTRAN'),('J.transpose_solve!','BTRAN'),('J.refactorize!','refactor'),('J.copy_basis_factorization','copy'),('J.replace_column!','replace'),('J._direct_lu_factor','factory_reference'),('A._bgb_factor','factory_candidate'),('module_._bgb_factor','factory_micro'),('A._bgb_reference_replace!','replace_reference'),('A._bgb_replace!','replace_candidate'),('A._bgb_test_eliminate!','eliminate'),('F._bgb_test_eliminate!','eliminate_fault')]:
  a=call+'(';b=f'HarnessRecords.api("{label}",{call},'
  if a in s:changes.append({'old':a,'new':b,'count':s.count(a)});s=s.replace(a,b)
 if prefix=='N':
  for a,b in [('function pivot!(t,k,a,z,swapped,fused)\n','function pivot!(t,k,a,z,swapped,fused)\n    HarnessRecords.tick("pivot")\n'),('for k in first:last\n','for k in first:last\n            HarnessRecords.tick("pure_row")\n'),('elseif event===:finish\n','elseif event===:finish\n        HarnessRecords.tick("finish")\n'),('    push!(t.events,event)\n','    HarnessRecords.tick("event_"*string(event))\n    push!(t.events,event)\n'),('        op(x,r,s.unit);op(y,c,s.unit)','        HarnessRecords.api(trans ? "BTRAN" : "FTRAN",op,x,r,s.unit);HarnessRecords.api(trans ? "BTRAN" : "FTRAN",op,y,c,s.unit)')]:
   s=rep(s,a,b);changes.append({'old':a,'new':b,'count':1})
 write(name,s);transforms[name]={'original':str(C/name),'sha256':sha(C/name),'clone_sha256':sha(H/name),'changes':changes}
js('test-transform.json',transforms);js('assertion-sites.json',sites)
fixtures=json.loads((C/'fixtures.json').read_text())['fixtures']
js('schedule.json',{'units':['panel','lifecycle']+[f['name']+'/'+b for f in fixtures for b in ['native','markowitz']],'fixtures':[{'name':f['name'],'n':f['n'],'updates':len(f['steps']),'pivot_agreement':f['pivot_agreement'],'minimum_panels':f['minimum_panels']} for f in fixtures],'expected_red_units':[f['name']+'/'+b for f in fixtures if f['minimum_panels']>0 for b in ['native','markowitz']]})
print('Prepared controls and test clones',len(sites),'sites')
