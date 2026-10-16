"""One-shot source/inverse and dependency inspection; not Julia parse or runtime."""
from pathlib import Path
import json,hashlib,subprocess,sys
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION';sys.path.insert(0,str(D))
from control import config,predecessor,validate_environment

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def req(v,m):
 if not v:raise RuntimeError(m)
checks={};m=rd(D/'source-map.json');files=set()
checks['byte_identical_guards']=all(sha(D/n)==sha(src) for n,src in m['byte_identical'].items())
f=rd(P/'observer-seams.json');s=(D/'observed-factorization.jl').read_text()
for i in reversed(f['application_order']):
 e=f['edits'][i];req(s.count(e['after'])==e['count'],'Source inverse anchor');s=s.replace(e['after'],e['before'])
checks['whole_source_inverse']=s==Path(m['observer_source']).read_text()
t=rd(D/'test-inverse.json');s=(D/'observed-tests.jl').read_text()
for e in reversed(t['edits']):req(s.count(e['after'])==1,'Test inverse anchor');s=s.replace(e['after'],e['before'])
checks['whole_test_inverse']=s==Path(t['original']).read_text()
x=Path(m['recorder_source']).read_text();checks['recorder_exact']=x[x.index('module RecordedTests'):x.index('function main()')]==(D/'recorder.jl').read_text()
old=rd(P/'overlay-manifest.json')['candidate'];new=rd(D/'overlay-manifest.json')['candidate']
checks['overlay76']=len(new)==len(old)==76 and all(n==o for n,o in zip(new,old) if n['destination']!='src/factorization.jl')
checks['overlay_hashes']=all(sha(e['source'])==e['sha256'] for e in new)
probe=(D/'probe.jl').read_text();driver=(D/'driver.jl').read_text();observed=(D/'observed-tests.jl').read_text()
checks['preincrement_cap']=probe.index('attempts[k,i]+=1')<probe.index('need(attempts[k,i]<=caps[k]')
checks['sticky_failure']='failed[]=true' in probe and 'failed[]=false' not in probe and 'need(!failed[]' in probe
checks['fixed_storage']=all(v in probe for v in ['zeros(Int,4,9)','zeros(Int,2,9)','zeros(UInt64,20,9)','PUBLIC_CAPS=(64,64,4096,4096)','RECOVERY_CAPS=(2,0,2,6)']) and 'push!' not in probe
checks['controls_per_case']=probe.count('get_umfpack_control')==1 and probe.index('get_umfpack_control')<probe.index('function enter!')
checks['probe_before_load']=driver.index('include(joinpath(@__DIR__,"probe.jl"))')<driver.index('using JSimplex')
checks['raw_before_exit']=driver.index('TOML.print')<driver.index('    exit(')
checks['one_selected_include']=driver.count('include(joinpath(@__DIR__,"observed-tests.jl"))')==1 and 'native_pivot_policy_tests' not in driver
checks['case_brackets']=observed.count('Main.NativePivotIntegrationProbe.begin_case!')==2 and observed.count('Main.NativePivotIntegrationProbe.end_case!')==2
checks['custom_not_numerical']='struct ProbeFailure <: Exception' in probe and 'ProbeFailure' not in (R/'src/dual_simplex.jl').read_text().split('end',1)[0]
checks['no_native_owner_storage']=not any(s in probe for s in ['Vector{Any}','Ref{Any}','push!','deepcopy','copy(backend'])
validate_environment();inputs,groups=predecessor('integration');files.update(inputs);checks['predecessor']=len(groups)==216
checks['no_stage']=not Path(config('integration')['stage']).exists() and not (D/'runs').exists()
checks['python_green']=rd(D/'offline-GREEN.json')['all_passed'] is True and rd(D/'offline-RED.json')['all_passed'] is False
actual={}
for n in subprocess.check_output(['git','ls-files','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R,text=True).splitlines():
 req((R/n).read_bytes()==subprocess.check_output(['git','show','HEAD:'+n],cwd=R),'Actual changed '+n);actual[n]=sha(R/n)
checks['actual520']=len(actual)==520
for p in [D/'source-check.py',D/'probe.jl',D/'driver.jl',D/'observed-tests.jl',D/'observed-factorization.jl',D/'overlay-manifest.json',D/'test-inverse.json',D/'source-map.json',P/'observer-seams.json',P/'native_pivot_integration_tests.jl',R/'src/dual_simplex.jl',R/'src/hypersparse_factorization.jl',R/'src/hypersparse_updates.jl',R/'src/triangular_factorization.jl',R/'src/simplex_recovery.jl']:files.add(p)
with (D/'actual-baseline.json').open('x') as f:json.dump(dict(sha256=actual,scope='Readtime actual files equal HEAD; not execution coverage'),f,indent=2);f.write('\n')
with (D/'source-check.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in sorted(files)},scope='Literal source/inverse checks ONLY, no Julia parser/runtime proof'),f,indent=2);f.write('\n')
req(all(checks.values()),'Source checks failed, preserve');print(dict(checks=len(checks),bindings=len(files),actual=len(actual)))
