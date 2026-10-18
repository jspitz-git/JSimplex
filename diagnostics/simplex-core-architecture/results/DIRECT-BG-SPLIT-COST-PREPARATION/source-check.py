"""New source/inverse/stage checks only. No Julia parsing/import/run."""
from control import *
import re,tomllib
checks={}
def ok(v,k):
 checks[k]=bool(v)
 require(v,k)
def unrename(t,m):
 for a,b in sorted(m.items(),key=lambda x:-len(x[1])):t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(b)+r'(?![A-Za-z0-9_!])',a,t)
 return t
j=rd(D/'probe-inverse.json');u=(D/'probe-upper.jl').read_text();ok(u.startswith(j['header']),'probe_header')
u=unrename(u[len(j['header']):],j['renames'])
for item in reversed(j['injections']):
 mark='\n    # SPLIT_COST_PROBE_BEGIN\n'+item['code']+'\n    # SPLIT_COST_PROBE_END\n'
 ok(u.count(item['anchor']+mark)==1,'injection_'+str(len(checks)))
 u=u.replace(item['anchor']+mark,item['anchor'])
for v in reversed(j['replacements']):
 ok(u.count(v['new'])==1,'replacement_'+str(len(checks)));u=u.replace(v['new'],v['old'])
ok(u==(C/'split-upper.jl').read_text(),'exact_upper_inverse')
ok(unrename((D/'probe-bg.jl').read_text(),j['renames'])==(C/'split-bg.jl').read_text(),'exact_adapter_inverse')
a=(C/'split-oracles.jl').read_text().split('function _sbu_materialize')[0];o=(D/'probe-oracles.jl').read_text();ok(o.startswith(a) and unrename(o[len(a):],j['renames'])==a+j['helper'],'two_pure_checker_inverses')
ok(o.count('function _sbu_check(')==1 and o.count('function _probe_sbu_check(')==1 and '@test' not in o,'no_method_overwrite_Test')
s=rd(D/'stages.json')['cost'];root=Path(s['path']);base=Path(s['source'])
ok(len(s['sha256'])==84 and len(s['baseline_sha256'])==81,'stage_membership')
for n,h in s['baseline_sha256'].items():
 text=(root/n).read_bytes()
 if n=='src/JSimplex.jl':text=text.replace(s['inserted_includes'].encode(),b'')
 ok(hashlib.sha256(text).hexdigest()==h,'stage_inverse_'+n)
ok(all((D/n).read_bytes()==(root/'src'/n).read_bytes() for n in ['probe-upper.jl','probe-bg.jl','probe-oracles.jl']),'probe_stage_bytes')
ok(tomllib.loads((D/'inputs.toml').read_text())==rd(D/'inputs.json'),'exact_input_formats')
for n,v in rd(D/'reused-files.json').items():ok(sha(D/n)==v['sha256']==sha(v['source']),'reuse_'+n)
t=(D/'cost.jl').read_text();life=t[t.index('function lifecycle'):t.index('# No extra factor')]
ok('_split_probe_counts' not in life and 'summarysize' not in life and 'checkpoint(' not in life,'no_timed_instrumentation')
ok('timed=@timed lifecycle' in t and 'factory(side,F,fixture.matrices[1],backend)' in life,'whole_lifecycle_setup_timed')
ok('for pair in 1:10' in t and 'pair>3' in t and 'isodd(pair) ⊻ startswith(PHASE,"cost2")' in t,'fixed_schedule')
ok('J._split_bg_factor(B,backend,policy(backend))' in t and '_dynamic' not in t,'only_packed_and_Block_factories')
ok('for m in (J,LinearAlgebra,SparseArrays,TOML,PrecompileTools)' in t and set(rd(D/'loaded-paths.json'))=={'SparseArrays','LinearAlgebra','TOML','PrecompileTools'},'exact_five_loaded_keys')
ok('include("probe.jl")' in t[:t.index('function main()')] and t.rstrip().endswith('main()'),'top_level_definitions')
ok('save("growth.toml",growth_probe())' in t and 'for c in 1:64' in (D/'probe.jl').read_text(),'bounded_growth_probe')
ok('getfield(getfield(a,:ref),:mem)' in (D/'probe.jl').read_text(),'actual_backing_memory')
validate_sources();validate_environment();ok(True,'all_current_sources_runtime_stage_environment')
predecessor('cost1-300');ok(True,'accepted_GREEN_predecessor')
h=full_host();save(D/'author-host.json',h);ok(not h['matches'] and len(h['groups'])==244,'fresh_groups_sessions_noJulia')
ok(not (D/'runs').exists(),'no_seal_reservation_output')
for p in D.glob('*.py'):compile(p.read_text(),str(p),'exec')
ok(True,'new_Python_syntax_only')
files=sorted(p for p in D.iterdir() if p.is_file())
save(D/'source-check.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in files},scope='Text/source/runtime verification only; Julia unexecuted'))
print('Source/inverse checks',len(checks),'PASS')
