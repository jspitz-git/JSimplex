"""New fail-closed offline auditor. Alternate paths support synthetic failure tests only."""
from common_final import *
import sys,tomllib

def invocation_valid(process,pin_hash):
 invocation=read(H/'guard-invocation.json');reservation=read(H/'attempt-reserved.json')
 log=read(H/'guard-output.log')
 expected=[sys.executable,str(G),'run',str(H/'launch-pins.json'),str(O),'--seconds','120','--',*command()]
 return (type(invocation.get('returncode')) is int and invocation['returncode']==0 and 'error' not in invocation
  and invocation.get('command')==expected and reservation.get('command')==command()
  and reservation.get('pins_sha256')==pin_hash and log==process
  and type(reservation.get('time_ns')) is int and type(invocation.get('started_ns')) is int and type(invocation.get('ended_ns')) is int
  and reservation['time_ns']<=invocation['started_ns']<=invocation['ended_ns']
  and invocation['host']['boot_id']==process['runner']['boot_id'] and invocation['host']['matches']==[])

def audit(out):
 try:
  process=read(out/'process.json');pins=read(out/'pins.json');schema=read(H/'schema.json')
  resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
  raw=tomllib.loads((out/'report.toml').read_text());c=raw['checks'];v=raw['observations'];a=raw['at_throw'];z=raw['after_unwind']
  expected=schema['work'];obs=schema['observations']
  text=C.read_text();setup=text.split('    # BEGIN SOURCE SETUP\n')[1].split('    # END SOURCE SETUP')[0]
  call=text.split('        # BEGIN SOURCE CALL\n')[1].split('        # END SOURCE CALL')[0].strip()
  restored=setup.replace('SimplexProgressContext{T,typeof(d)}','SimplexProgressContext{T,Nothing}').replace('7,11,d,policy)','7,11,nothing,policy)')
  inverse=''.join('        '+x for x in restored.splitlines(True))+'            '+call.replace(';policy,progress,stop=guard)',';policy,progress)')+'\n'
  groups=absent([process['runner']['pgid'],process['child']['pgid']])
  checks={
   'elapsed_guard':type(process.get('elapsed_including_launch')) in (int,float) and 0<=process['elapsed_including_launch']<=120,
   'guard_invocation':invocation_valid(process,sha(out/'pins.json')),
   'process_exit0':process['reason']=='exit0' and type(process['returncode']) is int and process['returncode']==0,
   'guard_pins_unchanged':process['pins_unchanged'] is True,
   'manifest_binding':sha(out/'pins.json')==process['pins_sha256']==sha(H/'launch-pins.json'),
   'full_required_inventory':inventory_ok(pins),
   'admission_bindings':accepted()['accepted'] is True,
   'exact_candidate':sha(C)==EXPECTED,
   'exact_source_inverse':inverse==(H.parent/'S5-Q/existing-setup.txt').read_text() and inverse in (R/'test/simplex_precision_tests.jl').read_text(),
   'one_source_initializer_and_case':text.count('JSimplex.initialize_from_basis(')==1 and text.count('s5r_case(only(ARGS))')==1,
   'raw_tables':set(raw)=={'checks','observations','at_throw','after_unwind'} and all(type(x) is dict for x in (c,v,a,z)),
   'literal40':set(c)==set(schema['checks']) and len(c)==40 and all(x is True for x in c.values()),
   'observation_schema':set(v)==set(obs) and all(type(v[k]).__name__==t for k,t in obs.items()),
   'observations_exact':all(v[k]==x and type(v[k]) is type(x) for k,x in schema['observation_values'].items()) and type(v['start_ns']) is str and v['start_ns'].isdigit() and 0<int(v['start_ns'])<2**64,
   'two_work_records':all(set(x)==set(expected) and all(type(x[k]) is type(y) and x[k]==y for k,y in expected.items()) for x in (a,z)),
   'resource_guard':bool(resources) and all(type(s['available_kib']) is int and s['available_kib']>=6*1024**2 and type(s['swap_used_kib']) is int and 0<=s['swap_used_kib']<=1024**2 and 0<=s['elapsed']<=120 for s in resources),
   'exact_command':process['command']==command() and process['cwd']==str(R),
   'groups_absent':not groups['matches'] and groups['boot_id']==process['runner']['boot_id']==process['child']['boot_id'],
   'user6':all(sha(p)==v for p,v in read(H/'host-before.json')['user_hashes'].items()),
  }
  return dict(checks=checks,all_passed=all(checks.values()),pin_count=len(pins['inventory']),observations=v,at_throw=a,after_unwind=z,groups=groups,failed_predicates=[k for k in schema['checks'] if c.get(k) is not True],invocation_sha256={str(H/n):sha(H/n) for n in ('guard-invocation.json','guard-output.log','attempt-reserved.json')},raw_sha256={str(p.relative_to(out)):sha(p) for p in out.iterdir() if p.is_file()},time_ns=time.time_ns())
 except Exception as error:
  return dict(checks={'readable_valid_complete_inputs':False},all_passed=False,error=repr(error),time_ns=time.time_ns(),scope='Qualification failed or incomplete. Preserve all artifacts and STOP; no retry or tuning.')
if __name__=='__main__':
 out=O if len(sys.argv)==1 else Path(sys.argv[1]);dest=H/'audit.json' if len(sys.argv)==1 else Path(sys.argv[2])
 result=audit(out);dump(dest,result);print(json.dumps(result));raise SystemExit(0 if result['all_passed'] else 1)
