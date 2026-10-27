from pathlib import Path
import json,hashlib,re,subprocess,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27'); Q=D/'RED-run';M=Path('/home/jspitz/JSimplex.jl')
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
pins=read(Q/'pins.json')
for name,v in pins['inventory'].items():
 p=Path(name);need(str(p.resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'pin '+name)
for tree in pins['trees']:
 need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'membership '+tree)
need((Q/'pins.json').read_bytes()==(Q/'output/pins.json').read_bytes(),'copied pins')
base=read(D/'baseline-tree.json')
for n,h in base.items():
 need(sha(D/'baseline'/n)==h and sha(M/n)==h,'baseline/main '+n)
 if n!='test/runtests.jl':need(sha(D/'RED'/n)==h,'RED baseline '+n)
need(sha(D/'new-test.jl')==sha(D/'RED/test/generic_quality_devex_tests.jl'),'test exact')
for n in ['HEAD','master','origin/master']:need(subprocess.check_output(['git','-C',str(M),'rev-parse',n],text=True).strip()=='7e306e24f064a8aa214bc88379e059def77661ab','ref '+n)
for doc in ['admission.json','audit.json']:
 for n,h in read(Q/doc)['bindings'].items():need(sha(Path(n))==h,'binding '+n)
for group in read(Q/'protected-before.json').values():
 for n,h in group.items():need(sha(Path(n))==h,'protected '+n)
log=(Q/'output/run.log').read_text();scopes=['direction','row','quality','quality_transposed','devex_shared','devex_solved']
fail=re.findall(r'^Whole-call allocation (\w+): Test Failed at (.+):(\d+)$',log,re.M)
need(fail==[(s,str(D/'RED/test/generic_quality_devex_tests.jl'),'481') for s in scopes],'exact six failures')
need('9465 passed, 6 failed, 0 errored, 0 broken.' in log,'ordinary Test counts')
need(re.search(r'^Quality Devex RED\s+\|\s+9465\s+6\s+9471\s+',log,re.M),'summary')
need(log.count('Test Failed at ')==6 and 'Error During Test' not in log,'no other failures')
need(log.count('Whole-function correctness BigFloat            |  573')==15,'15 BF contexts')
need('QUALITY_DEVEX_SOURCE '+str(D/'RED/src/JSimplex.jl') in log,'source assertion')
for s in scopes:need(re.search(r'^    Whole-call allocation '+s+r'\s+\|\s+3\s+1\s+4\s+',log,re.M),'gate '+s)
# The failure print includes all 18 pairs; independently extract all raw counters.
records=re.findall(r'Dict\("gc_seconds" => ([^,]+), "recompile_seconds" => ([^,]+), "seconds" => ([^,]+), "bytes" => (\d+), "events" => (\d+), "compile_seconds" => ([^,]+), "sink" => (\d+)\)',log)
need(len(records)==36,'36 raw allocation records')
for i in range(0,36,2):
 a,b=records[i:i+2];need(a[3:5]==b[3:5] and a[6]==b[6],'baseline/reference equal work');need(float(a[1])==float(a[5])==float(b[1])==float(b[5])==0,'compiled window')
p=read(Q/'output/process.json');g=read(Q/'output/gate.json');c=read(Q/'output/current.json');permit=read(Q/'output/permit.json');contract=read(Q/'contract.json');inv=read(Q/'invocation.json');sup=read(Q/'supervisor.json');done=read(Q/'completed.json')
need(p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'],'expected exit');need(p['command']==g['command']==permit['command']==c['command']==contract['command']==inv['Julia_command'],'commands')
need(p['runner']==g['parent']==c['runner'] and p['child']==g['identity']==c['child'],'identity');need(p['pins_sha256']==sha(Q/'pins.json'),'pins identity');need(g['current_sha256']==permit['current_sha256']==sha(Q/'output/current.json') and g['permit_sha256']==sha(Q/'output/permit.json'),'permit chain');need(g['parent_death_signal']==9,'parent death')
need(sup['accepted'] and sup['returncode']==0 and not sup['hard_timeout'] and not sup['soft_timeout'] and done['accepted'] and done['elapsed_shared_seconds']<1800,'completion')
samples=[json.loads(l) for l in (Q/'output/resources.jsonl').read_text().splitlines()];need(len(samples)==30,'samples');need(min(s['available_kib'] for s in samples)>=6*1024**2 and max(s['swap_used_kib'] for s in samples)<=1024**2,'resource bounds')
for name in ['launch-host.json','host-after.json','audit-host.json']:
 h=read(Q/name);need(h['boot_id']==p['runner']['boot_id'] and h['no_Julia'],'host');groups=set(h['groups'])
 for proc in h['processes']:need(proc['pgid'] not in groups and proc['sid'] not in groups,'historical absence')
files=[p for p in Q.rglob('*') if p.is_file()]+[D/'new-test.jl',D/'baseline-tree.json',D/'result-review.json',D/'RESULT-REVIEW.md',Path(__file__)]
result=dict(accepted=True,findings=[],reviewer='independent production reviewer',review_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=9465,expected_failures=6,total=9471,errors=0,broken=0,raw_records=36,inventory_entries=len(pins['inventory']),elapsed_shared_seconds=done['elapsed_shared_seconds'],notes=['Exactly the six intended whole-call allocation gates fail; each baseline/reference pair has identical bytes and events.','All 19 correctness contexts and all compilation assertions pass.','No Julia was run and no historical script was replayed.','GREEN and actual-master all-pass qualification remain required; prior allocation exceptions are not transferred.'],bindings={str(p):sha(p) for p in files})
with (Q/'result-review.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}));print('result_sha256',sha(Q/'result-review.json'))
