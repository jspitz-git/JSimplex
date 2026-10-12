from pathlib import Path
import json,re,hashlib,tomllib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-S';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();m=json.loads((E/'manifest.json').read_text());prior=json.loads((D/'results/S4-R/source-contract.json').read_text());host=json.loads((E/'host-before.json').read_text());checks={}
root=(R/'src/JSimplex.jl').read_text();mod=(E/'isolated-root.txt').read_text();hh=(R/'src/huangfu_hall_factorization.jl').read_text();candidate=(E/'candidate-hh.txt').read_text()
checks['70_original_64_selected_128_entries']=len(m['original_load_order'])==70 and len(m['selected_load_order'])==64 and len(m['entries'])==128
checks['six_exclusions_exact']=set(m['excluded'])=={'src/moi.jl','src/moi/optimizer.jl','src/moi/attributes.jl','src/moi/translation.jl','src/moi/results.jl','src/precompile.jl'}
b=mod
for p in reversed(m['root_substitutions']):assert b.count(p['new'])==1;b=b.replace(p['new'],p['old'])
checks['root_seven_inversions']=len(m['root_substitutions'])==7 and b==root
p=m['candidate_HH_substitution'];checks['candidate_one_inversion']=candidate.count(p['new'])==1 and candidate.replace(p['new'],p['old'])==hh
checks['source_entry_hashes']=all(sha(x['source'])==x['source_sha256'] for x in m['entries'])
def proposed(x):
 return mod.encode() if x['relative_source']=='src/JSimplex.jl' else candidate.encode() if x['side']=='candidate' and x['relative_source']=='src/huangfu_hall_factorization.jl' else Path(x['source']).read_bytes()
checks['proposed128_hashes']=all(hashlib.sha256(proposed(x)).hexdigest()==x['proposed_sha256'] and len(proposed(x))==x['proposed_bytes'] for x in m['entries'])
checks['all_other_bodies_identical']=all(x['source_sha256']==x['proposed_sha256'] for x in m['entries'] if x['relative_source']!='src/JSimplex.jl' and not(x['side']=='candidate' and x['relative_source']=='src/huangfu_hall_factorization.jl'))
checks['resident_four_dependency_aliases']=all('Main.JSimplex.'+x in mod for x in ['LinearAlgebra','Logging','SparseArrays','OrderedCollections'])
checks['relative_using_three']=all('using .'+x in mod for x in ['LinearAlgebra','Logging','SparseArrays'])
checks['no_precompile_or_moi_include']='include("moi.jl")' not in mod and 'include("precompile.jl")' not in mod and 'using PrecompileTools' not in mod
checks['same_child_name_no_routing_renames']=mod.startswith('module JSimplex\n') and m['no_routing_renames'] and 'function refactorize!' in candidate
checks['original_certificate_body_unmodified']=all(x['source_sha256']==x['proposed_sha256'] for x in m['entries'] if x['relative_source']=='src/solver.jl')
methods=m['external_methods'];selected=[x for x in methods if x['selected']]
checks['62_explicit_29_selected_33_excluded']=len(methods)==62 and len(selected)==29 and sum(not x['selected'] for x in methods)==33
expected={'Bound':4,'_UnreliableBasisSolve':1,'IndexedVector':1,'MPSParseError':1,'_UnitTransposeRHS':3,'UpperRowIndices':13,'DiagnosticObserverFailure':1,'_PriceAuditMatrix':2,'_PrimalActivityBounds':3}
checks['selected_owned_type_counts']={t:sum(x['owner']==t for x in selected) for t in expected}==expected
checks['excluded_all_optimizer']=all(x['owner']=='Optimizer' for x in methods if not x['selected'])
checks['equality_signature_not_truncated']=any('Base.:(==)(left::Bound, right::Bound)' in x['signature'] for x in methods)
texts={rel:(R/rel).read_text() for rel in m['selected_load_order']};clean={k:re.sub(r'"""[\s\S]*?"""','',v) for k,v in texts.items()}
checks['no_custom_eval_or_init']=not any(re.search(r'\b(?:eval|__init__)\s*\(|@eval\b',v) for v in clean.values())
checks['literal_includes_only']=sum(len(re.findall(r'\binclude\s*\(',v)) for v in texts.values())==sum(len(re.findall(r'^include\("[^"\n]+"\)',v,re.M)) for v in texts.values())
checks['only_two_function_body_ccalls']=sum(len(re.findall(r'\bccall\(',v)) for v in clean.values())==2 and all('ccall(' not in v for k,v in clean.items() if k!='src/markowitz_factorization.jl')
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base');pc=Path('/home/jspitz/.julia/packages/PrecompileTools/QUxvR');work=(pc/'src/workloads.jl').read_text();enum=(base/'Enums.jl').read_text()
checks['precompile_version_1_3_4']=tomllib.loads((R/'Manifest.toml').read_text())['deps']['PrecompileTools'][0]['version']==tomllib.loads((pc/'Project.toml').read_text())['version']=='1.3.4'
checks['both_workload_verbose_override']=work.count('if $iscompiling || $PrecompileTools.verbose[]')==2
checks['generated_enum_5_owned_families']=all(x in enum for x in ['Enums.namemap(::Type{$(esc(typename))})','Base.typemin(x::Type{$(esc(typename))})','Base.typemax(x::Type{$(esc(typename))})','Enums._enum_hash(x::$(esc(typename)), h::UInt)','Base.instances(::Type{$(esc(typename))})'])
checks['four_enum_declarations']=sum(len(re.findall(r'^@enum ',v,re.M)) for v in clean.values())==4
checks['kwdef_local_constructor']='sig = Expr(:call, esc(T),' in (base/'util.jl').read_text() and 'Base.@kwdef struct SolveStatistics' in texts['src/options.jl']
checks['R570_readtime_unchanged']=len(prior['sha256'])==570 and all(sha(p)==v for p,v in prior['sha256'].items())
checks['user6_unchanged']=len(host['user_hashes'])==6 and all(sha(p)==v for p,v in host['user_hashes'].items())
checks['source_test_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
checks['host_previous_full_groups_empty']=host['matches']==[] and host['pids_present']==[]
paths=set(prior['sha256']);paths.update(str((R/x).resolve()) for x in m['original_load_order']);paths.update(str(p) for p in [base/'Enums.jl',base/'expr.jl',base/'util.jl',pc/'Project.toml',pc/'src/PrecompileTools.jl',pc/'src/workloads.jl']);paths.update(str(p.resolve()) for p in [*E.iterdir(),D/'S4-ISOLATED-MODULE-LOADING-CONTRACT.md',D/'S4-PUBLIC-CONTROLLER-REUSE-CONTRACT-REVIEW.md',D/'results/S4-R/ledger.md',R/'docs/superpowers/plans/2026-10-12-hh-isolated-public-lp-work-contract.md'])
obj=dict(checks=checks,all_passed=all(checks.values()),sha256={p:sha(p) for p in sorted(paths)},scope='Conditional offline source manifest and literal predicates, manually reviewed forms; no Julia parser/load/runtime method proof',julia_calls=0,native_calls=0,module_loads=0,manifest_sha256=sha(E/'manifest.json'))
with (E/'source-contract.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,hashes=len(paths),all_passed=obj['all_passed'])));assert obj['all_passed']
