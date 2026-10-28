from pathlib import Path
import json,hashlib,tomllib,statistics as st,math,re,os,subprocess,datetime
D=Path(__file__).resolve().parent;K=D/'correctness-qualification';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
for record in [read(D/'audit-qualified.json'),read(D/'cost-audit-recovery-review.json'),read(K/'result-review.json')]:
 need(record['accepted'] is True,'accepted supporting review')
 for n,h in record['bindings'].items():need(sha(n)==h,'support binding '+n)
pins=read(D/'pins-ready.json')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership')
for section in read(D/'protected-before.json').values():
 for n,h in section.items():need(sha(n)==h,'protected '+n)
con=read(D/'contract-ready.json');proc=read(D/'output/process.json');sup=read(D/'supervisor.json');inv=read(D/'invocation.json');res=read(D/'reservation.json');audit=read(D/'audit-qualified.json');log=(D/'output/run.log').read_text()
need(proc['reason']=='exit1' and proc['returncode']==1 and proc['pins_unchanged'] is True and sup['accepted'] is False and sup['returncode']==1 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'preserved original failed process')
need(sup['elapsed_seconds']<=900 and not (D/'completed.json').exists(),'failed-run deadline/status')
need(proc['command']==con['command']==inv['Julia_command'] and proc['pins_sha256']==sha(D/'pins-ready.json')==res['pins_sha256'],'command/pins')
need(res['admission_sha256']==sha(D/'admission-ready.json') and res['guard_deadline']==res['started_monotonic']+892 and res['outer_deadline']==res['started_monotonic']+900,'admission/deadline')
gate=read(D/'output/gate.json');cur=read(D/'output/current.json');permit=read(D/'output/permit.json')
need(proc['runner']==sup['guard_identity']==cur['runner']==gate['parent'] and proc['child']==cur['child']==gate['identity'],'identities')
need(gate['command']==cur['command']==permit['command']==con['command'] and gate['parent_death_signal']==9,'gate')
need(gate['current_sha256']==sha(D/'output/current.json')==permit['current_sha256'] and gate['permit_sha256']==sha(D/'output/permit.json') and sha(D/'output/pins.json')==sha(D/'pins-ready.json'),'gate hashes')
need(re.findall(r'^ERROR: (.*)$',log,re.M)==['LoadError: Some tests did not pass: 111259 passed, 90 failed, 0 errored, 0 broken.'] and 'Error During Test' not in log,'exact original Test error')
locations=re.findall(r'Test Failed at (.*?):(\d+)',log);need(len(locations)==90 and all(p==str(D/'extra-tests-ready.jl') and n=='127' for p,n in locations),'exact failed locations')
need(log.count('Expression: Rational{BigInt}(precise) == exactweight')==90 and 'SUM_RATIONAL_GROWTH_COMPLETE' not in log,'original failure expressions/no false success')
need(read(K/'result-review.json')['assertions']==28227 and read(K/'result-review.json')['measured_windows']==0,'correctness qualification')
raw=tomllib.loads((D/'output/results.toml').read_text());grid=read(D/'expected-cases.json');reported=read(D/'summary-qualified.json')
need(set(raw)=={'cells','preparation'} and len(raw['cells'])==2636 and len(raw['preparation'])==2674 and len(reported)==2636,'raw lengths')
contexts=list(dict.fromkeys(v['context'] for v in grid));need(len(contexts)==19 and re.findall(r'^CONTEXT (.*)$',log,re.M)==contexts,'raw ordered contexts')
costkeys={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
def cost(x):
 need(set(x)==costkeys,'cost fields')
 need(all(type(x[k]) in [int,float] and math.isfinite(x[k]) and x[k]>=0 for k in costkeys),'valid nonnegative cost')
 need(type(x['bytes']) is int and type(x['events']) is int,'integer allocations')
def sample(w):
 need(set(w)==costkeys|{'result','capture_preparation'},'sample fields');cost({k:w[k] for k in costkeys});cost(w['capture_preparation'])
def ratios(a,b):return [1.0 if x==y==0 else y/x if x>0 else None for x,y in zip(a,b)]
recomputed=[];gc_windows=[];prep_index=0;cell_index=0
for context in contexts:
 for key in ['correctness','GC']:
  pp=raw['preparation'][prep_index];prep_index+=1;need(set(pp)=={'context',key} and pp['context']==context,'context preparation');cost(pp[key])
 for spec in [v for v in grid if v['context']==context]:
  cell=raw['cells'][cell_index];cell_index+=1;need(set(cell)==set(spec)|{'windows'} and all(type(cell[k]) is type(v) and cell[k]==v for k,v in spec.items()),'typed cell')
  windows=cell['windows'];need(len(windows)==18,'18 windows');pairs=[]
  for i,w in enumerate(windows):
   pair=i//2+1;arms=['original',spec['variant']] if pair%2 else [spec['variant'],'original'];need(set(w)==costkeys|{'result','capture_preparation','pair','arm'} and type(w['pair']) is int and w['pair']==pair and w['arm']==arms[i%2],'pair ordering')
   sample({k:v for k,v in w.items() if k not in ['pair','arm']});need(w['compile_seconds']==w['recompile_seconds']==0,'compile-zero')
   if spec['scope'] in ['rows','growth']:need(type(w['result']) is float and math.isfinite(w['result']),'float result')
   elif spec['scope']=='scheduled':need(type(w['result']) is str and w['result'] in ['none','limit','fill','pivot_growth','residual','cost'],'symbol result')
   else:need(type(w['result']) is int and w['result'] in [0,1],'integer result')
   if w['gc_seconds']>0:gc_windows.append(dict(cell=spec['id'],pair=pair,arm=w['arm'],seconds=w['gc_seconds']))
  for pair in range(1,10):
   a=next(w for w in windows if w['pair']==pair and w['arm']=='original');b=next(w for w in windows if w['pair']==pair and w['arm']==spec['variant']);need(type(a['result']) is type(b['result']) and a['result']==b['result'],'paired typed result');pairs.append((a,b))
  row=dict(spec)
  for key in ['seconds','bytes','events']:
   a=[p[0][key] for p in pairs];b=[p[1][key] for p in pairs];q=ratios(a,b);valid=all(v is not None for v in q);median=st.median(q) if valid else None
   row[key]=dict(before=st.median(a),after=st.median(b),paired_ratios=q,paired_median=median,paired_min=min(q) if valid else None,paired_max=max(q) if valid else None,paired_MAD=st.median(abs(v-median) for v in q) if valid else None,undefined_zero_baseline=sum(v is None for v in q))
  need(row==reported[cell_index-1],'independent statistics comparison');recomputed.append(row)
  pp=raw['preparation'][prep_index];prep_index+=1;need(set(pp)=={'cell','fixture','validation','final_validation','cold','warm','resets'} and pp['cell']==spec['id'],'cell preparation')
  for key in ['fixture','validation','final_validation']:cost(pp[key])
  need(len(pp['cold'])==2 and len(pp['warm'])==6 and len(pp['resets'])==18,'preparation counts')
  for key in ['cold','warm']:
   for entry in pp[key]:need(set(entry)=={'cost','reset'},'preparation sample');sample(entry['cost']);cost(entry['reset'])
  for entry in pp['resets']:cost(entry)
need(cell_index==2636 and prep_index==2674 and len(gc_windows)==22,'all counts/GC')
resources=[json.loads(v) for v in (D/'output/resources.jsonl').read_text().splitlines()];need(resources and all(v['available_kib']>=6*1024**2 and v['swap_used_kib']<=1024**2 for v in resources),'resource samples')
need(proc['terminal_memory']['available_kib']>=6*1024**2 and proc['terminal_memory']['swap_used_kib']<=1024**2,'terminal resources')
need(audit['original_run_accepted'] is False and audit['original_assertions_passed']==111259 and audit['original_failed_assertions']==90 and audit['qualification_assertions']==28227 and audit['gc_windows']==22,'qualified audit honesty')
observer=read(D/'qualified-audit-invoker.json');need(observer['command'][-1]==str(D/'audit-qualified-recovery.py') and observer['boot_id']==proc['runner']['boot_id'] and observer['start_ticks']>proc['runner']['start_ticks'],'new audit observer')
def affected(r):return r['type']==('Rational{BigInt}' if r['variant']=='B' else 'BigFloat')
def group(rows):
 out=dict(cells=len(rows))
 for key in ['seconds','bytes','events']:
  q=[r[key]['paired_median'] for r in rows];need(all(v is not None for v in q),'undefined cell statistic')
  out[key]=dict(median_ratio=st.median(q),minimum_cell_ratio=min(q),maximum_cell_ratio=max(q),lower=sum(v<1 for v in q),equal=sum(v==1 for v in q),higher=sum(v>1 for v in q),raw_pair_min=min(r[key]['paired_min'] for r in rows),raw_pair_max=max(r[key]['paired_max'] for r in rows),median_pair_MAD=st.median(r[key]['paired_MAD'] for r in rows),median_before=st.median(r[key]['before'] for r in rows),median_after=st.median(r[key]['after'] for r in rows))
 return out
groupsummary={}
for arm in ['A','B','C']:
 affected_rows=[r for r in recomputed if r['variant']==arm and affected(r)];controls=[r for r in recomputed if r['variant']==arm and not affected(r)]
 need(all(r[key]['paired_median']<=1 for r in affected_rows for key in ['bytes','events']),'affected allocation regression')
 need(all(r['events']['before']==r['events']['after'] for r in controls),'unchanged control event regression')
 groupsummary[arm+'_controls']=group(controls)
 for scope in sorted({r['scope'] for r in affected_rows}):
  rr=[r for r in affected_rows if r['scope']==scope];groupsummary[arm+'_'+scope]=group(rr)
  if arm=='C':
   for chain in [0,8,32]:groupsummary['C_'+scope+'_chain'+str(chain)]=group([r for r in rr if r['chain']==chain])
 for density in ['sparse','dense']:groupsummary[arm+'_'+density]=group([r for r in affected_rows if r['density']==density and (arm!='C' or r['chain']>0)])
 for shape in sorted({r['shape'] for r in affected_rows}):groupsummary[arm+'_'+shape]=group([r for r in affected_rows if r['shape']==shape and (arm!='C' or r['chain']>0)])
slower=[dict(id=r['id'],ratio=r['seconds']['paired_median'],MAD=r['seconds']['paired_MAD'],ratios=r['seconds']['paired_ratios']) for r in recomputed if affected(r) and r['seconds']['paired_median']>1]
controlbytes=[dict(id=r['id'],before=r['bytes']['before'],after=r['bytes']['after'],events=r['events']['before']) for r in recomputed if not affected(r) and r['bytes']['before']!=r['bytes']['after']]
prep_stats={key:sum(p[key]['seconds'] for p in raw['preparation'] if key in p) for key in ['fixture','validation','final_validation','correctness','GC']}
prep_stats['correctness_compile_seconds']=sum(p['correctness']['compile_seconds'] for p in raw['preparation'] if 'correctness'in p)
prep_stats['validation_compile_seconds']=sum(p['validation']['compile_seconds'] for p in raw['preparation'] if 'validation'in p)
prep_stats['cold_compile_seconds']=sum(z['cost']['compile_seconds'] for p in raw['preparation'] if 'cold'in p for z in p['cold'])
prep_stats['warm_compile_seconds']=sum(z['cost']['compile_seconds'] for p in raw['preparation'] if 'warm'in p for z in p['warm'])
put('independent-cost-statistics.json',dict(groups=groupsummary,all_slower_affected_cells=slower,all_unchanged_control_byte_differences=controlbytes,gc_windows=gc_windows,preparation_seconds=prep_stats,statistics_recomputed_from_all_raw_windows=True))
# Fresh host closure after all independent source/raw/statistics work.
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(all(git(M,'rev-parse',v)=='ce5d4a74019e0dc2e656d08161641c498b159e7b' for v in ['HEAD','master','origin/master']),'master refs')
need(git(R,'rev-parse','HEAD')=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic ref')
need(not git(M,'diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
seed=read(D/'host-seed.json');historical=set(seed['groups'])
for record in [proc,read(K/'output/process.json')]:historical.update(record[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
need(len(historical)==653,'historical identifiers');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot')
allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance')
allowed=read(allowance)['identities'];processes=[];collisions=[]
for path in Path('/proc').glob('[0-9]*'):
 try:
  fields=(path/'stat').read_text().rsplit(')',1)[1].split();cmd=[x.decode(errors='replace') for x in (path/'cmdline').read_bytes().split(b'\0') if x];comm=(path/'comm').read_text().strip();ident=dict(pid=int(path.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=cmd,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+cmd[:1]),'live Julia')
  if ident['pgid'] in historical or ident['sid'] in historical:need(ident in allowed,'historical group/session');collisions.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-result-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(historical),processes=processes,collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
lines=['# Independent result review: A, B and C accepted for permanent gates and production staging','',
'All three exact private candidates are accepted for the next production gate. This decision combines the preserved whole-function comparison with the separately admitted correctness-only qualification. It does not approve a commit, integration or push without the planned permanent regression RED/GREEN and production checks. The original numerical attempt remains failed: 111,259 assertions passed and 90 decoder assertions failed. The unchanged candidates then passed all 28,227 correctness assertions with the decoder-only correction and explicit characterization of the old error. No timing measurement was repeated.','',
'The comparison contains all 2,636 ordered cells, 47,448 compile/recompile-zero windows, and 2,674 preparation records. All nine alternating pairs and three warmups per cell remain; all 22 GC windows are retained. Independent parsing checked every typed result, allocation/time field, preparation entry and paired statistic, and reproduced summary-qualified.json exactly. Original/correctness commands, gate/process identities, pins, resource/deadline evidence and the new post-exit observer were checked. Fresh closure checks all 653 groups AND sessions; protected files/indexes and refs remain unchanged. The earlier stopped post-exit audit remains recorded with an unknown occupant cause.','',
'Ratios below are candidate/reference, calculated as the median across cell-level medians of nine paired ratios; they are not pooled elapsed-time speedups. C rows include 180 empty-chain cells per scope.','',
'| Whole function | Cells | Time ratio | Bytes ratio | Events ratio |','|---|---:|---:|---:|---:|']
for label,key in [('A row bounds','A_rows'),('A original feasibility','A_feasible'),('B Rational{BigInt} certificate','B_cert'),('C growth','C_growth'),('C forced refresh','C_refresh'),('C scheduled reason','C_scheduled')]:
 g=groupsummary[key];lines.append(f"| {label} | {g['cells']} | {g['seconds']['median_ratio']:.3f} | {g['bytes']['median_ratio']:.3f} | {g['events']['median_ratio']:.3f} |")
lines.extend(['',
'A saves allocations in all 360 affected cells; 356 have lower paired-median time. Four timing regressions remain in the evidence. The largest is BF64_Down/16/sparse/positive/feasible at1.699x, with paired ratios0.761–5.927, MAD0.927 and no GC in those windows; the source of that timing variation is unresolved. The unpaired call medians there are28.1 to30.7 microseconds, while bytes/events fall20,880 to17,072 and654 to518. This is not hidden or labeled a speedup. Positive/negative row trajectories give larger reductions than mixed signs, consistent with the reached same-sign shortcut. Sparse and dense aggregate timing ratios are0.787/0.777, with corresponding allocation reductions.','',
'B improves median time, bytes and events in all 48 exact-BigInt certificate cells, covering sparse/dense, both orientations, valid/invalid/one-sided cases, and small/wide numerators. Sparse/dense timing ratios are0.856/0.793. A representative wide dense n64 certificate has median295.2 to217.0 microseconds,649,456 to474,624 bytes and17,593 to12,909 events. Large individual timing outliers remain: the largest B paired ratio is217.277. All 432 unchanged floating/fixed-rational controls retain equal allocation-event medians; their median timing ratio is1.000.','',
'C has lower cell-median time, bytes and events in every one of the 1,080 nonempty-chain whole-call cells. All 540 empty-chain cells retain equal bytes/events; their median timing ratio is1.000 and their sub-microsecond samples are too coarse for a useful speed claim. For chains8/32, growth time ratios are0.315/0.263; complete forced-refresh ratios0.407/0.294; scheduled-reason ratios0.399/0.301. Positive entries yield the largest benefit, mixed entries less, and negative entries retain negation work; nonempty negative aggregate time ratio is0.875. Real packed updates, age/cache/fixed-policy gates and reason priority were exercised.','',
'No unnecessary added scan, solve, array copy or retained numerical buffer was found. A adds two sign loads/comparison at each reached cancellation gate and removes the unused BigFloat negation only for nonzero same-sign operands; CSC products/sums, finite/precision guards, underflow and enclosures remain. It affects row accumulation and final primal certification, not a changed simplex iteration count. B removes one exact signed-unit product per reached matrix nonzero and corresponding slack unit arithmetic, adds scalar orientation selection, and preserves CSC order, finite-bound/zero/allowance tests and exception handling; no O(m) oriented vector or floating/fixed-width change is introduced. C reduces L+1 unit constructors to one per call and skips unused positive-value negations over P packed values while keeping O(L+P) nested reductions. Forced refresh still includes storage/recovery-precision scans; scheduled refresh occurs at existing age1/every8/near-interval gates and obeys cached/fixed-policy paths. No precision/tolerance/safeguard was relaxed.','',
'Allocation-event medians are identical in all 608 unchanged-type controls. Nine Rational{BigInt} A/C controls nevertheless have differing byte medians despite unchanged code paths/events, including5,872 versus7,152 bytes in one C growth control. Their cause was not established; all are listed in independent-cost-statistics.json. This variability prevents an assertion of identical byte behavior in every control. No affected candidate cell has higher median bytes or events.','',
f"Preparation is separate: fixture construction totals{prep_stats['fixture']:.3f}s; correctness{prep_stats['correctness']:.3f}s, including{prep_stats['correctness_compile_seconds']:.3f}s recorded compilation; pre-window validation{prep_stats['validation']:.3f}s, including{prep_stats['validation_compile_seconds']:.3f}s compilation; final validation{prep_stats['final_validation']:.3f}s; explicit GC{prep_stats['GC']:.3f}s. Per-cell cold/warm windows report zero compilation because correctness runs first. They are first-per-cell observations, not isolated per-variant cold-start measurements. Outer-driver/startup compilation is not fully attributed. Result-capture and reset costs remain separately recorded, outside whole-call timings.", '',
'These are short, single-process, warmed whole-function measurements on small representative sparse/dense fixtures, across BigFloat64/128/256 with five rounding modes and native/exact controls. Raw paired extremes and per-cell MAD, all slower cells, all GC records and control-byte differences are retained in independent-cost-statistics.json. Timer quantization materially affects empty/unchanged fast controls. Additional method/closure compilation and native retained-memory behavior are not fully measured. Julia allocation counters and process resource guards are not a native retained-memory proof. No full-solver throughput, trajectory-independent end-to-end speedup, large-problem scaling, x64 or full-suite claim is made.','',
'Accepted variants: A, B, C, provided production staging preserves these exact edits and all numerical safeguards. Next steps are the authorized permanent correctness/allocation gates with original RED evidence, exact source inverse, independent production review and required production GREEN checks. No Julia, previous audit or measurement was rerun by this independent review.'])
with (D/'RESULT-REVIEW.md').open('x') as f:f.write('\n'.join(lines)+'\n')
paths=[D/n for n in ['audit-qualified.json','summary-qualified.json','independent-cost-statistics.json','independent-cost-result-review.py','independent-result-host.json','RESULT-REVIEW.md','pins-ready.json','contract-ready.json','admission-ready.json','Reference.jl','A.jl','B.jl','C.jl','changes.json','fixtures-reviewed.jl','extra-tests-ready.jl','driver-ready.jl','output/run.log','output/results.toml','output/process.json','output/resources.jsonl','supervisor.json','qualified-audit-invoker.json','audit-qualified-recovery.py','cost-audit-host-rejection.json','cost-audit-recovery-review.json','decoder-root-cause-review.json']]+[K/n for n in ['result-review.json','audit.json','extra-corrected.jl','output/run.log','output/process.json']]
put('result-review.json',dict(accepted=True,findings=[],accepted_variants=['A','B','C'],acceptance_scope='permanent gates and exact production staging; not integration/push',bindings={str(p):sha(p) for p in paths},original_run_accepted=False,original_passes=111259,original_failures=90,qualification_assertions=28227,cases=2636,windows=47448,preparation=2674,gc_windows=22,all_statistics_independently_recomputed=True,affected_allocation_regressions=0,unchanged_control_byte_differences=len(controlbytes),Julia_executed=False))
print(json.dumps(dict(accepted=True,accepted_variants=['A','B','C'],cases=2636,windows=47448,gc_windows=22,control_byte_differences=len(controlbytes),historical_groups_and_sessions=653)))
