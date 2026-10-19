"""New independent saved GREEN result review; no old script imports or Julia calls."""
from pathlib import Path
import json,tomllib,hashlib,math,os,subprocess,time,re
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-TYPED-HARNESS');R=D.parents[3];RUN=D/'runs/p011-green300';RED=D/'runs/p011-red300';O=D/'outers/p011-green300'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');PHASE='p011-green300';HEAD='a01d1cde19feb72ee0b6396981281cabf5bd9672';MASTER='26e2291745999f485a74f643298ca997d65c7205'
checks=[]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(v,n):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def bind(j,key='sha256'):
 for n,h in j[key].items():ck(sha(Path(n) if Path(n).is_absolute() else R/n)==h,'binding '+n)
def inv(files,trees):
 paths={Path(n) for n in files}
 for n in trees:
  root=Path(n);ck(root.is_dir() and not root.is_symlink(),'tree root '+n);entries=list(root.rglob('*'));ck(not any(p.is_symlink() for p in entries),'tree symlink absence '+n);paths.update(p for p in entries if p.is_file())
 return {str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)}
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def integer(v):return type(v) is int and 0<=v<=2**63-1
def finite(v,limit):return type(v) in (int,float) and math.isfinite(v) and 0<=v<=limit
def safehost(h,s):
 ck(h['matches']==[] and h['unreadable_identity_pids']==[],'host no matches/readable identities')
 ck(all(h[k]==s[k] for k in ['head','master','boot_id']),'host refs/boot')
 ck(set(h['remote'].splitlines())=={s['head']+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'host remote refs')
def main():
 names={'posthost.json','audit.json','sealed.json','config.json','host.json','launch-pins.json','launcher.log','admission.json','outer-closure.json','invocation.json','reservation.json','prehost.json'}
 payloadnames={'load.toml','panel-load.toml','tests-load.toml','probe-setup.toml','probe-cost.toml','tests-cost.toml','probe.toml','raw.toml','unit-1.toml'};outnames={'current.json','process.json','pins.json','run.log','resources.jsonl'}
 files={str(p.relative_to(RUN)) for p in RUN.rglob('*') if p.is_file()}
 ck(files==names|{'output/'+n for n in outnames}|{'payload/'+n for n in payloadnames} and len(files)==26,'exact26 run files before receipt')
 ck(not any(p.is_symlink() for p in RUN.rglob('*')),'run no symlinks')
 ck({p.name for p in O.iterdir()}=={'outer-ready.json','release.json','outer-invocation.json','outer-outcome.json'},'exact four outer files')
 s=rd(RUN/'sealed.json');ad=rd(RUN/'admission.json');lp=rd(RUN/'launch-pins.json');cfg=rd(RUN/'config.json');a=rd(RUN/'audit.json');pc=rd(E/'postcheck.json')
 ck(sha(RUN/'sealed.json')=='7f582dcb27e49e942b07550462ce3ee7c55ea9130fe21872b366df153bd50356' and sha(RUN/'admission.json')=='38f9e3f59b7fefadf2710ddc80bfddadcf8ab0a70309884dd68356a94a185776','original seal/admission immutable')
 ck(ad['accepted'] is True and ad['findings']==[] and ad['scope']=='P011 typed exact-run admission' and ad['phase']==PHASE and ad['pins_sha256']==sha(RUN/'sealed.json'),'exact admission acceptance')
 ck(set(ad['sha256'])==set(s['files'])|{str(RUN/'sealed.json')},'exact admission membership');bind(ad);bind(ad,'evidence_sha256')
 prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');rt=rd(D/'runtime-inputs-complete.json')['inventory'];bs=rd(D/'baseline.json');stage=rd(D/'stages.json')['red'];st=Path(stage['path'])
 ck(pr['accepted'] is True and pr['findings']==[] and pr['launch_admitted'] is False and pr['pins_sha256']==sha(D/'preparation-pins.json'),'preparation acceptance unchanged')
 ck(set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']) and set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')},'preparation exact membership');bind(prep);bind(pr);bind(pr,'evidence_sha256')
 ck(len(rt)==609 and inv(rt,[])==rt,'609 runtime paths and resolved hashes')
 for label,root in [('diagnostic',R),('production',W)]:
  ck(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(bs[label]),label+' baseline membership')
  for n,h in bs[label].items():ck(sha(root/n)==h,label+' baseline '+n)
 ck(len(stage['sha256'])==75 and {str(p.relative_to(st)) for p in st.rglob('*') if p.is_file()}==set(stage['sha256']),'exact75 stage')
 for n,h in stage['sha256'].items():ck(sha(st/n)==h,'stage '+n)
 rr=rd(RED/'result-review.json');redfiles={str(p) for p in RED.rglob('*') if p.is_file() and p.name!='result-review.json'}
 ck(rr['accepted'] is True and rr['findings']==[] and rr['phase']=='p011-red300' and rr['scope']=='P011 typed RED result' and set(rr['sha256'])==redfiles,'accepted RED unchanged exact membership');bind(rr);bind(rr,'evidence_sha256')
 rc=rd(RED/'outer-closure.json');bind(rc);ra=rd(RED/'audit.json');bind(ra);ck(ra['all_passed'] is True and ra['result']['totals']==[11759,1,0,0] and rc['all_passed'] is True,'accepted RED gate')
 redouter=D/'outers/p011-red300';predecessors=redfiles|{str(RED/'result-review.json')}|{str(redouter/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}
 prepared=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256'])
 expected=prepared|set(rt)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in bs[label]}|{str(st/n) for n in stage['sha256']}|predecessors|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
 ck(len(predecessors)==31 and s['files']==sorted(expected) and len(s['files'])==1932,'exact1932 seal membership')
 typed=D.with_name('DIRECT-BG-P011-TYPED-REPAIR');ck(s['trees']==[str(st),str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')),str(typed)] and s['inputs']==[],'exact sealed trees/input scope')
 ck(inv(s['files'],s['trees'])==s['inventory'],'fresh complete1932 sealed inventory')
 extra={str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(O/n) for n in ['release.json','outer-invocation.json']}
 ck(set(lp['files'])==set(s['files'])|extra and lp['trees']==s['trees'] and lp['inputs']==[] and len(lp['files'])==1937,'exact1937 launch membership')
 ck(inv(lp['files'],lp['trees'])==lp['inventory'] and rd(RUN/'output/pins.json')==lp,'fresh1937 launch inventory and guard pins')
 wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh';command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(st),str(D/'driver.jl'),str(RUN/'payload'),str(st),PHASE]
 ck(cfg==s['config']==dict(phase=PHASE,mode='red',seconds=300,expected_exit=0,stage=str(st),run=str(RUN),output=str(RUN/'output'),payload=str(RUN/'payload'),command=command),'exact GREEN configuration')
 ready=rd(O/'outer-ready.json');oi=ready['identity'];release=rd(O/'release.json');oinv=rd(O/'outer-invocation.json');outcome=rd(O/'outer-outcome.json')
 ck(ready['waiting_only'] is True and ready['phase']==PHASE and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py') and oi==s['outer_identity'],'outer ready identity')
 ck(release.get('one_attempt') is True and release==dict(phase=PHASE,sealed_sha256=sha(RUN/'sealed.json'),admission_sha256=sha(RUN/'admission.json'),outer_ready_sha256=sha(O/'outer-ready.json'),one_attempt=True),'exact oneattempt release')
 ck(oinv==dict(identity=oi,phase=PHASE,seal_sha256=sha(RUN/'sealed.json'),review_sha256=sha(RUN/'admission.json'),release_sha256=sha(O/'release.json'),launcher_sha256=sha(D/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'exact outer invocation')
 ck(outcome['identity']==oi and outcome['launched'] is True and type(outcome['returncode']) is int and outcome['returncode']==0 and outcome['error']=='' and finite(outcome['elapsed_with_checks_seconds'],1200),'outer success')
 p=rd(RUN/'output/process.json');cur=rd(RUN/'output/current.json');i=rd(RUN/'invocation.json');sup=i['supervisor'];res=rd(RUN/'reservation.json')
 ck(p['command']==cur['command']==i['command']==command and p['cwd']==cur['cwd']==str(R),'command/cwd linkage')
 ck(p['pins_sha256']==cur['pins_sha256']==i['pins_sha256']==sha(RUN/'launch-pins.json') and p['pins_unchanged'] is True,'pin linkage')
 ck(res.get('one_attempt') is True and res==dict(one_attempt=True,phase=PHASE,command=command,pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=300),'exact reservation')
 ck(i['review_sha256']==sha(RUN/'admission.json') and i['reservation_sha256']==sha(RUN/'reservation.json'),'invocation bindings')
 gc=[i['python'],'-B',str(D/'guard.py'),'run',str(RUN/'launch-pins.json'),str(RUN/'output'),'--seconds','292','--deadline',str(i['monotonic_start']+292),'--expected-exit','0','--',*command]
 ck(i['guard_command']==gc and Path(i['python']).resolve()==Path('/usr/bin/python3').resolve(),'exact guard command/deadline')
 ck(cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'saved process identities agree')
 for q in [oi,p['runner'],p['child']]:ck(q['pid']==q['pgid']==q['sid'] and integer(q['start_ticks']) and q['start_ticks']>0 and q['boot_id']==s['boot_id'] and q['command'],'process session/start/boot')
 ck(p['runner']['command']==' '.join(gc)+' ' and p['child']['command']==' '.join(command)+' ','guard/child actual command strings')
 ck(oi['start_ticks']<p['runner']['start_ticks']<p['child']['start_ticks'],'process creation ordering')
 ck(type(p['returncode']) is int and p['returncode']==0 and p['reason']=='exit0' and type(sup['returncode']) is int and sup['returncode']==0 and sup['accepted'] is True,'successful exit0')
 ck(all(sup.get(k) is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and not ({'error','remaining_group','remaining_session'}&set(p)),'no timeout/cleanup/residual flags')
 ck(finite(p['elapsed_including_launch'],292) and finite(sup['elapsed_seconds'],300) and finite(i['elapsed_seconds'],300),'292/300 inclusive limits')
 ck(p['started']==cur['started'] and p['ended']>=p['started'],'saved child wall chronology')
 resources=[json.loads(t) for t in (RUN/'output/resources.jsonl').read_text().splitlines()];previous=-1
 ck(len(resources)==9,'nine resource samples')
 for x in resources:
  ck({'available_kib','swap_used_kib','elapsed'}<=set(x)<={'available_kib','swap_used_kib','elapsed','child_memory'},'sample schema')
  ck(finite(x['elapsed'],p['elapsed_including_launch']) and x['elapsed']>=previous,'sample monotone bounded time');previous=x['elapsed']
  ck('child_memory' not in x or type(x['child_memory']) is list and all(type(v) is str for v in x['child_memory']),'sample memory text')
 ck(set(p['terminal_memory'])=={'available_kib','swap_used_kib'},'terminal memory schema')
 for x in resources+[p['terminal_memory']]:ck(all(integer(x[k]) for k in ['available_kib','swap_used_kib']) and x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2,'sample/terminal resource threshold')
 ck(finite(p['child_maxrss_kib'],8*1024**2) and p['child_maxrss_kib']>0,'positive bounded maxrss')
 ck((RUN/'output/run.log').read_text()=='' and json.loads((RUN/'launcher.log').read_text())==p,'empty Julia log/exact launcher process record')
 ck(not re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Failed|Test Error|TEST FAILURE',(RUN/'launcher.log').read_text(),re.I),'no warning/unexpected failure')
 payload={n:tomllib.loads((RUN/'payload'/n).read_text()) for n in payloadnames};costs={n:payload[n] for n in payloadnames-{'probe.toml','raw.toml','unit-1.toml'}}
 for n,c in costs.items():
  ck(set(c)=={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'},n+' schema');ck(integer(c['bytes']) and integer(c['events']),n+' integral allocations');ck(all(finite(c[k],300) for k in c if k not in ['bytes','events']),n+' bounded finite times')
 probe=payload['probe.toml'];ck(set(probe)=={'bytes','events','consumed_bytes','consumed_events','warm','bytes_decision','events_decision','values_unchanged','owners_unchanged'},'probe schema')
 ck(all(type(probe[k]) is int and probe[k]==0 for k in ['bytes','events','consumed_bytes','consumed_events']) and probe['values_unchanged'] is True and probe['owners_unchanged'] is True,'four zero meters and value/owner flags')
 for name in ['warm','bytes_decision','events_decision']:
  v=probe[name];ck(v==dict(start=1,count=0,accepted=False,reason='dimensions',finite=True,counters=[0]*20) and set(v)=={'start','count','accepted','reason','finite','counters'},'complete '+name+' decision')
  ck(type(v['start']) is int and type(v['count']) is int and v['accepted'] is False and v['finite'] is True and type(v['counters']) is list and all(type(z) is int for z in v['counters']),name+' strict types')
 u=payload['unit-1.toml'];ck(set(u)=={'index','name','complete','fatal','tests','records'} and type(u['index']) is int and u['index']==1 and u['name']=='panel' and u['complete'] is True and u['fatal']=='','unit schema/completion')
 counts={f'P{x:03}':1 for x in range(1,103)}
 for x,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:counts[f'P{x:03}']=n
 for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
  for x in range(lo,hi+1):counts[f'P{x:03}']=n
 rec=u['records'];ck(set(rec)=={'sites','events','apis','failures','failure_count','active'} and rec['sites']==counts and all(type(v) is int for v in rec['sites'].values()),'all102 exact site multiplicities')
 ck(rec['events']=={} and rec['apis']=={} and rec['failures']==[] and type(rec['failure_count']) is int and rec['failure_count']==0 and rec['active']=='','no failures/extra records')
 tree=u['tests'];keys={'name','pass','fail','error','broken','children'};ck(set(tree)==keys and tree['name']=='panel' and all(type(tree[k]) is int and tree[k]==0 for k in ['pass','fail','error','broken']) and len(tree['children'])==4,'empty root/four groups')
 groupnames=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses']
 for t,name,n in zip(tree['children'],groupnames,[31,11619,74,44]):ck(set(t)==keys and t['name']==name and t['children']==[] and all(type(t[k]) is int for k in ['pass','fail','error','broken']) and [t[k] for k in ['pass','fail','error','broken']]==[n,0,0,0],'exact group '+name)
 raw=payload['raw.toml'];ck(set(raw)=={'schema','phase','complete','fatal','qualification','test_source','loaded','threads','blas_threads','probe','unit','totals'},'raw schema')
 loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(st/'src/JSimplex.jl'))
 ck(type(raw['schema']) is int and raw['schema']==1 and raw['phase']==PHASE and raw['complete'] is True and raw['fatal']=='' and raw['qualification']=='p011_typed_structural' and raw['test_source']==str(typed/'panel-tests.jl') and raw['loaded']==loaded,'raw completion/scope/loaded paths')
 ck(type(raw['threads']) is type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'one Julia/BLAS thread')
 ck(raw['probe']==probe and raw['unit']==u and raw['totals']==[11768,0,0,0] and all(type(v) is int for v in raw['totals']) and sum(counts.values())==11768,'duplicates and totals')
 text=(typed/'panel-tests.jl').read_text();ck('@check "P011" p011.bytes == 0' in text and set(re.findall(r'@check(?:throws)? "(P[0-9]+)"',text))==set(counts),'exact observed repaired source spelling/sites')
 ck(sha(typed/'panel-tests.jl')=='15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910' and sha(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')/'panel.jl')=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295','exact repaired source/shared candidate')
 auditfiles={str(RUN/n) for n in files-{'audit.json','outer-closure.json'}};ck(set(a['sha256'])==auditfiles and len(auditfiles)==24,'exact24 audit inputs');bind(a)
 ck(a['all_passed'] is True and a['pure_timeout'] is False and a['error']=='' and a['phase']==PHASE and a['result']['totals']==raw['totals'] and a['result']['probe']==probe and a['result']['preparation']==costs and a['result']['expected_failure_sites']==[],'saved admitted audit matches independent results')
 closure=rd(RUN/'outer-closure.json');cp={str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RUN/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']}
 ck(closure['all_passed'] is True and closure['outer_identity']==oi and set(closure['sha256'])==cp,'exact external closure');bind(closure)
 historical=set(rc['host']['groups']);new={q[k] for q in [oi,p['runner'],p['child']] for k in ['pgid','sid']};full=historical|new
 releasehost=rd(E/'release-host.json');fullhost=rd(E/'full-group-closure.json');post=rd(RUN/'posthost.json')
 ck(len(historical)==283 and len(full)==286 and set(releasehost['groups'])==historical and set(fullhost['groups'])==full,'exact full283 release/full286 closure')
 ck(set(s['groups'])==historical-{200591} and set(post['groups'])==set(s['groups'])|new-{oi['pid']} and set(closure['host']['groups'])==full-{200591},'frozen coverage and supplemental old RED outer coverage')
 for h in [rd(RUN/'host.json'),rd(RUN/'prehost.json'),post,releasehost,fullhost,closure['host']]:safehost(h,s)
 ck(releasehost['time']<=p['started']<=p['ended']<=closure['host']['time']<=fullhost['time'],'release/execution/closure chronology')
 ck(pc['all_passed'] is True and len(pc['checks'])==13 and all(v is True for v in pc['checks'].values()) and pc['probe']==probe and pc['totals']==raw['totals'] and pc['preparation']==costs,'saved13 supplemental checks/result')
 expectedpc={str(RUN/n) for n in files}|{str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(E/n) for n in ['full-group-closure.json','host-entry.json','entry-check.json','request.txt','outer.log','postcheck.py']}
 ck(set(pc['sha256'])==expectedpc,'exact36 postcheck bindings');bind(pc)
 env=rd(D/'environment.json');ck({k:os.environ.get(k) for k in env}==env,'fresh loading environment')
 refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),production=git('rev-parse','HEAD',cwd=W),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
 ck(refs['head']==s['head']==HEAD and refs['master']==refs['production']==s['master']==MASTER and set(refs['remote'].splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'fresh local/remote refs')
 ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no tracked drift')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ck(boot==s['boot_id'],'fresh boot')
 matches=[];unreadable=[];badidentity=[];scanned=0
 for q in Path('/proc').glob('[0-9]*'):
  try:
   stt=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();arg=(q/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe='';scanned+=1
   try:exe=str((q/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(q.name))
   except FileNotFoundError:pass
   if int(stt[2]) in full or int(stt[3]) in full or any(Path(x).name.lower().startswith('julia') for x in [comm,arg,exe]):matches.append(dict(pid=int(q.name),pgid=int(stt[2]),sid=int(stt[3]),comm=comm,argv0=arg,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:badidentity.append(int(q.name))
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
 fresh=dict(time=time.time(),groups=sorted(full),matches=matches,unreadable_exe_pids=unreadable,unreadable_identity_pids=badidentity,processes_scanned=scanned,refs=refs,boot_id=boot,memory=memory)
 ck(matches==[] and badidentity==[],'fresh full286 no process/session member or visible Julia')
 ck(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'fresh memory thresholds')
 return dict(totals=raw['totals'],groups=[31,11619,74,44],sites=len(counts),sealed_files=len(s['files']),launch_files=len(lp['files']),result_files=len(files),costs=costs,fresh_host=fresh,resource_summary=dict(samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib']),process_seconds=p['elapsed_including_launch'],supervisor_seconds=sup['elapsed_seconds'],invocation_seconds=i['elapsed_seconds'],outer_seconds=outcome['elapsed_with_checks_seconds'],identities=dict(outer=oi,guard=p['runner'],child=p['child']))
result={}
try:result=main();result['all_passed']=True
except Exception as e:result.update(all_passed=False,error=repr(e))
result.update(findings=[] if result['all_passed'] else [result.get('error','Check failed')],total=len(checks),passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks,script_sha256=sha(__file__),runtime_executed=False)
with (E/'result-review-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','costs','identities','fresh_host']},indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
