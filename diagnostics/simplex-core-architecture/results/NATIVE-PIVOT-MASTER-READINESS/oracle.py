"""Pure saved-data predicates; no file/process/Julia side effects."""
import math

def need(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int and v>=0
def test_results(raw,expected,loaded):
 need(raw['complete'] is True and raw['fatal']=='','Incomplete/fatal')
 need(raw['threads']==raw['blas_threads']==1 and raw['loaded']==loaded,'Loaded source/threads')
 root=raw['tests']
 def node(t):
  need(set(t)=={'name','pass','fail','error','broken','failures','children'},'Test schema')
  need(all(integer(t[k]) for k in ['pass','fail','error','broken']),'Counts')
  need(t['fail']==t['error']==t['broken']==0 and t['failures']==[],'Test failure')
  need(type(t['children']) is list,'Children')
  return t['pass']+sum(node(c) for c in t['children'])
 total=node(root);need(root['name']=='root' and root['pass']==0 and total==expected['assertions'],'Total')
 need([[t['name'],node(t)] for t in root['children']]==expected['groups'],'Exact groups')
 for t in root['children']:
  if t['name']=='Native pivot policy public integration':
   need(t['pass']==0 and [[c['name'],node(c)] for c in t['children']]==expected['public_children'],'Public tree')
   need(all(c['children']==[] for c in t['children']),'Public depth')
  else:need(t['children']==[],'Unexpected nested group')
 return dict(assertions=total,groups=expected['groups'],scope='Permanent tests only; no new observer/work measurement')
def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded=None):
 # Integrity/resource/closed-process validation is mandatory before calling this.
 if not (process.get('reason')=='wall_time' and process.get('returncode') in (-15,-9) and 'error' not in process and process.get('pins_unchanged') is True):return False
 if supervisor.get('returncode')!=1 or supervisor.get('hard_timeout') or 'cleanup_error' in supervisor:return False
 if not (math.isfinite(elapsed) and 0<=elapsed<=seconds):return False
 if raw is not None:
  # A present record is evidence only when its entire partial schema is valid.
  def valid_node(t):
   return (type(t) is dict and set(t)=={'name','pass','fail','error','broken','failures','children'}
    and type(t['name']) is str and bool(t['name'])
    and all(integer(t[k]) for k in ['pass','fail','error','broken'])
    and t['fail']==t['error']==t['broken']==0 and t['failures']==[]
    and type(t['children']) is list and all(valid_node(c) for c in t['children']))
  if not (type(raw) is dict and set(raw)=={'complete','fatal','loaded','threads','blas_threads','tests'}
   and raw['complete'] is False and raw['fatal']==''
   and type(raw['threads']) is int and raw['threads']==1
   and type(raw['blas_threads']) is int and raw['blas_threads']==1
   and loaded is not None and raw['loaded']==loaded and valid_node(raw['tests'])
   and raw['tests']['name']=='root' and raw['tests']['pass']==0):return False
 if any(s in log for s in ['TEST FAILURE:','BROKEN TEST:','ERROR:','LoadError','Test Failed','Test Error','OutOfMemoryError','Wrong package source','Thread count','Group/count mismatch']):return False
 # A checkpoint proves execution reached this driver; import-only/empty logs stay unknown.
 return 'BEGIN native_pivot_policy_tests.jl' in log
