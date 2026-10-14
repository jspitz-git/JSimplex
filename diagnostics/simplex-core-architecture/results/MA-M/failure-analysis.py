"""New offline analysis of the consumed failed attempt; no old audit rerun."""
from pathlib import Path
import hashlib,json,tomllib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
raw=tomllib.loads((D/'run-1/raw.toml').read_text());red=tomllib.loads((D/'run-1/red.toml').read_text());proc=read(D/'run-1/process.json');inv=read(D/'invocation-1.json');pins=read(D/'pins-reviewed.json');rs=red['records']
checks={
'actual_RED8pass2fail':len(rs)==10 and sum(x['type']=='Pass' for x in rs)==8 and sum(x['type']=='Fail' for x in rs)==2,
'exact_two_printed_scratch_failures':all(x['type']=='Pass' or x['expression']=='(MAL_TRACE[]).scratch == 1' for x in rs),
'frozen_test_same_expression':(D.parent/'MA-L/tests-reviewed.jl').read_text().count('@test MAL_TRACE[].scratch == 1')==1,
'driver_literal_mismatch':"r[\"expression\"]==\"MAL_TRACE[].scratch == 1\"" in (D/'driver-reviewed.jl').read_text(),
'sole_driver_error':len(raw['errors'])==1 and raw['errors'][0].startswith('unexpected RED expression\n'),
'no_GREEN_or_cost':not (D/'run-1/green.toml').exists() and raw['costs']==[] and raw['cost_body_seconds']==0 and raw['first_calls_seconds']==0,
'no_second_third_attempt':all(not (D/n).exists() for n in ('run-2','run-3','reservation-2.json','reservation-3.json','aggregate.json')),
'failure_preserved':proc['returncode']==1 and proc['reason']=='exit1' and read(D/'audit-1.json')['all_passed'] is False,
'guard_and_pins':proc['pins_unchanged'] is True and inv['elapsed_seconds']<120 and proc['elapsed_including_launch']<114,
'full3814_hashes':len(pins['inventory'])==3814 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),
'ambient_and_trace':raw['ambient_restored'] is True and raw['trace_cleared'] is True,
'loaded_module_paths_pinned':all(str(Path(p).resolve()) in {v['resolved'] for v in pins['inventory'].values()} for p in raw['loaded_paths'].values()),
}
samples=[json.loads(s) for s in (D/'run-1/resources.jsonl').read_text().splitlines()];checks['resource_limits']=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples+[proc['terminal_memory']])
groups=read(D/'posthost-1.json')['groups'];matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full140groups_ANDsessions_absent']=len(groups)==140 and not matches
checks['actual_source_unchanged']=not subprocess.check_output(['git','diff','HEAD','--','src','test','Project.toml','.github'],cwd=R).strip()
checks['protected_unchanged']=all(sha(p)==v for p,v in read(D/'host.json')['protected'].items())
record=dict(all_passed=all(checks.values()),checks=checks,decision='NOT ACCEPTED: expected optimization RED observed, harness expression formatting gate failed; GREEN/cost unexecuted; no retry',elapsed_seconds=inv['elapsed_seconds'],resource_samples=len(samples),min_available_kib=min(s['available_kib'] for s in samples),max_swap_kib=max(s['swap_used_kib'] for s in samples),host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),sha256={str(p):sha(p) for p in list((D/'run-1').iterdir())+[D/n for n in ('driver-reviewed.jl','audit_reviewed.py','admission-review-final.json','pins-reviewed.json','invocation-1.json','audit-1.json','failure-analysis.py')] if p.is_file()})
with (D/'failure-analysis.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('sha256','host')},indent=2))
if not record['all_passed']:raise ValueError('failure analysis incomplete')
