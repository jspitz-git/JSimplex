from pathlib import Path
import json,hashlib,tomllib,subprocess,os,statistics,math,re,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS';E=H.with_name('DIRECT-BG-ZERO-COUNTS-RUN');run=H/'runs/zero-counts-300';outer=H/'outers/zero-counts-300';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def git(*a,root=R):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
def bind(d):
 for p,h in d.items():assert sha(p)==h,p
checks={}
def ok(k,v=True):assert v,k;checks[k]=True
s=rd(run/'sealed.json');pins=rd(run/'launch-pins.json');ad=rd(run/'admission.json');audit=rd(run/'audit.json');an=rd(E/'analysis.json');cl=rd(run/'outer-closure.json')
for m in (s,pins):
 assert len(m['files'])==len(set(m['files'])) and set(m['files'])==set(m['inventory'])
 for p,item in m['inventory'].items():
  assert str(Path(p).resolve())==item['resolved'],p
  assert sha(p)==item['sha256'],p
 for tree in m['trees']:
  actual={str(p) for p in Path(tree).rglob('*') if p.is_file()}
  expected={p for p in m['inventory'] if p.startswith(tree+'/')}
  assert actual==expected,(tree,actual^expected)
ok('all_launch_1876_and_seal_1871_sha256_resolved_paths_and_tree_membership',len(s['inventory'])==1871 and len(pins['inventory'])==1876)
ok('launch_matches_guard_pins',rd(run/'output/pins.json')==pins)
extras={str(run/n) for n in ('sealed.json','admission.json','prehost.json')}|{str(outer/n) for n in ('release.json','outer-invocation.json')}
ok('exact_launch_inventory_extension',set(pins['inventory'])==set(s['inventory'])|extras and all(pins['inventory'][p]==v for p,v in s['inventory'].items()))
prep=rd(H/'preparation-pins.json');pr=rd(H/'review.json');runtime=rd(H/'runtime-inputs-complete.json')['inventory'];base=rd(H/'baseline.json');stage=rd(H/'stages.json')['red']
for d in (prep['sha256'],pr['sha256'],pr['evidence_sha256'],ad['sha256'],ad['evidence_sha256'],cl['sha256'],audit['sha256'],an['sha256']):bind(d)
ok('preparation_227_and_review_228_exact_membership',len(prep['sha256'])==227 and set(prep['sha256'])==set(rd(H/'required-paths.json')['paths']) and set(pr['sha256'])==set(prep['sha256'])|{str(H/'preparation-pins.json')})
ok('preparation_receipt',pr['accepted'] is True and pr['findings']==[] and pr['launch_admitted'] is False and pr['pins_sha256']==sha(H/'preparation-pins.json'))
ok('exact_admission_1872',ad['accepted'] is True and ad['findings']==[] and ad['scope']=='BG zero-count exact-run admission' and ad['phase']=='zero-counts-300' and ad['pins_sha256']==sha(run/'sealed.json') and len(ad['sha256'])==1872 and set(ad['sha256'])==set(s['inventory'])|{str(run/'sealed.json')})
for p,v in runtime.items():assert pins['inventory'][p]==v
ok('runtime609',len(runtime)==609)
for label,root in [('diagnostic',R),('production',W)]:
 assert set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(base[label])
 for p,h in base[label].items():assert sha(root/p)==h
 assert not git('diff','--name-only',root=root) and not git('diff','--cached','--name-only',root=root)
ok('baseline514_516_exact_source_membership_hashes_clean_tracked_index',len(base['diagnostic'])==514 and len(base['production'])==516)
assert {str(p.relative_to(stage['path'])) for p in Path(stage['path']).rglob('*') if p.is_file()}==set(stage['sha256'])
for p,h in stage['sha256'].items():assert sha(Path(stage['path'])/p)==h
ok('stage75',len(stage['sha256'])==75)
expected_seal=set(prep['sha256'])|{str(H/'preparation-pins.json'),str(H/'review.json')}|set(pr['evidence_sha256'])|set(runtime)|{str(root/p) for label,root in [('diagnostic',R),('production',W)] for p in base[label]}|{str(Path(stage['path'])/p) for p in stage['sha256']}|{str(run/'host.json'),str(run/'config.json'),str(outer/'outer-ready.json')}
ok('independently_rebuilt_exact_seal_membership',set(s['files'])==expected_seal)
head='42e6e50ad0c8b6ffd762394a27f1d8d5fd9e782d';master='26e2291745999f485a74f643298ca997d65c7205'
ok('local_head_master_unchanged',git('rev-parse','HEAD')==head and git('rev-parse','master')==master and git('rev-parse','HEAD',root=W)==master)
env=rd(H/'environment.json');ok('environment_unchanged',{k:os.environ.get(k) for k in env}==env)
for n,item in rd(H/'copied-files.json').items():assert sha(H/n)==sha(item['source'])==item['sha256']
ok('frozen_copied_controls')
orig=(R/'diagnostics/direct-bg-blocked-update/reproduce/panel.jl').read_text();candidate=H.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')/'panel.jl';ct=candidate.read_text()
expected=orig.replace('struct BGNoCounts end','const _BGB_ZERO_COUNTS = ntuple(_ -> 0, Val(20))\nstruct BGNoCounts end',1).replace('BGPanelCounts(ntuple(_ -> 0,20))','BGPanelCounts(_BGB_ZERO_COUNTS)',1).replace('counts(::BGNoCounts) = ntuple(_->0,20)','counts(::BGNoCounts) = _BGB_ZERO_COUNTS',1).replace('true,ntuple(_->0,20))','true,_BGB_ZERO_COUNTS)',1)
ok('complete_candidate_diff_only_initializer_and_three_replacements',ct==expected)
ok('accepted_candidate_test_hashes',sha(candidate)=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295' and sha(candidate.with_name('zero-counts-tests.jl'))=='927789cf6260b52694bdc258529696a62af3ab338744a32b4564dd6aad0dae6f')
files={p.name:tomllib.loads(p.read_text()) for p in (run/'payload').iterdir()}
prepnames=['load','reference-load','candidate-load','setup','snapshot-before','snapshot-after','tests-cost']
assert set(files)=={f'record-{i}.toml' for i in range(1,61)}|{f'{n}.toml' for n in prepnames}|{'tests.toml','raw.toml'}
ok('exact69_payload_regular_no_symlinks',all(p.is_file() and not p.is_symlink() for p in (run/'payload').iterdir()))
raw=files['raw.toml'];rows=raw['records'];ts=files['tests.toml'];aresult=audit['result']
ok('complete_raw_strict_success_and_input_owner_observations',raw['complete'] is True and raw['fatal']=='' and raw['schema']==1 and raw['qualification']=='zero_counts_diagnostic' and raw['input_unchanged'] is True and raw['replacement_unchanged'] is True)
ok('exact_loaded_paths',raw['loaded']==dict(rd(H/'loaded-paths.json'),JSimplex=str(Path(stage['path'])/'src/JSimplex.jl')))
assert raw['tests']==ts==aresult['tests']==an['test_tree']
assert ts['failure_count']==0 and ts['failures']==[]
root=ts['tree'];assert all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','error','broken'])
assert [c['pass'] for c in root['children']]==[7,300,10,26,7]
assert all(c['children']==[] and all(type(c[k]) is int and c[k]==0 for k in ['fail','error','broken']) for c in root['children'])
ok('exact350_assertions_no_fail_error_broken',sum(c['pass'] for c in root['children'])==350 and aresult['structural_assertions']==an['structural_assertions']==350)
schedule=[('first',0,'reference'),('first',0,'candidate'),('warm',0,'candidate'),('warm',0,'reference')]
for pair in range(1,5):schedule.extend(('sample',pair,arm) for arm in (('reference','candidate') if pair%2 else ('candidate','reference')))
assert len(rows)==60 and rows==aresult['records']
for i,row in enumerate(rows,1):
 assert row==files[f'record-{i}.toml']
 case=['zeros','constructor','dimensions','eligibility','original'][(i-1)//12];phase,pair,arm=schedule[(i-1)%12]
 assert (row['index'],row['case'],row['phase'],row['pair'],row['arm'])==(i,case,phase,pair,arm)
 assert row['assignment_ok'] is True and row['decision_ok'] is True
 assert len(row['observed']['counters'])==20 and all(type(v) is int and v==0 for v in row['observed']['counters'])
 if case=='constructor':assert row['observed']=={'counters':[0]*20,'fresh_owner':True}
 elif case=='zeros':assert row['observed']=={'counters':[0]*20}
 else:assert row['observed']=={'counters':[0]*20,'start':1,'count':0,'accepted':False,'reason':'dimensions','finite':True}
 for k in ('inner_bytes','inner_events'):assert type(row[k]) is int and row[k]>=0
 for name in ('bytes_wrapper','events_wrapper','consumed_result'):
  m=row[name];assert set(m)=={'bytes','events','seconds','compile_seconds','recompile_seconds','gc_seconds'}
  for k,v in m.items():assert type(v) in (int,float) and math.isfinite(v) and v>=0 and (k not in ('bytes','events') or int(v)==v)
ok('60_exact_ordered_full_records_equal_raw_files_audited_records')
summary={}
for case in ('zeros','constructor','dimensions','eligibility','original'):
 arms={}
 for arm in ('reference','candidate'):
  rr=[v for v in rows if v['case']==case and v['arm']==arm and v['phase']=='sample'];assert len(rr)==4
  arms[arm]={'bytes':[v['inner_bytes'] for v in rr],'events':[v['inner_events'] for v in rr],'consumed_seconds':[v['consumed_result']['seconds'] for v in rr],'consumed_bytes':[v['consumed_result']['bytes'] for v in rr],'consumed_events':[v['consumed_result']['events'] for v in rr],'clean':all(v[k][f]==0 for v in rr for k in ('bytes_wrapper','events_wrapper','consumed_result') for f in ('compile_seconds','recompile_seconds','gc_seconds'))}
  arms[arm]['median_seconds']=statistics.median(arms[arm]['consumed_seconds']);assert arms[arm]['clean']
 ratios=[y/x for x,y in zip(arms['reference']['consumed_seconds'],arms['candidate']['consumed_seconds'])]
 summary[case]={'arms':arms,'paired_time_ratios':ratios,'median_paired_time_ratio':statistics.median(ratios)}
ok('independent_full_summary_recalculation_and_all40_samples_gc_compile_recompile_zero',summary==an['summary'])
preparation={n:files[n+'.toml'] for n in prepnames}
print('PREPARATIONKEYS',list(aresult['preparation']))
# Saved names use TOML filenames in the auditor preparation dictionary.
assert {n+'.toml':v for n,v in preparation.items()}==aresult['preparation']==an['preparation']
ok('all_seven_preparation_records_match_analysis_audit')
cfg=rd(run/'config.json');p=rd(run/'output/process.json');cur=rd(run/'output/current.json');inv=rd(run/'invocation.json');sup=inv['supervisor'];ready=rd(outer/'outer-ready.json');rel=rd(outer/'release.json');oinv=rd(outer/'outer-invocation.json');outcome=rd(outer/'outer-outcome.json');reservation=rd(run/'reservation.json')
assert s['config']==cfg and cfg['phase']=='zero-counts-300' and cfg['seconds']==300
assert p['command']==cur['command']==inv['command']==cfg['command'] and p['cwd']==str(R)
assert p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child']
assert p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(run/'launch-pins.json')
assert inv['reservation_sha256']==sha(run/'reservation.json') and inv['review_sha256']==sha(run/'admission.json')
assert reservation==dict(one_attempt=True,phase='zero-counts-300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300)
assert ready['identity']==s['outer_identity']==oinv['identity']==outcome['identity']==cl['outer_identity']
assert rel==dict(phase='zero-counts-300',sealed_sha256=sha(run/'sealed.json'),admission_sha256=sha(run/'admission.json'),outer_ready_sha256=sha(outer/'outer-ready.json'),one_attempt=True)
assert oinv['seal_sha256']==sha(run/'sealed.json') and oinv['review_sha256']==sha(run/'admission.json') and oinv['release_sha256']==sha(outer/'release.json') and oinv['launcher_sha256']==sha(H/'launch.py')
assert all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and sup['accepted'] is True and sup['returncode']==0
assert p['returncode']==0 and p['reason']=='exit0' and p['pins_unchanged'] is True
assert not {'error','remaining_group','remaining_session'}&set(p) and 'cleanup_error' not in sup
assert outcome['launched'] is True and outcome['returncode']==0 and outcome['error']==''
assert 0<=p['elapsed_including_launch']<=292 and 0<=inv['elapsed_seconds']<=300 and 0<=sup['elapsed_seconds']<=300
assert audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']==''
assert p['elapsed_including_launch']==an['process_elapsed_seconds'] and inv['elapsed_seconds']==an['supervised_elapsed_seconds'] and p['child_maxrss_kib']==an['peak_rss_kib']
assert (run/'output/run.log').read_text()=='' and rd(run/'launcher.log')==p
ok('process_supervisor_outer_exact_success_and_hash_identity_linkage')
resources=[json.loads(x) for x in (run/'output/resources.jsonl').read_text().splitlines()]
assert len(resources)==9 and [x['elapsed'] for x in resources]==sorted(x['elapsed'] for x in resources)
for x in resources:
 assert set(x)=={'available_kib','swap_used_kib','elapsed','child_memory'} and 0<=x['elapsed']<=p['elapsed_including_launch']
 assert all(re.fullmatch(r'Vm(?:Peak|HWM|RSS|Swap):\s+\d+ kB',line) for line in x['child_memory'])
for x in resources+[p['terminal_memory']]:assert type(x['available_kib']) is int and x['available_kib']>=6*1024**2 and type(x['swap_used_kib']) is int and 0<=x['swap_used_kib']<=1024**2
assert an['resources']==dict(samples=9,minimum_available_kib=min(x['available_kib'] for x in resources),maximum_swap_used_kib=max(x['swap_used_kib'] for x in resources))
ok('resources_recalculated_with_limits_and_terminal_sample')
assert set(cl['sha256'])=={str(outer/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(run/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']}
ch=cl['host'];post=rd(run/'posthost.json');groups=set(ch['groups'])
assert cl['all_passed'] is True and len(groups)==280 and groups==set(s['groups'])|set(post['groups'])|{s['outer_identity']['pgid'],s['outer_identity']['sid']}
for h in [ch,post,rd(run/'host.json'),rd(run/'prehost.json')]:
 assert h['matches']==[] and h['unreadable_identity_pids']==[] and h['head']==head and h['master']==master and h['boot_id']==s['boot_id']
 assert head+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and master+'\trefs/heads/master' in h['remote']
assert ch['time']>p['ended'] and ch['memory']['available_kib']>=6*1024**2 and ch['memory']['swap_used_kib']==0
ok('external_closure_exact8_bindings_280_groups_AND_sessions_and_refs')
fresh={'time':time.time(),'matches':[],'unreadable_identity_pids':[],'unreadable_exe_pids':[],'groups':sorted(groups),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
for q in Path('/proc').glob('[0-9]*'):
 try:
  st=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();argv0=(q/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
  try:exe=str((q/'exe').resolve(strict=True))
  except PermissionError:fresh['unreadable_exe_pids'].append(int(q.name))
  except FileNotFoundError:pass
  if int(st[2]) in groups or int(st[3]) in groups or any(Path(v).name.lower().startswith('julia') for v in [comm,argv0,exe]):fresh['matches'].append({'pid':int(q.name),'pgid':int(st[2]),'sid':int(st[3]),'comm':comm,'argv0':argv0,'exe':exe})
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:fresh['unreadable_identity_pids'].append(int(q.name))
ok('fresh_readonly280_group_AND_session_scan_no_visible_Julia',fresh['matches']==[] and fresh['unreadable_identity_pids']==[] and fresh['boot_id']==s['boot_id'])
runfiles=sorted(p for p in run.rglob('*') if p.is_file());outerfiles=sorted(p for p in outer.rglob('*') if p.is_file())
ok('analysis_exact_all_run_outer_bindings',set(an['sha256'])=={str(p) for p in runfiles+outerfiles})
ok('audit_exact_completed_prefix_bindings',set(audit['sha256'])=={str(p) for p in runfiles if p.name not in ('audit.json','outer-closure.json')})
subjects=runfiles+outerfiles+[E/n for n in ['analysis.py','analysis.json','REPORT.md','admission-review.md','admission-review.json','authorization.json','host-entry.json','outer-start.json']]
result=dict(accepted=True,findings=[],scope='BG zero-count completed-run independent result review',phase='zero-counts-300',julia_invoked=False,old_auditor_or_scripts_rerun=False,source_schedule_operations=204,checks=checks,counts=dict(sealed=1871,admission=1872,launch=1876,runtime=609,diagnostic_baseline=514,production_baseline=516,stage=75,payload=69,records=60,structural_assertions=350,sample_pairs_per_case=4,run_files=len(runfiles),outer_files=len(outerfiles),result_bindings=len(subjects)),summary=summary,fresh_host=fresh,process_elapsed_seconds=p['elapsed_including_launch'],supervised_elapsed_seconds=inv['elapsed_seconds'],resources=an['resources'],peak_rss_kib=p['child_maxrss_kib'],unnecessary_production_work_or_memory_found=False,production_promoted=False,p011_accepted=False,sha256={str(p):sha(p) for p in subjects})
Path('/tmp/zero-result-review-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'counts':result['counts'],'summary':summary,'fresh_host':fresh},indent=2))
