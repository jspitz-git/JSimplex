"""Independent saved-data review. Standard library only; no old code imports or solver execution."""
from pathlib import Path
import json,tomllib,hashlib,struct,math,statistics,traceback
from fractions import Fraction
Q=Path(__file__).resolve().parent;D=Q.parent/'NATIVE-ACCURACY-PREPARATION';R=Q.parents[3]
def read(p):return json.loads(Path(p).read_text())
def toml(p):return tomllib.loads(Path(p).read_text())
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def binary(t):
 assert len(t)==16 and all(c in '0123456789abcdef' for c in t)
 x=struct.unpack('>d',bytes.fromhex(t))[0];assert math.isfinite(x);return x
def rat(t):return Fraction(binary(t))
def token(v):return struct.pack('>d',v).hex()
checks=[];details={}
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
def stats(v,short=False):
 m=statistics.median(v);return dict(zip(('median','min','max','mad') if short else ('median','minimum','maximum','mad'),(m,min(v),max(v),statistics.median(abs(x-m) for x in v))))
def entries(m):
 n=m['n'];p=m['colptr'];ix=m['rowval'];v=m['nzval'];assert len(p)==n+1 and p[0]==1 and p[-1]==len(v)+1 and len(ix)==len(v)
 return [(ix[k]-1,j,rat(v[k])) for j in range(n) for k in range(p[j]-1,p[j+1]-1)]
cache={};matrixcache={}
def residual(m,orientation,x,b):
 key=(json.dumps(m,sort_keys=True),orientation,tuple(x),tuple(b))
 if key not in cache:
  mid=key[:2]
  if mid not in matrixcache:
   ee=[(j,i,v) if orientation else (i,j,v) for i,j,v in entries(m)];norms=[Fraction(0)]*m['n']
   for i,j,v in ee:norms[i]+=abs(v)
   matrixcache[mid]=(ee,max(norms))
  ee,norm=matrixcache[mid];xx=list(map(rat,x));bb=list(map(rat,b));assert len(xx)==len(bb)==m['n'];rr=[-z for z in bb]
  for i,j,v in ee:rr[i]+=v*xx[j]
  error=max(map(abs,rr));bound=Fraction(128*m['n'],2**52)*max(1,norm*max(map(abs,xx)),max(map(abs,bb)))
  cache[key]={'passed':error<=bound,'max_residual':str(error),'bound':str(bound),'ratio':float(error/bound)}
 return cache[key]
def main():
 required=read(Q/'result-review-required.json')['paths'];check('exact review membership',len(required)==len(set(required))==314 and all(Path(p).is_file() for p in required))
 launch=read(Q/'accuracy-launch-pins.json');sealed=read(Q/'accuracy-sealed-pins.json')
 for name,m in [('launch',launch),('sealed',sealed),('preparation',read(D/'preparation-pins-reviewed.json'))]:
  check(name+' inventory membership',set(m['files'])==set(m['inventory']) and m['trees']==[])
  check(name+' all resolved targets and hashes',all(str(Path(p).resolve())==v['resolved'] and digest(p)==v['sha256'] for p,v in m['inventory'].items()))
  details[name+'_pins']=len(m['files'])
 check('launch delta',set(launch['files'])==set(sealed['files'])|{str(Q/'accuracy-sealed-pins.json'),str(Q/'accuracy-admission.json')})
 baseline=read(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];check('all 514 production baseline hashes',len(baseline)==514 and all(digest(R/p)==h for p,h in baseline.items()))
 admission=read(Q/'accuracy-admission.json');check('admission accepted',admission['accepted'] and not admission['findings'])
 check('1190 exact admission bindings',set(admission['sha256'])==set(sealed['files'])|{str(Q/'accuracy-sealed-pins.json')} and all(digest(p)==h for p,h in admission['sha256'].items()))
 names={p.name for p in (Q/'accuracy-run').iterdir()};expected={f'window-{i:03}.toml' for i in range(1,133)}|{f'lifecycle-{a}.toml' for a in 'CPR'}|{'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}
 check('141 original and 141 identical portable files',names==expected=={p.name for p in (Q/'portable').iterdir()} and all((Q/'accuracy-run'/p).read_bytes()==(Q/'portable'/p).read_bytes() for p in names))
 check('raw pins equal launch pins',read(Q/'accuracy-run/pins.json')==launch)
 audit=read(Q/'accuracy-audit.json');postcheck=read(Q/'postcheck.json');summary=read(Q/'summary.json');result=audit['result']
 check('13 saved integrity gates',audit['all_passed'] and len(audit['checks'])==13 and all(audit['checks'].values()) and not audit['error'])
 check('9 saved supplemental gates',postcheck['all_passed'] and len(postcheck['checks'])==9 and all(postcheck['checks'].values()))
 for label,record in [('audit',audit),('postcheck',postcheck),('summary',summary)]:check(label+' evidence hashes',all(digest(p)==h for p,h in record['sha256'].items()))
 inv=read(Q/'accuracy-invocation.json');reservation=read(Q/'accuracy-reservation.json');proc=read(Q/'accuracy-run/process.json');current=read(Q/'accuracy-run/current.json');cfg=read(D/'config.json')['accuracy'];sup=inv['supervisor']
 check('literal admitted command',inv['command']==proc['command']==current['command']==reservation['command']==cfg['command'])
 check('single reservation and pins',reservation==dict(one_attempt=True,phase='accuracy',command=cfg['command'],pins_sha256=digest(Q/'accuracy-launch-pins.json'),review_sha256=digest(Q/'accuracy-admission.json'),max_seconds=45))
 check('invocation binding',inv['reservation_sha256']==digest(Q/'accuracy-reservation.json') and inv['review_sha256']==reservation['review_sha256'] and inv['pins_sha256']==proc['pins_sha256']==current['pins_sha256']==reservation['pins_sha256'])
 expectedguard=[inv['python'],'-B',str(D/'guard.py'),'run',str(Q/'accuracy-launch-pins.json'),cfg['output'],'--seconds','39','--deadline',str(inv['monotonic_start']+39),'--',*cfg['command']]
 check('39 second guard literal command',inv['guard_command']==expectedguard)
 check('accepted 45 second supervisor exit without timeout',sup['accepted'] and sup['returncode']==0 and 0<inv['elapsed_seconds']<=45 and 0<sup['elapsed_seconds']<=45 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
 check('guard exit and closure identities',proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] and 0<proc['elapsed_including_launch']<=39 and current['runner']==proc['runner']==sup['guard_identity'] and current['child']==proc['child'])
 hosts=[read(Q/n) for n in ['accuracy-seal-host.json','accuracy-prehost.json','accuracy-posthost.json','result-host.json']]
 check('saved refs boot and no live processes',all(not h['matches'] and h['head']=='1720f7460458d7418b5702099967ab773166caa7' and h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and h['boot_id']==proc['runner']['boot_id']==proc['child']['boot_id'] for h in hosts))
 check('206 historical groups and new group/session closure',len(hosts[0]['groups'])==206 and set(hosts[0]['groups'])<=set(hosts[-1]['groups']) and all(proc[k][f] in hosts[-1]['groups'] for k in ['runner','child'] for f in ['pgid','sid']))
 resources=[json.loads(s) for s in (Q/'accuracy-run/resources.jsonl').read_text().splitlines()];allmemory=resources+[proc['terminal_memory']]
 check('RAM swap budgets and terminal peak',len(resources)==3 and min(x['available_kib'] for x in allmemory)==summary['min_available_kib']>=6*1024**2 and max(x['swap_used_kib'] for x in allmemory)==summary['max_swap_kib']==0 and proc['child_maxrss_kib']==summary['terminal_peak_rss_kib']==399924)
 for v in resources:
  m={s.split()[0].rstrip(':'):int(s.split()[1]) for s in v['child_memory']};assert set(m)=={'VmRSS','VmHWM','VmPeak','VmSwap'} and 0<=m['VmRSS']<=m['VmHWM']<=proc['child_maxrss_kib'] and m['VmPeak']<=8*1024**2 and m['VmSwap']==0
 check('sampled resident and virtual memory remain separate',True)
 data=read(D/'inputs.json');check('JSON TOML input equality',data==toml(D/'inputs.toml'));fs={f['name']:f for f in data['fixtures']};windows=[toml(Q/f'accuracy-run/window-{i:03}.toml') for i in range(1,133)];lives={a:toml(Q/f'accuracy-run/lifecycle-{a}.toml') for a in 'CPR'};raw=toml(Q/'accuracy-run/raw.toml')
 check('raw complete and unchanged inputs',raw['completed'] and raw['inputs_unchanged'] and raw['fatal']=='' and raw['threads']==raw['blas_threads']==1 and raw['index_bits']==64 and raw['stdlib_paths']==read(D/'stdlib-paths.json'))
 check('exact whole driver call ledger',raw['counts']==dict(fresh=141,refactor=9,copy=3,ftran=4245,btran=2133,snapshot=12))
 base=lives['C']['initial']['control'];assert len(base)==20 and binary(base[3])==.1 and binary(base[7])==0 and binary(base[15])==.001
 def controls(a,c):
  expected=list(base);expected[3]=token(1. if a=='P' else .1);expected[7]=token(2. if a=='R' else 0.);assert c==expected
 def state(a,s,n):
  assert all(s[k] is True for k in ['native_owned','native_match','control_private','control_equal']);controls(a,s['control']);assert s['W']==n*(5 if a=='R' else 1) and s['Wi']==n and s['sym_pivot']==base[15]
 observed=[];metadata={a:dict(attempted=0,taken=0,flops=0) for a in 'CPR'};bits={};old=toml(Q.parent/'DIRECT-LU-BACKEND-PREPARATION/probe-run/fresh.toml')['outputs'][1];oldmatches=[]
 def solve(label,a,f,x,info,rhs):
  row=residual(f['matrix'],rhs=='unit',x,f['rhs'][rhs]);observed.append(dict(label=label,arm=a,**row));status,taken,attempted,flops=map(binary,info);assert status==0 and taken.is_integer() and attempted.is_integer() and 0<=taken<=attempted<=(2 if a=='R' else 0) and flops>=0
  for k,v in [('attempted',int(attempted)),('taken',int(taken)),('flops',flops)]:metadata[a][k]+=v
 for a,l in lives.items():
  assert l['arm']==a and len(l['outputs'])==len(l['info'])==14 and all(l[k] is True for k in ['poisoned_private','copy_contract','independent_T','independent_V','preserved','singular']) and l['cause'] in ('SingularException','LinearAlgebra.SingularException') and l['status']==1
  for k in ['initial','first','second','fresh','finalF','finalS']:state(a,l[k],32)
  for k,(x,info) in enumerate(zip(l['outputs'],l['info'])):
   original=k<4 or k>=10;f=data['lifecycle'] if original else fs['sparse32'];rhs='unit' if k%2 else ('a' if original else 'dse');solve(f'life-{a}-{k+1}',a,f,x,info,rhs)
 check('all lifecycle ownership controls workspaces singular outcomes',True)
 costs={};factors={};strategy={};warm=0
 for spec,w in zip(data['schedule'],windows):
  assert w['schedule']==spec;a=spec['arm'];name=spec['fixture'];f=fs[name];n=f['matrix']['n'];assert len(w['outputs'])==len(w['info'])==48
  state(a,w['before'],n);state(a,w['after'],n);assert w['before']==w['after'];assert w['before']['strategy']==(1 if name.startswith('sparse') else 3);strategy.setdefault(name+':'+a,set()).add(w['before']['strategy']);warm+=spec['warm']
  for k,(x,info) in enumerate(zip(w['outputs'],w['info'])):
   rhs=['a','dse','unit'][k%3];solve(f'window-{spec["id"]}-{k+1}',a,f,x,info,rhs);bits.setdefault(name+':'+a+':'+rhs,set()).add(tuple(x))
   if name=='sparse96' and a=='C' and rhs=='dse':oldmatches.append(x==old)
  for region in ['construction','solve']:
   timing=w[region];assert set(timing)=={'seconds','bytes','events','gctime','compile_time','recompile_time'} and all(type(v) in (float,int) and math.isfinite(v) and v>=0 for v in timing.values())
   if not spec['warm']:
    assert timing['compile_time']==timing['recompile_time']==timing['gctime']==0
    if region=='solve':assert timing['bytes']==timing['events']==0
    costs.setdefault(name+':'+a+':'+region,{})[str(spec['round'])]=timing
  if spec['round']==11:factors[name+':'+a]=w['factor']
  else:assert 'factor' not in w
 check('132 complete windows 36 warm 96 measured and 12 snapshots',warm==36 and len(factors)==12)
 check('all 6378 independently exact saved residuals',len(observed)==6378 and observed==result['residuals']);details['exact_residuals']=len(observed);details['unique_exact_evaluations']=len(cache)
 check('independent refinement metadata',metadata==result['metadata'] and metadata['R']['attempted']==metadata['R']['taken']==1232 and metadata['C']['attempted']==metadata['P']['attempted']==0)
 check('176 C failure bits preserved',len(oldmatches)==176 and all(oldmatches) and oldmatches==result['C_saved_DSE_matches'])
 check('within-arm repeated bits stable',all(len(v)==1 for v in bits.values()) and {k:len(v) for k,v in bits.items()}==result['within_arm_distinct_bits'])
 failures={a:sum(not v['passed'] for v in observed if v['arm']==a) for a in 'CPR'};check('per arm 2126 and C176 P0 R0 failures',all(sum(v['arm']==a for v in observed)==2126 for a in 'CPR') and failures==summary['failures']=={'C':176,'P':0,'R':0});details['failures']=failures
 check('reported residual maxima',summary['max_residual_ratio']=={a:max(v['ratio'] for v in observed if v['arm']==a) for a in 'CPR'})
 for name,samples in costs.items():
  assert set(samples)==set(map(str,range(4,12)));saved=result['cost'][name];assert samples==saved['samples'];fixture,a,region=name.split(':');ref=costs[fixture+':C:'+region]
  assert {k:stats([s[k] for s in samples.values()]) for k in samples['4']}==saved['summary']
  assert {k:stats([samples[r][k]/ref[r][k] for r in map(str,range(4,12))]) if all(s[k]>0 for s in ref.values()) else None for k in ['seconds','bytes','events']}==saved['paired_C_ratios']
 check('all 192 measured regions and 24 complete cost statistics recomputed',len(costs)==24)
 for name in fs:
  cs=lambda a,reg,r:costs[f'{name}:{a}:{reg}'][str(r)]['seconds']
  numerator=[cs('P','construction',r)-cs('R','construction',r) for r in range(4,12)];denominator=[(cs('R','solve',r)-cs('P','solve',r))/16 for r in range(4,12)];cross=summary['crossover'][name]
  assert min(denominator)>0 and cross['denominator_positive_all_pairs'];assert stats(numerator,True)==cross['P_minus_R_construction_seconds'] and stats(denominator,True)==cross['R_minus_P_per_triplet_seconds'];assert stats([max(0,x/y) for x,y in zip(numerator,denominator)],True)==cross['paired_break_even_triplets'];assert max(0,max(numerator))/min(denominator)==cross['conservative_observed_spread_upper']
 check('four paired crossover models and spread bounds',True)
 for key,factor in factors.items():
  name,a=key.split(':');m=fs[name]['matrix'];n=m['n'];controls(a,factor['control']);assert factor['n']==factor['nzd']==n and factor['status']==0 and factor['do_recip'] in (0,1)
  def unpack(v,csr):
   ee=entries(dict(n=n,colptr=v['ptr'],rowval=v['indices'],nzval=v['values']));assert v['format']==('csr' if csr else 'csc');return {(j,i) if csr else (i,j):x for i,j,x in ee}
  lower=unpack(factor['L'],True);upper=unpack(factor['U'],False);assert len(lower)==factor['lnz'] and len(upper)==factor['unz'];assert all(i>=j for i,j in lower) and all(i<=j for i,j in upper);assert all(lower[i,i]==1 and upper[i,i]!=0 for i in range(n));assert sorted(factor['p'])==sorted(factor['q'])==list(range(1,n+1))
  scales=list(map(rat,factor['Rs']));assert len(scales)==n and min(scales)>0;scaled={(i,j):v*scales[i] if factor['do_recip'] else v/scales[i] for i,j,v in entries(m)};product={};ur={}
  for (i,j),v in upper.items():ur.setdefault(i,[]).append((j,v))
  for (i,k),v in lower.items():
   for j,x in ur[k]:product[i,j]=product.get((i,j),Fraction(0))+v*x
  error=max(abs(product.get((i,j),0)-scaled.get((factor['p'][i]-1,factor['q'][j]-1),0)) for i in range(n) for j in range(n));maxu=max(map(abs,upper.values()));maxb=max(map(abs,scaled.values()));report=result['factors'][key]
  assert report['max_U']==str(maxu) and report['max_scaled_B']==str(maxb) and report['growth']==float(maxu/maxb) and report['factor_identity_residual']==str(error) and report['factor_identity_exact']==(error==0)
  assert report['fill_L']==factor['lnz'] and report['fill_U']==factor['unz'] and report['graph_bytes']==factor['graph_bytes'];assert len(factor['info'])==90
  assert report['native_info']=={k:binary(factor['info'][i]) for k,i in [('strategy',18),('peak_units',41),('numeric_units',40),('factor_flops',42),('unit_bytes',3)]}
 check('12 independent exact scaled permuted factor identities growth fill native metadata',True)
 for name in fs:
  keys=['L','U','p','q','Rs','do_recip'];same={a:all(factors[name+':'+a][k]==factors[name+':C'][k] for k in keys) for a in 'PR'};assert same['R'] and same['P']==(name!='sparse96');assert summary['factor_bits'][name]==dict(P_equals_C=same['P'],R_equals_C=same['R']);assert factors[name+':R']['graph_bytes']-factors[name+':C']['graph_bytes']==32*fs[name]['matrix']['n']
 check('P and R mechanism and retained graph differences',True)
 c=result['factors']['sparse96:C'];p=result['factors']['sparse96:P'];check('sparse96 growth fill and native size claims',c['growth']==245688.02631578944 and p['growth']==1 and p['fill_U']-c['fill_U']==15 and p['fill_L']==c['fill_L']==234 and (p['native_info']['numeric_units']-c['native_info']['numeric_units'])*16==48)
 for key,record in summary['refinement'].items():
  name,a,rhs=key.split(':');offset=['a','dse','unit'].index(rhs);vv=[w['info'][k] for w in windows if w['schedule']['fixture']==name and w['schedule']['arm']==a for k in range(offset,48,3)];aa=[int(binary(v[2])) for v in vv];tt=[int(binary(v[1])) for v in vv];assert record==dict(calls=len(vv),attempted=sum(aa),taken=sum(tt),maximum_attempts=max(aa),histogram={str(i):aa.count(i) for i in sorted(set(aa))})
 check('all refinement histograms',True)
 check('fixed diagnostic output and info payload counts',sum(len(x) for w in windows for x in w['outputs'])==405504 and sum(len(x) for w in windows for x in w['info'])==25344)
 check('old cost1 remains false',read(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
 details.update(raw_files=141,portable_files=141,baseline_hashes=514,required_paths=314,additional_continuation_path=str(Q/'continuation-text.md'),metadata=metadata)
 return True
try:
 accepted=main();error=''
except Exception:
 accepted=False;error=traceback.format_exc()
record=dict(accepted=accepted,checks=checks,check_count=len(checks),details=details,error=error,sha256={str(Path(__file__).resolve()):digest(__file__)},scope='New independent Python standard-library saved-data checker only. No old auditor or solver execution.')
with (Q/'result-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['checks','sha256']},indent=2))
raise SystemExit(0 if accepted else 1)
