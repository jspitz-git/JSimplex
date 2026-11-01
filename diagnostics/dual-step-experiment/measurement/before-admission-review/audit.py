from pathlib import Path
import sys,json,math,statistics as S
D=Path(__file__).resolve().parent
TAGS=('PREP','QUAL','REFERENCE_WORK','INSPECT','FALLBACK','SAMPLE','CHECK','PREP_GC','CASE_BEGIN','CASE_DONE')
def records(log):
 out={k:[] for k in TAGS}
 for line in log.splitlines():
  tag=line.split(' ',1)[0]
  if tag not in out:continue
  pairs=[x.split('=',1) for x in line.split()[1:]]
  if any(len(x)!=2 for x in pairs) or len({k for k,v in pairs})!=len(pairs):raise ValueError('scalar record schema')
  out[tag].append(dict(pairs))
 return out
NAMES=('afiro.mps','netlib/adlittle.mps','netlib/sc50a.mps','generated/degenerate-box.mps','generated/phase-one.mps','generated/scaled-diagonal.mps')
CASES=[f'n{n}_{d}' for n in (16,64) for d in ('sparse','dense')]+['mps_'+n.replace('/','_').replace('.','_')+'_p'+str(p) for n in NAMES for p in (0,1)]
def require(v,m):
 if not v:raise ValueError(m)
def stats(xs):
 med=S.median(xs);return dict(median=med,min=min(xs),max=max(xs),mad=S.median(abs(x-med) for x in xs))
def analyze(mode,log):
 r=records(log);require('TASK6_COMPLETED '+mode in log,'completion marker');require('Test Failed' not in log and 'Error During Test' not in log,'ordinary tests no failures/errors')
 require([x['case'] for x in r['CASE_BEGIN']]==CASES and [x['case'] for x in r['CASE_DONE']]==CASES,'all16 frozen cases completed in order')
 require(len(r['PREP'])==16,'all input preparation records');summary={}
 if mode=='qualify':
  require(len(r['QUAL'])==len(r['REFERENCE_WORK'])==16 and len(r['FALLBACK'])==1,'all qualification/whole reference count records')
  for q in r['QUAL']:
   require(q['status']==q['reference']=='OPTIMAL' and math.isfinite(float(q['objective'])),'complete optimal result '+q['case'])
   require(int(q['entries'])<=1 and int(q['legacy_fallbacks'])<=1 and int(q['import_failures'])==0,'truthful activation')
   if q['case'].startswith('n'):
    require(int(q['EC_accepted_pivots'])>0 and all(int(q[k])==0 for k in ('legacy_fallbacks','original_retries','original_cleanups','original_recoveries')),'designated activated/no fallback '+q['case'])
    require(int(q['KC_dense_prices' if q['case'].endswith('dense') else 'KC_sparse_prices'])>0,'actual designated route')
   inspected=[x for x in r['INSPECT'] if x['case']==q['case']]
   require({x['stage'] for x in inspected}==({'setup','exit'} if int(q['imports']) else set()),'actual inspection stage membership')
   for x in inspected:
    require(int(x['graph_bytes'])>0 and int(x['unique_vector_payload_bytes'])>0,'real graph/capacity capture')
    for k,v in x.items():
     if k.endswith('_capacity'):require(int(v)>=int(x[k[:-9]+'_length']),'physical capacity >= logical '+k)
   if inspected:
    a=next(x for x in inspected if x['stage']=='setup');b=next(x for x in inspected if x['stage']=='exit')
    for k,v in a.items():
     if k.endswith('_capacity') and k.startswith(('proposal_','journal_','invariants_','supports_','kernels_','recovery_','residual_scale','rows_')):require(b.get(k)==v,'fixed engine reserve retained '+k)
   summary[q['case']]=q
  f=r['FALLBACK'][0];require(f['status']==f['reference']=='INFEASIBLE' and int(f['EC_accepted_pivots'])==0 and int(f['legacy_fallbacks'])==1,'genuine fallback is not activation')
 else:
  require(len(r['SAMPLE'])==224 and len(r['CHECK'])==224 and len(r['PREP_GC'])==16,'224 complete windows/checks/16 separately recorded warm GCs')
  for c in CASES:
   rows=[x for x in r['SAMPLE'] if x['case']==c];checks=[x for x in r['CHECK'] if x['case']==c]
   expected=[(phase,str(pair),arm) for phase,count in [('warm',2),('measure',5)] for pair in range(1,count+1) for arm in (('reference','candidate') if pair%2 else ('candidate','reference'))]
   require([(x['phase'],x['pair'],x['arm']) for x in rows]==expected,'exact rotated schedule '+c)
   require([(x['phase'],x['pair'],x['arm']) for x in checks]==expected and all(x['passed']=='true' for x in checks),'all external checks '+c)
   for x in rows:
    require(x['status']=='OPTIMAL' and math.isfinite(float(x['objective'])),'valid terminal output '+c)
    require(all(math.isfinite(float(x[k])) and float(x[k])>=0 for k in ('seconds','bytes','allocs','gctime','compile','recompile','record_bytes')),'finite nonnegative metrics')
    if x['phase']=='measure':require(float(x['compile'])==float(x['recompile'])==0,'compile-zero accepted window '+c)
    if x['arm']=='candidate':
     require(int(x['entries'])<=1 and int(x['legacy_fallbacks'])<=1 and int(x['import_failures'])==0,'bounded candidate activation')
     if c.startswith('n'):require(int(x['EC_accepted_pivots'])>0 and all(int(x[k])==0 for k in ('legacy_fallbacks','original_retries','original_cleanups','original_recoveries')),'designated candidate actual commits')
   measured=[x for x in rows if x['phase']=='measure'];arms={a:[x for x in measured if x['arm']==a] for a in ('reference','candidate')}
   summary[c]={a:{k:stats([float(x[k]) for x in xs]) for k in ('seconds','bytes','allocs','gctime','iterations','refactors','record_bytes')} for a,xs in arms.items()}
   for k in ('seconds','bytes','allocs'):
    ratios=[float(b[k])/float(a[k]) for a,b in zip(arms['reference'],arms['candidate'])]
    summary[c]['paired_'+k]=stats(ratios)
   summary[c]['activated']=all(int(x['EC_accepted_pivots'])>0 and int(x['legacy_fallbacks'])==0 for x in arms['candidate'])
 return dict(accepted=True,mode=mode,records=r,summary=summary,scope='ordinary focused whole-solve qualification or five paired solve windows; no native allocation ledger/large-model claim')
def main():
 mode=sys.argv[1];out=Path(sys.argv[2]);log=(out/'guard/run.log').read_text();result=analyze(mode,log)
 with (out/'audit.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(accepted=True,mode=mode,cases=len(result['summary']))))
if __name__=='__main__':main()
