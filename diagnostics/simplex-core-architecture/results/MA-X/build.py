from pathlib import Path
import json,hashlib,tomllib,ast
D=Path(__file__).resolve().parent;R=D.parents[3];V=D.with_name('MA-V');S=D.with_name('MA-S-2');L=D.with_name('MA-S-LOAD');U=D.with_name('MA-U')
def save(n,s):
 with (D/n).open('x') as f:f.write(s)
def js(n,o):save(n,json.dumps(o,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
edits=[];s=(L/'driver.jl').read_text()
def edit(a,b):
 global s
 if s.count(a)!=1:raise ValueError(a)
 edits.append(dict(old=a,new=b));s=s.replace(a,b)
edit('# MA-S UNEXECUTED guarded driver. All R sources remain unchanged.','# MA-X UNEXECUTED complete qualification. Frozen R tests and U candidate.')
edit('using Test, TOML, LinearAlgebra','using Test, TOML, LinearAlgebra\nVERSION == v"1.13.0" || error("unsupported private-API runtime")')
edit('const P = MADenseProbe','const UD = abspath(joinpath(@__DIR__, "../MA-U"))\nconst P = MADenseProbe')
edit('function costs(index)\n    records=Any[]','''const JOURNAL = Ref{Union{Nothing,IOStream}}(nothing)
function journal_record(record)
    io=JOURNAL[];io===nothing && error("journal not open")
    TOML.print(io,Dict("records"=>[record]));flush(io)
end
function costs(index,records)
'''.rstrip())
edit('            x=TST.bundle','            setup_started=time_ns()\n            x=TST.bundle')
edit('            ws=Any[]; expected=nothing','''            ws=Any[]; expected=nothing
            row=Dict{String,Any}("id"=>c["id"],"eligible"=>c["eligible"],"windows"=>ws,"expected"=>String[],"bundle_snapshot_setup_seconds"=>(time_ns()-setup_started)/1e9)
            push!(records,row)''')
edit('''                    output=serialtokens(y.dest)
                    expected===nothing && (expected=output)
                    output==expected || error("window output mismatch")''','''                    merge!(w,Dict("side"=>side==1 ? "reference" : "candidate","pair"=>pair,"order"=>oi,
                        "phase"=>pair<=3 ? "warm" : "measured","calls"=>4))
                    push!(ws,w)
                    location="cost/$(c["id"])/$pair/$side"
                    journal_record(Dict("kind"=>"whole-metrics","location"=>location,"window"=>copy(w)))
                    output=serialtokens(y.dest)
                    expected===nothing && (expected=output;row["expected"]=output)''')
edit('''                    preserved || error("window input changed")
                    merge!(w,Dict("side"=>side==1 ? "reference" : "candidate","pair"=>pair,"order"=>oi,
                        "phase"=>pair<=3 ? "warm" : "measured","output"=>output,"preserved"=>preserved,"calls"=>4))
                    push!(ws,w)''','''                    merge!(w,Dict("output"=>output,"preserved"=>preserved))
                    journal_record(Dict("kind"=>"whole-complete","location"=>location,"window"=>copy(w)))
                    output==expected || error("window output mismatch")
                    preserved || error("window input changed")''')
edit('            push!(records,Dict("id"=>c["id"],"eligible"=>c["eligible"],"windows"=>ws,"expected"=>expected))','            # row already retained before the first window')
edit('    try\n        if index==1','''    journalpath=joinpath(out,"partial-windows.toml")
    ispath(journalpath) && error("journal exists")
    JOURNAL[]=open(journalpath,"w")
    try
        if index==1''')
edit('Base.include(P,joinpath(RD,"candidate.jl"))','Base.include(P,joinpath(UD,"candidate.jl"))')
edit('Base.include(P,joinpath(RD,"instrumented.jl"))','Base.include(P,joinpath(UD,"instrumented.jl"))')
edit('        raw["costs"]=Base.invokelatest(costs,index)','''        cost_started=time_ns()
        try
            Base.invokelatest(costs,index,raw["costs"])
        finally
            raw["cost_inclusive_seconds"]=(time_ns()-cost_started)/1e9
        end''')
edit('    finally\n        raw["ambient_restored"]','    finally\n        close(JOURNAL[]);JOURNAL[]=nothing\n        raw["ambient_restored"]')
edit('println("MA-S process $index complete")','println("MA-X process $index complete")')
save('driver.jl',s)
# Original scalar validator and aggregate reducer retained verbatim.
a=(S/'audit.py').read_text();v=(V/'audit.py').read_text()
a=a.replace('MA-S-2 fail-closed','MA-X fail-closed')
a=a[:a.index('def stage_scalars')]+v[v.index('def stage_scalars'):v.index('def process_costs')]+a[a.index('def aggregate'):]
a=a.replace('<=180','<=270').replace('==180','==270').replace('>=166','>=170').replace("context['maximum_processes']==2","context['maximum_processes']==3").replace("sequence['maximum_processes']==2","sequence['maximum_processes']==3")
a=a.replace("  checks['generated_code_actual']="+a.split("  checks['generated_code_actual']=")[1].split('\n')[0]+'\n','')
extra='''def process_costs(raw):
 rows=[]
 for c,fixture in zip(raw['costs'],spec()['cost_cases']):
  ws=[w for w in c['windows'] if w['phase']=='measured'];ref=[w for w in ws if w['side']=='reference'];cand=[w for w in ws if w['side']=='candidate']
  r=[b['seconds']/a['seconds'] for a,b in zip(ref,cand)]
  rt=statistics.median(w['seconds']/4 for w in ref);ct=statistics.median(w['seconds']/4 for w in cand)
  pr=dict(ratio=statistics.median(r),reference_seconds_per_call=rt,candidate_seconds_per_call=ct,reference_bytes=statistics.median(w['bytes'] for w in ref),candidate_bytes=statistics.median(w['bytes'] for w in cand),reference_events=statistics.median(w['events'] for w in ref),candidate_events=statistics.median(w['events'] for w in cand))
  pr['pass']=(pr['ratio']<1 and pr['candidate_bytes']<pr['reference_bytes'] and pr['candidate_events']<pr['reference_events']) if fixture['eligible'] else (ct-rt<=max(.10*rt,.4e-6) and pr['candidate_bytes']<=pr['reference_bytes'] and pr['candidate_events']<=pr['reference_events'])
  rows.append(dict(id=c['id'],**pr))
 return rows

def journal_expected(raw):
 expected=[]
 for c in raw['costs']:
  for w in c['windows']:
   side=1 if w['side']=='reference' else 2;location=f"cost/{c['id']}/{w['pair']}/{side}"
   expected.append(dict(kind='whole-metrics',location=location,window={k:v for k,v in w.items() if k not in ('output','preserved')}))
   expected.append(dict(kind='whole-complete',location=location,window=w))
 return expected

def journal_valid(records,raw):
 expected=journal_expected(raw)
 require(len(records)==len(expected)==2080,'journal count')
 require(records==expected,'journal content/order')
 return True

'''
a=a.replace('def stage_scalars',extra+'def stage_scalars',1)
a=a.replace("  raw=tomllib.loads((out/'raw.toml').read_text());checks.update(validate_raw(raw,index))", "  raw=tomllib.loads((out/'raw.toml').read_text());checks.update(validate_raw(raw,index))\n  require(passed(validate_raw(raw,index)),'raw schema')\n  checks['setup_intervals']=finite(raw['cost_inclusive_seconds']) and all(finite(c['bundle_snapshot_setup_seconds']) for c in raw['costs'])\n  cost_rows=process_costs(raw);checks['per_process_costs']=all(p['pass'] for p in cost_rows)")
a=a.replace("return dict(all_passed=passed(checks),checks=checks,error=error,sha256=", "return dict(all_passed=passed(checks),checks=checks,error=error,process_costs=locals().get('cost_rows',[]),sha256=")
save('audit.py',a)
for n in ('supervisor.py','guard.py','supervisor-tests.py'):save(n,(V/n).read_text())
l=(V/'launcher.py').read_text().replace('MA-V one','MA-X one').replace('two serial','three serial').replace("'micro-batch.jl','tests-recorded.jl','guard-tests-recorded.jl',", "'source-map.json',")
l=l.replace("==2 and context", "==3 and context").replace('(1,2)', '(1,2,3)').replace('>=166','>=170').replace('maximum_processes=2','maximum_processes=3').replace('total_cap_seconds=180','total_cap_seconds=270').replace('total<=180','total<=270').replace("print('2 processes", "print('3 processes")
save('launcher.py',l)
cmd=json.loads((S/'commands.json').read_text())
for i,c in cmd.items():c[-3:]=[str(D/'driver.jl'),i,str(D/f'run-{i}')]
js('commands.json',cmd)
f=tomllib.loads((D.with_name('MA-R')/'fixtures.toml').read_text())
js('schedule.json',dict(costs=f['cost_cases'],processes=3,pairs=10,warm_pairs=3,measured_pairs=7,calls_per_window=4,correctness_cases=160,correctness_entries=488,cost_entries=12480,total_entries=12968,setup_factorizations=318,correctness_setup_factorizations=162,cost_setups=156,pfi_copies=2,windows=3120,warm_windows=936,measured_windows=2184,seconds_per_process=90,total_seconds=270,no_retry=True))
js('source-map.json',dict(driver_source=str(L/'driver.jl'),driver_source_sha256=sha(L/'driver.jl'),driver_edits=edits,original_validator=str(S/'audit.py'),unchanged_functions=['validate_raw','aggregate','expected_correctness'],byte_exact_copies={n:dict(source=str(V/n),sha256=sha(V/n)) for n in ('supervisor.py','guard.py')},candidate=str(U/'candidate.jl'),candidate_sha256=sha(U/'candidate.jl'),instrumented=str(U/'instrumented.jl'),instrumented_sha256=sha(U/'instrumented.jl'),reference=str(D.with_name('MA-R')/'reference.jl'),tests=str(D.with_name('MA-R')/'tests.jl'),fixtures=str(D.with_name('MA-R')/'fixtures.toml')))
print('driver, admission code and fixed schedule created; no execution')
