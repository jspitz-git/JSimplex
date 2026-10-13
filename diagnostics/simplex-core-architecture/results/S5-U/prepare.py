"""One exclusive offline admission preparation; no Julia or old script execution."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();H=Path(__file__).resolve().parent;T=H.parent/'S5-T';S=H.parent/'S5-S'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def save(p,x):
 with Path(p).open('x') as f:f.write(x)
c={}
for n,num in [('pins.json',891),('evidence.json',6),('independent.json',7),('closure.json',25)]:
 x=read(T/n)['sha256'];c[n]=len(x)==num and all(sha(k)==v for k,v in x.items())
for n,num in [('evidence.json',21),('independent.json',8),('closure.json',14),('publication-check.json',6)]:
 x=read(T/n);c['gates_'+n]=len(x['checks'])==num and x['all_passed'] is True and all(v is True for v in x['checks'].values())
assert all(c.values());dump(H/'entry-checks.json',dict(checks=c,all_passed=True))
save(H/'original-test.jl',(R/'test/simplex_precision_tests.jl').read_text());save(H/'guard.py',(S/'guard-reviewed.py').read_text())
p=read(T/'provenance.json');suffix=(T/'append.jl').read_text()
record='''    U_RECORD[]=(checks=checks,at_throw=probe.at_throw,after_unwind=after,
        observations=(stage=probe.stage,start_ns=string(progress.start_ns),
            caught_type=string(typeof(caught)),backend=string(backend),
            sentinel_type=string(typeof(sentinel)),stop_calls=probe.stop_calls,
            update=string(update),scalar=string(T),throws=probe.throws,
            guard_exception_type=string(typeof(guard.exception)),returned=returned,
            callbacks=probe.callbacks))
'''
insertions=[dict(anchor='function _basis_initialization_stop_checks()\n',before='',after='    U_COUNTS[1]+=1\n'),dict(anchor='        ws=JSimplex.initialize_from_basis(p,basis,options;policy,progress,stop=guard)\n',before='        U_COUNTS[2]+=1\n',after=''),dict(anchor='@testset "Supplied-basis checkpoint stop preserves ownership and consumed work" begin\n',before='',after='    U_COUNTS[3]+=1\n'),dict(anchor='    return checks\n',before=record,after='')]
executed=suffix
for x in insertions:
 assert executed.count(x['anchor'])==1;executed=executed.replace(x['anchor'],x['before']+x['anchor']+x['after'])
inverse=executed
for x in reversed(insertions):inverse=inverse.replace(x['before']+x['anchor']+x['after'],x['anchor'])
assert inverse==suffix
save(H/'expected-suffix.jl',executed)
expected={k:p[v] for k,v in [('candidate','candidate_sha256'),('prefix','prefix_sha256'),('suffix','append_sha256')]};expected['executed']=hashlib.sha256(executed.encode()).hexdigest();expected['checks']=p['predicate_names']
save(H/'expected.toml',''.join(k+' = '+json.dumps(v)+'\n' for k,v in expected.items()))
save(H/'insertions.toml','\n'.join('[[insertions]]\n'+''.join(k+' = '+json.dumps(v)+'\n' for k,v in x.items()) for x in insertions))
dump(H/'schema.json',read(S/'schema.json'))
dump(H/'source-preparation.json',dict(checks=dict(exact_inverse=inverse==suffix,one_init=executed.count('JSimplex.initialize_from_basis(')==1,one_testset=executed.count('@testset')==1,forty_assertions=executed.count('@test checks.')==40,actual_test_unchanged=sha(R/'test/simplex_precision_tests.jl')==p['prefix_sha256'],guard_byteidentical=sha(H/'guard.py')==sha(S/'guard-reviewed.py')),all_passed=True,sha256={str(H/n):sha(H/n) for n in ('prepare.py','original-test.jl','expected-suffix.jl','expected.toml','insertions.toml','schema.json','guard.py')}))
print('S5-U offline source preparation PASS; actual test unchanged')
