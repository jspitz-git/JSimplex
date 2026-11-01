from pathlib import Path
import importlib.util,json,copy
D=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('new_task6_parser',D/'audit.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
def line(tag,d):return tag+' '+' '.join(str(k)+'='+str(v) for k,v in d.items())
def fixture(mode):
 rows=[]
 for c in A.CASES:
  rows+=[line('CASE_BEGIN',dict(case=c,mode=mode)),line('PREP',dict(case=c))]
  if mode=='qualify':
   q=dict(case=c,status='OPTIMAL',reference='OPTIMAL',objective='1',entries='1',imports='1',import_failures='0',legacy_fallbacks='0',original_retries='0',original_cleanups='0',original_recoveries='0',EC_accepted_pivots='1',KC_dense_prices='1',KC_sparse_prices='1')
   rows+=[line('QUAL',q),line('REFERENCE_WORK',dict(case=c))]
   for stage in ('setup','exit'):rows+=[line('INSPECT',dict(case=c,stage=stage,graph_bytes='100',unique_vector_payload_bytes='80',proposal_ids_length='10',proposal_ids_capacity='10'))]
  else:
   for phase,count in [('warm',2),('measure',5)]:
    for pair in range(1,count+1):
     for arm in (('reference','candidate') if pair%2 else ('candidate','reference')):
      d=dict(case=c,phase=phase,pair=pair,arm=arm,seconds='0.1' if arm=='reference' else '0.08',bytes='100',allocs='5',gctime='0',compile='0',recompile='0',record_bytes='0',status='OPTIMAL',objective='1',iterations='1',refactors='1')
      if arm=='candidate':d.update(entries='1',import_failures='0',legacy_fallbacks='0',original_retries='0',original_cleanups='0',original_recoveries='0',EC_accepted_pivots='1')
      rows+=[line('SAMPLE',d),line('CHECK',dict(case=c,phase=phase,pair=pair,arm=arm,passed='true'))]
   rows+=[line('PREP_GC',dict(case=c))]
  rows+=[line('CASE_DONE',dict(case=c,mode=mode))]
 if mode=='qualify':rows+=[line('FALLBACK',dict(status='INFEASIBLE',reference='INFEASIBLE',EC_accepted_pivots='0',legacy_fallbacks='1'))]
 count=236 if mode=='qualify' else 749
 rows+=['Test Summary: | Pass Total Time',f'Task6 {mode} whole verified solves | {count} {count} 1.0s','TASK6_COMPLETED '+mode]
 return '\n'.join(rows)+'\n'
checks=[]
def test(name,mode,raw,accepted):
 try:A.analyze(mode,raw);actual=True
 except (ValueError,KeyError,ZeroDivisionError):actual=False
 if actual!=accepted:raise ValueError(name)
 checks.append(dict(check=name,passed=True))
for mode in ('qualify','compare'):
 raw=fixture(mode);test('valid_'+mode,mode,raw,True)
 test('missing_completion_'+mode,mode,raw.replace('TASK6_COMPLETED','WRONG_COMPLETED'),False)
 test('missing_case_'+mode,mode,raw.replace('CASE_DONE case=n16_sparse','WRONG_DONE case=n16_sparse'),False)
 test('wrong_status_'+mode,mode,raw.replace('status=OPTIMAL','status=NUMERICAL_ERROR',1),False)
 test('duplicate_key_'+mode,mode,raw.replace('CASE_BEGIN case=n16_sparse','CASE_BEGIN case=n16_sparse case=n16_sparse',1),False)
 test('zero_designated_commits_'+mode,mode,raw.replace('EC_accepted_pivots=1','EC_accepted_pivots=0',1),False)
 test('wrong_ordinary_count_'+mode,mode,raw.replace('Pass Total Time','Pass Total Time').replace(f'| {236 if mode=="qualify" else 749} ', '| 1 ',1),False)
raw=fixture('qualify')
test('duplicate_qualification_case','qualify',raw.replace('QUAL case=n16_dense','QUAL case=n16_sparse',1),False)
test('duplicate_reference_case','qualify',raw.replace('REFERENCE_WORK case=n16_dense','REFERENCE_WORK case=n16_sparse',1),False)
test('missing_ordinary_summary','qualify',raw.replace('Task6 qualify whole verified solves |','WRONG qualify |'),False)
test('ordinary_broken_not_pass','qualify',raw.replace('Pass Total Time','Pass Broken Total Time').replace('| 236 236 1.0s','| 235 1 236 1.0s'),False)
raw=fixture('qualify');test('bad_capacity','qualify',raw.replace('proposal_ids_capacity=10','proposal_ids_capacity=9',1),False)
test('physical_reserve_changed','qualify',raw.replace('stage=exit graph_bytes=100 unique_vector_payload_bytes=80 proposal_ids_length=10 proposal_ids_capacity=10','stage=exit graph_bytes=100 unique_vector_payload_bytes=80 proposal_ids_length=10 proposal_ids_capacity=11',1),False)
test('missing_actual_route','qualify',raw.replace('KC_sparse_prices=1','KC_sparse_prices=0',1),False)
test('false_fallback','qualify',raw.replace('FALLBACK status=INFEASIBLE','FALLBACK status=OPTIMAL'),False)
raw=fixture('compare');test('compile_not_zero','compare',raw.replace('phase=measure pair=1 arm=reference seconds=0.1 bytes=100 allocs=5 gctime=0 compile=0','phase=measure pair=1 arm=reference seconds=0.1 bytes=100 allocs=5 gctime=0 compile=0.1',1),False)
test('wrong_pair_order','compare',raw.replace('phase=measure pair=1 arm=reference','phase=measure pair=1 arm=candidate',1),False)
test('nonfinite_metrics','compare',raw.replace('seconds=0.1','seconds=NaN',1),False)
test('failed_verification','compare',raw.replace('passed=true','passed=false',1),False)
test('missing_warm_gc','compare',raw.replace('PREP_GC case=n16_sparse','WRONG_GC case=n16_sparse',1),False)
with (D/'parser-tests.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,scope='new pure offline parser synthetic fixtures only; not Julia/numerical evidence'),f,indent=2)
print('PASS parser synthetic cases',len(checks))
