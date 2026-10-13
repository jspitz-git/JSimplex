"""Exclusive S5-M offline acceptance. Missing raw is a preserved failed gate."""
from pathlib import Path
import hashlib,json,tomllib,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent;O=R/'.superpowers/simplex-core-architecture/S5-M/qualification-1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=json.loads((O/'process.json').read_text());pins=json.loads((O/'pins.json').read_text());schema=json.loads((H/'schema.json').read_text());resources=[json.loads(l) for l in (O/'resources.jsonl').read_text().splitlines()]
raw={};raw_error=None
try:raw=tomllib.loads((O/'report.toml').read_text())
except (OSError,ValueError) as e:raw_error=repr(e)
c=raw.get('checks',{});v=raw.get('observations',{})
checks={'process_exit0':p['reason']=='exit0' and p['returncode']==0,'guard_pins_unchanged':p['pins_unchanged'] is True,'pins_identity':sha(O/'pins.json')==p['pins_sha256'],
 'full_inventory':all(sha(f)==x['sha256'] and str(Path(f).resolve())==x['resolved'] for f,x in pins['inventory'].items()),
 'tree_membership':all({str(f) for f in Path(t).rglob('*') if f.is_file()}=={f for f in pins['inventory'] if Path(f).is_relative_to(t)} for t in pins['trees']),
 'raw_schema':set(raw)=={'checks','observations'} and set(c)==set(schema['checks']) and set(v)==set(schema['observations']),
 'forty_literal_true':len(c)==40 and all(x is True for x in c.values()),
 'observation_types':len(v)==15 and all(type(v.get(k)) is int and v[k]>=0 for k in schema['integer_observations']) and all(type(v.get(k)) is str for k in ('outcome_type','cause_type','last_event')),
 'exact_candidate':sha(H.parent/'S5-L/candidate.jl')==schema['candidate_sha256'],
 'one_latch_hit':v.get('latch_count')==v.get('hit_count')==1,
 'wrapped_sentinel':v.get('outcome_type') in schema['outcome_types'] and v.get('cause_type') in schema['cause_types'] and c.get('wrapper') is True and c.get('same_cause') is True,
 'resource_guard':bool(resources) and min(s['available_kib'] for s in resources)>=6*1024**2 and max(s['swap_used_kib'] for s in resources)<=1024**2 and max(s['elapsed'] for s in resources)<=120,
 'user6':all(sha(f)==x for f,x in json.loads((H/'host-before.json').read_text())['user_hashes'].items())}
valid=checks['observation_types']
checks['work_monotone_and_stops_at_throw']=valid and v['entry_iterations']<=v['final_iterations']==v['throw_iterations'] and v['entry_refactors']<=v['final_refactors']==v['throw_refactors']
checks['event_prefix']=valid and v['callback_count']==v['throw_callbacks']>=2 and v['final_phase_events']==v['throw_phase_events']>0 and v['last_event']=='pricing_phase_reset'
expected=json.loads((H/'command.json').read_text())['command'];checks['exact_command']=p['command']==expected and p['cwd']==str(R)
groups={53479,53481,52772,52774,49081,49084,23249,23257,p['runner']['pgid'],p['child']['pgid']};matches=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  s=(q/'stat').read_text();f=s[s.rindex(')')+2:].split()
  if int(f[2]) in groups or (q/'comm').read_text().strip()=='julia':matches.append({'pid':int(q.name),'pgid':int(f[2]),'start_ticks':int(f[19]),'command':(q/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')})
 except FileNotFoundError:pass
checks['fullgroups_absent']=not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==p['runner']['boot_id']
x={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'raw_error':raw_error,'observations':v,'failed_predicates':[k for k in schema['checks'] if c.get(k) is not True],'matches':matches,'time_ns':time.time_ns(),'raw_sha256':{str(f.relative_to(O)):sha(f) for f in O.iterdir() if f.is_file()}}
with (H/'audit.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
