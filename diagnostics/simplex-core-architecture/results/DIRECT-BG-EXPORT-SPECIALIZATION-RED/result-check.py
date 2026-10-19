"""Independent failed-attempt evidence checker. Standard library only.
No Julia invocation, no imports/execution of frozen checkers or auditors.
Source saved before execution. Writes its own new report exclusively.
"""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import hashlib,json,math,re,statistics,struct,subprocess,time,tomllib,traceback
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER'
Q=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED'); RUN=D/'runs/red300'; O=RUN/'output'
MASTER='26e2291745999f485a74f643298ca997d65c7205'; HEAD='e780e6158ea5365adf5cde36dceaa8032a34fe9c'
checks={}; evidence={}
def need(value,name):
    checks[name]=bool(value)
    if not value:raise AssertionError(name)
def read(path):return json.loads(Path(path).read_text())
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def hashes(mapping):
    return all(digest(Path(p) if Path(p).is_absolute() else R/p)==h for p,h in mapping.items())
def inventory(pin):
    names=set(pin['files'])
    for tree in pin['trees']:
        root=Path(tree)
        if not root.is_dir() or root.is_symlink():return False
        for p in root.rglob('*'):
            if p.is_symlink() and (p.is_dir() or not p.exists()):return False
            if p.is_file():names.add(str(p))
    return names==set(pin['inventory']) and all(str(Path(p).resolve(strict=True))==v['resolved'] and digest(p)==v['sha256'] for p,v in pin['inventory'].items())
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def safe(h):return h['matches']==[] and h['unreadable_identity_pids']==[]
def number(token):
    if not isinstance(token,str) or re.fullmatch('[0-9a-f]{16}',token) is None:raise ValueError('invalid binary token')
    value=struct.unpack('>d',bytes.fromhex(token))[0]
    if not math.isfinite(value):raise ValueError('nonfinite binary token')
    return Fraction.from_float(value)
def matrices(f):
    result=[]
    for m in f['matrices']:
        n=f['n'];cp=m['colptr'];rv=m['rowval'];vv=m['nzval']
        if m['n']!=n or len(cp)!=n+1 or cp[0]!=1 or cp[-1]!=len(vv)+1 or len(rv)!=len(vv) or cp!=sorted(cp):raise ValueError('CSC shape')
        rows=[[] for _ in range(n)];columns=[[] for _ in range(n)]
        for j in range(n):
            inds=rv[cp[j]-1:cp[j+1]-1]
            if inds!=sorted(set(inds)) or not all(1<=i<=n for i in inds):raise ValueError('CSC structure')
            for k in range(cp[j]-1,cp[j+1]-1):
                i=rv[k]-1;v=number(vv[k]);rows[i].append((j,v));columns[j].append((i,v))
        result.append((rows,columns))
    return result
# Exact Fraction arithmetic, independently implemented. Cache only immutable
# identical (fixture,matrix,orientation,output,rhs) queries; all 1200 bindings
# are visited even where identical token outputs recur across windows.
@lru_cache(maxsize=None)
def residual(cell,mi,transpose,tokens,rhs):
    rows=decoded[cell][mi][int(transpose)];n=len(rows)
    if len(tokens)!=n or len(rhs)!=n:return False
    x=tuple(map(number,tokens));b=tuple(map(number,rhs))
    matrix_norm=max(sum(abs(v) for _,v in row) for row in rows)
    xnorm=max(map(abs,x));bnorm=max(map(abs,b))
    error=max(abs(sum(v*x[j] for j,v in row)-b[i]) for i,row in enumerate(rows))
    bound=Fraction(128*n,2**52)*max(Fraction(1),matrix_norm*xnorm,bnorm)
    return error<=bound

def main():
    s=read(RUN/'sealed.json');a=read(RUN/'admission.json');p=read(RUN/'launch-pins.json');audit=read(RUN/'audit.json')
    need(s['phase']=='red300' and s['head']==HEAD and s['master']==MASTER,'sealed_identity')
    need(len(s['files'])==len(s['inventory'])==2111 and inventory(s),'sealed_exact_2111_inventory')
    need(a['accepted'] is True and a['findings']==[] and a['scope']=='BG specialization exact-stage admission' and a['phase']=='red300','exact_admission_scope')
    need(set(a['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and len(a['sha256'])==2112 and hashes(a['sha256']) and a['pins_sha256']==digest(RUN/'sealed.json'),'admission_exact_2112_bindings')
    need(hashes(a['evidence_sha256']),'admission_evidence_bindings')
    a2=read(Q/'admission-check2.json');a1=read(Q/'admission-check.json')
    need(a2['all_passed'] is True and len(a2['checks'])==50 and all(a2['checks'].values()) and a1['all_passed'] is False and a1['evidence']['error']=="AssertionError('environment')",'saved_admission_pass_and_preserved_initial_reviewer_error')
    prep=read(D/'preparation-pins.json');pr=read(D/'review.json')
    need(set(prep['sha256'])==set(read(D/'required-paths.json')['paths']) and hashes(prep['sha256']),'preparation_membership_and_hashes')
    need(pr['accepted'] is True and pr['findings']==[] and pr['red_expectation_supported'] is True and pr['pins_sha256']==digest(D/'preparation-pins.json') and set(pr['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and hashes(pr['sha256']),'preparation_review_bindings')
    need(set(p['files'])==set(s['files'])|{str(RUN/n) for n in ('sealed.json','admission.json','prehost.json')} and p['trees']==s['trees'] and inventory(p) and read(O/'pins.json')==p and len(p['inventory'])==2114,'launch_inventory_and_saved_pin_identity')
    need(all(p['inventory'][k]==v for k,v in s['inventory'].items()),'seal_to_launch_immutable')
    stages=read(D/'stages.json')
    for mode,stage in stages.items():
        root=Path(stage['path']);actual={str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()}
        need(not root.is_symlink() and not any(x.is_symlink() for x in root.rglob('*')) and actual==set(stage['sha256']) and all(digest(root/n)==h for n,h in stage['sha256'].items()),'stage_'+mode+'_exact')
    production=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
    for label,root in [('diagnostic',R),('production',production)]:
        baseline=read(D/'baseline.json')[label]
        need(set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(baseline) and all(digest(root/n)==h for n,h in baseline.items()),label+'_baseline_unchanged')
    need(git('rev-parse','HEAD')==HEAD and git('rev-parse','master')==MASTER and git('rev-parse','HEAD',cwd=production)==MASTER,'current_git_pins')
    need(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked_workspace_unchanged')
    cfg=read(RUN/'config.json');inv=read(RUN/'invocation.json');reservation=read(RUN/'reservation.json');proc=read(O/'process.json');current=read(O/'current.json');sup=inv['supervisor']
    need(cfg==s['config'] and cfg['phase']=='red300' and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1 and cfg['stage']==stages['red']['path'],'exact_config_and_limit')
    need(proc['command']==current['command']==inv['command']==cfg['command'] and proc['cwd']==str(R),'command_and_cwd')
    need(all(x in cfg['command'] for x in ('--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--compiled-modules=existing','--history-file=no')),'fixed_runtime_options')
    need(proc['pins_sha256']==current['pins_sha256']==inv['pins_sha256']==digest(RUN/'launch-pins.json') and proc['pins_unchanged'] is True,'runtime_pin_links')
    need(reservation==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=digest(RUN/'launch-pins.json'),review_sha256=digest(RUN/'admission.json'),max_seconds=300) and inv['reservation_sha256']==digest(RUN/'reservation.json') and inv['review_sha256']==digest(RUN/'admission.json'),'one_attempt_reservation')
    need(inv['guard_command']==[inv['python'],'-B',str(D/'guard.py'),'run',str(RUN/'launch-pins.json'),str(O),'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','1','--',*cfg['command']],'inner_absolute_deadline')
    need(proc['runner']==current['runner']==sup['guard_identity'] and proc['child']==current['child'],'process_identity_linkage')
    need(all(proc[role]['pid']==proc[role]['pgid']==proc[role]['sid'] and proc[role]['start_ticks']>0 and proc[role]['command'] and proc[role]['boot_id']==s['boot_id'] for role in ('runner','child')),'owned_sessions_boot_start')
    need(proc['returncode']==2 and proc['reason']=='exit2' and 'error' not in proc and sup['returncode']==1 and sup['accepted'] is False,'failed_exit_preserved')
    need(all(sup[k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in sup and all(0<=x<=300 for x in (inv['elapsed_seconds'],sup['elapsed_seconds'],proc['elapsed_including_launch'])),'not_timeout_and_duration_within_limit')
    need(not any(k in proc for k in ('remaining_group','remaining_session')),'no_saved_cleanup_remainder')
    hosts=[read(RUN/n) for n in ('host.json','prehost.json','posthost.json')];close=read(Q/'outer-closure.json');outer=read(Q/'outer-outcome.json');ready=read(Q/'outer-ready.json');release=read(Q/'release.json')
    need(all(safe(h) and h['head']==HEAD and h['master']==MASTER and h['boot_id']==s['boot_id'] for h in hosts),'saved_prepost_host_safe')
    need(set(s['groups'])<=set(hosts[1]['groups'])<=set(hosts[2]['groups']),'inner_historical_group_coverage')
    groups=set(read(D/'host-closure.json')['groups'])|set(hosts[2]['groups'])|{outer['identity'][k] for k in ('pgid','sid')}|{proc[r][k] for r in ('runner','child') for k in ('pgid','sid')}
    need(close['all_passed'] is True and safe(close['host']) and set(close['host']['groups'])==groups and len(groups)==259 and {116092,116909,116910}<=groups and hashes(close['sha256']),'separate_outer_full_259_group_session_closure')
    need(close['outer_identity']==outer['identity']==ready['identity']==s['outer_identity'] and outer['launched'] is True and outer['returncode']==2,'outer_identity_and_failed_outcome')
    need(close['host']['head']==HEAD and close['host']['master']==MASTER and close['host']['boot_id']==s['boot_id'] and HEAD+'\trefs/heads/codex/simplex-core-architecture' in close['host']['remote'] and MASTER+'\trefs/heads/master' in close['host']['remote'],'saved_closure_ref_identity')
    need(release==dict(phase='red300',sealed_sha256=digest(RUN/'sealed.json'),admission_sha256=digest(RUN/'admission.json'),outer_ready_sha256=digest(Q/'outer-ready.json'),one_attempt=True),'release_binding')
    samples=[json.loads(line) for line in (O/'resources.jsonl').read_text().splitlines()]
    need(len(samples)==10 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in samples+[proc['terminal_memory']]),'all_saved_resource_samples_within_limits')
    need(all(0<=x['elapsed']<=proc['elapsed_including_launch'] for x in samples) and [x['elapsed'] for x in samples]==sorted(x['elapsed'] for x in samples) and proc['child_maxrss_kib']>0,'resource_order_and_rss')
    guard=(D/'guard.py').read_text();supervisor=(D/'supervisor.py').read_text();control=(D/'control.py').read_text()
    need('resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in guard and 'preexec_fn=limits' in guard and 'JULIA_PKG_OFFLINE=\'true\'' in guard and 'JULIA_PKG_PRECOMPILE_AUTO=\'0\'' in guard,'resource_and_loading_guard_source')
    need("v.get('accepted') is True" in control and "'BG specialization RED result'" in control and "a.get('all_passed') is True" in control and "a.get('pure_timeout') is True" in control,'failed_review_cannot_admit_green_or_timeout_extension')
    need(audit['all_passed'] is False and audit['pure_timeout'] is False and audit['error']=="ValueError('Measured compilation')" and audit['result']=={} and audit['phase']=='red300','original_failed_audit_preserved')
    oldfiles={str(x) for x in RUN.rglob('*') if x.is_file() and x.name not in ('audit.json','result-review.json')}
    need(set(audit['sha256'])==oldfiles and len(oldfiles)==66 and hashes(audit['sha256']),'original_audit_exact_all_66_preexisting_run_bindings')
    expected_names={f'window-{cell}-{w}.toml' for cell,total in ((1,20),(2,20),(3,10)) for w in range(1,total+1)}
    need({x.name for x in O.iterdir()}==expected_names|{'current.json','pins.json','process.json','raw.toml','resources.jsonl','run.log'} and all(x.is_file() and not x.is_symlink() for x in O.iterdir()),'exact_output_prefix_no_extra_or_missing_files')
    raw=tomllib.loads((O/'raw.toml').read_text());loaded=dict(read(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'))
    need(set(raw)==set('phase complete fatal loaded threads blas_threads tests'.split()) and raw['phase']=='red300' and raw['complete'] is False and raw['fatal'].startswith('Measured compilation\nStacktrace:') and 'driver.jl:47' in raw['fatal'],'raw_fatal_at_gate')
    need(raw['loaded']==loaded and raw['threads']==raw['blas_threads']==1 and all(str(Path(p).resolve())==p for p in loaded.values()),'loaded_sources_threads')
    root=raw['tests'];children=root['children']
    need(set(root)==set('name pass fail error broken failures children'.split()) and root['name']=='root' and all(root[k]==0 for k in ('pass','fail','error','broken')) and root['failures']==[],'partial_test_root')
    need(len(children)==2 and [[x[k] for k in ('name','pass','fail','error','broken')] for x in children]==read(D/'expected-tests.json')['red']['groups'][:2] and all(x['children']==[] and len(x['failures'])==1 and 'driver.jl:57' in x['failures'][0] for x in children),'exact_two_failed_leaf_assertions')
    log=(O/'run.log').read_text()+'\n'+(RUN/'launcher.log').read_text()
    need(log.count('TEST FAILURE:')==2 and log.count('FATAL DRIVER:')==1 and 'GROUP/COUNT MISMATCH OR FATAL' in log and re.search(r'(?i)\bwarning\b|world[ -]age',log) is None,'failure_log_no_warning_world_age')
    fixtures=read(D/'inputs.json')['fixtures'][:3]
    need([f['name'] for f in fixtures]==['sparse32','dense32','sparse96'] and all(len(f['matrices'])==9 and len(f['steps'])==8 for f in fixtures),'fixture_source_and_shape')
    global decoded
    decoded=[matrices(f) for f in fixtures];allrows=[];anomalies=[];counts=[];stats={};residual_count=0
    fields=set('pair order side measured policy correct inputs_unchanged modes seconds bytes events gc_seconds compile_seconds recompile_seconds retained_bytes nested_seconds outputs'.split())
    for cell,(f,total) in enumerate(zip(fixtures,(20,20,10)),1):
        rows=[]
        for w in range(1,total+1):
            path=O/f'window-{cell}-{w}.toml';row=tomllib.loads(path.read_text());pair=(w+1)//2;order=(w-1)%2+1
            side=('reference','candidate')[(order-1) if pair%2 else 2-order]
            need(set(row)==fields and type(row['pair']) is int and type(row['order']) is int and row['pair']==pair and row['order']==order and row['side']==side and row['measured'] is (pair>3) and row['policy']=='threshold_one',f'{path.name}_schema_schedule')
            need(row['correct'] is True and row['inputs_unchanged'] is True and row['modes']==['normalized']*3,f'{path.name}_saved_flags_modes')
            need(all(type(row[k]) in (int,float) and math.isfinite(row[k]) and row[k]>=0 for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','retained_bytes')) and row['seconds']>0 and all(type(row[k]) is int for k in ('bytes','events','retained_bytes')) and len(row['nested_seconds'])==6 and all(type(x) in (float,int) and math.isfinite(x) and x>=0 for x in row['nested_seconds']) and sum(row['nested_seconds'])<=row['seconds']+1e-9,f'{path.name}_metrics')
            need(len(row['outputs'])==24 and all(len(x)==f['n'] for x in row['outputs']),f'{path.name}_output_dimensions')
            okay=True
            for k,step in enumerate(f['steps']):
                for j,key,mi,tr in ((0,'a',k,False),(1,'dse',k,False),(2,'unit',k+1,True)):
                    okay &= residual(cell-1,mi,tr,tuple(row['outputs'][3*k+j]),tuple(step[key]));residual_count+=1
            need(okay,f'{path.name}_24_exact_residuals')
            if pair>3 and (row['compile_seconds']!=0 or row['recompile_seconds']!=0):
                anomalies.append(dict(file=path.name,fixture=f['name'],**{k:v for k,v in row.items() if k!='outputs'}))
            rows.append(row)
        need(all(rows[i]['outputs']==rows[i+1]['outputs'] and rows[i]['modes']==rows[i+1]['modes'] for i in range(0,total,2)),f'{f["name"]}_all_saved_pairs_bit_identical')
        metrics={}
        for metric in ('events','bytes','seconds','retained_bytes','compile_seconds','recompile_seconds','gc_seconds'):
            metrics[metric]={side:{'values':[r[metric] for r in rows if r['measured'] and r['side']==side], 'median':statistics.median(r[metric] for r in rows if r['measured'] and r['side']==side)} for side in ('reference','candidate')}
        stats[f['name']]={'completed':total==20,'observed_pairs':total//2-3,'metrics':metrics}
        if total==20:
            need(not all(metrics[m]['candidate']['median']<=metrics[m]['reference']['median'] for m in ('events','bytes')),f'{f["name"]}_recomputed_allocation_predicate_false')
        allrows.extend(rows);counts.append(total)
    need(residual_count==1200 and len(allrows)==50 and sum(r['measured'] for r in allrows)==32,'all_50_windows_1200_residual_bindings')
    need(len(anomalies)==1 and anomalies[0]['file']=='window-3-10.toml' and anomalies[0]['side']=='candidate' and anomalies[0]['pair']==5 and anomalies[0]['order']==2 and anomalies[0]['compile_seconds']==0.0068022 and anomalies[0]['recompile_seconds']==0,'sole_saved_measured_compilation_anomaly')
    need([(stats[f]['metrics']['events'][s]['median'],stats[f]['metrics']['bytes'][s]['median']) for f in ('sparse32','dense32') for s in ('reference','candidate')]==[(1274,294664),(1279,292696),(1282,755520),(1291,742952)],'independent_complete_cell_medians')
    driver=(D/'driver.jl').read_text();kernel=(D/'red-kernel.jl').read_text()
    need(driver.index('save_window("window-')<driver.index('require(row["correct"]')<driver.index('"Measured compilation"')<driver.index('paired[row["side"]]=row') and 'exit(valid ? (MODE=="red" ? 1 : 0) : 2)' in driver,'saved_before_guard_then_exit2_source_termination')
    need('for pair in 1:10' in driver and 'for k in 1:8' in kernel and kernel.count('J.forward_solve!(')==2 and kernel.count('J.transpose_solve!(')==1 and kernel.count('J.replace_column!(')==1 and kernel.count('J.refactorize!(')==2 and 'clocks=zeros(UInt64,6)' in kernel and 'Base.summarysize(factor)' in kernel,'source_budget_loop_entries')
    matches=[];denied_exe=[];denied_identity=[]
    for pth in Path('/proc').glob('[0-9]*'):
        try:
            st=(pth/'stat').read_text().rsplit(')',1)[1].split();comm=(pth/'comm').read_text().strip();argv=(pth/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
            try:exe=str((pth/'exe').resolve(strict=True))
            except PermissionError:denied_exe.append(int(pth.name))
            except (FileNotFoundError,ProcessLookupError):pass
            if int(st[2]) in groups or int(st[3]) in groups or any(Path(z).name.lower().startswith('julia') for z in (comm,argv,exe)):
                matches.append({'pid':int(pth.name),'pgid':int(st[2]),'sid':int(st[3]),'comm':comm,'argv0':argv,'exe':exe})
        except (FileNotFoundError,ProcessLookupError):pass
        except PermissionError:denied_identity.append(int(pth.name))
    need(not matches and not denied_identity and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==s['boot_id'],'fresh_readonly_all_group_session_and_julia_scan')
    need({x.name for x in (D/'runs').iterdir()}=={'red300'},'no_retry_or_green_run_directory')
    evidence.update(window_counts=counts,window_metrics=stats,measured_anomalies=anomalies,exact_residual_bindings=residual_count,exact_residual_unique_calculations=residual.cache_info().misses,resource_samples=len(samples),minimum_available_kib=min(x['available_kib'] for x in samples+[proc['terminal_memory']]),maximum_swap_used_kib=max(x['swap_used_kib'] for x in samples+[proc['terminal_memory']]),child_maxrss_kib=proc['child_maxrss_kib'],guard_elapsed_including_launch=proc['elapsed_including_launch'],supervisor_elapsed=inv['elapsed_seconds'],outer_elapsed=outer['elapsed_with_checks_seconds'],fresh_host=dict(time=time.time(),groups=sorted(groups),matches=matches,unreadable_exe_pids=denied_exe,unreadable_identity_pids=denied_identity),source_derived_reached_work=dict(constructors=50,refactors=100,updates=400,explicit_FTRAN=800,explicit_BTRAN=400,solve_outputs=1200,build_routes=150,orientation_solve_upper_bound=150,warm_windows=18,observed_windows=32,clock_scalar_payload_bytes=2400,fixture_output_scalar_payload_bytes=30720,serialized_float_tokens=53760,serialized_scalar_payload_bytes=430080),limitations=['Failed partial experiment; no full RED acceptance or GREEN permission.','No function-level compilation trace; final nested refactor time does not identify compiled method.','RSS is high-water resident memory, not native retained-memory proof; resource samples are discrete.','Unreadable exe symlinks limit universal executable-identity proof; stat/comm/argv0 and all recorded groups/sessions were checked.','Exact residual verification checks saved outputs; immutable pins and recorded input flags cannot reconstruct every transient in-memory mutation.','No numerical rerun or frozen auditor/checker execution.'])

if __name__=='__main__':
    try:main()
    except Exception:evidence['error']=traceback.format_exc()
    runfiles={str(p):digest(p) for p in sorted(RUN.rglob('*')) if p.is_file() and p.name!='result-review.json'}
    result=dict(all_passed=bool(checks) and all(checks.values()) and 'error' not in evidence,qualification_accepted=False,scope='Independent offline BG specialization RED failed-attempt diagnostic checks',checks=checks,evidence=evidence,run_sha256=runfiles,evidence_sha256={str(p):digest(p) for p in [Path(__file__),Q/'RESULT.md',Q/'outer-closure.json',Q/'post-summary.json',Q/'admission-review.md']})
    with (Q/'result-check.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],error=evidence.get('error'),run_bindings=len(runfiles),residual_bindings=evidence.get('exact_residual_bindings'))))
