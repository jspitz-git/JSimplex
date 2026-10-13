"""New offline auditor. No run is admitted merely by the existence of this file."""
from common import *
import tomllib

def validate_records(process,inv,reservation,guard_log,pinhash,allowancehash):
 try:
  runner,child=process['runner'],process['child'];boot=inv['host']['boot_id']
  commands=[' '.join(command())+' ',' '.join([str(RUNTIME),'--startup-file=no',*command()[2:]])+' ']
  identities=(all(type(obj[k]) is int and obj[k]>0 for obj in (runner,child) for k in ('pid','pgid','start_ticks')) and runner['boot_id']==child['boot_id']==boot and
   runner['pid']==runner['pgid'] and child['pid']==child['pgid'] and runner['pid']!=child['pid'] and child['start_ticks']>=runner['start_ticks'] and
   runner['command']==' '.join(guard_command())+' ' and child['command'] in commands)
  return (terminal_ok(process) and identities and process['command']==command() and process['cwd']==str(OVERLAY) and process['pins_sha256']==pinhash and
   type(inv['returncode']) is int and inv['returncode']==0 and 'error' not in inv and inv['command']==guard_command() and inv['host']['matches']==[] and
   type(reservation['time_ns']) is int and type(inv['started_ns']) is int and type(inv['ended_ns']) is int and
   inv['started_ns']<=reservation['time_ns']<=inv['ended_ns'] and guard_log==process and
   reservation['command']==command() and reservation['output']==str(OUT) and reservation['pins_sha256']==pinhash and reservation['allowance_sha256']==allowancehash)
 except (KeyError,TypeError):return False

def cost_ok(record,fixture):
 try:
  samples=record['samples'];expected=[(r,s) for r in range(1,13) for s in (['reference','candidate'] if r%2 else ['candidate','reference'])]
  if [(s['round'],s['side']) for s in samples]!=expected:return False
  if not (record['inputs_preserved'] is True and record['fixture']==fixture['id'] and record['input_sha256']==fixture['nzval_sha256'] and record['m']==fixture['m'] and record['n']==fixture['n'] and record['nnz']==len(fixture['rowval'])):return False
  for s in samples:
   if s['fixture']!=fixture['id'] or s['calls']!=16 or s['ok'] is not True or s['measured'] is not (s['round']>4):return False
   if any(type(s[k]) not in (int,float) or not math.isfinite(s[k]) or s[k]<0 for k in ['seconds','gc_seconds','compile_seconds','recompile_seconds']):return False
   if any(type(s[k]) is not int or s[k]<0 for k in ['bytes','allocations']):return False
   if s['measured'] and (s['compile_seconds']!=0 or s['recompile_seconds']!=0):return False
  return True
 except (KeyError,TypeError):return False

def main():
 checks={};rawhash={}
 try:
  pins=read(D/'launch-pins.json');pinhash=sha(D/'launch-pins.json');a=read(D/'allowance.json')
  checks['allowance']=allowance_valid(a,pinhash,current_refs())
  checks['pins']=manifest_ok(pins,read(D/'required-paths.json'))
  process=read(OUT/'process.json');inv=read(D/'invocation.json');res=read(D/'attempt-reserved.json')
  checks['invocation']=validate_records(process,inv,res,json.loads((D/'launcher.log').read_text()),pinhash,sha(D/'allowance.json'))
  checks['reservation_binding']=inv['reservation_sha256']==sha(D/'attempt-reserved.json')
  checks['copied_pins']=sha(OUT/'pins.json')==pinhash
  checks['current_process']=read(OUT/'current.json')['child']==process['child']
  resources=[json.loads(l) for l in (OUT/'resources.jsonl').read_text().splitlines()]
  checks['resources']=bool(resources) and all(type(v['available_kib']) is int and v['available_kib']>=6*1024**2 and type(v['swap_used_kib']) is int and 0<=v['swap_used_kib']<=1024**2 and type(v['elapsed']) in (int,float) and math.isfinite(v['elapsed']) and 0<=v['elapsed']<=180 for v in resources)
  checks['all_groups_sessions_closed']=not absent([process['runner']['pgid'],process['child']['pgid']])['matches']
  regression=tomllib.loads((OUT/'raw/regression.toml').read_text())
  counts=[90,40,416,34,16,31,28]
  checks['regression']=regression['counts']=={'pass':755,'fail':0,'error':0,'broken':0}
  checks['children']=len(regression['children'])==7 and all(t['counts']=={'pass':n,'fail':0,'error':0,'broken':0} for t,n in zip(regression['children'],counts))
  checks['loaded_source']=regression['source']==str(OVERLAY/'src/JSimplex.jl') and regression['candidate_sha256']==sha(C/'candidate-primal-updates.jl') and regression['tests_sha256']==sha(C/'candidate-tests.jl')
  spec=tomllib.loads((D/'fixtures.toml').read_text());fixture_names=[]
  for f in spec['fixtures']:
   name=f['id']+'.toml';fixture_names.append(name);checks[f['id']]=cost_ok(tomllib.loads((OUT/'raw'/name).read_text()),f)
  expected={'regression.toml','complete.toml',*fixture_names}
  checks['exact_raw_names']={p.name for p in (OUT/'raw').iterdir()}==expected
  final=tomllib.loads((OUT/'raw/complete.toml').read_text())
  checks['complete']=final==dict(fixtures=8,windows=192,cost_audits=3072,regression_pass=755,loaded_source=str(OVERLAY/'src/JSimplex.jl'),completed=True)
  rawhash={str(p):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
 except BaseException as e:checks['audit_exception']=False;error=repr(e)
 else:error=None
 result={'checks':checks,'all_passed':bool(checks) and all(checks.values()),'error':error,'raw_sha256':rawhash,'invocation_sha256':{str(p):sha(p) for p in [D/'launcher.log',D/'invocation.json',D/'attempt-reserved.json'] if p.is_file()}}
 dump(D/'audit.json',result)
 return 0 if result['all_passed'] else 1
if __name__=='__main__':sys.exit(main())
