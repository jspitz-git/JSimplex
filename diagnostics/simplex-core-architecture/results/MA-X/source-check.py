from pathlib import Path
import ast,json,hashlib,tomllib
D=Path(__file__).resolve().parent;R=D.parents[3];B=D.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def fn(p,n):return next(x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef) and x.name==n)
m=rd(D/'source-map.json');s=(D/'driver.jl').read_text();checks={}
for i,e in enumerate(reversed(m['driver_edits'])):
 checks['inverse_edit_'+str(i)]=s.count(e['new'])==1
 s=s.replace(e['new'],e['old'])
checks['driver_inverse']=s==Path(m['driver_source']).read_text() and sha(m['driver_source'])==m['driver_source_sha256']
for n in m['unchanged_functions']:checks['original_AST_'+n]=ast.dump(fn(D/'audit.py',n))==ast.dump(fn(B/'MA-S-2/audit.py',n))
for n,o in m['byte_exact_copies'].items():checks['exact_'+n]=sha(D/n)==o['sha256']==sha(o['source'])
checks['candidate']=sha(m['candidate'])==m['candidate_sha256']=='50b1421e06eabed34cbc0b9fd50bb1a0977aada3fe9159a4e005513cbefca98b'
checks['instrumented']=sha(m['instrumented'])==m['instrumented_sha256']==sha(B/'MA-R/instrumented.jl')
checks['reference_reuse']=sha(B/'MA-R/reference.jl')==sha(B/'MA-U/reference.jl')
v=rd(B/'MA-V/pins.json')['inventory'];reached=[p for p in v if '/src/' in p or '/share/julia/base/' in p or '/share/julia/stdlib/' in p]
checks['reached_V_identity']=all(sha(p)==v[p]['sha256'] and str(Path(p).resolve())==v[p]['resolved'] for p in reached)
sched=rd(D/'schedule.json');fixtures=tomllib.loads((B/'MA-R/fixtures.toml').read_text())
checks['schedule52']=sched['costs']==fixtures['cost_cases'] and len(sched['costs'])==52
# Derive original correctness and setup counts directly from fixture categories.
n=len(fixtures['bits'])*len(fixtures['sizes'])*len(fixtures['layouts'])*len(fixtures['directions'])+len(fixtures['specials'])*2+len(fixtures['mixed_stored_ambient'])*2+len(fixtures['matching_rounding'])*2+len(fixtures['scoped_mismatch'])*2+4
calls=n+2
checks['budgets']=n==sched['correctness_cases']==160 and calls*3+2==sched['correctness_entries']==488 and n+2==sched['correctness_setup_factorizations']==162 and 3*52==sched['cost_setups']==156 and 162+156==sched['setup_factorizations']==318 and 3*52*20*4==sched['cost_entries']==12480 and sched['total_entries']==12968
s=(D/'driver.jl').read_text();checks['cold_boundaries']=s.count('Base.invokelatest')==2 and 'Base.invokelatest(TST.qualification)' in s and 'Base.invokelatest(costs,index,raw["costs"])' in s
checks['RED_before_candidate']=s.index('raw["red"]=red()')<s.index('Base.include(P,joinpath(UD,"candidate.jl"))')
checks['runtime_before_candidate']=s.index('VERSION == v"1.13.0"')<s.index('Base.include(P,joinpath(UD,"candidate.jl"))')
checks['journal_before_checks']=s.index('"whole-metrics"')<s.index('output=serialtokens(y.dest)')<s.index('"whole-complete"')<s.index('output==expected || error')
checks['journal_flush']='TOML.print(io,Dict("records"=>[record]));flush(io)' in s
checks['timed_batch_exact']=s[s.index('@noinline function batch'):s.index('const JOURNAL')]==Path(m['driver_source']).read_text().split('@noinline function batch',1)[1].split('function costs',1)[0].join(['@noinline function batch',''])
l=(D/'launcher.py').read_text();checks['stop_before_next_process']="result=audit.stage(i)" in l and "and result['all_passed'],'failed qualification; stop, no retry'" in l and l.count('for i in (1,2,3):')==1
for n in ('offline-tests.json','supervisor-tests-final.json'):
 o=rd(D/n);checks[n]=o['all_passed'] is True and all(sha(p)==h for p,h in o['sha256'].items())
checks['no_outputs']=not any((D/n).exists() for n in ('launch-context.json','numerical-review.json','sequence-reservation.json','run-1','run-2','run-3'))
paths=[p for p in D.iterdir() if p.is_file() and p.name not in ('source-check.json',)]+[Path(m[k]) for k in ('driver_source','original_validator','candidate','instrumented','reference','tests','fixtures')]+[R/'docs/superpowers/plans/2026-10-14-ma-denselu-complete-qualification.md']
o=dict(all_passed=all(checks.values()),checks=checks,reached_V_identity_count=len(reached),sha256={str(p):sha(p) for p in paths})
with (D/'source-check.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,bindings=len(paths),reached=len(reached))))
if not o['all_passed']:raise SystemExit(1)
