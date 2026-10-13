"""Exclusive new offline synthetic failures. No Julia, prior scripts or numerics."""
from common import *
from audit import data_checks,audit
import tempfile,copy
schema=read(H/'schema.json');observations={k:(0 if t=='int' else False if t=='bool' else '') for k,t in schema['observations'].items()};observations.update(schema['values']);observations.update(callbacks=6,sentinel_type='LinearAlgebra.SingularException',cause_type='LinearAlgebra.SingularException',caught_type='JSimplex.DiagnosticObserverFailure{LinearAlgebra.SingularException}')
record=dict(iterations=2,refactorizations=2,crash_pivot=2,refactor_other=1,crash_fallback=1,crash_accepted=0,callbacks=6)
raw=dict(checks={k:True for k in schema['checks']},observations=observations,refactor_work=dict(iterations=2,refactorizations=2),fallback_record=record,after_record=dict(record),entry_clock=dict(start_ns='123',iteration_offset=0,refactorization_offset=0),entry_work=dict(iterations=0,refactorizations=0))
c={'synthetic_control':all(data_checks(raw,schema).values())}
for name,mutate in [('false_predicate',lambda x:x['checks'].update(no_return=False)),('integer_predicate',lambda x:x['checks'].update(no_return=1)),('missing_predicate',lambda x:x['checks'].pop('no_return')),('wrong_cause',lambda x:x['observations'].update(cause_identity=False)),('wrong_type',lambda x:x['observations'].update(cause_type='ErrorException')),('extra_work',lambda x:x['after_record'].update(refactorizations=3)),('wrong_merge',lambda x:x['refactor_work'].update(iterations=3))]:
 bad=copy.deepcopy(raw);mutate(bad);c[name]=not all(data_checks(bad,schema).values())
p=dict(reason='exit0',returncode=0,pins_unchanged=True,elapsed_including_launch=1.0)
c['terminal_control']=terminal_ok(p)
for n,v in [('overrun',120.01),('nan',float('nan')),('bool',True),('negative',-1)]:c['terminal_'+n]=not terminal_ok(dict(p,elapsed_including_launch=v))
c['nonzero_exit']=not terminal_ok(dict(p,returncode=1));c['changed_pins']=not terminal_ok(dict(p,pins_unchanged=False))
with tempfile.TemporaryDirectory(prefix='s5y-offline-') as tmp:
 t=Path(tmp);c['missing_input_failclosed']=audit(t)['all_passed'] is False
 (t/'process.json').write_text('{bad');c['malformed_input_failclosed']=audit(t)['all_passed'] is False
 cmd=[sys.executable,str(G),'run',str(t/'missing-pins.json'),str(t/'never-created'),'--seconds','120','--','/usr/bin/false']
 inv=invoke(cmd,t/'guard-output.log',t/'invocation.json',R,absent());c['prefolder_refusal_logged']=inv['returncode']==1 and (t/'guard-output.log').stat().st_size>0 and not (t/'never-created').exists() and read(t/'invocation.json')==inv
 dump(t/'reserved.json',{'attempt':1})
 try:dump(t/'reserved.json',{'attempt':2});c['exclusive_reservation']=False
 except FileExistsError:c['exclusive_reservation']=read(t/'reserved.json')=={'attempt':1}
 # preserve the synthetic failure log and invocation outside the temporary folder
 with (H/'synthetic-guard-refusal.log').open('x') as f:f.write((t/'guard-output.log').read_text())
 dump(H/'synthetic-guard-invocation.json',inv)
dump(H/'failure-tests.json',dict(checks=c,all_passed=all(c.values()),scope='Synthetic Python/guard checks only; zero Julia.'))
print(json.dumps(c));assert all(c.values())
