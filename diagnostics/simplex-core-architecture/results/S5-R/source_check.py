"""Exclusive source-text checks, no Julia parsing/execution."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();O=R/'diagnostics/simplex-core-architecture/results/S5-R';Q=O.parent/'S5-Q';s=(O/'candidate-reviewed.jl').read_text();p=json.loads((O/'provenance.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
setup=s.split('    # BEGIN SOURCE SETUP\n')[1].split('    # END SOURCE SETUP')[0]
call=s.split('        # BEGIN SOURCE CALL\n')[1].split('        # END SOURCE CALL')[0].strip()
restored=setup.replace('SimplexProgressContext{T,typeof(d)}','SimplexProgressContext{T,Nothing}').replace('7,11,d,policy)','7,11,nothing,policy)')
inverse=''.join('        '+x for x in restored.splitlines(True))+'            '+call.replace(';policy,progress,stop=guard)',';policy,progress)')+'\n'
names=re.findall(r'^        (\w+)=',s.split('    checks=(\n')[1].split('    )\n')[0],re.M)
probe=s.split('mutable struct S5RProbe\n')[1].split('\nend')[0]
fields=re.findall(r'^    (\w+)::',probe,re.M)
callback=s.split('function (probe::S5RProbe)')[1].split('function s5r_case')[0]
checks={
 'exact_setup_inverse':inverse==(Q/'existing-setup.txt').read_text(),
 'source_excerpt_current':inverse.rstrip('\n') in (R/'test/simplex_precision_tests.jl').read_text(),
 'one_initializer':s.count('JSimplex.initialize_from_basis(')==1,
 'one_case_call':s.count('s5r_case(only(ARGS))')==1,
 'selected_float64_pfi_native':'T=Float64; update=:pfi; backend=:native' in s,
 '40_named_predicates':len(names)==40 and names==p['predicate_names'],
 '15_probe_fields':len(fields)==15,
 'two_input_copies':s.count('copy(')==2,
 'no_callback_copies_scans':all(x not in callback for x in ['copy(','push!','collect(','for ','all(','sum(']),
 'ordinary_observer':'observer=probe,kernel_timing=true' in s and '_StageObserver' not in s,
 'original_guard_and_throw':'guard=JSimplex._guard_stop_callback(stop)' in s and 'throw(sentinel)' in s and 'guard.exception === sentinel' in s,
 'four_stage_conditions':all(x in callback for x in ['probe.stage == 0','probe.stage == 1','probe.stage == 2','probe.stage == 3']),
 'same_workspace_gate':callback.count('state === probe.workspace')==2,
 'two_work_captures':s.count('s5r_selected_work(')==3,
 'fixed_conditional_work':'ftran=2,btran=2,factor=1,iterations=0,refactors=1,checkpoint=1' in s,
 'source_native_flags':all(x in s for x in ['!policy.solve_refinement','!policy.stable_ratio','!policy.pivot_validation']),
 'raw_before_assert':s.index('TOML.print(io,raw)')<s.index('@assert all(values(checks))'),
 'no_extra_numerical_paths':all(x not in s for x in ['transfer_precision(','crash_basis(','forward_solve!(','backward_solve!(','solve(','setprecision(']),
 'protected_production_test_CI':not subprocess.check_output(['git','diff','master','--','src','test','.github']),
}
old=json.loads((O/'pins.json').read_text())['sha256'];assert all(sha(p)==v for p,v in old.items())
paths=set(old)|{str(p) for p in O.iterdir() if p.is_file()}
out=dict(checks=checks,all_passed=all(checks.values()),sha256={p:sha(p) for p in sorted(paths)},candidate_sha256=sha(O/'candidate-reviewed.jl'),candidate_lines=len(s.splitlines()),predicate_names=names,probe_fields=fields,scope='UNEXECUTED; no Julia parser/import/compile/native calls',time_ns=time.time_ns())
with (O/'evidence.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,pins=len(paths),candidate_sha256=out['candidate_sha256'])));assert out['all_passed']
