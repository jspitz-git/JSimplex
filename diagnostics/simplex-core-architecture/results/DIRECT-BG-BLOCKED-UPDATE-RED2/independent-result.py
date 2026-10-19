"""Independent saved-result review. No Julia, harness imports, auditor calls, or process launches."""
from pathlib import Path
import hashlib,json,tomllib,re,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS'
D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2'); run=H/'runs/red300'; out=run/'output'; outer=H/'outers/red300'
checks=[]; hashes={}; sizes={}
def ck(name,value):
    if not value:raise AssertionError(name)
    checks.append(name)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    p=Path(p);key=str(p)
    if key not in hashes:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        hashes[key]=h.hexdigest();sizes[key]=p.stat().st_size
    return hashes[key]
def bind(data,label,key='sha256'):
    for name,value in data[key].items():
        p=Path(name);p=p if p.is_absolute() else R/p
        ck(label+' '+str(p),sha(p)==value)
def inventory(data,label):
    names=set(data['files'])
    for tree in data['trees']:
        root=Path(tree);ck(label+' tree symlinks '+tree,not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
        names.update(str(p) for p in root.rglob('*') if p.is_file())
    ck(label+' exact inventory membership',names==set(data['inventory']))
    for name,item in data['inventory'].items():
        ck(label+' resolved '+name,str(Path(name).resolve(strict=True))==item['resolved'])
        ck(label+' hash '+name,sha(name)==item['sha256'])
s=read(run/'sealed.json');lp=read(run/'launch-pins.json');ad=read(run/'admission.json');a=read(run/'audit.json');summ=read(D/'summary.json');prep=read(H/'preparation-pins.json');pr=read(H/'review.json')
ck('frozen commit and master',s['head']=='b6c37d08e94fc3e6c6b28a967a8f995549929e94' and s['master']=='26e2291745999f485a74f643298ca997d65c7205')
for ref,key in [('HEAD','head'),('master','master')]:
    ck('current local '+ref,subprocess.check_output(['git','rev-parse',ref],cwd=R,text=True).strip()==s[key])
ck('sealed files exact 1996',len(s['files'])==len(set(s['files']))==len(s['inventory'])==1996)
inventory(s,'seal');inventory(lp,'launch')
ck('launch copy exact',sha(run/'launch-pins.json')==sha(out/'pins.json'))
ck('preparation accepted separately',pr['accepted'] is True and pr['findings']==[] and pr['scope']=='BG blocked U RED2 preparation' and pr['launch_admitted'] is False)
ck('preparation membership',set(prep['sha256'])==set(read(H/'required-paths.json')['paths']) and len(prep['sha256'])==347)
ck('preparation review membership',set(pr['sha256'])==set(prep['sha256'])|{str(H/'preparation-pins.json')} and len(pr['sha256'])==348)
for label,item in [('preparation',prep),('preparation review',pr),('preparation publication',read(H/'publication.json')),('admission',ad),('audit',a),('summary',summ)]:bind(item,label)
bind(pr,'preparation reviewer evidence','evidence_sha256');bind(ad,'admission reviewer evidence','evidence_sha256')
ck('exact admission receipt',ad['accepted'] is True and ad['findings']==[] and ad['scope']=='BG blocked U RED2 exact-stage admission' and ad['phase']=='red300' and ad['pins_sha256']==sha(run/'sealed.json'))
ck('exact admission 1997 bindings',len(ad['sha256'])==1997 and set(ad['sha256'])==set(s['inventory'])|{str(run/'sealed.json')})
ae=read(D/'independent-admission-evidence.json')
ck('original admission 6938 checks',ae['accepted'] is True and ae['findings']==[] and len(ae['checks'])==ae['check_count']==6938 and all(x['passed'] is True for x in ae['checks']) and ae['sealed_files']==1996 and ae['admission_bindings']==1997)
st=read(H/'stages.json')['red'];ck('75 repaired stage members',len(st['sha256'])==75 and set(st['sha256'])=={str(p.relative_to(st['path'])) for p in Path(st['path']).rglob('*') if p.is_file()})
for n,h in st['sha256'].items():ck('repaired stage '+n,sha(Path(st['path'])/n)==h)
for name,item in read(H/'copied-files.json').items():ck('unchanged copied diagnostic '+name,sha(H/name)==sha(item['source'])==item['sha256'])
p=read(out/'process.json');inv=read(run/'invocation.json');cl=read(run/'outer-closure.json');post=read(run/'posthost.json');cfg=read(run/'config.json');res=read(run/'reservation.json');ready=read(outer/'outer-ready.json');release=read(outer/'release.json');oi=read(outer/'outer-invocation.json');oo=read(outer/'outer-outcome.json')
bind(cl,'external closure')
ck('closure exact bindings',set(cl['sha256'])=={str(outer/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(run/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']})
ck('one run and outer',sorted(x.name for x in (H/'runs').iterdir())==['red300'] and sorted(x.name for x in (H/'outers').iterdir())==['red300'])
ck('single reservation fixed configuration',res==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300))
ck('single exact release',release==dict(phase='red300',sealed_sha256=sha(run/'sealed.json'),admission_sha256=sha(run/'admission.json'),outer_ready_sha256=sha(outer/'outer-ready.json'),one_attempt=True))
ck('outer binding',oi==dict(identity=ready['identity'],phase='red300',seal_sha256=sha(run/'sealed.json'),review_sha256=sha(run/'admission.json'),release_sha256=sha(outer/'release.json'),launcher_sha256=sha(H/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'))
ck('fixed cfg',cfg==s['config'] and cfg['seconds']==300 and cfg['expected_exit']==1 and cfg['stage']==st['path'] and cfg['phase']=='red300')
ck('command bindings',p['command']==inv['command']==cfg['command'] and inv['pins_sha256']==p['pins_sha256']==sha(run/'launch-pins.json') and inv['review_sha256']==sha(run/'admission.json') and inv['reservation_sha256']==sha(run/'reservation.json'))
ck('expected thread flags',all(x in cfg['command'] for x in ['--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--compiled-modules=existing']))
u=tomllib.loads((out/'unit-1.toml').read_text());raw=tomllib.loads((out/'raw.toml').read_text())
ck('only saved unit1',sorted(x.name for x in out.glob('unit-*.toml'))==['unit-1.toml'])
ck('unit complete',set(u)=={'complete','fatal','index','name','observations','records','tests'} and u['complete'] is True and u['fatal']=='' and u['index']==1 and u['name']=='panel')
expected={f'P{i:03d}':1 for i in range(1,95)}
for i,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:expected[f'P{i:03d}']=n
for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
    for i in range(lo,hi+1):expected[f'P{i:03d}']=n
rr=u['records'];ck('all94 panel sites exact occurrence rules',rr['sites']==expected and sum(expected.values())==11760)
ck('panel no lifecycle/stream APIs',rr['events']==rr['apis']=={} and rr['active']=='' and u['observations']==[])
expected_children=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses']
ck('four named flat testsets',[t['name'] for t in u['tests']['children']]==expected_children and all(t['children']==[] for t in u['tests']['children']))
def counts(t):
    ck('test tree schema '+t['name'],set(t)=={'name','pass','fail','error','broken','children'} and all(type(t[k]) is int and t[k]>=0 for k in ['pass','fail','error','broken']))
    total=[t[k] for k in ['pass','fail','error','broken']]
    for child in t['children']:total=[x+y for x,y in zip(total,counts(child))]
    return total
ct=counts(u['tests']);ck('11759 pass 1 fail',ct==[11759,1,0,0])
f=rr['failures'];ck('only P011 comparison failure',rr['failure_count']==len(f)==1 and f[0]['site']=='P011' and f[0]['kind']=='fail' and '@allocated(K._bgb_eligibility(f, 1)) == 0' in f[0]['detail'])
ck('raw incomplete before aggregate',raw['complete'] is False and raw['units_completed']==0 and raw['totals']==[0,0,0,0] and 'Unexpected unit failure; saved prefix retained' in raw['fatal'])
loaded=read(H/'loaded-paths.json');loaded['JSimplex']=str(Path(st['path'])/'src/JSimplex.jl')
ck('actual repaired load path and one thread',raw['loaded']==loaded and raw['threads']==raw['blas_threads']==1)
log=(out/'run.log').read_text();launchlog=(run/'launcher.log').read_text()
ck('single panel begin/end',log.count('UNIT BEGIN 1 panel')==log.count('UNIT END 1 panel')==log.count('TEST FAILURE:')==1 and 'UNIT BEGIN 2' not in log and 'N026' not in log)
ck('no loader/warning diagnostics',re.search(r'warning|world.?age|method.*overwrite|UndefVarError',log+launchlog,re.I) is None)
ck('failed original audit',a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Exact exit')" and a['result']=={})
ck('child2 guard1 outer2',p['returncode']==2 and p['reason']=='exit2' and inv['supervisor']['returncode']==1 and oo['returncode']==2 and oo['launched'] is True and inv['supervisor']['accepted'] is False)
ck('no timeout kill',all(inv['supervisor'][x] is False for x in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and p['pins_unchanged'] is True)
ck('elapsed including launch',inv['elapsed_seconds']==14.206057686998975 and p['elapsed_including_launch']==13.563551717990777 and 0<p['elapsed_including_launch']<=inv['elapsed_seconds']<300)
resource=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck('13 samples exact memory summaries',len(resource)==13 and min(x['available_kib'] for x in resource)==21831500 and max(x['swap_used_kib'] for x in resource)==0 and p['child_maxrss_kib']==955848)
ck('all resource thresholds',all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resource+[p['terminal_memory']]))
ck('identity linkage',cl['outer_identity']==s['outer_identity']==ready['identity']==oi['identity']==oo['identity'] and inv['supervisor']['guard_identity']==p['runner'])
required=set(s['groups'])|{p[k][g] for k in ['runner','child'] for g in ['pgid','sid']}|{cl['outer_identity'][g] for g in ['pgid','sid']}
ck('274 groups/sessions exact',len(s['groups'])==271 and len(required)==274 and set(cl['host']['groups'])==required and set(post['groups'])<=required)
for role,i in [('outer',cl['outer_identity']),('runner',p['runner']),('child',p['child'])]:ck(role+' identity complete',i['pid']==i['pgid']==i['sid'] and i['start_ticks']>0 and i['boot_id']==s['boot_id'] and bool(i['command']))
for label,host in [('posthost',post),('external closure',cl['host'])]:
    ck(label+' recorded absence refs boot',host['matches']==[] and host['unreadable_identity_pids']==[] and all(host[k]==s[k] for k in ['head','master','boot_id']) and s['head']+'\trefs/heads/codex/simplex-core-architecture' in host['remote'] and s['master']+'\trefs/heads/master' in host['remote'])
ck('external closure accepted saved evidence',cl['all_passed'] is True and cl['host']['time']>post['time']>p['ended'])
ck('no qualifying receipt',not (run/'result-review.json').exists() and summ['qualification_pass'] is False and summ['expected_N026_reached'] is False and summ['allocated_bytes'] is None and summ['allocated_events'] is None and all(v is True for v in summ['checks'].values()))
ck('summary exact observed values',summ['counts']==ct and summ['raw_totals']==raw['totals'] and summ['groups']==cl['host']['groups'] and summ['inclusive_supervisor_seconds']==inv['elapsed_seconds'] and summ['process_seconds']==p['elapsed_including_launch'])
policy=read(D/'publication-policy.json');ck('exact raw whitespace exception',policy['raw']==str((D/'outer-console.log').relative_to(R)) and policy['sha256']==sha(D/'outer-console.log') and policy['allowed_warning']==policy['raw']+':19: new blank line at EOF.\n' and (D/'outer-console.log').read_bytes().endswith(b'\n\n'))
ck('no authored whitespace exception','no authored whitespace exception' in policy['reason'])
reviewed=set(hashes)|{str(p) for root in [run,outer] for p in root.rglob('*') if p.is_file()}|{str(D/n) for n in ['REPORT.md','summary.json','summary.py','report.py','admission-review.md','publication-policy.json','outer-console.log']}|{str(H/n) for n in ['ADMISSION.md','review.md','MEMORY-WORK.md','driver.jl','recorder.jl','panel-tests.jl','oracle.py','control.py','guard.py','supervisor.py','post-return.py','audit.py']}
for pth in reviewed:sha(pth)
evidence=dict(accepted=True,findings=[],qualification_accepted=False,scope='Independent saved failed RED2 diagnostic integrity review only',check_count=len(checks),checks=checks,sha256={p:hashes[p] for p in sorted(reviewed)},unique_files_hashed=len(hashes),logical_bytes_hashed=sum(sizes.values()),counts=ct,resource_samples=len(resource),closure_groups=len(required),no_julia_or_auditor_rerun=True,allocated_bytes=None,allocated_events=None)
with (D/'independent-result-evidence.json').open('x') as f:json.dump(evidence,f,indent=2);f.write('\n')
print(json.dumps({k:evidence[k] for k in ['accepted','qualification_accepted','check_count','unique_files_hashed','counts','closure_groups']}))
