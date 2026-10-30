from pathlib import Path
import hashlib,json,shutil,difflib,re,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';D=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';T=Path('/tmp/devex-production-preparation-20261030');Q=D/'prepared'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
def fresh(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def put(rel,s):fresh(Q/rel,s.encode())
def change(s,a,b):
 need(s.count(a)==1,'unique transform '+a[:90]);return s.replace(a,b,1)
D.mkdir(parents=True,exist_ok=False);copies={};transforms={};sources={}
for name in ('host.json','preflight.py','prepare.py'):
 fresh(D/name,(T/name).read_bytes());copies[str(T/name)]=dict(copy=str(D/name),sha256=sha(T/name))
# Prospective permanent tests are prepared before production source payload.
for old,new in [('reference.jl','support/devex_refinement_reference.jl'),('legacy_rebuild_reference.jl','support/devex_legacy_rebuild_reference.jl')]:
 fresh(Q/'test'/new,(O/'tests'/old).read_bytes());copies[str(O/'tests'/old)]=dict(copy=str(Q/'test'/new),sha256=sha(O/'tests'/old))
rules={
'refinement_outcome_tests.jl':('refinement_outcome_tests.jl',[("# Prospective ordinary tests, UNEXECUTED during Task1 source preparation.","# Refinement outcomes, refusal provenance, aliasing and strict API regressions.")]),
'reference_comparison_tests.jl':('refinement_reference_comparison_tests.jl',[("# Diagnostic comparison only. Include after refinement_outcome_tests.jl in the\n# same parent module; no whole-module clone or production method overwrite.","# Frozen legacy numerical comparison; include after refinement_outcome_tests.jl.\n# Test-only references; no whole-module clone or production method overwrite."),("include(\"reference.jl\")","include(\"support/devex_refinement_reference.jl\")")]),
'recovery_weight_tests.jl':('recovery_weight_tests.jl',[("# Prospective ordinary Task2 tests. Julia syntax/runtime UNEXECUTED.\n# Include after canonical Task1 refinement_outcome_tests-reviewed.jl.","# Recovery weight eligibility, private Devex state and strict legacy regressions.\n# Include after refinement_outcome_tests.jl."),("include(\"legacy_rebuild_reference.jl\")","include(\"support/devex_legacy_rebuild_reference.jl\")")]),
'recovery_devex_fallback_tests.jl':('recovery_devex_fallback_tests.jl',[("# Task3 prospective ordinary tests; Julia UNEXECUTED during preparation.\n# Include after canonical Task1 and Task2 tests in a fresh source overlay.","# Dual recovery scope, private ownership and transactional Devex publication.\n# Declared test factors forward genuine solves before injecting failures.")])}
for old,(new,rs) in rules.items():
 s=(O/'tests'/old).read_text();before=s
 for a,b in rs:s=change(s,a,b)
 put('test/'+new,s);transforms['test/'+new]=dict(source=str(O/'tests'/old),source_sha256=sha(O/'tests'/old),replacements=[dict(old=a,new=b) for a,b in rs],scope='comments/include paths only; entire test bodies and invokelatest entries retained')
# Retain all endpoint assertions and numerical calls; remove only profiling/output.
s=(O/'endpoint.jl').read_text();replacements=[]
def endpoint_change(a,b):
 global s
 s=change(s,a,b);replacements.append(dict(old=a,new=b))
endpoint_change('module Task4Endpoint','module RecoveryDevexPivotTests')
endpoint_change('using Test,JSimplex,LinearAlgebra,SparseArrays,TOML','using Test,JSimplex,LinearAlgebra,SparseArrays')
endpoint_change('stats(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),\n    "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)\n','')
endpoint_change('    prep=@timed fixture(T);f=prep.value','    f=fixture(T)')
endpoint_change('    build=@timed J._recovery_trial_with_pricing(f.ws,f.c,J._guard_stop_callback(()->false);algorithm=:dual,build_factor=f.builder)\n    pending=build.value','    pending=J._recovery_trial_with_pricing(f.ws,f.c,J._guard_stop_callback(()->false);algorithm=:dual,build_factor=f.builder)')
endpoint_change('    weight_rows=f.builder.last.units\n','')
endpoint_change('    component_prep=@timed begin\n        probe=J._candidate_workspace(pending.workspace)\n        J._copy_pricing_state!(probe,f.ws)\n        probe.scratch.recovery_active=true\n        probe\n    end\n    probe=component_prep.value;count=(f.builder.last.forwards,f.builder.last.backwards)','    probe=J._candidate_workspace(pending.workspace)\n    J._copy_pricing_state!(probe,f.ws)\n    probe.scratch.recovery_active=true\n    count=(f.builder.last.forwards,f.builder.last.backwards)')
endpoint_change('    revalidation=@timed (J._finite_workspace(probe) && J._recomputed_basis_reliable(probe))\n    @test revalidation.value','    revalidation=(J._finite_workspace(probe) && J._recomputed_basis_reliable(probe))\n    @test revalidation')
endpoint_change('    reset=@timed J._prepare_recovery_devex!(probe)\n    @test reset.value===nothing','    reset=J._prepare_recovery_devex!(probe)\n    @test reset===nothing')
start=s.index('    Dict("type"=>string(T),"preparation"=>stats(prep)')
old_tail=s[start:]
new_tail='''    # Preserve the former raw-record auditor's complete endpoint work oracle.
    @test calls==(1,3) && (f.builder.last.forwards,f.builder.last.backwards)==(2,4)
    nothing
end
function runtests()
    @testset "Devex fallback permits a certified dual pivot" begin
        for T in (Float32,Float64)
            run_case(T)
        end
    end
end
end
Base.invokelatest(RecoveryDevexPivotTests.runtests)
'''
endpoint_change(old_tail,new_tail);put('test/recovery_devex_pivot_tests.jl',s);transforms['test/recovery_devex_pivot_tests.jl']=dict(source=str(O/'endpoint.jl'),source_sha256=sha(O/'endpoint.jl'),replacements=replacements,scope='same fixture/options/policy/private factors/numerics and all23 assertion sites; strip profiling/records/TOML; one new ordinary assertion replaces original auditor final work oracle')
includes=['refinement_outcome_tests.jl','refinement_reference_comparison_tests.jl','recovery_weight_tests.jl','recovery_devex_fallback_tests.jl','recovery_devex_pivot_tests.jl']
old=(W/'test/runtests.jl').read_text();anchor='    include("basis_recovery_tests.jl")\n';added=''.join('    include("'+n+'")\n' for n in includes);new=change(old,anchor,added+anchor);put('test/runtests.jl',new);transforms['test/runtests.jl']=dict(source=str(W/'test/runtests.jl'),source_sha256=sha(W/'test/runtests.jl'),replacements=[dict(old=anchor,new=added+anchor)],scope='exactly5 ordered includes before existing basis recovery; all old includes/test bodies unchanged')
# Only the three already qualified source files, exact complete bytes.
for n in ('simplex_numerics.jl','simplex_recovery.jl','simplex_pivot.jl'):
 src=O/'overlays/candidate/src'/n;fresh(Q/'src'/n,src.read_bytes());copies[str(src)]=dict(copy=str(Q/'src'/n),sha256=sha(src))
payload=sorted(str(p.relative_to(Q)) for p in Q.rglob('*') if p.is_file());need(len(payload)==11,'payload11')
for rel in payload:
 src=W/rel
 if src.exists():fresh(D/'baseline'/rel,src.read_bytes())
patch=[]
for rel in payload:
 old=(D/'baseline'/rel).read_text() if (D/'baseline'/rel).exists() else '';new=(Q/rel).read_text();patch.append(f'diff --git a/{rel} b/{rel}\n')
 if not (D/'baseline'/rel).exists():patch.append('new file mode 100644\n')
 patch.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+rel if (D/'baseline'/rel).exists() else '/dev/null',tofile='b/'+rel))
fresh(D/'production.patch',''.join(patch).encode())
manifest=dict(scope='OFFLINE production integration payload; no actual src/test edits, Julia or production commit',baseline_head='2d226b84e79e8afeff3ec8d8961b15af44b12085',master='c0fa748ffa61ccb7c1caaf248c40324f60bc737b',prepared_runtime_unexecuted=True,payload=payload,payload_sha256={rel:sha(Q/rel) for rel in payload},baseline_sha256={str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()},exact_copies=copies,transforms=transforms,ordered_new_includes=includes,endpoint_assertion_sites_original=23,endpoint_assertion_sites_prepared=24,warning='lexical assertion sites are not an aggregate runtime count; future ordinary integration verification required')
# Site counts source-bound, not Julia runtime claims.
pat=r'@test(?:_throws|_broken|_skip)?\b';manifest['lexical_test_sites']={rel:len(re.findall(pat,(Q/rel).read_text())) for rel in payload if rel.endswith('_tests.jl')};need(manifest['lexical_test_sites']['test/recovery_devex_pivot_tests.jl']==24,'endpoint24sites');need(len(re.findall(pat,(O/'endpoint.jl').read_text()))==23,'original23sites');fresh(D/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode());print(json.dumps(dict(prepared=True,payload_files=len(payload),source_files=3,test_files=8,actual_src_test_unchanged=True,Julia=False,endpoint_sites=24,new_include_count=5)))
