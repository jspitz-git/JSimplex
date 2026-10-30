from pathlib import Path
import ast,copy,hashlib,json,os,struct,subprocess,sys
sys.dont_write_bytecode=True
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl')
D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'
R=W/'.superpowers/dual-recovery-devex-task4/cost-1/reference-cost'
HEAD='d618023b27a42170438c26995c50a036af01c2b4'
checks={};bindings={};cache={}
def sha(p):
 p=Path(p);key=str(p)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
  cache[key]=h.hexdigest()
 bindings[key]=cache[key];return cache[key]
def read(p):sha(p);return json.loads(Path(p).read_text())
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise AssertionError(k)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def reject(k,fn):
 try:fn()
 except (ValueError,KeyError,FileNotFoundError):ck(k,True)
 else:ck(k,False)
seal=read(R/'seal.json');pins=read(R/'pins.json');contract=read(D/'contract.json')
ck('concrete seal hash',sha(R/'seal.json')=='4456da15f6621f4bcd44b79bae753065e25c08ce5db10cbd24b4c34abcea985a')
ck('concrete pins hash',sha(R/'pins.json')==seal['pins_sha256']=='c422ea44a387cf346cae88358c132f90dba61afda225d3f1ae5ba63de203e709')
ck('only seal and pins exist',sorted(p.name for p in R.iterdir())==['pins.json','seal.json'])
ck('no candidate directory',(not (R.parent/'candidate-cost').exists()))
ck('exact HEAD and branch',git('rev-parse','HEAD')==seal['head']==HEAD and git('branch','--show-current')=='codex/native-quality-finite')
ck('master local refs',git('rev-parse','master')==git('rev-parse','origin/master')==seal['master']=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b')
ck('tracked tree and index unchanged',not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'))
ck('production test CI unchanged against master',not git('diff','master','HEAD','--','src','test','Project.toml','.github'))
remote={a.split()[1]:a.split()[0] for a in git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines()}
ck('remote refs',remote=={'refs/heads/master':seal['master'],'refs/heads/codex/native-quality-finite':HEAD})
sys.path.insert(0,str(D));import common as C;import binding_checks as B;import cost_checks as K;import audit as A
ck('exact command environment scope',seal['command']==C.command('reference-cost')==contract['commands']['reference-cost'] and seal['environment']==C.environment('reference-cost')==contract['environments']['reference-cost'] and seal['phase']=='reference-cost' and seal['expected_exit']==0)
ck('actual mandatory inventory',len(pins['inventory'])==566 and C.check_inventory(pins,C.required_paths('reference-cost')))
for p,v in pins['inventory'].items():ck('pin '+p,sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'])
B.interpreter(seal,pins,sys.executable);ck('exact absolute resolved interpreter',sys.executable==seal['guard_python']=='/usr/bin/python3')
folders=[C.ORIGINAL,C.OLD_RED,C.OLD_GREEN,C.FIX,C.GREEN2_PREP,C.GREEN2_RESULT,D]
public=set();maps={}
for folder in folders:
 pub=read(folder/'publication.json');ck('publication accepted '+str(folder),pub['accepted'] is True)
 for rel in pub['expected_names']:
  p=W/rel;public.add(str(p));data=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  ck('committed exact '+rel,blob==git('rev-parse','HEAD:'+rel) and not p.is_symlink())
  if rel in pub.get('blobs_excluding_publication',{}):ck('published blob '+rel,blob==pub['blobs_excluding_publication'][rel])
 closure=read(folder/'closure.json');maps.update(closure.get('explicit_exact_copy_maps',{}))
ck('526 prior plus34 new publications',len(public)==560 and len(read(D/'publication.json')['expected_names'])==34)
for src,target in maps.items():
 sha(target)
 if Path(src).is_file():ck('portable exact '+src,sha(src)==sha(target))
def mapped_record(p,label):
 a=read(p)
 for source,h in a.get('bindings',{}).items():
  target=maps.get(source,source);ck(label+' binding '+source,sha(target)==h)
 return a
pres=read(D/'preservation.json');ck('526 preserved',len(pres['frozen_publications'])==526)
for p,h in pres['frozen_publications'].items():ck('old immutable '+p,sha(p)==h)
for p,v in pres['copies'].items():ck('exact guard/helper '+p,sha(p)==sha(v['source'])==v['sha256'])
source=mapped_record(D/'source-check.json','source evidence');ck('19 accepted source checks',source['accepted'] is True and len(source['checks'])==19 and all(v is True for v in source['checks'].values()) and len(source['bindings'])==546)
review=mapped_record(D/'review-final.json','offline preparation review');ck('2110 offline review checks697bindings',review['accepted'] is True and review['numerical_admission'] is False and len(review['checks'])==2110 and all(v is True for v in review['checks'].values()) and len(review['bindings'])==697)
red=mapped_record(C.OLD_RED/'red/audit.json','RED');green=mapped_record(C.GREEN2_RESULT/'green2/audit.json','GREEN2');g_review=mapped_record(C.GREEN2_RESULT/'review-final.json','GREEN2 independent result')
ck('RED7pass1expectedfail',red['accepted'] is True and red['test_summary']=={'Pass':7,'Fail':1,'Total':8})
bad=read(C.OLD_GREEN/'green/supervisor.json');ck('failed GREEN remains rejected no audit',bad['accepted'] is False and bad['returncode']==1 and not (C.OLD_GREEN/'green/audit.json').exists())
ck('GREEN2 5774 and independent2182checks724bindings',green['accepted'] is True and green['test_summary']=={'Pass':5774,'Total':5774} and g_review['accepted'] is True and len(g_review['checks'])==2182 and len(g_review['bindings'])==724 and g_review['cost_qualified'] is False)
used,facts=C.prior('reference-cost');ck('all consumed attempt times retained',used==seal['used_seconds']==1033.6005972509156 and facts==seal['previous'] and [v['elapsed'] for v in facts]==[33.35953255696222,494.6009602919803,505.6401044019731])
ck('remaining shared1800 no reset',1800-used==seal['remaining_seconds']==766.3994027490844 and seal['shared_total_seconds']==1800)
reject('candidate refuses absent closed reference',lambda:C.prior('candidate-cost'))
ck('original cost schedule',C.driver_ready() and contract['cost']==read(C.ORIGINAL/'contract.json')['cost'])
projects={s:{str(p.relative_to(C.ORIGINAL/'overlays'/s)):p for p in (C.ORIGINAL/'overlays'/s).rglob('*') if p.is_file()} for s in ('reference','candidate')}
ck('two74file projects',len(projects['reference'])==len(projects['candidate'])==74 and projects['reference'].keys()==projects['candidate'].keys())
differences=[]
for n,p in projects['reference'].items():
 q=projects['candidate'][n]
 if sha(p)!=sha(q):differences.append(n)
 if n.startswith('src/'):ck('reference production '+n,sha(p)==sha(W/n))
 ck('candidate tested GREEN2 '+n,sha(q)==sha(C.FIX/'prepared/overlays/candidate'/n))
ck('only3 candidate source differences',sorted(differences)==['src/simplex_numerics.jl','src/simplex_pivot.jl','src/simplex_recovery.jl'])
a=(C.ORIGINAL/'tests/reference.jl').read_text().replace('JS.','');b=(C.ORIGINAL/'overlays/reference/src/simplex_recovery.jl').read_text()
ck('legacy public body exact',a[a.index('function refine_basis_solve!'):a.index('\nfunction _refine_basis_solve!')].strip()==b[b.index('function refine_basis_solve!'):b.index('\n_checkpoint_model')].strip())
ck('legacy private body exact',a[a.index('function _refine_basis_solve!'):a.index('\nend # module')].strip()==b[b.index('function _refine_basis_solve!'):b.index('\n# A clock-only guard')].strip())
ck('primary256eps policy','default_solve = exact ? zero(T) : T(256)*eps(T)' in (W/'src/simplex_numerics.jl').read_text())
for T,layout,bad in K.KEYS:
 fmt='>f' if T=='Float32' else '>d';encode=lambda v:struct.pack(fmt,v).hex()
 independently=[]
 for col in range(64):
  for row in range(64):
   value=64 if row==col else 0
   if row!=col and (layout=='dense' or abs(row-col)==1):
    value=(1+((row+1)+2*(col+1))%5)*(-1 if (row+col)%2==0 else 1)/64
   independently.append(encode(value))
 ck('independent4096matrix '+str((T,layout,bad)),independently==K.expected_matrix(T,layout))
 ck('independent nnz '+str((T,layout,bad)),sum(v!=encode(0) for v in independently)==(190 if layout=='sparse' else 4096))
 ck('tolerance literal '+str((T,layout,bad)),encode(256*2**(-23 if T=='Float32' else -52))==('38000000' if T=='Float32' else '3d30000000000000'))
log='Test Summary: | Pass Total Time\nTASK4_COST | 272 272 1.0s\nTASK4_COST_COMPLETED reference\n'
ck('ordinary flat272 parser',A.ordinary(log,'reference-cost')=={'Pass':272,'Total':272})
for i,badlog in enumerate([log.replace('272 272','271 271'),log.replace('reference','candidate'),log+log,'ERROR: x\n'+log]):reject('ordinary refusal '+str(i),lambda b=badlog:A.ordinary(b,'reference-cost'))
ck('warm measured calls assertions work counts',8*(3+7)==80 and 4*(3+7)==40 and 8*(3*2+7*4)==272 and contract['cost']['api_calls_per_side']==80 and contract['cost']['assertions_per_side']==272)
for name,n in [('offline-tests.log',11),('offline-tests-final.log',13)]:
 text=(D/name).read_text();ck('read submitted log '+name,'Ran '+str(n)+' tests' in text and text.rstrip().endswith('OK'))
for p in D.rglob('*.py'):ast.parse(p.read_text());sha(p)
host=C.host();ck('fresh736groups ANDsessions noJulia',len(host['checked_groups'])==736 and host['conflicts']==[] and host['still_active_current_launcher']==[])
ck('freshboot refs memory',host['boot_id']==seal['preflight']['boot_id']=='781795f4-f7af-4c3b-9ce9-45c7cae76ecb' and host['refs']['HEAD']==HEAD and host['memory']['available_kib']>=6*1024**2 and host['memory']['swap_used_kib']<=1024**2)
old=read(C.GREEN2_RESULT/'postcheck.json');identities=[]
for a in old['closed_owner_identities']:
 try:now=C.identity(a['pid'])
 except (FileNotFoundError,ProcessLookupError):now=None
 ck('old owner absent '+str(a['pid']),now is None or (now['boot_id'],now['start_ticks'])!=(a['boot_id'],a['start_ticks']))
 identities.append({'original':a,'current':now})
for p in Path('/tmp/devex-reference-cost-run-20261030').iterdir():
 if p.is_file():sha(p)
for p in D.rglob('*'):
 if p.is_file():sha(p)
sha(__file__)
ck('no submitted mains guards tests imported',not any(n in sys.modules for n in ['seal','launch','close','guard_reviewed','supervisor_reviewed','entry_gate','offline_tests','offline_tests_final']))
ck('still only seal and pins',sorted(p.name for p in R.iterdir())==['pins.json','seal.json'])
result=dict(accepted=True,scope='fresh concrete reference numerical admission check',checks=checks,bindings=bindings,host=host,remote_refs=remote,old_owners=identities,used_seconds=used,remaining_seconds=1800-used)
with Path('/tmp/devex-reference-cost-numerical-check-result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings),pins=len(pins['inventory']),publications=len(public),groups=len(host['checked_groups']),memory=host['memory'],used=used,remaining=1800-used)))
