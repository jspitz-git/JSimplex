from pathlib import Path
import sys,json,re,subprocess,os,hashlib,ast,statistics,tomllib,collections,datetime
sys.dont_write_bytecode=True;os.environ['GIT_OPTIONAL_LOCKS']='0'
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common as c
M=c.M;R=c.R;G=D/'GREEN';P=D/'MASTER-run';Q=D/'comparison-2';load=lambda n:json.loads((D/n).read_text());sha=c.sha
co=load('production-commit.json');target=co['commit'];base=c.TARGET;hist=load('historical-path-map.json');integration=load('integration-historical-path-map.json');di=load('diagnostic-index-before.json');protected=load('protected-before.json');baseline=load('baseline-tree.json');used={};cache={}
def digest(p):
 p=str(p)
 if p not in cache:cache[p]=sha(p)
 return cache[p]
def resolve(p,h):
 p=Path(p)
 if digest(p)==h:return
 q=None
 if str(p) in hist['master_index_before']:q=Path(hist['master_index_before'][str(p)]['before'])
 elif str(p) in di:q=Path(di[str(p)]['before'])
 elif str(p) in hist['continuation_before']:q=Path(hist['continuation_before'][str(p)]['before'])
 elif p.is_relative_to(M/'src') or p.is_relative_to(M/'test'):q=D/'baseline'/p.relative_to(M)
 assert q is not None and q.is_file() and digest(q)==h,('unresolved historical binding',str(p),h)
 used[str(p)+'@'+h]=str(q)
git=lambda args,root=M:subprocess.check_output(['/usr/bin/git','-C',str(root),*args])
g=lambda args,root=M:git(args,root).decode().strip()
assert target=='ce5d4a74019e0dc2e656d08161641c498b159e7b'
assert g(['rev-parse','HEAD'])==g(['rev-parse','master'])==g(['rev-parse','origin/master'])==g(['ls-remote','origin','refs/heads/master']).split()[0]==target
assert g(['rev-list','--parents','-n','1',target]).split()==[target,base] and g(['rev-parse',target+'^{tree}'])==co['tree']
assert g(['diff-tree','--no-commit-id','--name-only','-r',target]).splitlines()==co['names']
assert g(['rev-parse','HEAD'],R)==load('host-before.json')['diagnostic_head']
assert not g(['diff','--cached','--raw','-z'],R)
for tree in ['src','test']:
 actual={str(p.relative_to(M)):digest(p) for p in (M/tree).rglob('*') if p.is_file()};staged={str(p.relative_to(G)):digest(p) for p in (G/tree).rglob('*') if p.is_file()};assert actual==staged
for n in co['names']:assert git(['show',target+':'+n])==(M/n).read_bytes()==(G/n).read_bytes()
assert not g(['diff','--name-only','HEAD','--','src','test','Project.toml'])
assert set(baseline)=={str(p.relative_to(D/'baseline')) for p in (D/'baseline').rglob('*') if p.is_file()}
for n,h in baseline.items():assert digest(D/'baseline'/n)==h
assert hist['master_before']==base and hist['master_source_before']==integration['source_before'] and hist['master_index_before']==integration['master_index_before']
assert set(hist['master_source_before'])=={str(M/n) for n in co['names'] if n in baseline}
for p,v in hist['master_source_before'].items():
 n=str(Path(p).relative_to(M));assert v['before']==str(D/'baseline'/n) and v['sha256']==baseline[n]==digest(v['before'])
mi=g(['rev-parse','--path-format=absolute','--git-path','index']);ri=g(['rev-parse','--path-format=absolute','--git-path','index'],R)
assert set(hist['master_index_before'])=={mi} and hist['master_index_before'][mi]['sha256']==protected['indexes'][mi]==digest(D/'before-master/master.index')
assert hist['master_index_before'][mi]['before']==str(D/'before-master/master.index')
assert set(di)=={ri} and di[ri]['before']==str(D/'before-diagnostic/diagnostic.index') and di[ri]['sha256']==protected['indexes'][ri]==digest(di[ri]['before'])
for p,h in load('MASTER-run/protected-before.json')['indexes'].items():assert digest(p)==h
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
assert set(hist['continuation_before'])==allowed
for p,h in protected['files'].items():
 if p in allowed:
  v=hist['continuation_before'][p];expected=D/'continuation-before'/('STATUS.md' if Path(p).name=='STATUS.md' else 'roadmap.md')
  assert v['before']==str(expected) and v['sha256']==h==digest(expected)
  data=Path(p).read_bytes();assert data.endswith(expected.read_bytes()) and data.count(b'# Current continuation \xe2\x80\x94 bounds, norm and infeasibility scalar savings integrated, 2026-10-27')==1
  assert target.encode() in data[:data.index(b'## Previous continuation')]
 else:assert digest(p)==h
assert c.environment()==load('environment.json')['inherited']
reviews=['admission-ready.json','comparison-2/admission.json','correctness-qualification/admission.json','correctness-qualification/result-review.json','comparison-2/cost-qualification-review.json','result-review.json','production-review.json','publication-preparation-reviewed.json','commit-review.json','RED-run/admission.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/result-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','finalization-preparation-review.json']
for n in reviews:
 r=load(n);assert r['accepted'] and not r['findings']
 for p,h in r['bindings'].items():resolve(p,h)
manifests=[(D,n) for n in ['pins.json','pins-reviewed.json','pins-ready.json']]+[(D/n,'pins.json') for n in ['comparison-2','correctness-qualification','RED-run','GREEN-run','MASTER-run']]
counts=[]
for phase,name in manifests:
 pins=json.loads((phase/name).read_text());assert set(pins['files'])==set(pins['inventory']);counts.append(len(pins['inventory']))
 for p,v in pins['inventory'].items():
  assert str(Path(p).resolve(strict=True))==v['resolved'];resolve(p,v['sha256'])
 for tree in pins['trees']:
  tree=Path(tree);expected={str(Path(p).relative_to(tree)) for p in pins['inventory'] if Path(p).is_relative_to(tree)};actual={str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file()}
  if actual!=expected and tree in [M/'src',M/'test']:
   old=D/'baseline'/tree.relative_to(M);actual={str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()}
  assert actual==expected,('tree membership',tree)
master=load('MASTER-run/audit.json');green=load('GREEN-run/audit.json');mc=load('MASTER-run/contract.json');gc=load('GREEN-run/contract.json')
assert master['accepted'] and green['accepted'] and master['passed']==master['total']==green['passed']==green['total']==mc['expected_total']==314009
assert master['expected_failures']==green['expected_failures']==0 and mc['files']==gc['files'] and len(mc['files'])==51
for phase,arm,expected_samples in [(D/'GREEN-run','GREEN',1755),(P,'MASTER',1926)]:
 rd=lambda n:json.loads((phase/n).read_text())
 contract=rd('contract.json');proc=rd('output/process.json');sup=rd('supervisor.json');done=rd('completed.json');gate=rd('output/gate.json');cur=rd('output/current.json');permit=rd('output/permit.json');reservation=rd('reservation.json')
 assert proc['returncode']==0 and proc['pins_unchanged'] and sup['accepted'] and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup
 assert proc['command']==contract['command']==gate['command']==cur['command']==permit['command']
 assert proc['runner']==sup['guard_identity']==gate['parent']==cur['runner'] and proc['child']==gate['identity']==cur['child']
 assert gate['parent_death_signal']==9 and gate['current_sha256']==permit['current_sha256']==digest(phase/'output/current.json') and gate['permit_sha256']==digest(phase/'output/permit.json')
 assert proc['pins_sha256']==digest(phase/'pins.json')==digest(phase/'output/pins.json')==reservation['pins_sha256']
 assert done['accepted'] and 0<proc['elapsed_including_launch']<=sup['elapsed_seconds']<=done['elapsed_shared_seconds']<=3000
 assert reservation['guard_deadline']==reservation['started_monotonic']+2992 and reservation['outer_deadline']==reservation['started_monotonic']+3000
 log=(phase/'output/run.log').read_text();assert re.findall(r'^INCLUDING (.*)$',log,re.M)==contract['files']
 assert re.findall(r'^BNI_SOURCE (.*)$',log,re.M)==[str(Path(contract['source_root'])/'src/JSimplex.jl')]
 headers=re.findall(r'^Test Summary:.*\|(.+)$',log,re.M);assert len(headers)==1 and headers[0].split()==['Pass','Total','Time']
 vals=re.findall(r'^Bounds norm infeasibility '+arm+r'\s*\|\s*(\d+)\s+(\d+)\s+\S+\s*$',log,re.M);assert vals==[('314009','314009')]
 assert re.findall(r'^BNI_COMPLETED (.*)$',log,re.M)==[arm] and 'Test Failed at ' not in log and 'Error During Test' not in log and not re.search(r'^ERROR:',log,re.M)
 resources=[json.loads(x) for x in (phase/'output/resources.jsonl').read_text().splitlines()];assert len(resources)==expected_samples
 assert all(x['available_kib']>=6*1024**2 and x['swap_used_kib']==0 for x in resources)
 assert proc['terminal_memory']['available_kib']>=6*1024**2 and proc['terminal_memory']['swap_used_kib']==0
assert load('admission.json')['accepted'] is False
assert load('output/process.json')['returncode']==1 and load('output/process.json')['pins_unchanged'] and not (D/'output/results.toml').exists()
assert load('comparison-2/output/process.json')['returncode']==1 and not load('comparison-2/supervisor.json')['accepted']
red=load('RED-run/audit.json');k=load('correctness-qualification/audit.json');q=load('comparison-2/audit-qualified.json')
assert (red['passed'],red['expected_failures'],red['total'])==(15911,10,15921) and red['accepted']
assert k['accepted'] and k['assertions']==15881
assert q['accepted'] and not q['original_run_accepted'] and (q['cases'],q['windows'],q['gc_windows'],q['raw_original_failures'],q['original_assertions_passed'])==(1632,29376,25,18,51891)
raw=tomllib.loads((Q/'output/results.toml').read_text());summary=load('independent-production-costs.json')['summary'];groups=collections.defaultdict(list);windows=gcwindows=0
for cell in raw['cells']:
 pairs=collections.defaultdict(dict)
 for w in cell['windows']:
  assert w['compile_seconds']==w['recompile_seconds']==0;windows+=1;gcwindows+=w['gc_seconds']>0;pairs[w['pair']][w['arm']]=w
 assert len(pairs)==9
 if cell['type']=='BigFloat' or cell['type']=='Rational{BigInt}' and cell['variant']=='A':groups[cell['type']+'/'+cell['scope']].append({m:statistics.median(p[cell['variant']][m]/p['original'][m] for p in pairs.values()) for m in ['seconds','bytes','events']})
assert len(raw['cells'])==1632 and windows==29376 and gcwindows==25 and len(raw['preparation'])==1670
report=(D/'FINAL-REPORT.md').read_text()
for key,values in groups.items():
 for metric in ['seconds','bytes','events']:
  value=statistics.median(x[metric] for x in values);assert value==summary[key]['ratios'][metric] and f'{value:.6f}' in report
assert target in report and '1757.683/1928.781s' in report and 'A separate PASS closure and exact diagnostic staged/committed publication are still required.' in report
assert 'broader/full-suite/x64/native-retention work remains open' in report
pub=load('publication.json');assert pub['accepted'] and pub['normal_nonforce_push'] and pub['commit']==pub['local_master']==pub['tracking']==pub['remote_master']==target and pub['parent']==base and pub['names']==co['names'] and pub['master_tests']==314009
assert 'master' in (D/'push.log').read_text()
for n in ['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py']:ast.parse((D/n).read_text())
assert not (D/'closure.json').exists() and not (D/'diagnostic-publication-plan.json').exists() and not (D/'publication-after.json').exists()
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[key][v] for key in ['runner','child'] for v in ['pgid','sid'])
host=c.host(extra);assert len(host['groups'])==649
c.put('independent-final-host.json',host)
with (D/'independent-final-review.py').open('x') as f:f.write(Path(__file__).read_text())
text=f'''# Independent final review

Accepted the actual final report, current continuation prefixes, exact historical maps, production publication and the prepared next-step closure/diagnostic-publication controls. No unresolved findings. Production `{target}` is the exact independently reviewed four-path commit, sole parent `{base}`, and local HEAD/master, origin/master and live remote master agree. This review does not claim PASS closure or diagnostic publication; those remain separate required actions.

Actual source/test trees remain byte-identical to tested GREEN, and changed files match actual committed blobs. Fresh actual MASTER independently passed 314,009/314,009 assertions in the same 51 ordered whole files as GREEN. I independently rechecked both raw ordinary Test summaries, exact source/includes/completion markers, expected exit0, accepted supervisor, runner/child/gate/permit identity/hash links, copied pins and absolute/shared deadlines. The MASTER contract freezes GREEN's 314,009 total. Inclusive GREEN/MASTER times are 1,757.683/1,928.781 seconds; all 1,755/1,926 resource samples and terminal checks meet limits with zero swap. Ordinary solver recovery Info messages remain distinguished from top-level runtime errors. No previous test result was substituted for actual MASTER.

All sixteen prerequisite independent reviews and all eight phase manifest sets resolve. Their inventory counts are {counts}. Current hashes are required unless an exact historical beforeimage is necessary; I verified {len(used)} unique old path/hash substitutions. Only preserved baseline source/test bytes, the exact before-master index, the separately saved diagnostic index and the two exact continuation beforeimages were eligible. Complete baseline membership/hashes, resolved file identities and historical/current tree membership were checked. Older maps and raw/rejected records remain unchanged. This reviewer did not call common.unchanged after integration or rerun an old audit, finalizer or test.

The historical master source map contains exactly the three changed preexisting paths with baseline bytes; the new test has no invented beforeimage. Original master index equals its recorded protected hash. The diagnostic index beforeimage and current diagnostic index match, and all other current indexes match actual-MASTER protected state. Both current continuation files contain exactly one new case prefix and preserve their complete original bytes as an exact suffix; every other protected file and inherited environment remains unchanged. The case date 2026-10-27 identifies the diagnostic case started that day; the review's current UTC timestamp is {datetime.datetime.now(datetime.timezone.utc).isoformat()}.

I independently recomputed the report's ten affected type/path median time/bytes/events ratios from the preserved 1,632 raw cells and 29,376 windows. Measured compilation/recompilation is zero, and all 25 GC windows plus 1,670 preparation records remain. Report ratios match the independently saved calculations. The initial loader exit1, subsequent comparison exit1 with 51,891 passes and 18 wrong cap expectations, rejected supervisor, corrected correctness-only 15,881-assertion qualification, and original RED 15,911 passes plus ten allocation failures remain distinct and correctly described. No cost remeasurement or conversion of either failed launch into a pass occurred. The broad-error-check false positive in the offline GREEN reviewer is separately preserved and did not change raw results.

Work/memory conclusion: no unnecessary additional production scan, solve, copy, conversion, invariant pass or persistent numerical cache was found. Candidate arithmetic order, finite/unbounded/tolerance guards, interval widenings, aliases and context behavior remain those already reviewed. Per-row readiness checks and six additional cold method bodies are acknowledged costs. Allocation traffic reductions are supported, while direct-norm/checked-FTRAN timing and native retained-memory benefits are not established. The final report qualifies these claims and leaves broader/full-suite/x64/native-retention coverage open, with CI off, automation paused and HH reuse disabled.

The normal nonforce production push record and live remote equality agree. Exact unexecuted closure and diagnostic-publication scripts still match their accepted preparation bindings. Closure must separately validate this review, all old/current bindings and exact beforeimages, then record PASS; diagnostic publication must subsequently verify complete explicit staged/committed names and blobs, sole diagnostic parent, protected state and normal nonforce remote equality. Neither output existed at review time. Fresh host observation covers 649 historical groups AND sessions/boot/start ticks/commands with no Julia, using only the exact fixed unrelated-WSL allowance. No Julia or Git mutation was performed by this reviewer.
'''
with (D/'FINAL-REVIEW.md').open('x') as f:f.write(text)
paths=[D/n for n in ['FINAL-REPORT.md','progress-final.md','FINAL-REVIEW.md','independent-final-review.py','independent-final-host.json','historical-path-map.json','integration-historical-path-map.json','diagnostic-index-before.json','publication.json','push.log','production-commit.json','staged-tree.json','source-inverse.json','protected-before.json','baseline-tree.json','final-host.json','finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py','independent-production-costs.json']+reviews]
paths += [Path(p) for p in allowed]+[Path(v['before']) for v in hist['continuation_before'].values()]+[Q/'output/results.toml',Q/'output/run.log',Q/'audit-qualified.json',D/'correctness-qualification/audit.json',D/'RED-run/audit.json']
for phase in ['GREEN-run','MASTER-run']:
 paths += [D/phase/n for n in ['audit.json','contract.json','pins.json','output/run.log','output/process.json','output/resources.jsonl','output/current.json','output/permit.json','output/gate.json','supervisor.json','completed.json','reservation.json']]
paths += [phase/name for phase,name in manifests]
c.put('final-review.json',dict(accepted=True,findings=[],production_commit=target,parent=base,passed=314009,files=51,pinsets=8,pin_counts=counts,groups=649,Julia_executed=False,Git_mutated=False,historical_resolutions=used,closure_pending=True,diagnostic_publication_pending=True,bindings={str(p):digest(p) for p in paths}))
print('accepted final independent review;',len(used),'exact historical resolutions; 8pinsets; 649groups; PASSclosure/DIpublication pending')
