"""Fail-closed ordinary Test/TOML/process audit; no Julia or launch on import."""
from pathlib import Path
import json,math,re,struct,tomllib,statistics,sys
import common as C
import binding_checks as B

def integer(v):return type(v) is int and v>=0
def number(v):return type(v) in (int,float) and math.isfinite(v) and v>=0
def test_summary(log,name):
 rows=log.splitlines()
 for i,line in enumerate(rows):
  if line.startswith(name) and '|' in line and line.split('|',1)[0].strip()==name:
   header=next((rows[j] for j in range(i-1,-1,-1) if rows[j].startswith('Test Summary:')),None)
   C.require(header is not None,'missing Test header')
   keys=re.findall(r'Pass|Fail|Error|Broken|Total|Time',header.split('|',1)[1]);values=line.split('|',1)[1].split()
   C.require(len(keys)==len(values),'Test summary columns')
   record={k:int(v) for k,v in zip(keys,values) if k!='Time'}
   return record
 raise ValueError('missing ordinary Test summary '+name)
def stats_ok(r,measured=False):
 C.require(isinstance(r,dict),'stats type')
 C.require(all(number(r[k]) for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds')),'invalid time')
 C.require(integer(r['bytes']) and integer(r['events']),'invalid allocation type')
 if measured:C.require(r['compile_seconds']==r['recompile_seconds']==0,'measured compilation')
def bits(v,T):return struct.pack('>f' if T=='Float32' else '>d',v).hex()
def expected_matrix(T,layout):
 return [bits(64.0 if i==j else ((-1 if (i+j)%2==0 else 1)*(1+(i+2*j)%5))/64 if layout=='dense' or abs(i-j)==1 else 0.0,T) for j in range(1,65) for i in range(1,65)]
def check_cost(r,side):
 C.require(r.get('side')==side and type(r.get('cases')) is list and len(r['cases'])==8,'cost side/count')
 seen=set()
 for q in r['cases']:
  key=(q['type'],q['layout'],q['unreliable']);C.require(key not in seen and key[0] in ('Float32','Float64') and key[1] in ('sparse','dense') and type(key[2]) is bool,'case keys');seen.add(key)
  T,layout,bad=key;C.require(type(q['dimension']) is int and q['dimension']==64,'dimension')
  matrix=expected_matrix(T,layout);C.require(q['matrix_bits']==matrix,'matrix bits')
  zero=bits(0,T);rhs=matrix[0::64];point=[bits(0.5 if bad else 1,T)]+[zero]*63
  C.require(type(q['nnz']) is int and q['nnz']==sum(b!=zero for b in matrix),'nnz')
  C.require(len(q['warm'])==3 and len(q['samples'])==7,'3 warm/7 samples')
  stats_ok(q['preparation']);stats_ok(q['post_warm_gc'])
  for w in q['warm']:stats_ok(w)
  C.require(type(q['solve_entries_total']) is int and type(q['stop_entries_total']) is int and q['solve_entries_total']==q['stop_entries_total']==(10 if bad else 0),'whole call counts')
  C.require(integer(q['retained_julia_bytes']),'retained bytes')
  for i,s in enumerate(q['samples'],1):
   stats_ok(s,True);C.require(s['index']==i and type(s['index']) is int,'sample index')
   C.require(s['finite'] is True and s['reliable'] is (not bad) and s['owners_preserved'] is True,'quality/owners')
   C.require(s['point_bits']==point and s['rhs_bits']==rhs,'unchanged inputs/output bits')
   C.require(s['absolute_bits']==bits(32 if bad else 0,T) and s['relative_bits']==bits(1/3 if bad else 0,T),'literal quality')
   C.require(type(s['solve_entries']) is int and type(s['stop_entries']) is int and s['solve_entries']==s['stop_entries']==int(bad),'sample work counts')
 C.require(len(seen)==8,'complete Cartesian cases')
 return True

def compare_cost(ref,record):
 check_cost(ref,'reference');check_cost(record,'candidate')
 reports=[]
 for a,b in zip(ref['cases'],record['cases']):
  C.require((a['type'],a['layout'],a['unreliable'])==(b['type'],b['layout'],b['unreliable']),'paired cases')
  C.require(b['retained_julia_bytes']<=a['retained_julia_bytes'],'new retained graph')
  for x,y in zip(a['samples'],b['samples']):
   C.require(all(x[k]==y[k] for k in ('absolute_bits','relative_bits','point_bits','rhs_bits','finite','reliable','solve_entries','stop_entries','owners_preserved')),'paired outputs/work')
  C.require(statistics.median(s['bytes'] for s in b['samples'])<=statistics.median(s['bytes'] for s in a['samples']) and statistics.median(s['events'] for s in b['samples'])<=statistics.median(s['events'] for s in a['samples']),'systematic default API allocation increase')
  reference_times=[q['seconds'] for q in a['samples']];candidate_times=[q['seconds'] for q in b['samples']]
  rm=statistics.median(reference_times);cm=statistics.median(candidate_times)
  C.require(rm>0,'zero reference median')
  reports.append(dict(type=a['type'],layout=a['layout'],unreliable=a['unreliable'],reference_median_seconds=rm,candidate_median_seconds=cm,median_ratio=cm/rm,reference_range=[min(reference_times),max(reference_times)],candidate_range=[min(candidate_times),max(candidate_times)]))
 return reports

def audit_phase(phase):
 C.phase_ok(phase);out=C.RUN/phase
 seal=C.read(out/'seal.json');proc=C.read(out/'guard/process.json');supervisor=C.read(out/'supervisor.json');done=C.read(out/'completion.json')
 C.require(type(proc['returncode']) is int and proc['returncode']==seal['expected_exit'] and proc['reason']=='exit'+str(seal['expected_exit']) and proc['pins_unchanged'] is True,'exit/guard/pins')
 C.require(supervisor['accepted'] is True and done['supervisor_accepted'] is True and number(done['total_inclusive_seconds']) and done['total_inclusive_seconds']<=1800,'inclusive guard')
 C.require(proc['command']==seal['command']==C.command(phase),'command')
 C.require(C.read(out/'postflight.json')['conflicts']==[],'process closure')
 attempt=C.read(out/'attempt.json');ad=C.read(attempt['admission_path']);C.require(C.sha(attempt['admission_path'])==attempt['admission_sha256'] and ad.get('accepted') is True and ad.get('seal_sha256')==C.sha(out/'seal.json') and C.sha(ad['review_report'])==ad['review_report_sha256'],'admission changed')
 pins=C.read(out/'pins.json');B.interpreter(seal,pins,sys.executable)
 for admitted_head in (C.read(out/'prelaunch-host.json')['refs']['HEAD'],C.read(out/'postflight.json')['refs']['HEAD'],C.git('rev-parse','HEAD')):B.head(seal,ad,admitted_head)
 C.require(C.sha(out/'pins.json')==seal['pins_sha256']==proc['pins_sha256'] and C.read(out/'guard/pins.json')==pins,'sealed manifest changed')
 C.require(all(C.sha(n)==v['sha256'] for n,v in pins['inventory'].items()),'postexit pins')
 log=(out/'guard/run.log').read_text(errors='replace')
 C.require(not any(s in log.lower() for s in ('world age','error during test','undefvarerror','syntax:','segmentation fault')),'load/test/runtime defect')
 key='TASK4_RED' if phase=='red' else 'TASK4_GREEN' if phase=='green' else 'TASK4_COST'
 summary=test_summary(log,key)
 if phase=='red':
  C.require(summary.get('Pass')==7 and summary.get('Fail')==1 and summary.get('Error',0)==0 and summary.get('Broken',0)==0 and summary.get('Total')==8,'sole expected RED')
  C.require(log.count('Test Failed at')==1 and 'Expression: recovery_ready === true' in log,'behavioral RED, not missing API')
 else:
  C.require(summary.get('Pass',0)>0 and summary.get('Total')==summary.get('Pass') and all(summary.get(k,0)==0 for k in ('Fail','Error','Broken')),'ordinary tests not green')
  C.require(('TASK4_GREEN_COMPLETED' if phase=='green' else 'TASK4_COST_COMPLETED '+seal['phase'].split('-')[0]) in log,'completion marker')
 if phase=='green':
  expected=C.read(C.D/'contract.json')['green_includes']
  actual=re.findall(r'^TASK4_INCLUDED (.+)$',log,re.M)
  C.require(actual==expected,'exact ordinary include order/coverage')
  records=tomllib.loads((out/'result.toml').read_text())['cases'];C.require(len(records)==2 and {r['type'] for r in records}=={'Float32','Float64'},'endpoint cases')
  for q in records:
   for k in ('preparation','whole_fallback','component_preparation','component_revalidation','component_reset'):stats_ok(q[k])
   C.require(all(q[k] is True for k in ('original_primal_certified','original_optimality_certified','invalid_witness_rejected','invalid_row_rejected','trajectory_changed')),'endpoint oracles')
   C.require(all(type(q[k]) is int for k in ('iterations','factorizations','attempted_weight_rows','avoided_weight_rows','core_and_weight_ftran','core_and_weight_btran','final_ftran','final_btran')) and all(type(v) in (int,float) and math.isfinite(v) for k in ('point','witness') for v in q[k]) and q['point']==[1,0] and q['witness']==[1,0] and q['iterations']==q['factorizations']==q['attempted_weight_rows']==q['avoided_weight_rows']==1,'endpoint counts')
   C.require((q['core_and_weight_ftran'],q['core_and_weight_btran'])==(1,3),'fallback work')
 if phase.endswith('cost'):
  side=phase.split('-')[0];record=tomllib.loads((out/'result.toml').read_text());check_cost(record,side)
  C.require(summary.get('Pass')==272,'cost assertion budget')
  if phase=='candidate-cost':
   ref=tomllib.loads((C.RUN/'reference-cost/result.toml').read_text());check_cost(ref,'reference')
   comparison=compare_cost(ref,record)
   C.fresh(out/'comparison.json',dict(cases=comparison,limitation='Separate processes, not interleaved; no universal or end-to-end speedup claim'))
 C.require(proc['terminal_memory']['available_kib']>=6*1024**2 and proc['terminal_memory']['swap_used_kib']<=1024**2,'terminal memory')
 samples=[json.loads(s) for s in (out/'guard/resources.jsonl').read_text().splitlines()]
 C.require(samples and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples),'resource guards')
 bindings={str(p):C.sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='audit.json'}
 if phase=='candidate-cost':bindings[str(C.RUN/'reference-cost/result.toml')]=C.sha(C.RUN/'reference-cost/result.toml')
 bindings[attempt['admission_path']]=C.sha(attempt['admission_path']);bindings[ad['review_report']]=C.sha(ad['review_report'])
 C.fresh(out/'audit.json',dict(accepted=True,phase=phase,test_summary=summary,bindings=bindings,production_admission=False,scope='this guarded stage only; independent result review remains required'))
 return True
if __name__=='__main__':
 C.require(len(sys.argv)==2,'phase required');audit_phase(sys.argv[1])
