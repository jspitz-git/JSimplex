"""Prospective source-branch enumeration; no Julia or simulated floating arithmetic."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
groups=[
('BG slots: import and stable q',4*8+3*2+4+4+1+3+1,'four imports8 +three nonempty2 +four q/order +four badq +square +three CSC +nonfinite'),
('BG slots: unlink, exact zero, free reuse and local guards',3+2*2+50*2+16+16+1+4*2+6,'3baseline+two zero2+50reuse2+16insert+16delete+empty+four value2+five throws/snapshot'),
('BG slots: capacity and allocation failure',5+3*5+4+7*4+3+1,'5capacity+three growth5+dirty success4+seven OOM4+invalid3+fill1'),
('BG slots: swaps and rotations',2*(4*3+1+2+1+1+1+3+1)+3*3,'two q arms22 each +three shapes3'),
('BG slots: checker detects corrupt structures',12+1,'12 independent corruptions +original'),
('Seven fixed fixtures, two policies, direct reference',4*91+10*(91+8*55+5+55+2*12+7*14+14),'pair_state10;solve_pair14;replace_pair55;all cases91;ten n>=2 add8replacements/copy5+savedreplacement/refactor24/sevensaved98/finalsaved14'),
('Private scratch and supported routes',2*(2*4+14+1+1+14+1+3+3+1)+2*(3*2+2)+2+3+1+1,'two arms46;stub16solve+2update+3factory+calls+Float32factory'),
('Fallback, normalization fallback, q, transactional refactor',2*(2+3*55+14+1+14+14+1+14)+1+10,'two q arms225 +unsafe normalization1+pair10'),
('Exact storage branches, failures, ordering',5*13+6+5+14+(55+2+2*14+55)+3+2*3,'five explicit successes13;zero fail6;imported nonfinite5;finiteoverflow14;map140;growth3;twotraces3')]
expected=dict(red=dict(assertions=8,groups=[['Missing dynamic BG U contracts (eight expected failures)',0,8,0,0]]),green=dict(assertions=sum(n for _,n,_ in groups),groups=[[name,n,0,0,0] for name,n,_ in groups]))
work=dict(scope='Prospective source-derived API/setup entries only, not runtime/native instruction counts',groups={
 'lifecycle':dict(cases=14,cases_with_updates=10,backend_construction_attempts=152,singular_attempts=14,real_exports=124,throwing_exports=14,manager_constructors=28,refactor_attempts=124,manager_copies=20,forward_entries=632,transpose_entries=208,replace_entries=180),
 'aliases_rejections':dict(backend_construction_attempts=4,real_exports=4,manager_constructors=4,forward_entries=16,transpose_entries=12,rejected_solve_entries=24,rejected_replace_entries=14,rejected_factory_entries=4,test_only_reject_factor=1),
 'export_modes':dict(backend_construction_attempts=14,real_exports=4,supplied_exports=6,unavailable_exports=4,manager_constructors=6,refactor_attempts=8,manager_copies=4,forward_entries=40,transpose_entries=12,replace_entries=12),
 'focused':dict(backend_construction_attempts=24,supplied_exports=24,manager_constructors=24,manager_copies=2,forward_entries=10,transpose_entries=6,replace_entries=20,expected_partial_replace_failures=2,dynamic_elimination_helper_calls=3,test_only_map_rebase_arena=1)
 },totals=dict(manager_constructors=62,refactor_attempts=132,backend_construction_attempts=194,native_attempts=110,markowitz_attempts=84,singular_attempts=14,real_exports=132,supplied_exports=30,unavailable_exports=4,throwing_exports=14,manager_copies=26,forward_entries=698,transpose_entries=238,valid_solve_entries=936,rejected_solve_entries=24,replace_entries=212,expected_partial_replace_failures=2,rejected_replace_entries=14,rejected_factory_entries=4,unit_metadata_entries=196,native_orientation_solve_upper_bound=66),
 notes=[
 'RED has8 expected missing-contract failures, zero factor/solve/update calls. GREEN includes unchanged Task1 structural tests and unchanged Task2 reviewed differential tests.',
 'Entry totals count direct API calls. Rejected solve/update/factory entries are separate; some rejected dimension/pivot calls read dimension or scratch metadata but do not enter backend solve.',
 'Singular14 backend attempts occur only on dynamic refactors; injected14 exporter failures occur after real backend setup. No omission of failed construction work.',
 'Real native export orientation may use at most one backend solve per eligible native export;66 is a conservative bound including empty/unit-scaling cases, not an observed count. Other constructor/native factorization work is not replaced by API counts.',
 'Task1 structural suite has no basis factors/solves. It performs arena import, growth, exact topology checks,12 deepcopies and7 injected allocation failures. Maximum matrix n5/capacity40 except requested growth100/overflow checks (capacity helper only). Task2 maximum fixture n16; temporary outputs/oracle Rational arrays/snapshots/traces and retained saved copies are explicit correctness instrumentation, not performance windows.',
 'Extra copy-map test imports one owned arena; unsupported-route sentinel imports one arena and directly constructs one RejectBackend factor, neither a real backend setup. Normal dynamic factory success creates83 arenas;13 dynamic copies are additional deep arena copies.',
 'Prepared hit/miss paths and row histories retain their real implementation work, not rewritten/instrumented. General native allocation/free, import/init work, complete floating-operation budgets and observer neutrality remain unproved.',
 'Task3 costs remain a later separately prepared/admitted stage after accepted correctness. No time/allocation performance inference from GREEN process elapsed or RSS.'
 ])
for n,j in [('expected-tests.json',expected),('work-ledger.json',work)]:
 with (D/n).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
with (D/'expected-tests.toml').open('x') as f:
 for mode in ('red','green'):
  f.write('['+mode+']\nassertions = '+str(expected[mode]['assertions'])+'\n')
  for name,p,fail,error,broken in expected[mode]['groups']:
   f.write('[[ '+mode+'.groups ]]\nname = '+json.dumps(name)+'\npass = '+str(p)+'\nfail = '+str(fail)+'\nerror = '+str(error)+'\nbroken = '+str(broken)+'\n')
with (D/'assertion-derivation.json').open('x') as f:json.dump(dict(formulas=[dict(name=n,assertions=v,derivation=d) for n,v,d in groups],sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),C/'slot-upper-tests-reviewed.jl',C/'dynamic-bg-tests-reviewed.jl']}),f,indent=2);f.write('\n')
print('Expected GREEN',expected['green']['assertions'],[n for _,n,_ in groups],'; RED8expected failures; UNEXECUTED')
