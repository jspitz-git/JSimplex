"""Cold saved-record schemas. No process actions, numerical work or Julia imports."""
import math,re

def require(ok,message):
 if not ok:raise ValueError(message)
def keys(v,names):require(type(v) is dict and set(v)==set(names.split()),'Exact record keys: '+names)
def uint(v):return type(v) is int and v>=0
def positive(v):return type(v) is int and v>0
def finite(v):return type(v) in (int,float) and math.isfinite(v) and v>=0
def text(v):return type(v) is str and bool(v)
def strings(v):return type(v) is list and bool(v) and all(type(x) is str for x in v)
def digest(v):return type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None
def identity(v):
 keys(v,'pid pgid sid start_ticks boot_id command')
 require(all(positive(v[k]) for k in ('pid','pgid','sid','start_ticks')) and text(v['boot_id']) and text(v['command']),'Identity types')
def memory(v):
 keys(v,'available_kib swap_used_kib');require(all(uint(x) for x in v.values()),'Memory integer values')
def host(v):
 keys(v,'time groups matches boot_id head master unreadable_exe_pids unreadable_identity_pids scope')
 require(finite(v['time']) and all(text(v[k]) for k in ('boot_id','head','master','scope')),'Host scalar types')
 for k in ('groups','unreadable_exe_pids','unreadable_identity_pids'):
  require(type(v[k]) is list and all(positive(x) for x in v[k]) and len(v[k])==len(set(v[k])),'Host PID types')
 require(v['groups']==sorted(v['groups']) and type(v['matches']) is list and not v['matches'] and not v['unreadable_identity_pids'],'Host closure types')
def supervisor(v):
 keys(v,'soft_timeout hard_timeout child_kill guard_term guard_kill guard_identity returncode elapsed_seconds accepted')
 require(all(type(v[k]) is bool for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','accepted')) and type(v['returncode']) is int and finite(v['elapsed_seconds']),'Supervisor types')
 identity(v['guard_identity'])
def success(p,sup):
 return (type(p.get('returncode')) is int and p['returncode']==0 and p.get('reason')=='exit0' and type(sup.get('returncode')) is int and sup['returncode']==0 and sup.get('accepted') is True and all(sup.get(k) is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')))
def runtime(p,cur,inv,resources,hosts,limit):
 common='command cwd started runner pins_sha256 reason returncode child'
 keys(cur,common);keys(p,common+' elapsed_including_launch child_maxrss_kib terminal_memory ended pins_unchanged')
 for v in (cur,p):
  require(strings(v['command']) and text(v['cwd']) and finite(v['started']) and digest(v['pins_sha256']) and text(v['reason']),'Process scalar types')
  identity(v['runner']);identity(v['child'])
 require(cur['returncode'] is None and cur['reason']=='launch_error' and type(p['returncode']) is int and type(p['pins_unchanged']) is bool,'Process status types')
 require(finite(p['ended']) and finite(p['elapsed_including_launch']) and p['elapsed_including_launch']<=limit and positive(p['child_maxrss_kib']),'Process time/RSS')
 memory(p['terminal_memory'])
 keys(inv,'monotonic_start command guard_command python pins_sha256 review_sha256 reservation_sha256 supervisor elapsed_seconds')
 require(finite(inv['monotonic_start']) and finite(inv['elapsed_seconds']) and inv['elapsed_seconds']<=limit and strings(inv['command']) and strings(inv['guard_command']) and text(inv['python']) and all(digest(inv[k]) for k in ('pins_sha256','review_sha256','reservation_sha256')),'Invocation types')
 supervisor(inv['supervisor']);require(inv['supervisor']['elapsed_seconds']<=limit,'Supervisor inclusive limit')
 require(type(resources) is list and bool(resources),'Resource list')
 previous=-1
 for s in resources:
  require(type(s) is dict and set(s) in ({'available_kib','swap_used_kib','elapsed'},{'available_kib','swap_used_kib','elapsed','child_memory'}),'Resource sample keys')
  memory({k:s[k] for k in ('available_kib','swap_used_kib')})
  require(finite(s['elapsed']) and previous<=s['elapsed']<=p['elapsed_including_launch'],'Resource elapsed');previous=s['elapsed']
  if 'child_memory' in s:require(type(s['child_memory']) is list and all(type(x) is str for x in s['child_memory']),'Resource child memory types')
 for h in hosts:host(h)

def probe(v):
 keys(v,'states outputs inputs_unchanged constructions refactors updates ftran btran copies counts coexistence_graph_peak cache_charge_sum cache_charge_peak')
 require(type(v['inputs_unchanged']) is bool and all(uint(v[k]) for k in ('constructions','refactors','updates','ftran','btran','copies','cache_charge_sum','cache_charge_peak')) and positive(v['coexistence_graph_peak']),'Probe scalar types')
 require(type(v['states']) is list and type(v['outputs']) is list and all(type(side) is list and all(type(row) is list and all(type(x) is str for x in row) for row in side) for side in v['outputs']),'Probe collections')
 for s in v['states']:
  keys(s,'step refactored equal graphs cache probe_cache counts coexistence_graph_peak')
  require(uint(s['step']) and type(s['refactored']) is bool and type(s['equal']) is bool and type(s['graphs']) is list and positive(s['coexistence_graph_peak']),'Probe checkpoint types')
def controls(v):
 keys(v,'complete inputs_unchanged orientation_synthetic_calls orientation_requests orientation_payload constructions copies refactors explicit_solves imports transitions')
 require(all(type(v[k]) is bool for k in ('complete','inputs_unchanged')) and all(uint(v[k]) for k in ('orientation_synthetic_calls','orientation_requests','orientation_payload','constructions','copies','refactors','explicit_solves')),'Control scalar types')
 require(type(v['imports']) is list and type(v['transitions']) is list,'Control collections')
 for z in v['imports']:
  keys(z,'name correct u counts');require(text(z['name']) and type(z['correct']) is bool and uint(z['u']),'Import scalar types')
 for x in v['transitions']:
  keys(x,'backend states copy_cache constructions copies refactors explicit_solves')
  require(text(x['backend']) and type(x['states']) is list and all(uint(x[k]) for k in ('constructions','copies','refactors','explicit_solves')),'Transition scalar types')
  for s in x['states']:
   keys(s,'name cache graphs coexistence_graph');require(text(s['name']) and type(s['graphs']) is list and positive(s['coexistence_graph']),'Transition state types')
def cell(v):
 keys(v,'fixture manager backend policy windows');require(all(text(v[k]) for k in ('fixture','manager','backend','policy')) and uint(v['windows']),'Cell scalar types')
def raw(v):
 keys(v,'phase loaded completed fatal cells windows threads blas_threads')
 require(text(v['phase']) and type(v['loaded']) is dict and all(text(k) and text(x) for k,x in v['loaded'].items()) and type(v['completed']) is bool and type(v['fatal']) is str and all(uint(v[k]) for k in ('cells','windows','threads','blas_threads')),'Raw scalar types')
