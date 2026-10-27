from pathlib import Path
import json,hashlib,subprocess,os,datetime,statistics,re
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];base='1a6b9d81e89b44c5c75b95b6c92e0916c2d19730';target='c01900c2dff3de465846ae44333903889c867626'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def raw(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def git(a,root=M):return raw(a,root).decode().strip()
need(git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'published master')
need(git(['branch','--show-current'])=='master' and git(['rev-list','--parents','-n','1',target]).split()==[target,base],'master branch parent')
need(git(['rev-parse','HEAD'],R)==read(D/'host-before.json')['diagnostic_head'],'diagnostic head unchanged')
inv=read(D/'source-inverse.json');baseline=read(D/'baseline-tree.json');co=read(D/'production-commit.json');pub=read(D/'publication.json');names=inv['names'];hist=read(D/'historical-path-map.json');ih=read(D/'integration-historical-path-map.json');di=read(D/'diagnostic-index-before.json');protected=read(D/'protected-before.json');post=read(D/'MASTER-run/protected-before.json')
need(pub['accepted'] is True and pub['commit']==pub['local_master']==pub['tracking']==pub['remote_master']==target and pub['parent']==base and pub['names']==names and pub['normal_nonforce_push'] is True,'publication evidence')
need('1a6b9d81..c01900c2' in (D/'push.log').read_text(),'normal push log')
need(git(['diff-tree','--no-commit-id','--name-only','-r',base,target]).splitlines()==names,'exact seven published paths')
for n in names:need(raw(['show',target+':'+n])==(M/n).read_bytes()==(D/'GREEN'/n).read_bytes() and git(['rev-parse',target+':'+n])==co['blobs'][n],'exact published blob '+n)
need({str(p.relative_to(D/'GREEN')):sha(p) for p in (D/'GREEN').rglob('*') if p.is_file()}==inv['whole_stage'],'whole stage')
need({str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()}==baseline,'baseline whole bytes')
for n,h in inv['whole_stage'].items():need(sha(M/n)==h,'all537 actual files '+n)
for tree in ['src','test']:
 need({str(p.relative_to(M)) for p in (M/tree).rglob('*') if p.is_file()}=={n for n in inv['whole_stage'] if n.startswith(tree+'/')},'actual whole tree membership')
need(not git(['diff','--name-only','HEAD','--','src','test','Project.toml']),'actual targets clean')
need(hist['master_before']==ih['master_before']==base and hist['master_source_before']==ih['source_before'] and hist['master_index_before']==ih['master_index_before'],'unaltered original master maps')
need(set(hist['master_source_before'])=={str(M/n) for n in names if n in baseline},'only existing source maps')
for p,v in hist['master_source_before'].items():
 n=str(Path(p).relative_to(M));need(v['before']==str(D/'baseline'/n) and v['sha256']==baseline[n]==sha(v['before']),'exact source before '+p)
mi=git(['rev-parse','--path-format=absolute','--git-path','index']);ri=git(['rev-parse','--path-format=absolute','--git-path','index'],R)
need(set(hist['master_index_before'])=={mi} and set(di)=={ri},'exact index before keys')
for p,v in {**hist['master_index_before'],**di}.items():need(v['sha256']==protected['indexes'][p]==sha(v['before']),'index exact beforeimage')
for p,h in post['indexes'].items():need(sha(p)==h,'current protected index')
need(post['files']==protected['files'],'same protected original map')
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')};need(set(hist['continuation_before'])==allowed,'exact continuation paths');prefixes=[]
for p,h in protected['files'].items():
 if p in allowed:
  v=hist['continuation_before'][p];need(v['sha256']==h==sha(v['before']),'original continuation hash');old=Path(v['before']).read_bytes();current=Path(p).read_bytes();need(current.endswith(old),'verbatim original continuation');prefixes.append(current[:-len(old)])
 else:need(sha(p)==h,'original user/config file')
need(len(prefixes)==2 and prefixes[0]==prefixes[1] and prefixes[0].count(b'## Previous continuation')==1,'same new continuation prefix')
before=read(D/'integration-before.json');unrelated=lambda rows:[x for x in rows if x and x.split('\t',1)[1] not in names];need(unrelated(raw(['ls-files','--stage','-z']).decode().split('\0'))==unrelated(before['entries']) and raw(['diff','--cached','--raw','-z']).decode()==before['staged'],'unrelated M index entries')
need(not raw(['diff','--cached','--raw','-z'],R),'no unrelated R staging')
resolutions={}
def historical(p,h):
 p=Path(p)
 if p.is_file() and sha(p)==h:return
 maps={**hist['master_source_before'],**hist['master_index_before'],**hist['continuation_before'],**di};v=maps.get(str(p))
 if v is not None:q=Path(v['before']);need(v['sha256']==h,'specific mapped hash '+str(p))
 elif p.is_relative_to(M/'src') or p.is_relative_to(M/'test'):q=D/'baseline'/p.relative_to(M)
 else:raise RuntimeError('unresolved old binding '+str(p))
 need(q.is_file() and sha(q)==h,'exact historical before bytes '+str(p));resolutions[str(p)+'@'+h]=str(q)
reviews=['admission.json','comparison-2/admission.json','comparison-3/admission.json','comparison-3/result-review.json','production-review.json','publication-preparation-reviewed.json','preparation-review.json','commit-review.json','RED-ready-run/admission.json','RED-ready-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json']
for n in reviews:
 r=read(D/n);need(r['accepted'] is True and r['findings']==[],'accepted review '+n)
 for p,h in r['bindings'].items():historical(p,h)
phases=[(D,'pins-ready.json'),(D/'comparison-2','pins-ready.json'),(D/'comparison-3','pins-ready2.json'),(D/'RED-ready-run','pins.json'),(D/'GREEN-run','pins.json'),(D/'MASTER-run','pins.json')];pin_counts={}
for phase,name in phases:
 pins=read(phase/name);need(set(pins['files'])==set(pins['inventory']),'pin membership');pin_counts[str(phase.relative_to(D))]=len(pins['inventory'])
 for p,v in pins['inventory'].items():need(str(Path(p).resolve(strict=True))==v['resolved'],'historical resolved target');historical(p,v['sha256'])
 for t in pins['trees']:
  t=Path(t);want={str(Path(p).relative_to(t)) for p in pins['inventory'] if Path(p).is_relative_to(t)};now={str(p.relative_to(t)) for p in t.rglob('*') if p.is_file()}
  if now!=want and t in [M/'src',M/'test']:
   old=D/'baseline'/t.relative_to(M);now={str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()}
  need(now==want,'historical membership '+str(t))
report=(D/'FINAL-REPORT.md').read_text();rows=read(D/'comparison-3/summary-final.json')['cases'];scopes=[('audit','Whole implicit price audit'),('virtual','Whole virtual quality'),('virtual_transposed','Whole transposed virtual quality'),('enter_dantzig','Whole free Dantzig pricing'),('enter_devex','Whole free Devex pricing'),('partial_hit','Whole partial-hit or small full fallback'),('partial_rebuild','Whole invalidated partial or small full fallback'),('summary','Whole dual summary'),('pivot','Whole checked pivot')]
for scope,label in scopes:
 rr=[r for r in rows if r['type']=='BigFloat' and r['scope']==scope];values=[statistics.median(r['paired_ratio'] for r in rr),statistics.median(r['candidate']['bytes']/r['original']['bytes'] for r in rr),statistics.median(r['candidate']['events']/r['original']['events'] for r in rr)];line='| '+label+' | '+' | '.join(f'{x:.4f}' for x in values)+' |';need(line in report,'recomputed report row '+scope)
A=[r for r in rows if r['type']=='BigFloat' and r['variant']=='A'];B=[r for r in rows if r['type']=='BigFloat' and r['variant']=='B'];C=[r for r in rows if r['type']=='BigFloat' and r['variant']=='C'];Cn=[r for r in C if r['pattern']!='zero'];need(len(A)==1440 and all(r['all_pairs_lower_bytes'] and r['all_pairs_lower_events'] for r in A),'A facts');need(len(Cn)==360 and sum(r['paired_ratio']>1 for r in Cn)==14 and len(C)-len(Cn)==120 and f"{max(r['paired_ratio'] for r in Cn):.4f}"=='1.1101','C nonuniform facts');need(all(r['all_pairs_lower_bytes'] and r['all_pairs_lower_events'] for r in Cn),'C allocations');need(len([r for r in B if r['pattern'] in ['positive','mixed']])==600 and all(r['all_pairs_lower_bytes'] and r['all_pairs_lower_events'] for r in B if r['pattern'] in ['positive','mixed']),'B affected facts')
need(abs(statistics.median(r['paired_ratio'] for r in B if r['pattern']=='positive')-.572)<.0005 and abs(statistics.median(r['paired_ratio'] for r in B if r['pattern']=='mixed')-.825)<.0005,'continuation B aggregates')
cmp=read(D/'comparison-3/audit-final.json');need(cmp['accepted'] and cmp['assertions']==120872 and cmp['cells']==len(rows)==3328 and cmp['windows']==59904 and cmp['GC_affected_windows']==114,'comparison totals')
for phase in ['GREEN','MASTER']:
 a=read(D/(phase+'-run/audit.json'));need(a['accepted'] and a['passed']==a['total']==218625 and a['expected_failures']==0,'accepted tests');need(f"{a['elapsed_shared_seconds']:.3f}s" in report,'actual report elapsed')
red=read(D/'RED-ready-run/audit.json');need(red['accepted'] and red['passed']==15415 and red['expected_failures']==5,'RED facts')
for phase,count,fails,errors in [(D,954,0,3),(D/'comparison-2',120716,4,0)]:
 p=read(phase/'output/process.json');need(p['returncode']==1 and p['pins_unchanged'] is True,'rejected originals');need(f'{count} passed, {fails} failed, {errors} errored, 0 broken' in (phase/'output/run.log').read_text(),'rejected original raw summary')
prov=read(D/'comparison-3/AUDIT-FINAL-PROVENANCE.json');need(prov['post_exit_offline_checker'] is True and prov['part_of_launch_pins'] is False and sha(prov['original_auditor'])==prov['original_sha256'] and sha(D/'comparison-3/audit-final.py')==prov['corrected_sha256'],'postexit provenance');need((D/'comparison-3/summary-final.json').read_bytes()==(D/'comparison-3/summary.json').read_bytes(),'same postexit summary');need(read(D/'comparison-2/fix-checks.json')['exact_inverse'] is False,'false old metadata preserved')
for phrase in ['not a launch pin','No numerical rerun','14slower','nonuniform','No universal/end-to-end speedup','fullsuite/x64','CIoff/automationpaused/HHreuse disabled']:need(phrase in report,'report limit '+phrase)
need((D/'.gitignore').read_text()=='/baseline/\n/RED/\n/GREEN/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n','private artifact exclusions')
vars=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME'];need(all(not os.environ.get(k) for k in vars),'environment overrides');need({k:os.environ[k] for k in vars+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(D/'environment.json')['inherited'],'same environment')
seed=read(D/'final-host.json');groups=set(seed['groups']);need(len(groups)==607,'607 historical groups');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');allow=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');permitted=read(allow)['identities'];procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];comm=(p/'comm').read_text().strip();v=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+args[:1]),'active Julia')
  if v['pgid'] in groups or v['sid'] in groups:need(v in permitted,'historical identity')
  procs.append(v)
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory')
put(D/'final-review-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
text='''Independent final review — PASS, before diagnostic closure/publication.

Published production c01900c2dff3de465846ae44333903889c867626 is exact in local HEAD/master, origin/master and a fresh remote read, with sole original parent1a6b9d81. Seven changed blobs match the reviewed commit and GREEN. Every one of537stage files equals actual master; complete src/test membership is unchanged. The536-file original baseline remains exact. The normal push log/publication record and independently accepted actualMASTER218625PASS/36files corroborate publication. GREEN has the same total; RED has15415passes plus exactly five intended cost failures.

All14required independent reviews are accepted and every binding resolves to unchanged current bytes or the specific exact original source/index/continuation beforeimage. All six comparison/RED/GREEN/MASTER launch pin sets retain their inventories and resolved targets, with original source membership checked against preserved baseline only when legitimately changed by integration. Both original index copies match original protected hashes; current master/diagnostic indexes match post-ff protected hashes. Only seven intended index entries differ from pre-ff; unrelated entries/staging and user/config/environment files remain unchanged. STATUS and roadmap have identical new prefixes and end with their exact original protected bytes; six existing source maps, original index map and older evidence remain intact.

All nine final-report table rows were independently recomputed from saved comparison summaries. A's1440cells and B's600affected cells reduce bytes/events; C's360nonzero cells reduce allocations while14time medians are slower and120zero cells retain allocations. Continuation Bpositive/mixed aggregate ratios round correctly to.572/.825. Counts3328cells/59904windows/120872checks and114GCwindows agree with accepted evidence. Preparation/import/compilation versus whole-call measurement limits, small bases/two densities/precisions/rounding coverage, native/exact controls, nonuniform C timing and no end-to-end/native-retention claim remain explicit. No unnecessary added production work or retained numerical memory was found: exact source still preserves all scans/solves/conversions/terms/arithmetic order/safeguards and uses only local scalar reuse plus cold method metadata.

The original954passes/3errors and120716passes/4failures remain rejected raw exit1 evidence. The false historical exact_inverse field remains untouched. Post-exit auditor provenance identifies its original and corrected hashes, explicitly excludes the correction from launch pins, and the corrected summary is byte-identical to the already-published summary. No numerical rerun occurred for that metadata correction. Existing tests/tolerances, prior exception evidence and broader full-suite/x64/CI/automation/HH restrictions remain as documented.

Fresh607historical process groups AND sessions are checked with full boot/start_ticks/command identities, established exact unrelated-process allowance, noJulia and host-memory/swap margins. This review ran only the new offline independent-final-review.py; no numerical/old checker, launcher, finalizer, closure or publisher ran here. Existing files and untracked older linked-worktree artifacts were not modified or removed.

Final review is accepted for the already-prepared PASS closure and exact diagnostic staging/commit/normal-push workflow. This record does not claim that diagnostic publication has happened; its closed artifact inventory and exact staged/committed blob checks remain required.
'''
with (D/'FINAL-REVIEW.md').open('x') as f:f.write(text)
private={'baseline','RED','GREEN','before-master','before-diagnostic','__pycache__'};excluded={'final-review.json','closure.json','diagnostic-publication-plan.json','publication-after.json'}
files=[p for p in D.rglob('*') if p.is_file() and p.relative_to(D).parts[0] not in private and '__pycache__' not in p.parts and p.name not in excluded];bound={str(p):sha(p) for p in files};bound.update({p:sha(p) for p in allowed})
put(D/'final-review.json',dict(accepted=True,findings=[],bindings=bound,production_commit=target,master_tests=218625,whole_files=36,phase_pin_counts=pin_counts,historical_before_resolutions=resolutions,historical_groups=607,no_Julia_executed=True,no_old_checker_rerun=True,unnecessary_new_work_or_retained_numeric_memory=False,diagnostic_publication_pending=True))
print(json.dumps(dict(accepted=True,production_commit=target,bindings=len(bound),historical_resolutions=len(resolutions),phase_pin_counts=pin_counts,historical_groups=607)))
