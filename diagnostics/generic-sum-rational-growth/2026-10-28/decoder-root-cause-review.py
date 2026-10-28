from pathlib import Path
from fractions import Fraction
import re,json,hashlib,tomllib
D=Path(__file__).resolve().parent
P=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/mpfr.jl')
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads((D/p).read_text())
s=(D/'output/run.log').read_text();source=P.read_text();process=read('output/process.json')
need(process['returncode']==1 and process['reason']=='exit1' and process['pins_unchanged'] is True,'failed process terminal evidence')
need('BigInt(ldexp(x,s)) // (BigInt(1) << s)' in source and 'function ldexp(x::BigFloat, n::Clong)\n    z = BigFloat()' in source,'source decoder/ambient allocation')
need(s.count('Test Failed at ')==90 and s.count('Expression: Rational{BigInt}(precise) == exactweight')==90 and 'Error During Test' not in s,'exact failure class')
locations=re.findall(r'Test Failed at (.*)',s)
need(all(x==str(D/'extra-tests-ready.jl')+':127' for x in locations),'failure location')
need('ERROR: LoadError: Some tests did not pass: 111259 passed, 90 failed, 0 errored, 0 broken.' in s,'terminal Test summary')
need(re.search(r'^Sum rational growth whole-function comparison\s*\|\s*111259\s+90\s+111349\s+',s,re.M),'root totals')
need('SUM_RATIONAL_GROWTH_COMPLETE' not in s,'failed root must not print success')
expected=Fraction(1)+Fraction(1,2**53)+Fraction(1,2**400);context=None;checks=[]
for line in s.splitlines():
 if line.startswith('CONTEXT '):context=line[8:]
 m=re.fullmatch(r'   Evaluated: (\d+)//(\d+) == (\d+)//(\d+)',line)
 if m:
  pbits,mode=re.fullmatch(r'BF(64|128|256)_(Nearest|Down|Up|ToZero|FromZero)',context).groups();bits=int(pbits)
  actual=Fraction(int(m[1]),int(m[2]));want=Fraction(int(m[3]),int(m[4]))
  rounded=Fraction(1)+Fraction(1,2**53)+(Fraction(1,2**(bits-1)) if mode in ['Up','FromZero'] else Fraction(0))
  need(want==expected and actual==rounded and actual!=want,'exact independent decoder formula '+context);checks.append(context)
need(len(checks)==90 and len(set(checks))==15 and all(checks.count(k)==6 for k in set(checks)),'six failures per BF context')
raw=tomllib.loads((D/'output/results.toml').read_text());grid=read('expected-cases.json')
need(len(raw['cells'])==2636 and len(raw['preparation'])==2674 and sum(len(v['windows']) for v in raw['cells'])==47448,'complete serialized counts')
need([{k:v for k,v in cell.items() if k!='windows'} for cell in raw['cells']]==grid,'serialized grid exact')
for cell in raw['cells']:
 need(len(cell['windows'])==18,'every cell windows')
 for sample in cell['windows']:need(sample['compile_seconds']==sample['recompile_seconds']==0,'compile zero')
 for pair in range(1,10):
  rows=[v for v in cell['windows'] if v['pair']==pair];need(len(rows)==2 and {v['arm'] for v in rows}=={'original',cell['variant']},'paired arms')
  need(type(rows[0]['result']) is type(rows[1]['result']) and rows[0]['result']==rows[1]['result'],'paired result')
bindings={str(p):sha(p) for p in [P,D/'output/run.log',D/'output/process.json',D/'output/results.toml',D/'extra-tests-ready.jl',D/'expected-cases.json',Path(__file__)]}
report=dict(root_cause_confirmed=True,comparison_passed=False,cost_acceptance=False,Julia_executed=False,host_audit_executed=False,failed_assertions=90,passed_assertions=111259,errored_assertions=0,cells=2636,windows=47448,preparation=2674,all_measured_compile_zero=True,all_paired_result_keys_equal=True,failures_by_context={k:checks.count(k) for k in dict.fromkeys(checks)},bindings=bindings)
with (D/'decoder-root-cause-review.json').open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
text='''# Independent decoder failure review

The comparison failed: 111,259 assertions passed, 90 failed, none errored or were broken, and the process exited1. All90 failures are exactly the Rational{BigInt}(precise)==exactweight assertion at extra-tests-ready.jl:127, six in each of15 BigFloat contexts. The failure is in the test decoder, not demonstrated in candidate arithmetic.

Installed Julia mpfr.jl:566 converts an AbstractFloat by computing BigInt(ldexp(x,s))//2^s. Its BigFloat ldexp implementation at842 allocates its output with BigFloat(), hence ambient precision. The computed positive result has stored precision512 and exact intended value1+2^-53+2^-400, but the decoder runs after the explicit512 scope has restored ambient64/128/256. Independent integer Fraction analysis matches every printed observed numerator/denominator: Nearest/Down/ToZero decode1+2^-53; Up/FromZero decode1+2^-53+2^(1-p). Every printed expected rational remains exactly1+2^-53+2^-400. No expected value or candidate arithmetic needs alteration.

A separate correctness-only qualifier may run the identical correctness fixtures with only the decoder scoped to precision(precise). This removes unintended decoding loss and does not raise candidate/input/measurement arithmetic precision. It should retain the exact rational expected value and all original assertions, explicitly characterize the old ambient decoder against the independently derived rounded formula, and check ambient restoration. No repeated cost measurement is required. Its concrete driver/guard/pins still require independent admission.

The failed attempt serialized all2,636 original ordered cells,47,448 windows and2,674 preparation entries. Every measured window reports zero compile/recompile time, and all paired result keys agree. These are preservation/completeness facts, not performance or correctness acceptance. The success marker is correctly absent because the failed ordinary root testset throws after the finally serialization block. Keep this attempt, original auditor and admissions immutable. A separately reviewed strict qualified auditor must require exactly these90 explained failures plus complete passing qualifier evidence and all original resource/identity/pin/cost checks before accepting any cost comparison.

No Julia or host audit was executed by this review, and no candidate, input, measurement, production or Git state was changed. Source and raw output bindings are recorded in decoder-root-cause-review.json.
'''
with (D/'DECODER-ROOT-CAUSE-REVIEW.md').open('x') as f:f.write(text)
print(json.dumps({k:v for k,v in report.items() if k not in ['bindings','failures_by_context']}))
