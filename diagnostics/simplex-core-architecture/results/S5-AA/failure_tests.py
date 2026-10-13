"""New synthetic Python failure tests only. No Julia or old auditor imports."""
import copy,tempfile,math,tomllib
import common as c
import audit as a
H=c.H;checks={}
def test(n,x):checks[n]=x is True;assert checks[n],n
schema=c.read(H/'schema.json');raw=tomllib.loads((H.parent/'S5-Y/portable/raw.toml').read_text())
test('saved_Y_schema_positive',all(a.data_checks(raw,schema).values()))
for k in schema['checks']:
 x=copy.deepcopy(raw);x['checks'][k]=False;test('false_predicate_'+k,not all(a.data_checks(x,schema).values()))
for n,mut in [('integer_bool',lambda x:x['checks'].update(no_return=1)),('missing_predicate',lambda x:x['checks'].pop('no_return')),('extra_predicate',lambda x:x['checks'].update(extra=True)),('wrong_cause',lambda x:x['observations'].update(cause_type='ErrorException')),('later_work',lambda x:x['after_record'].update(iterations=3)),('clock_offset',lambda x:x['entry_clock'].update(iteration_offset=1)),('clock_bool',lambda x:x['entry_clock'].update(start_ns=True)),('missing_table',lambda x:x.pop('checks'))]:
 x=copy.deepcopy(raw);mut(x)
 try:valid=all(a.data_checks(x,schema).values())
 except (KeyError,TypeError,AttributeError):valid=False
 test(n,not valid)
p={'elapsed_including_launch':1.0,'reason':'exit0','returncode':0,'pins_unchanged':True};test('terminal_positive',c.terminal_ok(p))
for n,v in [('late',120.0001),('nan',math.nan),('inf',math.inf),('bool',True),('negative',-1),('missing',None)]:test('terminal_'+n,not c.terminal_ok({**p,'elapsed_including_launch':v}))
for n,v in [('nonzero',1),('bool',False),('null',None)]:test('exit_'+n,not c.terminal_ok({**p,'returncode':v}))
refs=c.INITIAL_REFS
base=dict(accepted=True,unresolved_findings=[],stage='green',root=str(c.R),refs=refs,candidate_sha256=c.EXPECTED,command=c.command('green'),sha256={k:c.EXPECTED for k in c.stage_required('green')})
hashfn=lambda k:c.EXPECTED
test('stage_positive',c.stage_record_valid(base,'green',hashfn,refs))
for n,patch in [('wrong_stage',dict(stage='master')),('wrong_root',dict(root=str(c.M))),('wrong_refs',dict(refs={})),('wrong_command',dict(command=c.command('master'))),('missing_paths',dict(sha256={})),('rejected',dict(accepted=False)),('unresolved',dict(unresolved_findings=['x'])),('wrong_candidate',dict(candidate_sha256='x'))]:test(n,not c.stage_record_valid({**base,**patch},'green',hashfn,refs))
# GREEN evidence synthetic full23 positive, then omitted/tampered raw and invocation.
gh=c.H/'green';graw={k:'raw' for k in c.GREEN_RAW};giv={str(gh/n):'raw' for n in ('guard-invocation.json','guard-output.log','attempt-reserved.json')}
ga=dict(all_passed=True,checks={'gate':True},raw_sha256=graw,invocation_sha256=giv);gp=dict(all_passed=True,checks={'gate':True},sha256={str(gh/n):'raw' for n in ('audit.json','pins.json')})
def evidence(au=ga,po=gp,txt='Verdict: ACCEPTED\nUnresolved findings: []',hf=lambda k:'raw'):
 try:return c.green_evidence(hf,lambda p:au if Path(p).name=='audit.json' else po,lambda p:txt)
 except (AssertionError,KeyError,TypeError):return None
from pathlib import Path
test('green_full23',len(evidence())==23)
for n,mut in [('missing_raw',lambda x:x['raw_sha256'].pop('raw/case.toml')),('missing_inv',lambda x:x['invocation_sha256'].pop(str(gh/'guard-output.log'))),('failed_audit',lambda x:x.update(all_passed=False))]:
 x=copy.deepcopy(ga);mut(x);test(n,evidence(x) is None)
test('rejected_green_review',evidence(txt='Verdict: REJECTED\nUnresolved findings: []') is None)
test('unbound_green_post',evidence(po={**gp,'sha256':{}}) is None)
test('raw_hash_tamper',evidence(hf=lambda k:'changed' if str(k).endswith('raw/case.toml') else 'raw') is None)
# Full audit refuses missing/malformed raw/process/resources/pins before launch.
with tempfile.TemporaryDirectory(prefix='s5aa-offline-') as td:
 d=Path(td)
 for n in ('empty','process','pins','raw','resource'):
  if n=='process':(d/'process.json').write_text('{')
  elif n=='pins':(d/'process.json').write_text('{}');(d/'pins.json').write_text('{')
  elif n=='raw':(d/'pins.json').write_text('{}');(d/'resources.jsonl').write_text('')
  elif n=='resource':(d/'resources.jsonl').write_text('{\n')
  test('audit_refuses_'+n,a.audit('green',d)['all_passed'] is False)
# Durable guard log even refusal before output directory creation.
inv=c.invoke([c.sys.executable,str(c.G),'run',str(H/'missing-synthetic-pins.json'),str(H/'must-not-exist'),'--seconds','120','--','/no/numerical/command'],H/'synthetic-guard.log',H/'synthetic-invocation.json',c.R,c.absent())
test('prefolder_failure_logged',inv['returncode']!=0 and (H/'synthetic-guard.log').stat().st_size>0 and not (H/'must-not-exist').exists())
# Exclusive atomic records refuse replacement.
f=H/'synthetic-exclusive.json';c.dump(f,{'first':True})
try:c.dump(f,{'first':False});refused=False
except FileExistsError:refused=True
test('exclusive_record',refused and c.read(f)=={'first':True})
c.dump(H/'failure-tests.json',dict(checks=checks,all_passed=all(checks.values()),scope='Python-only synthetic failures; no Julia or numerical work'))
print(len(checks),'offline tests PASS')
