import sys
sys.dont_write_bytecode=True
from control_reviewed import *
from auditor import *
import ast,copy,importlib.util,tomllib
checks={}
def reject(f):
 try:f();return False
 except (ValueError,KeyError,TypeError,FileNotFoundError,tomllib.TOMLDecodeError):return True
# Extract new synthetic constructors only; do not rerun exclusive synthetic script.
t=ast.parse((D/'synthetic.py').read_text());ns=dict(globals());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('enc','specimen')],type_ignores=[]),'synthetic-constructors','exec'),ns)
specimen=ns['specimen'];q=specimen('qualification','candidate')
for name,mut in [('context',lambda x:x.update(context_restored=False)),('missing_context',lambda x:x.pop('context_restored')),('missing_entries',lambda x:x.pop('route_entries')),('throw_as_success',lambda x:x['route_entries'].update(throws=5,successes=51)),('extra_throw',lambda x:x['route_entries'].update(throws=7,successes=49)),('missing_preentry',lambda x:x['route_entries'].update(candidate=27)),('unexpected_error',lambda x:x['errors'].append('unexpected'))]:
 x=copy.deepcopy(q);mut(x);checks['reject_'+name]=reject(lambda:validate(x,'qualification','candidate'))
x=specimen('red','reference');x['route_entries']={};checks['RED_route_rejected']=reject(lambda:validate(x,'red','reference'))
ref=specimen('cost','reference');cand=specimen('cost','candidate');grid={i:dict(reference=ref,candidate=cand) for i in range(1,11)}
checks['grid_positive']=complete_grid(grid);x=copy.deepcopy(grid);x.pop(10);checks['missing_pair']=reject(lambda:complete_grid(x));x=copy.deepcopy(grid);x[5].pop('candidate');checks['missing_side']=reject(lambda:complete_grid(x))
checks['missing_raw']=reject(lambda:tomllib.loads((D/'nonexistent-raw.toml').read_text()));checks['malformed_raw']=reject(lambda:tomllib.loads('bad = ['))
p=dict(reason='exit0',returncode=0,command=['cmd'],pins_sha256='hash',pins_unchanged=True,elapsed_including_launch=1,terminal_memory=dict(available_kib=7*1024**2,swap_used_kib=0))
for name,mut in [('worker_timeout',lambda x:x.update(reason='wall_time')),('memory',lambda x:x['terminal_memory'].update(available_kib=0)),('swap',lambda x:x['terminal_memory'].update(swap_used_kib=2*1024**2)),('session_leak',lambda x:x.update(reason='unexpected_descendants')),('cleanup_failed',lambda x:x.update(reason='cleanup_incomplete'))]:
 x=copy.deepcopy(p);mut(x);checks[name]=not terminal(x,2,['cmd'],'hash')
# Execute seal entry with fake review inputs; never run launcher, guard, Julia or write seal.
node=next(n for n in ast.parse((D/'seal-reviewed.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
for mode in ('missing','rejected','findings','pin','changed'):
 def fake_read(path):
  if mode=='missing':raise FileNotFoundError(path)
  return dict(accepted=mode!='rejected',unresolved_findings=['finding'] if mode=='findings' else [],pins_sha256='bad' if mode=='pin' else 'h',sha256={'/bound':'bad' if mode=='changed' else 'h'})
 fake=dict(globals(),read=fake_read,sha=lambda _: 'h',sys=type('Args',(),{'argv':[str(D/'seal-reviewed.py'),'seal']}))
 exec(compile(ast.Module(body=[node],type_ignores=[]),'seal-entry','exec'),fake)
 checks['review_'+mode]=reject(fake['main'])
# Source and identity gates supplement synthetic outcome tests; no runtime kill proof.
g=(D/'guard-reviewed.py').read_text();l=(D/'launcher-reviewed.py').read_text();driver=(D/'driver.jl').read_text()
checks['group_ANDsession_source']='int(fields[3]) == pgid' in g and "int(f[3]) in groups" in (D/'control_reviewed.py').read_text()
checks['absolute_terminal_deadline']='time.monotonic() >= args.deadline' in g
checks['missing_raw_failclosed_source']="raw=tomllib.loads((OUT/s['id']/'raw.toml').read_text());validate" in l and "except BaseException as e:record['errors'].append(repr(e))" in l
checks['context_finally']='finally:\n            Test.get_testset()===parent_testset' in driver and 'Test.@with_testset ts begin' in driver and 'Test.push_testset' not in driver
save(D/'additional-tests.json',dict(all_passed=all(checks.values()),checks=checks,scope='new pure-helper/admission AST synthetic tests plus explicitly source-only cleanup/context gates; no Julia/guard invocation/runtime kill proof'))
print(sum(checks.values()),'/',len(checks));require(all(checks.values()),'additional tests')
