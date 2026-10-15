"""Pure memory-schema checks and exact unchanged numerical implementation inverse."""
from control import *
from evidence import memory_report
import copy,math
checks={}
def check(n,v):req(v,n);checks[n]=True
def refuses(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError):checks[n]=True;return
 raise ValueError('Accepted invalid '+n)
samples=[dict(child_memory=['VmRSS: 40 kB','VmHWM: 50 kB','VmPeak: 400 kB','VmSwap: 0 kB'])];p=dict(child_maxrss_kib=60)
check('distinct_virtual_resident',memory_report(samples,p)['samples'][0]==dict(VmRSS=40,VmHWM=50,VmPeak=400,VmSwap=0))
for n,v in [('zero',0),('negative',-1),('nan',float('nan')),('bool',True),('below_sample',49)]:refuses(n,lambda v=v:memory_report(samples,dict(child_maxrss_kib=v)))
refuses('absent_terminal',lambda:memory_report(samples,{}));refuses('absent_samples',lambda:memory_report([],p))
for n,lines in [('virtual_only',['VmPeak: 400 kB']),('missing_hwm',['VmRSS: 40 kB','VmPeak: 400 kB','VmSwap: 0 kB']),('rss_exceeds_hwm',['VmRSS: 51 kB','VmHWM: 50 kB','VmPeak: 400 kB','VmSwap: 0 kB']),('wrong_unit',['VmRSS: 40 MB','VmHWM: 50 kB','VmPeak: 400 kB','VmSwap: 0 kB']),('duplicate',['VmRSS: 40 kB','VmRSS: 40 kB','VmHWM: 50 kB','VmPeak: 400 kB','VmSwap: 0 kB'])]:refuses(n,lambda lines=lines:memory_report([dict(child_memory=lines)],p))
fix=rd(D/'review-fix.json');initial=rd(D/'review.json');pins=rd(D/'preparation-pins.json')
check('rejected_review_preserved',initial['accepted'] is False and len(initial['findings'])==2 and initial['pins_sha256']==sha(D/'preparation-pins.json'))
check('initial48_hashes_reconciled',len(initial['sha256'])==48 and all(sha(fix['mappings'][n]['preserved'] if n in fix['mappings'] else n)==h for n,h in initial['sha256'].items()))
check('initial1166_pins_reconciled',len(pins['inventory'])==1166 and all(sha(fix['mappings'][n]['preserved'] if n in fix['mappings'] else n)==v['sha256'] for n,v in pins['inventory'].items()))
check('all_numerics_unchanged',(D/'driver.jl').read_text().replace('\nconst CAPI=SparseArrays.LibSuiteSparse','').replace('CAPI.UMFPACK_','API.UMFPACK_')==(D/'driver.jl.before-review').read_text())
check('no_stage_reservation',not Q.exists())
save(D/'review-fix-tests.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(q):sha(q) for q in [Path(__file__),D/'review-fix.json',D/'evidence.py',D/'driver.jl',D/'guard.py',D/'seal.py']},scope='Pure Python data and source checks; no Julia or processes'))
print(len(checks),'PASS')
