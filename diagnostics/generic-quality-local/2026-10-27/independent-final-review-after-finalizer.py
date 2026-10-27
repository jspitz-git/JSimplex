"""NEW offline checker. Run once, only after actual MASTER acceptance, normal push and finalizer."""
from pathlib import Path
import ast,datetime,hashlib,json,os,re,subprocess,sys
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
if sys.argv[1:]!=['--after-finalizer']:raise SystemExit('Explicit --after-finalizer required; never run during MASTER.')
required=['MASTER-run/result-review.json','MASTER-run/completed.json','publication.json','historical-path-map.json','diagnostic-index-before.json','FINAL-REPORT.md','final-host.json']
if not all((D/n).is_file() for n in required):raise SystemExit('Finalization prerequisites absent; no host/remote check performed.')
OUT=D/'independent-final-review-evidence.json'
if OUT.exists():raise SystemExit('Evidence already exists: never rerun or overwrite this completed checker.')
os.environ['GIT_OPTIONAL_LOCKS']='0';cache={};checks=[];historical={}
def sha(p):
 p=str(p)
 if p not in cache:cache[p]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
 return cache[p]
def read(n):return json.loads((D/n).read_text())
def need(v,s):
 if not v:raise AssertionError(s)
def git(*a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a])
def g(*a,root=M):return git(*a,root=root).decode().strip()
co=read('production-commit.json');target=co['commit'];base=co['parent'];hist=read('historical-path-map.json');di=read('diagnostic-index-before.json');protected=read('protected-before.json');prep=read('preparation-review.json')
need(target=='1a6b9d81e89b44c5c75b95b6c92e0916c2d19730' and base=='ca64312f7f74b1d7bec047718399f229674b3e1d','exact reviewed production commit/base')
need(prep['accepted'] is True and prep['findings']==[],'preparation acceptance')
need(read('MASTER-run/result-review.json')['accepted'] is True and read('MASTER-run/result-review.json')['findings']==[],'actual MASTER independent acceptance')
need(read('publication.json')['accepted'] is True and read('publication.json')['commit']==target and read('publication.json')['normal_nonforce_push'] is True,'normal production publication')
need(g('rev-parse','HEAD')==g('rev-parse','master')==g('rev-parse','origin/master')==target,'master refs')
need(g('rev-list','--parents','-n','1',target).split()==[target,base],'sole parent')
remote=dict((ref,h) for h,ref in (line.split() for line in g('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines()))
need(remote['refs/heads/master']==target,'remote production')
need(remote['refs/heads/codex/simplex-core-architecture']==g('rev-parse','HEAD',root=R)==read('host-before.json')['diagnostic_head'],'diagnostic ref still original')
need(g('remote','get-url','--push','--all','origin')=='git@github.com:jspitz-git/JSimplex.git','approved push endpoint')
need(not git('diff','--cached','--raw','-z',root=R),'no diagnostic staging yet');checks.append('exact local/remote production and unchanged diagnostic refs; sole parent; normal production publication')
def resolve(p,h):
 if sha(p)==h:return p
 if p in hist['continuation_before']:q=hist['continuation_before'][p]['before']
 elif p in hist['master_index_before']:q=hist['master_index_before'][p]['before']
 elif p in di:q=di[p]['before']
 else:
  need(Path(p).is_relative_to(M/'src') or Path(p).is_relative_to(M/'test'),'unmapped historical path '+p);q=str(D/'baseline'/Path(p).relative_to(M))
 need(sha(q)==h,'historical hash '+p);historical[p+'@'+h]=q;return q
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')};need(set(hist['continuation_before'])==allowed,'exact continuation mapping')
for p,h in protected['files'].items():
 q=resolve(p,h)
 if p in allowed:
  entry=hist['continuation_before'][p];need(entry['sha256']==h and q==entry['before'],'old continuation mapping')
  old=Path(q).read_bytes();live=Path(p).read_bytes();need(len(live)>len(old) and live.endswith(old),'verbatim old continuation suffix')
  prefix=live[:-len(old)].decode();need(target in prefix and '203205PASS/35wholefiles' in prefix and 'REJECTED' in prefix and 'CIoff/automationpaused/HHdisabled' in prefix and 'broader/fullsuite/x64/native-retention OPEN' in prefix,'prefix scope/counters')
 else:need(q==p,'unrelated protected file changed')
for p,h in read('MASTER-run/protected-before.json')['indexes'].items():need(sha(p)==h,'current protected index')
previous=read('integration-historical-path-map.json');need(hist['master_before']==base and hist['master_source_before']==previous['source_before'] and hist['master_index_before']==previous['master_index_before'],'original integration maps retained')
for p,v in hist['master_index_before'].items():need(sha(v['before'])==v['sha256']==protected['indexes'][p],'original master index preserved')
ri=g('rev-parse','--path-format=absolute','--git-path','index',root=R);need(set(di)=={ri} and di[ri]['sha256']==sha(di[ri]['before'])==sha(ri)==protected['indexes'][ri],'original diagnostic index preserved')
need(set(g('diff','--name-only','HEAD',root=R).splitlines())=={str(Path(p).relative_to(R)) for p in allowed},'only two tracked diagnostic continuation edits');checks.append('protected userfiles/environment/current indexes and exact source/index/continuation beforeimages')
reviews=['admission.json','comparison-2/admission.json','comparison-2/result-review.json','production-review.json','production-review-count-clarification.json','publication-preparation-reviewed.json','preparation-review.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json'];binding_count=0
for n in reviews:
 a=read(n);need(a['accepted'] is True and a['findings']==[],'review '+n)
 for p,h in a['bindings'].items():resolve(p,h);binding_count+=1
rejected=read('result-review.json');need(rejected['accepted'] is False,'original result rejection remains');need(read('output/process.json')['returncode']==1 and read('output/process.json')['pins_unchanged'] is True,'original failed process preserved')
for p,h in rejected['bindings'].items():resolve(p,h)
need(read('comparison-2/result-review.json')['accepted'] is True and read('comparison-2/audit.json')['assertions']==63391,'corrected comparison accepted separately')
checks.append('all independent accepted review chains bound; original comparison explicitly rejected and corrected comparison accepted')
phasecounts={}
for phase in [D,D/'comparison-2',D/'RED-run',D/'GREEN-run',D/'MASTER-run']:
 pins=json.loads((phase/'pins.json').read_text());need(set(pins['files'])==set(pins['inventory']),'inventory membership');phasecounts[str(phase.relative_to(D))]=len(pins['inventory'])
 for p,v in pins['inventory'].items():need(str(Path(p).resolve(strict=True))==v['resolved'],'path resolution '+p);resolve(p,v['sha256'])
 for tree in map(Path,pins['trees']):
  expected={str(Path(p).relative_to(tree)) for p in pins['inventory'] if Path(p).is_relative_to(tree)};actual={str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file()}
  if actual!=expected:
   need(tree in [M/'src',M/'test'],'unexpected changed historical tree');bt=D/'baseline'/tree.relative_to(M);actual={str(p.relative_to(bt)) for p in bt.rglob('*') if p.is_file()}
  need(actual==expected,'historical tree membership')
need(phasecounts=={'.':1224,'comparison-2':1251,'RED-run':1226,'GREEN-run':1229,'MASTER-run':697},'expected five phase inventories')
baseline=read('baseline-tree.json');need(set(baseline)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()},'baseline membership')
for n,h in baseline.items():need(sha(D/'baseline'/n)==h,'baseline '+n)
checks.append('all five phase inventories/resolved paths/tree memberships and full baseline verified')
files=g('ls-tree','-r','--name-only',target,'--','src','test').splitlines();need(len(files)==533,'533 source-test objects')
for tree in ['src','test']:need({str(p.relative_to(M)) for p in (M/tree).rglob('*') if p.is_file()}=={n for n in files if n.startswith(tree+'/')},'actual source membership')
for n in files:need(git('show',target+':'+n)==(M/n).read_bytes()==(D/'GREEN'/n).read_bytes(),'committed/tested/current '+n)
need(g('diff-tree','--no-commit-id','--name-only','-r',target).splitlines()==read('source-inverse.json')['names']==co['names'],'exact four changed paths')
for n,h in read('source-inverse.json')['candidate_sha256'].items():need(sha(M/n)==h,'source inverse binding')
need((M/'test/generic_dual_comparisons_tests.jl').read_bytes()==(D/'baseline/test/generic_dual_comparisons_tests.jl').read_bytes(),'prior Rational test unchanged');checks.append('all533 source-test commit/current/GREEN bytes and exact four paths; previous gate unchanged')
red=read('RED-run/audit.json');need(red['accepted'] and red['passed']==16579 and red['expected_failures']==4 and red['total']==16583,'RED precise cost witness')
sequences=[]
for arm in ['GREEN','MASTER']:
 a=read(arm+'-run/audit.json');r=read(arm+'-run/result-review.json');contract=read(arm+'-run/contract.json');raw=(D/(arm+'-run/output/run.log')).read_text()
 need(a['accepted'] is True and r['accepted'] is True and a['passed']==a['total']==r['passed']==r['total']==203205 and a['expected_failures']==0,'allpass '+arm)
 headers=[s for s in raw.splitlines() if s.startswith('Test Summary:')];need(len(headers)==1 and headers[0].split('|')[1].split()==['Pass','Total','Time'],'ordinary root schema '+arm)
 roots=[s for s in raw.splitlines() if s.startswith('Local quality '+arm) and '|' in s];need(len(roots)==1 and roots[0].split('|')[1].split()[:2]==['203205','203205'],'ordinary exact total '+arm)
 need(not re.search(r'^ERROR:|Test Failed at |Error During Test',raw,re.M),'runtime Test error '+arm)
 need(raw.count('LOCAL_QUALITY_COMPLETED '+arm)==1,'unique completion '+arm)
 inc=re.findall(r'^INCLUDING (.+)$',raw,re.M);need(inc==contract['files'] and len(inc)==len(set(inc))==35,'35 ordered whole files '+arm);sequences.append(inc)
 need('LOCAL_QUALITY_SOURCE '+contract['source_root']+'/src/JSimplex.jl' in raw,'actual runtime source '+arm)
 proc=read(arm+'-run/output/process.json');need(proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] is True,'successful process '+arm)
 completed=read(arm+'-run/completed.json');need(completed['accepted'] is True and completed['elapsed_shared_seconds']==a['elapsed_shared_seconds']<=completed['limit_seconds'],'inclusive admitted deadline '+arm)
need(sequences[0]==sequences[1] and 186622+16583==203205,'same complete qualification and exact count sum')
need(sha(M/'test/generic_quality_local_tests.jl')=='12c0b1a8d0be69095f9588fa3057ee0d86b31bf0efbb0e8f11492898aaf139ce','unchanged four whole-call gates')
checks.append('RED16579+4 and ordinary GREEN/MASTER203205 each, same35 files, frozen gate source, completion/exit/deadlines')
provenance=read('GREEN-run/checker-failure-evidence.json');need(provenance['accepted'] is False and 'reconstructed' in provenance['original_first_source_preservation'],'honest parser provenance')
for version,name in [('v1','independent-result-check-v1-reconstructed.py'),('v2','independent-result-check-v2-preserved.py'),('v3','independent-result-check-v3.py')]:need(sha(D/'GREEN-run'/name)==provenance[version+'_sha256'],'preserved parser '+version)
checks.append('GREEN parser failures/reconstruction/snapshot/v3 preserved honestly; no old checker rerun')
for n in ['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py','common_next.py']:ast.parse((D/n).read_text());need(sha(D/n)==prep['bindings'][str(D/n)],'accepted preparation script unchanged '+n)
need(not (D/'closure.json').exists() and not (D/'diagnostic-publication-plan.json').exists() and not (D/'publication-after.json').exists(),'closure/publication still pending')
report=(D/'FINAL-REPORT.md').read_text();need('Earlier7e306e24' in report and 'does not retroactively fix/reinterpret' in report and 'Fullsuite/x64/broaderS2/S3/S4/S5/S6/native-retention/end-to-end remain OPEN' in report and 'CIoff/automationpaused/HHreuse disabled' in report and 'Original first comparison remains REJECTED' in report,'report scope and old rejection preservation')
checks.append('finalizer/closure/publisher/helper exact preparation bytes; report leaves old exception/rejections and broader scope unchanged')
# New identity-aware observation, never common.host or any historical runner.
seed=read('host-seed.json');saved=read('final-host.json');groups=set(seed['groups']);allow=read('host-identity-allowance.json')
need(sha(D/'host-identity-allowance.json')=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92' and sha(allow['historical_record'])==allow['historical_sha256'],'fixed host identity evidence')
for p in [D/'output/process.json',D/'comparison-2/output/process.json',*D.glob('*-run/output/process.json')]:
 a=json.loads(p.read_text());groups.update(a[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
need(groups==set(saved['groups']) and saved['no_Julia'] is True,'finalizer checked every historical/current group')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id']==saved['boot_id'],'same boot');processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text().rsplit(')',1)[1].split();command=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();pgid,sid=int(stat[2]),int(stat[3]);identity=dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(stat[19]),command=command,boot_id=boot)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+command[:1]),'Julia remains active')
  if pgid in groups or sid in groups:need(identity in allow['identities'],'historical or unknown numeric occupant');collisions.append(identity)
  processes.append(identity)
 except (FileNotFoundError,ProcessLookupError):pass
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'host memory')
checks.append('fresh all-group/session identity check and noJulia; exact unrelated collisions reported rather than blanket numeric absence')
result=dict(accepted=True,findings=[],checks=checks,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),production_commit=target,remote_refs=remote,phase_inventory_counts=phasecounts,accepted_review_bindings=binding_count,historical_resolutions=historical,current_continuation_bindings={p:sha(p) for p in allowed},fresh_host=dict(boot_id=boot,groups=sorted(groups),processes=processes,unrelated_numeric_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']),no_Julia_launched=True,no_old_script_or_canonical_runner_execution=True,no_git_mutation=True)
with OUT.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print('PASS new final review checker;',len(files),'source-test objects;',len(checks),'checks;',len(groups),'groups examined;',len(collisions),'exact unrelated collisions; diagnostic publication pending')
