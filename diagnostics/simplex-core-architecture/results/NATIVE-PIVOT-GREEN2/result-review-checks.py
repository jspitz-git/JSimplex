"""Independent stored-data result review. No old scripts imported or executed; no Julia.
Only new reviewer JSON is written, exclusively. Finalizers are source-reviewed only.
"""
from pathlib import Path
import json,hashlib,tomllib,struct,math,os,time,subprocess
from fractions import Fraction
from collections import Counter
D=Path(__file__).resolve().parent; R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION';RUN=Q/'runs/green2';O=RUN/'output';OLD=D.parent/'NATIVE-PIVOT-QUALIFICATION';P=D.parent/'NATIVE-PIVOT-PREPARATION';F=D.parent/'NATIVE-PIVOT-OBSERVER-FIX'
checks={};cache={};bytes_read=0;start=time.monotonic()
def rd(p):return json.loads(Path(p).read_text())
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def sha(n):
 global bytes_read
 p=path(n);key=str(p)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b);bytes_read+=len(b)
  cache[key]=h.hexdigest()
 return cache[key]
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def bindings(p):
 z=rd(p);ck('bindings:'+str(p.relative_to(R)),all(sha(k)==v for k,v in z['sha256'].items()));return z
A=bindings(RUN/'audit.json');S=rd(RUN/'sealed.json');L=rd(RUN/'launch-pins.json');ADM=bindings(RUN/'admission.json');PREP=bindings(Q/'preparation-pins.json')
ck('audit_pass_scope',A['phase']=='green2' and A['all_passed'] is True and A['error']=='')
ck('audit74',len(A['sha256'])==74)
for n,z,count in [('seal',S,962),('launch',L,965)]:
 ck(n+'_exact_members',len(z['files'])==len(set(z['files']))==count and set(z['files'])==set(z['inventory']))
 ck(n+'_fresh_hashes_paths',all(sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in z['inventory'].items()))
ck('launch_union',set(L['files'])==set(S['files'])|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']})
ck('seal_launch_no_drift',all(L['inventory'][k]==v for k,v in S['inventory'].items()) and L['trees']==S['trees'] and L['inputs']==S['inputs']==[])
ck('output_pins',rd(O/'pins.json')==L)
ck('admission_scope_membership',ADM['accepted'] is True and ADM['findings']==[] and ADM['scope']=='exact-stage admission' and ADM['phase']=='green2' and ADM['pins_sha256']==sha(RUN/'sealed.json') and set(ADM['sha256'])==set(S['files'])|{str(RUN/'sealed.json')})
ck('admission_supplement',all(sha(k)==v for k,v in ADM['evidence_sha256'].items()))
ac=rd(RUN/'admission-checks.json');ck('admission99',ac['all_passed'] is True and len(ac['checks'])==99 and all(ac['checks'].values()))
ck('prep881',len(PREP['sha256'])==881 and set(PREP['sha256'])==set(rd(Q/'required-paths.json')['paths']))
review=bindings(Q/'review-final.json');ck('prep_review',review['accepted'] is True and review['findings']==[] and review['scope']=='offline preparation' and set(review['sha256'])==set(PREP['sha256'])|{str(Q/'preparation-pins.json')} and review['pins_sha256']==sha(Q/'preparation-pins.json'))
for n in ['source-check.json','reviewer-checks.json','reviewer-final-bindings.json','publication-review.json','closure.json','closure-supplement.json','publication-final.json']:
 z=bindings(Q/n);ck('accepted:'+n,z.get('all_passed',z.get('accepted')) is True and all(z.get('checks',{}).values()))
rt=bindings(OLD/'runtime-pins.json');ck('runtime679',len(rt['sha256'])==679 and set(rt['sha256'])<=set(S['files']))
manifest=rd(P/'overlay-manifest.json');cfg=rd(RUN/'config.json');stage=Path(cfg['stage'])
ck('candidate75_exact',len(manifest['candidate'])==75 and {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}=={e['destination'] for e in manifest['candidate']})
for arm,count in [('candidate',75),('reference',73)]:ck('manifest_'+arm,len(manifest[arm])==count and all(sha(e['source'])==e['sha256'] for e in manifest[arm]))
ck('stage_identity',all(not (stage/e['destination']).is_symlink() and sha(stage/e['destination'])==e['sha256'] for e in manifest['candidate']))
inv=rd(P/'inverse.json');ck('source_inverse_members',len(inv['original'])==7 and len(inv['edits'])==28)
for original in inv['original']:
 rel=str(Path(original).relative_to(R));s=(P/'candidate'/rel).read_text()
 for e in reversed([e for e in inv['edits'] if e['file']==rel]):
  assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'])
 ck('source_inverse:'+rel,s==Path(original).read_text())
for n,v in rd(OLD/'test-inverse.json').items():
 s=(OLD/n).read_text();assert sha(OLD/n)==v['sha256']
 for a,b,c in reversed(v['edits']):assert s.count(b)==c;s=s.replace(b,a)
 ck('test_inverse:'+n,s==Path(v['source']).read_text() and sha(v['source'])==v['source_sha256'])
joined='using Test, JSimplex, LinearAlgebra, SparseArrays\n'
for s in rd(OLD/'neighbor-slices.json'):
 text=(R/s['source']).read_text()[s['start']:s['end']];assert text==s['text'];joined+=text
ck('neighbor_slices',joined==(OLD/'neighbors-original.jl').read_text())
for n,p in rd(Q/'source-map.json')['byte_identical'].items():ck('identical:'+n,(Q/n).read_bytes()==Path(p).read_bytes())
i=rd(F/'inverse.json');support=(Q/'test-support-fixed.jl').read_text();u=support.replace(i['helper'],'')
for a,b in i['support_changes']:u=u.replace(b,a)
ck('observer_whole_inverse',u==(OLD/'test-support.jl').read_text())
driver=(Q/'test-driver.jl').read_text();s=driver.replace('include(joinpath(@__DIR__,"regression-reviewed.jl"))\n','').replace('root=RecordedTests.Capture("root")\n    regression=RecordedTests.Capture("regression")\n    helper_calls=Ref(0)','root=RecordedTests.Capture("root")')
block='''        raw["regression_counts_before"]=copy(NP.counts)
        Test.@with_testset regression begin
            DenseTokenRegression.run((format,v)->begin
                helper_calls[]+=1
                NP.dense_tokens(format,v)
            end,NP.scalar,NP.token)
        end
        raw["regression_counts_after"]=copy(NP.counts)
'''
assert s.count(block)==1;s=s.replace(block,'').replace('if phase=="green2"','if phase=="red"\n            include(joinpath(@__DIR__,"..","NATIVE-PIVOT-QUALIFICATION","red-contract.jl"))\n        elseif phase=="green"').replace('\n        raw["regression_tests"]=RecordedTests.dictionary(regression)\n        raw["regression_helper_calls"]=helper_calls[]','').replace('failed(root)==0 && failed(regression)==0 ? 0 : 1','failed(root)==0 ? 0 : 1')
ck('green2_driver_inverse',s==(F/'test-driver-fixed.jl').read_text())
for a,b in i['driver_routes']:s=s.replace(b,a)
ck('original_driver_inverse',s==(OLD/'test-driver-reviewed.jl').read_text())
raw=tomllib.loads((O/'raw.toml').read_text());budget=rd(Q/'budget.json');rb=rd(Q/'regression-budget.json')
ck('raw_complete',raw['complete'] is True and raw['fatal']=='' and raw['phase']=='green2' and raw['threads']==raw['blas_threads']==1)
def assert_tree(t):
 assert t['fail']==t['error']==t['broken']==0 and t['failures']==[]
 return t['pass']+sum(assert_tree(x) for x in t['children'])
ck('assertions6977',assert_tree(raw['tests'])==6858 and assert_tree(raw['regression_tests'])==119)
ck('original_nine_groups',[(x['name'],x['pass']) for x in raw['tests']['children']]==list(budget['test_groups'].items()) and all(not x['children'] for x in raw['tests']['children']) and raw['tests']['pass']==0)
ck('regression119_separate',raw['regression_tests']['name']=='regression' and raw['regression_tests']['pass']==0 and len(raw['regression_tests']['children'])==1 and raw['regression_tests']['children'][0]['name']=='Dense diagnostic tokens preserve sparse inputs' and rb['assertions']==1+12*9+4*2+2==119 and raw['regression_helper_calls']==12+4==16 and raw['regression_counts_before']==raw['regression_counts_after']=={})
expected=dict(Counter(budget['main'])+Counter(budget['neighbors']));obs=Counter()
for e in raw['events']:
 obs[e['call']]+=1;assert e['number']==obs[e['call']] and isinstance(e['exception'],str) and ('after_failure' in e)==bool(e['exception'])
 for key in ['before','after','after_failure']:
  z=e.get(key,{})
  if z.get('kind')=='UMFPACKBackend':
   assert z['policy'] in ['_NATIVE_PIVOT_DEFAULT','_NATIVE_PIVOT_ONE']
   if z['active']!='none':assert len(z['control'])==20 and z['control'][3]==('3ff0000000000000' if z['policy']=='_NATIVE_PIVOT_ONE' else '3fb999999999999a') and z['control'][7]=='0000000000000000'
ck('792events_controls',dict(obs)==expected==raw['counts']==A['result']['entry_counts'] and sum(obs.values())==792<=raw['observation_limit']==2048 and raw['main_counts']==budget['main'])
def rational(token):
 assert isinstance(token,str) and len(token)==16 and set(token)<=set('0123456789abcdef')
 bits=int(token,16);exp=(bits>>52)&2047;sig=bits&((1<<52)-1);assert exp!=2047
 if exp:sig|=1<<52;power=exp-1023-52
 else:power=1-1023-52
 return Fraction((-1 if bits>>63 else 1)*sig)*(Fraction(2)**power)
results=[];empty=0
for eq in raw['equations']:
 m=eq['matrix'];n=m['n'];cp=m['colptr'];rv=m['rowval'];nz=m['nzval'];assert type(n) is int and n>=0 and type(eq['transposed']) is bool
 if not n:
  assert m==dict(n=0,colptr=[1],rowval=[],nzval=[]) and eq['rhs']==eq['output']==[];empty+=1;continue
 assert len(cp)==n+1 and cp[0]==1 and cp[-1]==len(nz)+1 and len(rv)==len(nz) and all(type(x) is int for x in cp+rv) and all(a<=b for a,b in zip(cp,cp[1:]))
 dense=[[Fraction(0) for _ in range(n)] for _ in range(n)]
 for col in range(n):
  rows=rv[cp[col]-1:cp[col+1]-1];assert rows==sorted(set(rows)) and all(1<=r<=n for r in rows)
  for ix in range(cp[col]-1,cp[col+1]-1):
   row=rv[ix]-1
   if eq['transposed']:dense[col][row]=rational(nz[ix])
   else:dense[row][col]=rational(nz[ix])
 x=list(map(rational,eq['output']));b=list(map(rational,eq['rhs']));assert len(x)==len(b)==n
 residual=max(abs(sum((a*v for a,v in zip(row,x)),Fraction(0))-rhs) for row,rhs in zip(dense,b))
 norm=max(sum(map(abs,row),Fraction(0)) for row in dense)
 bound=Fraction(128*n,2**52)*max(Fraction(1),norm*max(map(abs,x)),max(map(abs,b)))
 assert residual<=bound;results.append(dict(passed=True,max_residual=str(residual),bound=str(bound),ratio=float(residual/bound)))
ck('324_exact_equations',len(raw['equations'])==324 and empty==32 and len(results)==292 and results==A['result']['equations'])
ck('260_nonzero',sum(Fraction(x['max_residual'])!=0 for x in results)==260)
ck('max_ratio',max(x['ratio'] for x in results)==0.0007731119791666666)
loaded=rd(Q/'loaded-paths.json');loaded['JSimplex']=str(stage/'src/JSimplex.jl');ck('loaded_paths',raw['loaded']==loaded and all(p in S['files'] for p in loaded.values()))
ck('environment',{k:os.environ.get(k) for k in rd(Q/'environment.json')}==rd(Q/'environment.json'))
I=rd(RUN/'invocation.json');proc=rd(O/'process.json');cur=rd(O/'current.json');reservation=rd(RUN/'reservation.json');sup=I['supervisor'];hosts=[rd(RUN/n) for n in ['host.json','prehost.json','posthost.json']]+[rd(D/'posthost.json')]
ck('config',cfg==S['config']==rd(Q/'config-preview.json') and cfg['phase']=='green2' and cfg['seconds']==60 and cfg['expected_exit']==0)
ck('exact_command',cfg['command']==I['command']==proc['command']==cur['command']==reservation['command'])
ck('command_options',cfg['command'][0]=='/bin/bash' and cfg['command'][2:7]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage)] and cfg['command'][7:]==[str(Q/'test-driver.jl'),str(O),'green2',str(stage)])
ck('guard_command',I['guard_command']==['/usr/bin/python3','-B',str(Q/'guard.py'),'run',str(RUN/'launch-pins.json'),str(O),'--seconds','52','--deadline',str(I['monotonic_start']+52),'--expected-exit','0','--',*cfg['command']])
ck('reservation',reservation==dict(one_attempt=True,phase='green2',command=cfg['command'],pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=60) and I['reservation_sha256']==sha(RUN/'reservation.json') and I['review_sha256']==sha(RUN/'admission.json'))
ck('pin_links',I['pins_sha256']==proc['pins_sha256']==cur['pins_sha256']==sha(RUN/'launch-pins.json'))
ck('success_within_caps',proc['returncode']==sup['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and sup['accepted'] is True and 0<proc['elapsed_including_launch']<sup['elapsed_seconds']<=I['elapsed_seconds']<=60 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup)
ck('identities',cur['runner']==proc['runner']==sup['guard_identity'] and cur['child']==proc['child'] and [(proc[k]['pid'],proc[k]['start_ticks']) for k in ['runner','child']]==[(249639,14817324),(249640,14817374)] and all(proc[k]['pid']==proc[k]['pgid']==proc[k]['sid'] and proc[k]['boot_id']==S['boot_id'] for k in ['runner','child']))
ck('identity_commands',proc['runner']['command'].strip()==' '.join(I['guard_command']) and proc['child']['command'].strip()==' '.join(cfg['command']))
ck('historical_hosts',all(not h['matches'] and all(h[k]==S[k] for k in ['head','master','boot_id']) for h in hosts) and set(S['groups'])<=set(hosts[1]['groups'])<=set(hosts[2]['groups'])==set(hosts[3]['groups']) and len(hosts[3]['groups'])==214 and {249639,249640}<=set(hosts[3]['groups']))
resources=[json.loads(s) for s in (O/'resources.jsonl').read_text().splitlines()]
ck('resources',len(resources)==30 and min(s['available_kib'] for s in resources)==21855112 and max(s['swap_used_kib'] for s in resources)==0 and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in resources+[proc['terminal_memory']]) and proc['child_maxrss_kib']==683124)
ck('resource_order',all(a['elapsed']<b['elapsed'] for a,b in zip(resources,resources[1:])) and 0<=resources[0]['elapsed']<resources[-1]['elapsed']<proc['elapsed_including_launch'])
ck('output_log',(O/'run.log').read_bytes()==b'' and json.loads((RUN/'launcher.log').read_text())==proc)
ck('output_members',{p.name for p in O.iterdir()}=={'process.json','raw.toml','pins.json','run.log','resources.jsonl','current.json'})
ck('sole_green2',{p.name for p in (Q/'runs').iterdir()}=={'green2'})
oldg=bindings(OLD/'runs/green/audit.json');oldr=bindings(OLD/'runs/green/result-review.json');ck('failed_green_preserved',oldg['all_passed'] is False and oldr['accepted'] is False and oldr['qualification_accepted'] is False and oldr['diagnostic_accepted'] is True)
ck('old_attempt_consumed',(OLD/'runs/green/reservation.json').is_file())
ck('old_direct_cost_false',rd(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
post=bindings(D/'postcheck.json');ck('postcheck18_12',post['all_passed'] is True and len(post['checks'])==18 and all(post['checks'].values()) and len(post['sha256'])==12)
# Independently enumerate the proposed mapping without importing or executing its writer.
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';preserved={str(status):D/'STATUS.md.before-GREEN2',str(road):D/'roadmap.md.before-GREEN2'}
ck('continuation_preimages',all(sha(p)==sha(k) for k,p in preserved.items()))
maps=[]
def walk(rec,z,loc=()):
 if isinstance(z,dict):
  for k,v in z.items():
   full=str(path(k))
   if full in preserved:
    value=v if isinstance(v,str) else v.get('sha256') if isinstance(v,dict) else None
    if value==sha(preserved[full]):maps.append(dict(record=str(rec.relative_to(R)),pointer=list(loc)+([k] if isinstance(v,str) else [k,'sha256']),sha256=value,preserved_path=str(preserved[full].relative_to(R))))
   walk(rec,v,loc+(k,))
 elif isinstance(z,list):
  for j,v in enumerate(z):walk(rec,v,loc+(j,))
for rec in sorted(list(Q.rglob('*.json'))+list(F.glob('*.json'))+list(D.glob('*.json'))):walk(rec,rd(rec))
needed=[Q/'closure.json',Q/'closure-supplement.json',Q/'publication-final.json',RUN/'sealed.json',RUN/'launch-pins.json',RUN/'admission.json']
ck('mapping_all_current_records',all({str(status),str(road)}<={m['pointer'][-2] if m['pointer'][-1]=='sha256' else m['pointer'][-1] for m in maps if m['record']==str(p.relative_to(R))} for p in needed))
ck('mapping_nested_inventories',all(any(m['record']==str(p.relative_to(R)) and m['pointer'][0]=='inventory' for m in maps) for p in [RUN/'sealed.json',RUN/'launch-pins.json']))
final=(D/'finalize.py').read_text();pub=(D/'publication.py').read_text()
ck('finalizer_source_scope',"value==sha(preserved[full])" in final and "save(D/'continuation-mappings.json'" in final and "list(Q.rglob('*.json'))" in final and "'stage result','green2'" in final and "p.open('x')" in final and "len(h['groups'])==214" in final)
ck('publication_source_scope',"git','add','--',*other" in pub and "'diff','--cached','--check'" in pub and "'Complete stage'" in pub and 'commit' not in pub.splitlines()[-1])
oldmaps={str(p.relative_to(R)):sha(p) for p in D.parent.rglob('continuation-mappings.json') if p.parent!=D}
ck('old_mapping_records_frozen',all(str(path(k)) in L['inventory'] or str(path(k)) in PREP['sha256'] for k in oldmaps if '/NATIVE-PIVOT-' in k))
# Fresh read-only host closure; inspect both PGID and SID and Julia comm/exe.
groups=set(hosts[-1]['groups']);matches=[];unreadable=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
ck('fresh214_groups_sessions_noJulia',len(groups)==214 and not matches and boot==S['boot_id'])
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
ck('refs',git('rev-parse','HEAD')==S['head']=='3feb815bf8a1507d5feecafaf038315b645a4243' and git('rev-parse','master')==S['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194')
ck('tracked_index_clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
report=dict(all_passed=all(checks.values()),checks=checks,unique_files_hashed=len(cache),bytes_hashed=bytes_read,elapsed_seconds=time.monotonic()-start,summary=dict(original_assertions=6858,regression_assertions=119,selected_entries=792,equations=324,empty=empty,nonempty=len(results),nonzero=260,max_residual_bound_ratio=max(x['ratio'] for x in results),inclusive_seconds=I['elapsed_seconds'],resource_samples=len(resources)),exact_residuals=results,proposed_continuation_mappings=maps,old_mapping_sha256=oldmaps,host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,scope='Both group and session checked; unreadable system exe symlinks remain a visibility limit'),sha256={str(Path(__file__)):sha(__file__)},scope='Independent stored-data and source result review; no Julia, old scripts, finalizer or publication execution')
with (D/'result-review-checks.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=report['all_passed'],checks=len(checks),files=len(cache),mapping_count=len(maps),summary=report['summary'])))
