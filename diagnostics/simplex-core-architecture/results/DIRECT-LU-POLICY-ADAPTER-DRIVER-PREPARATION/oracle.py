"""Pure saved-data validation; no filesystem, process or Julia side effects."""
import math

def need(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int and v>=0
def validate_node(t,allow_fail=False):
 need(type(t) is dict and set(t)=={'name','pass','fail','error','broken','failures','children'},'Test schema')
 need(type(t['name']) is str and bool(t['name']),'Name')
 need(all(integer(t[k]) for k in ['pass','fail','error','broken']),'Counts')
 need(type(t['failures']) is list and all(type(x) is str and bool(x) for x in t['failures']),'Failure schema')
 need(len(t['failures'])==t['fail']+t['error'],'Failure count')
 need(t['error']==t['broken']==0 and (allow_fail or t['fail']==0),'Test failure/error/broken')
 need(type(t['children']) is list,'Children')
 return sum(t[k] for k in ['pass','fail','error','broken'])+sum(validate_node(c,allow_fail) for c in t['children'])
def test_results(raw,expected,loaded,phase):
 need(type(raw) is dict and set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'},'Raw schema')
 need(raw['phase']==phase and raw['complete'] is True and raw['fatal']=='','Incomplete/fatal/phase')
 need(type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'Threads')
 need(raw['loaded']==loaded,'Loaded source')
 red=phase.startswith('red');root=raw['tests'];total=validate_node(root,red)
 need(root['name']=='root' and all(root[k]==0 for k in ['pass','fail','error','broken']) and root['failures']==[],'Root')
 need(total==expected['assertions'],'Total assertions')
 actual=[[t['name'],t['pass'],t['fail'],t['error'],t['broken']] for t in root['children']]
 need(actual==expected['groups'] and all(t['children']==[] for t in root['children']),'Exact leaf tree')
 return dict(assertions=total,groups=actual,scope='Expected missing-contract RED' if red else 'Adapter correctness only; no cost/public-solver acceptance')
def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):
 if not (process.get('reason')=='wall_time' and process.get('returncode') in (-15,-9) and 'error' not in process and process.get('pins_unchanged') is True):return False
 if supervisor.get('returncode')!=1 or supervisor.get('hard_timeout') or 'cleanup_error' in supervisor:return False
 if not (type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=seconds):return False
 if raw is not None:
  try:
   need(type(raw) is dict and set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'},'Partial schema')
   need(raw['phase']==phase and raw['complete'] is False and raw['fatal']=='','Partial flags')
   need(type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1 and raw['loaded']==loaded,'Partial source')
   validate_node(raw['tests'],False)
   need(raw['tests']['name']=='root' and all(raw['tests'][k]==0 for k in ['pass','fail','error','broken']),'Partial root')
  except (KeyError,TypeError,ValueError):return False
 if any(s in log for s in ['TEST FAILURE:','BROKEN TEST:','ERROR:','FATAL DRIVER:','LoadError','Test Failed','Test Error','OutOfMemoryError','Wrong package source','Thread count','GROUP/COUNT MISMATCH']):return False
 return 'BEGIN adapter driver '+phase in log
