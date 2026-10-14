from pathlib import Path
import json,hashlib,ast,difflib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-V';U=D.with_name('MA-U');S=D.with_name('MA-S-2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def save(n,o):
 with (D/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
checks={};maps=[]
# Inverse every allowed diagnostic-only test edit, independent of builder scripts.
s=(D/'tests-recorded.jl').read_text().replace('exception=ra.failure,output=ra.output,route_counts=P.route_counts())','exception=ra.failure,output=ra.output)').replace('joinpath(@__DIR__, "../MA-U/fixtures.toml")','joinpath(@__DIR__, "fixtures.toml")')
checks['tests_inverse']=s==(U/'tests.jl').read_text()
s=(D/'guard-tests-recorded.jl').read_text()
block='''const JOURNAL_HOOK = Ref{Any}(nothing)
function record!(records,record)
    push!(records,record)
    JOURNAL_HOOK[] === nothing || JOURNAL_HOOK[](record)
    return records
end
const PROGRESS = Dict{String,Any}()
'''
checks['one_hook']=s.count(block)==1;s=s.replace(block,'').replace('record!(records,','push!(records,').replace('record!(local_records,','push!(local_records,')
for a,b in [
 ('records = NamedTuple[]; PROGRESS["predicates"]=records','records = NamedTuple[]'),
 ('records = NamedTuple[]; PROGRESS["transitions"]=records; PROGRESS["task_fragments"]=Any[]','records = NamedTuple[]'),
 ('local_records = NamedTuple[]; push!(PROGRESS["task_fragments"],local_records)','local_records = NamedTuple[]'),
 ('records = NamedTuple[]; PROGRESS["whole"]=records','records = NamedTuple[]'),
 ('    PROGRESS["current_case"]=id\n',''),
 ('            record===nothing || (JOURNAL_HOOK[]===nothing || JOURNAL_HOOK[](record))\n','')]:
 checks['edit_'+str(len(checks))]=s.count(a)==1;s=s.replace(a,b)
checks['guard_tests_inverse']=s==(U/'guard-tests.jl').read_text()
checks['guard_exact']=sha(D/'guard.py')==sha(S/'guard.py')
checks['U_candidate_frozen']=sha(U/'candidate.jl')=='50b1421e06eabed34cbc0b9fd50bb1a0977aada3fe9159a4e005513cbefca98b'
checks['U_source34']=all(sha(p)==h for p,h in rd(U/'source-green.json')['sha256'].items())
checks['micro256']=(D/'micro-batch.jl').read_text().count('total += Int(probe(tag))')==256 and '@noinline probe(::Val{:old}) = G.old_guard()' in (D/'micro-batch.jl').read_text() and '@noinline probe(::Val{:new}) = P._dense_ma_rounding_matches()' in (D/'micro-batch.jl').read_text()
checks['no_effects_or_invokelatest']=all(x not in (D/'micro-batch.jl').read_text()+(D/'driver.jl').read_text() for x in ('@assume_effects','invokelatest'))
checks['early_loading']=(D/'driver.jl').read_text().index('module OldArm')<(D/'driver.jl').read_text().index('function main()')
oldcmd=rd(S/'commands.json');cmd=rd(D/'commands.json');checks['exact_commands']=set(cmd)=={'1','2'} and all(c[:-3]==oldcmd[i][:-3] and c[-3:]==[str(D/'driver.jl'),i,str(D/f'run-{i}')] for i,c in cmd.items())
checks['no_statistics_dependency']='Statistics' not in (D/'driver.jl').read_text()
# Preserve exact earlier check bindings, never rewrite their recorded hashes.
for name in ['offline-tests.json','offline-tests-final.json','offline-tests-canonical.json','supervisor-tests.json']:
 for p,h in rd(D/name)['sha256'].items():
  if sha(p)==h:continue
  matches=[q for q in D.glob(Path(p).name+'.before-*') if sha(q)==h]
  if not matches:raise ValueError('Missing preserved binding '+name+' '+p)
  maps.append(dict(source=str(D/name),path=p,preserved=str(sorted(matches)[0]),sha256=h))
checks['all_prior_tests_reconciled']=True
for n in ['offline-tests-complete.json','supervisor-tests-final.json']:
 o=rd(D/n);checks[n]=o['all_passed'] is True and all(sha(p)==h for p,h in o['sha256'].items())
for n in ['driver.jl','tests-recorded.jl','guard-tests-recorded.jl','micro-batch.jl']:
 checks['nonempty_'+n]=(D/n).stat().st_size>0
for n in ['audit.py','launcher.py','supervisor.py','guard.py','offline-tests.py','supervisor-tests.py']:ast.parse((D/n).read_text())
checks['no_run']=not any((D/n).exists() for n in ['launch-context.json','numerical-review.json','sequence-reservation.json','reservation-1.json','run-1','run-2'])
schedule=rd(D/'schedule.json');checks['exact_schedule']=len(schedule['costs'])==12 and len(schedule['red'])==2 and len(schedule['micro'])==6 and (12*2+2)*20*4==2080 and 6*2*20*256==61440
save('review-fix-map.json',dict(old_bindings=maps,scope='Only changed MA-V pre-review/intermediate synthetic result source bindings; initial records remain preserved'))
files=[D/n for n in ['source-check.py','driver.jl','tests-recorded.jl','guard-tests-recorded.jl','micro-batch.jl','audit.py','launcher.py','supervisor.py','guard.py','schedule.json','commands.json','admission.md','work-ledger.md','review-fix-map.json','offline-tests-complete.json','supervisor-tests-final.json']]+[U/n for n in ['candidate.jl','tests.jl','guard-tests.jl','source-green.json']]
save('source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in files},scope='Source/AST and existing records only; no Julia or launcher main'))
print(len(checks),all(checks.values()),'bindings',len(files),'historical maps',len(maps))
if not all(checks.values()):raise SystemExit(1)
