"""Pure strict P011 payload oracle. No filesystem, process, Julia or old audit calls."""
import math,re
METRICS={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
PREPARATION=('load.toml','setup.toml','snapshot-before.toml','snapshot-after.toml')
SCHEDULE=[('first',0,'original'),('first',0,'concrete'),('warm',0,'concrete'),('warm',0,'original')]
for pair in range(1,5):
 for arm in (('original','concrete') if pair%2 else ('concrete','original')):SCHEDULE.append(('sample',pair,arm))
PAYLOAD=set(PREPARATION)|{'raw.toml'}|{f'record-{i}.toml' for i in range(1,13)}
def require(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int and 0<=v<=2**63-1
def number(v):return type(v) in (int,float) and math.isfinite(v) and 0<=v<=300

def metrics(v):
 require(type(v) is dict and set(v)==METRICS,'Metric fields')
 require(all(integer(v[k]) for k in ('bytes','events')),'Integral allocation counters')
 require(all(number(v[k]) for k in METRICS-{'bytes','events'}),'Finite bounded times')
 return dict(v)
def row(v,index):
 keys={'index','phase','pair','arm','inner_bytes','inner_events','assignment_ok','decision_ok','bytes_wrapper','events_wrapper','consumed_result'}
 require(type(v) is dict and set(v)==keys,'Record fields')
 phase,pair,arm=SCHEDULE[index-1]
 require(type(v['index']) is int and v['index']==index and type(v['pair']) is int and v['pair']==pair and v['phase']==phase and v['arm']==arm,'Record order/arm')
 require(v['assignment_ok'] is True and v['decision_ok'] is True,'Decision/assignment')
 require(integer(v['inner_bytes']) and integer(v['inner_events']),'Inner counters')
 for name in ('bytes_wrapper','events_wrapper','consumed_result'):metrics(v[name])
 return v

def warning_log(log):
 return bool(re.search(r'warning|world[ -]?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Failed|Test Error',log,re.I))

def validate(payload,loaded):
 require(type(payload) is dict and set(payload)==PAYLOAD,'Exact17 payload files')
 prep={name:metrics(payload[name]) for name in PREPARATION}
 raw=payload['raw.toml'];keys={'schema','complete','fatal','qualification','records','loaded','input_unchanged','replacement_unchanged'}
 require(type(raw) is dict and set(raw)==keys,'Raw fields')
 require(type(raw['schema']) is int and raw['schema']==1 and raw['complete'] is True and raw['fatal']=='','Incomplete/fatal')
 require(raw['qualification']=='diagnostic_only' and type(raw['loaded']) is dict and raw['loaded']==loaded,'Qualification/path')
 require(raw['input_unchanged'] is True and raw['replacement_unchanged'] is True,'Input/owner mutation')
 require(type(raw['records']) is list and len(raw['records'])==12,'Raw record count')
 rows=[]
 for i in range(1,13):
  v=row(payload[f'record-{i}.toml'],i);row(raw['records'][i-1],i)
  require(v==raw['records'][i-1],'Raw/file record mismatch');rows.append(v)
 summaries={}
 for arm in ('original','concrete'):
  selected=[v for v in rows if v['arm']==arm and v['phase']=='sample']
  summaries[arm]=dict(inner_bytes=[v['inner_bytes'] for v in selected],inner_events=[v['inner_events'] for v in selected],
    clean_wrapper_indices=[v['index'] for v in selected if all(v[k][f]==0 for k in ('bytes_wrapper','events_wrapper','consumed_result') for f in ('compile_seconds','recompile_seconds','gc_seconds'))])
 return dict(records=rows,preparation=prep,descriptive_sample_counters=summaries,source_schedule_invocations=60,
  qualification='diagnostic_only',causal_attribution='unresolved',p011_accepted=False,red_accepted=False,
  scope='Inner bytes/events are distinct executions. No subtraction, threshold, automatic cause or speedup. Nonzero compile/GC retained.')
