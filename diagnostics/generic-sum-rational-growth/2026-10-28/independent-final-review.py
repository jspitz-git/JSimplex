from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime,re,statistics
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];S=D/'GREEN';BASE='ce5d4a74019e0dc2e656d08161641c498b159e7b';TARGET='bb765d008c6e8aab6187aa0ea49d49a4f8a03309';DIAG='c01e9376bdbcda7cb54ba55735cf053299b9af45';os.environ['GIT_OPTIONAL_LOCKS']='0'
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
cache={}
def sha(p):
 p=str(p)
 if p not in cache:
  with Path(p).open('rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def save(p,s):
 with Path(p).open('x') as f:f.write(s)
def put(p,v):save(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
def git(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a])
def g(a,root=M):return git(a,root).decode().strip()
script=D/'independent-final-review.py';save(script,Path(__file__).read_text())
co=read(D/'production-commit.json');pub=read(D/'publication.json');hist=read(D/'historical-path-map.json');integration=read(D/'integration-historical-path-map.json');base=read(D/'baseline-tree.json');protected=read(D/'protected-before.json');di=read(D/'diagnostic-index-before.json');names=co['names']
need(co['commit']==TARGET and co['parent']==BASE and co['names']==['src/dual_simplex.jl','src/factorization.jl','test/generic_sum_rational_growth_tests.jl','test/runtests.jl'],'exact production metadata')
need(pub['accepted'] is True and pub['normal_nonforce_push'] is True and pub['commit']==pub['local_master']==pub['tracking']==pub['remote_master']==TARGET and pub['master_tests']==345121 and pub['names']==names,'publication metadata')
need(g(['rev-parse','HEAD'])==g(['rev-parse','master'])==g(['rev-parse','origin/master'])==g(['ls-remote','origin','refs/heads/master']).split()[0]==TARGET,'actual published local/tracking/remote refs')
need(g(['rev-list','--parents','-n','1',TARGET]).split()==[TARGET,BASE] and g(['rev-parse',TARGET+'^{tree}'])==co['tree'],'actual sole parent/tree')
need(g(['rev-parse','HEAD'],R)==DIAG==g(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],R).split()[0],'diagnostics remain unpublished baseline')
need(g(['branch','--show-current'])=='master' and g(['branch','--show-current'],R)=='codex/simplex-core-architecture','expected branches')
need(g(['remote','get-url','--push','--all','origin'])=='git@github.com:jspitz-git/JSimplex.git','exact production endpoint')
need(not g(['diff','--name-only','HEAD','--','src','test','Project.toml']),'no production drift')
need(g(['diff-tree','--no-commit-id','--name-only','-r',BASE,TARGET]).splitlines()==names,'exact four production paths')
mi=g(['rev-parse','--path-format=absolute','--git-path','index']);ri=g(['rev-parse','--path-format=absolute','--git-path','index'],R)
need(hist['master_before']==integration['master_before']==BASE and hist['master_source_before']==integration['source_before'] and hist['master_index_before']==integration['master_index_before'],'exact historical map preservation')
expected={str(M/n):n for n in names if n in base};need(set(hist['master_source_before'])==set(expected),'exact three old source map keys')
for path,n in expected.items():
 v=hist['master_source_before'][path];need(v['before']==str(D/'baseline'/n) and v['sha256']==base[n]==sha(v['before']),'exact baseline beforeimage '+path)
need(set(hist['master_index_before'])=={mi},'only original main index mapping');v=hist['master_index_before'][mi];need(v['before']==str(D/'before-master/master.index') and v['sha256']==protected['indexes'][mi]==sha(v['before']),'exact original main index bytes')
need(set(di)=={ri} and di[ri]['before']==str(D/'before-diagnostic/diagnostic.index') and di[ri]['sha256']==protected['indexes'][ri]==sha(di[ri]['before'])==sha(ri),'exact untouched diagnostic index')
continuations={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):'STATUS.md',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):'roadmap.md'}
need(set(hist['continuation_before'])==set(continuations),'only two continuation changes');prefixes=[]
for path,n in continuations.items():
 entry=hist['continuation_before'][path];need(entry['before']==str(D/'continuation-before'/n) and entry['sha256']==protected['files'][path]==sha(entry['before']),'exact continuation beforeimage '+path)
 old=Path(entry['before']).read_bytes();current=Path(path).read_bytes();need(current.endswith(old) and len(current)>len(old),'verbatim preserved suffix '+path);prefixes.append(current[:-len(old)])
need(prefixes[0]==prefixes[1],'same actual continuation prefix');prefix=prefixes[0].decode();need(TARGET in prefix and 'FinalPASSclosure and exactdiagnosticpublication outcomes are recorded by canonical output files' in prefix,'precise continuation status')
for path,h in protected['files'].items():
 if path not in continuations:need(sha(path)==h,'protected file unchanged '+path)
for path,h in read(D/'MASTER-run/protected-before.json')['indexes'].items():need(sha(path)==h,'current protected index unchanged '+path)
need(set(base)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()},'complete baseline membership')
for n,h in base.items():need(sha(D/'baseline'/n)==h,'baseline bytes '+n)
inv=read(D/'source-inverse.json');need(set(inv['whole_stage'])=={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()},'whole tested stage membership')
for n,h in inv['whole_stage'].items():need(sha(S/n)==sha(M/n)==h,'entire live/tested source/test/environment '+n)
for sub in ['src','test']:need({str(p.relative_to(M)) for p in (M/sub).rglob('*') if p.is_file()}=={str(p.relative_to(S)) for p in (S/sub).rglob('*') if p.is_file()},'actual/tested complete membership '+sub)
# Actual commit membership and all production blobs, including unchanged files.
commit_entries={}
for entry in git(['ls-tree','-r','-z',TARGET,'--','src','test']).split(b'\0'):
 if entry:
  meta,path=entry.split(b'\t',1);mode,kind,blob=meta.decode().split();path=path.decode();data=(M/path).read_bytes();need(mode=='100644' and kind=='blob' and blob==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),'actual committed live blob '+path);commit_entries[path]=blob
need(set(commit_entries)=={str(p.relative_to(M)) for sub in ['src','test'] for p in (M/sub).rglob('*') if p.is_file()},'actual commit/live complete membership')
for name in names[:2]:
 text=(M/name).read_text()
 for ch in reversed(read(D/'changes.json')):
  if ch['file']==name:need(text.count(ch['new'])==1,'exact numerical replacement');text=text.replace(ch['new'],ch['old'])
 need(text==(D/'baseline'/name).read_text(),'actual production inverse '+name)
# Historical hashes resolve only to explicitly checked exact beforeimages.
allowed_before={**hist['master_source_before'],**hist['master_index_before'],**hist['continuation_before'],**di};used={}
def bound(path,h):
 if sha(path)==h:return
 need(path in allowed_before,'unmapped historical binding '+path);v=allowed_before[path];need(v['sha256']==h and sha(v['before'])==h,'exact mapped historical binding '+path);used[path+'@'+h]=v['before']
reviews=['admission-ready.json','correctness-qualification/admission.json','correctness-qualification/result-review.json','cost-qualification-review.json','cost-audit-recovery-review.json','result-review.json','production-review.json','publication-preparation-reviewed.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','finalization-preparation-review.json']
for name in reviews:
 r=read(D/name);need(r['accepted'] is True and r['findings']==[],'accepted independent review '+name)
 for path,h in r['bindings'].items():bound(path,h)
manifest_paths=[D/n for n in ['pins.json','pins-reviewed.json','pins-ready.json']]+[D/n/'pins.json' for n in ['correctness-qualification','RED-run','GREEN-run','MASTER-run']];pin_counts={}
for manifest in manifest_paths:
 pins=read(manifest);need(set(pins['files'])==set(pins['inventory']),'pin membership '+str(manifest));pin_counts[str(manifest)]=len(pins['inventory'])
 for path,v in pins['inventory'].items():need(str(Path(path).resolve(strict=True))==v['resolved'],'historical resolution '+path);bound(path,v['sha256'])
 for root in pins['trees']:
  root=Path(root);expected={str(Path(p).relative_to(root)) for p in pins['inventory'] if Path(p).is_relative_to(root)};actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
  if actual!=expected:
   need(root in [M/'src',M/'test'],'unexpected historical tree drift');old=D/'baseline'/root.relative_to(M);need(expected=={str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()},'exact old tree membership')
need(pin_counts[str(D/'GREEN-run/pins.json')]==1346 and pin_counts[str(D/'MASTER-run/pins.json')]==838,'current pin counts')
need(read(D/'admission.json')['accepted'] is False and read(D/'admission-reviewed.json')['accepted'] is False and read(D/'finalization-preparation-initial-review.json')['accepted'] is False,'all preserved initial rejections')
initial=read(D/'finalization-preparation-initial-review.json')
for path,h in initial['bindings'].items():bound(path,h)
original=read(D/'output/process.json');need(original['returncode']==1 and original['pins_unchanged'] is True and read(D/'supervisor.json')['accepted'] is False and not (D/'completed.json').exists(),'original failed run unchanged')
raw=(D/'output/run.log').read_text();need(re.search(r'^Sum rational growth whole-function comparison\s*\|\s*111259\s+90\s+111349\s+',raw,re.M) and raw.count('Test Failed at ')==90,'raw original111259+90')
qualified=read(D/'correctness-qualification/audit.json');need(qualified['accepted'] is True and qualified['assertions']==28227 and qualified['measured_windows']==0,'corrected qualification scope')
need(re.search(r'^SRG corrected exact-decoder qualification\s*\|\s*28227\s+28227\s+', (D/'correctness-qualification/output/run.log').read_text(),re.M),'raw corrected qualification count')
red=read(D/'RED-run/audit.json');need((red['passed'],red['expected_failures'],red['total'])==(28316,7,28323),'RED unchanged exact count')
green=read(D/'GREEN-run/audit.json');master=read(D/'MASTER-run/audit.json');gc=read(D/'GREEN-run/contract.json');mc=read(D/'MASTER-run/contract.json');need(gc['files']==mc['files'] and len(gc['files'])==57 and mc['expected_total']==345121,'same57 and frozen actual total')
for phase,audit in [('GREEN',green),('MASTER',master)]:
 need(audit['accepted'] is True and audit['passed']==audit['total']==345121 and audit['expected_failures']==0 and audit['elapsed_shared_seconds']<=3000,'actual all-pass '+phase)
 log=(D/(phase+'-run/output/run.log')).read_text();need(re.findall(r'^INCLUDING (.*)$',log,re.M)==gc['files'] and re.search(r'^Sum rational growth '+phase+r'\s*\|\s*345121\s+345121\s+',log,re.M) and re.findall(r'^SRG_COMPLETED (.*)$',log,re.M)==[phase] and not re.search(r'Test Failed at |Error During Test|^ERROR:',log,re.M),'raw whole test evidence '+phase)
 source=S if phase=='GREEN' else M;need(re.findall(r'^SRG_SOURCE (.*)$',log,re.M)==[str(source/'src/JSimplex.jl')],'actual raw source '+phase)
 process=read(D/(phase+'-run/output/process.json'));need(process['returncode']==0 and process['pins_unchanged'] is True and read(D/(phase+'-run/completed.json'))['accepted'] is True,'raw completion '+phase)
cost=read(D/'audit-qualified.json');need(cost['accepted'] is True and cost['original_run_accepted'] is False and (cost['cases'],cost['windows'],cost['preparation'],cost['gc_windows'])==(2636,47448,2674,22),'qualified unchanged costs')
rejection=read(D/'cost-audit-host-rejection.json');need(rejection['accepted_output_written'] is False and rejection['failed_occupant_not_captured'] is True and 'unknown' in rejection['occupant_cause'],'unknown rejected-host cause preserved')
report=(D/'FINAL-REPORT.md').read_text();rows=read(D/'summary-qualified.json');need(len(rows)==2636,'all summary cells')
scopes=[('BigFloat','A','rows','BigFloat complete row intervals'),('BigFloat','A','feasible','BigFloat original-model primal feasibility'),('Rational{BigInt}','B','cert','Rational{BigInt} whole infeasibility certificate'),('BigFloat','C','growth','BigFloat PFI growth measurement'),('BigFloat','C','refresh','BigFloat full forced metric refresh'),('BigFloat','C','scheduled','BigFloat full scheduled refactor reason')]
for typ,arm,scope,label in scopes:
 rr=[v for v in rows if v['type']==typ and v['variant']==arm and v['scope']==scope];line='| '+label+' | '+str(len(rr))+' | '+' | '.join(f'{statistics.median(v[k]["paired_median"] for v in rr):.6f}' for k in ['seconds','bytes','events'])+' |';need(line in report,'independently recomputed final table '+label)
for text in [TARGET,BASE,'about1.699x with no in-window GC','540 empty-chain','all1,080 nonempty-chain','nine Rational{BigInt}','original run remains failed','zero measurement windows','Outer driver/startup work and a complete per-variant cold-specialization budget remain incompletely measured','full cold cost and retention were not separately measured','native retention remains unqualified','occupant identity/cause was not captured and remains unknown','PID reuse is only a hypothesis','did not relabel the original numerical run as passing or introduce a PID exception','Final acceptance additionally requires PASS closure.json','recorded separately in publication-after.json']:
 need(text in report,'actual final limitation/provenance '+text)
need(f"elapsed{red['elapsed_shared_seconds']:.3f}s" in report and f"elapsed{green['elapsed_shared_seconds']:.3f}/{master['elapsed_shared_seconds']:.3f}s" in report,'actual displayed phase timings')
need('each345121PASS in the same57wholefiles' in prefix and 'GREEN/MASTER345121PASS57files' in (D/'progress-final.md').read_text(),'actual continuation/progress totals')
for absent in ['closure.json','diagnostic-publication-plan.json','publication-after.json']:need(not (D/absent).exists(),'future closure/publication not yet claimed '+absent)
# Fresh complete no-Julia host closure; do not reuse any existing observer.
seed=read(D/'MASTER-run/host-seed.json');groups=set(seed['groups'])
for p in D.rglob('output/process.json'):
 process=read(p)
 for role in ['runner','child']:
  for key in ['pgid','sid']:groups.add(process[role][key])
need(len(groups)==659 and groups==set(read(D/'final-host.json')['groups']),'all659 actual historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'same boot');allow=D.parents[1]/'generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed unrelated allowance');permitted=read(allow)['identities'];procs=[];allowed=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  stat=(proc/'stat').read_text().rsplit(')',1)[1].split();command=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();ident=dict(pid=int(proc.name),pgid=int(stat[2]),sid=int(stat[3]),start_ticks=int(stat[19]),boot_id=boot,command=command)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+command[:1]),'no active Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in permitted,'historical occupancy '+str(ident));allowed.append(ident)
  procs.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'fresh resource headroom')
overrides=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME'];need(all(not os.environ.get(x) for x in overrides),'environment override');need({k:os.environ[k] for k in overrides+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(D/'environment.json')['inherited'],'exact inherited environment')
put(D/'independent-final-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,allowed_seen=allowed,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],observer_pid=os.getpid(),observer_parent_pid=os.getppid(),observer_command=sys.argv,refs=dict(master=TARGET,tracking=TARGET,remote_master=TARGET,diagnostic=DIAG)))
put(D/'independent-final-historical-check.json',dict(accepted=True,pinsets=pin_counts,exact_before_resolutions=used,exact_continuation_paths=sorted(continuations),master_before=BASE,production_commit=TARGET,whole_live_tested_source_verified=True))
md='''# Independent final actual-output review

Accepted actual final report, progress record, continuation prefixes and publication evidence for canonical closure-reviewed.py and diagnostic-publish.py. Production bb765d008c6e8aab6187aa0ea49d49a4f8a03309 is the verified local master, tracking master and remote master, with sole parent ce5d4a74019e0dc2e656d08161641c498b159e7b and exactly the reviewed four changed paths. Complete committed/live/tested source and test membership and every blob agree; the complete542-file stage including environment matches actual master. No production drift or unrelated protected-file/index change was found.

GREEN and actual MASTER each passed345,121/345,121 ordinary assertions in the same57 complete files; actual raw source identities, ordered includes, all-pass root summaries and completion markers agree with the accepted reviews. The observed GREEN total was frozen in the actual-master contract. Inclusive elapsed times are1927.950752 and1903.905232 seconds, each within the shared3000-second limit. Original RED remains28,316 passes plus exactly seven allocation failures. The original comparison remains failed at111,259 passes plus90 decoder assertions; its raw log, failed process/supervisor and absent completed record remain intact. The separate corrected qualification remains28,227 assertions and zero measurement windows. Qualified saved costs remain2636 cells,47448 windows,2674 preparation entries and22 GC windows without a measurement repeat.

Every final report table ratio was independently recomputed from the unchanged qualified summary. They are medians of cell-level paired ratios, not pooled or end-to-end speedups. The report retains four slower A cells including the1.699x/no-window-GC outlier, nine unchanged rational control byte differences with unassigned cause, C540 empty and1080 active whole-call cells, and all GC evidence. Recorded preparation/compilation is separated; outer startup, complete per-variant cold specialization metadata and native retention remain incompletely measured. Whole-call closure overhead is included, but no native-free, universal, full-solver, large-scale, x64 or full-suite claim is made. The strict postexit host rejection still has unknown occupant/cause; PID reuse remains a hypothesis and no exception was added.

Numerical source review remains sound on the actual published bytes. A changes only the reached same-sign cancellation exclusion; zero/finite/precision gates, opposite-sign arithmetic, FastTwoSum, underflow safeguards and enclosures are retained. B preserves exact CSC accumulation, allowances, selected-bound checks and exception semantics while using read-only unit orientation only for RationalBigInt; floating and fixed-width paths remain. C preserves explicit-init left-fold maxima, mixed-precision/NaN/Inf/tie ownership, storage counting, recovery precision, scheduling cache/age gates and reason priority. No unnecessary added full scan, basis solve, copy, conversion pass, persistent numerical cache or retained numerical buffer was found. A adds constant sign checks, B removes unit products without an oriented vector, and C retains O(chain length+packed entries) work while reducing constructors/discarded negations. Two new specializations retain unmeasured cold compiler costs; numerical safeguards have not been traded for timing results.

All seven original/current pinsets were independently checked using current hashes or exact explicitly validated beforeimages; no pin was rewritten. Historical map keys, old master ref, original source/index paths and hashes match the integration map exactly. Current master and diagnostic indexes match their protected states. Only the two authorized continuation paths change, each with the same new prefix and a byte-exact original suffix; all other protected user/environment/older evidence remains unchanged. Initial rejected finalizer/closure drafts and the three-finding preparation rejection remain preserved. Canonical finalize-reviewed.py/closure-reviewed.py/diagnostic-publish.py still match accepted preparation bindings. The report correctly leaves PASS closure and exact diagnostic publication as required canonical outputs rather than claiming they already exist.

Fresh independent host checks cover all659 historical groups AND sessions, exact boot/start_ticks/commands, the existing fixed unrelated identity allowance, no Julia and resource headroom. This reviewer ran only new exclusive offline checks and read-only Git/host operations; no Julia, old script/import/rerun, measurement repeat, Git mutation or publication occurred. Actual final artifacts are accepted. The parent may now run canonical closure once, then the exact diagnostic publisher after PASS closure; final staged/committed names and blobs including the publication plan and remote result must pass that publisher's checks. Diagnostic publication itself is not claimed here. CI/automation/HH state and broader/full-suite/x64/native-retention scope remain as recorded.
'''
reportpath=D/'FINAL-REVIEW.md';save(reportpath,md)
paths=[script,reportpath,D/'independent-final-host.json',D/'independent-final-historical-check.json']+[D/n for n in reviews]+manifest_paths+[D/n for n in ['FINAL-REPORT.md','progress-final.md','historical-path-map.json','integration-historical-path-map.json','diagnostic-index-before.json','production-commit.json','publication.json','source-inverse.json','baseline-tree.json','protected-before.json','final-host.json','finalize-reviewed.py','closure-reviewed.py','diagnostic-publish.py','finalization_checks.py','publication_checks.py','finalization-preparation-initial-review.json','finalize.py','closure.py','audit-qualified.json','summary-qualified.json','output/run.log','output/results.toml','output/process.json','supervisor.json','correctness-qualification/audit.json','correctness-qualification/output/run.log','RED-run/audit.json','GREEN-run/audit.json','MASTER-run/audit.json','cost-audit-host-rejection.json','push.log']]+[Path(p) for p in continuations]+[Path(v['before']) for v in hist['continuation_before'].values()]+[M/n for n in names]
put(D/'final-review.json',dict(accepted=True,findings=[],production_commit=TARGET,parent=BASE,passed=345121,whole_files=57,pinsets=7,historical_groups_and_sessions=659,numerical_correctness_reviewed=True,unnecessary_work_or_memory_found=False,exact_historical_maps_and_continuations=True,actual_published_production_verified=True,canonical_closure_authorized=True,diagnostic_publication_requires_PASS_closure=True,diagnostic_publication_claimed=False,Julia_executed=False,Git_mutated=False,old_scripts_executed=False,bindings={str(p):sha(p) for p in sorted(set(paths))}))
print(json.dumps(dict(accepted=True,production_commit=TARGET,passed=345121,whole_files=57,pinsets=7,historical_groups_and_sessions=659,exact_historical_resolutions=len(used),Julia_executed=False,Git_mutated=False)))
