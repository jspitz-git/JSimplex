from pathlib import Path
import hashlib,json,re,tomllib,time
R=Path.cwd();H=R/'diagnostics/simplex-core-architecture/results/S5-H';G=H.parent/'S5-G';F=H.parent/'S5-F'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def out(name,x):
 with (H/name).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
original=(R/'test/simplex_precision_state_tests.jl').read_bytes();a=(H/'append.jl').read_text();candidate=(H/'candidate.jl').read_bytes();f=(F/'driver-reviewed.jl').read_text()
fixture=f.split('    # BEGIN EXISTING FIXTURE (only progress injection differs)\n')[1].split('    # END EXISTING FIXTURE')[0].replace('JS.','JSimplex.')
candidate_fixture=a[a.index('            p=LinearProblem'):a.index('            # Equality')]
norm=lambda x:re.sub(r'\s+','',x)
callback=a[a.index('observer=(reason,trial)'):a.index('            stop=')]
oldpins=json.loads((G/'qualification-1/pins.json').read_text())['inventory']
oldcheck={p:sha(p)==v['sha256'] for p,v in oldpins.items()}
fpins=tomllib.loads((F/'source-pins-reviewed.toml').read_text())['sha256']
raw={m:tomllib.loads((G/f'qualification-1/raw/{m}.toml').read_text()) for m in ('stop','throw')}
checks={
 'whole_prefix':candidate==original+a.encode(),
 'original_size':len(original)==10583,
 'fixture_exact_tokens':norm(fixture)==norm(candidate_fixture),
 'two_cases_one_transfer_site':a.count('for mode in (:stop,:throw)')==1 and a.count('JSimplex.transfer_precision(')==1,
 'callback_bounded':all(s not in callback for s in ('copy(', 'snapshot', 'recompute', 'solve', 'push!', 'ws.')) and 'retained[]=trial' in callback,
 'arm_after_setup':a.index('armed[]=true')>a.index('saved=map(copy,source)')>a.index('JSimplex.recompute!(ws)'),
 'direct_cause': 'caught isa JSimplex.DiagnosticObserverFailure' in a and 'caught.cause===failure' in a,
 'no_diagnostic_encoding':all(x not in a for x in ('TOML','Serialization','identity_token','string(', 'BigInt', '_checkpoint_matches')),
 'source_single_copy':a.count('map(copy,source)')==1 and a.count('=copy(ws.')==3,
 'fresh_empty': 'isempty(fresh.scratch.checkpoints) && isnothing(fresh.scratch.sparse_pricing)' in a,
 'ambient_and_time_type': '(precision(BigFloat),rounding(BigFloat))==ambient' in a and 'fresh.options.time_limit isa Float64' in a,
 'source_owner_and_cache': 'journal.workspace_id==objectid(ws)' in a and 'ws.scratch.sparse_pricing.rows.matrix===ws.problem.A' in a,
 'partial_work_bound': '1<=delta<=4' in a and '0<=delta<=3' in a and 'untimed' not in a and 'omit the direct unit BTRAN' in a,
 'G_all752_unchanged':len(oldcheck)==752 and all(oldcheck.values()),
 'F_all176_unchanged':len(fpins)==176 and all(sha(p)==v for p,v in fpins.items()),
 'G_original_false_preserved':json.loads((G/'audit.json').read_text())['all_passed']==False,
 'G_supplement_pass':json.loads((G/'outcome-supplement.json').read_text())['all_passed'],
 'G_executed_two_cases':all(len(raw[m]['checks'])==24 and all(raw[m]['checks'].values()) for m in raw),
}
red_tokens=['# BEGIN ACTIVE JOURNAL INTERRUPTION COVERAGE','ws.costs=copy(ws.costs);ws.lower=copy(ws.lower);ws.upper=copy(ws.upper)','caught.cause===failure','saved=map(copy,source)']
red={s:s not in original.decode() for s in red_tokens}
paths=set(oldpins)|set(fpins)
paths.update(str(p.resolve()) for p in H.iterdir() if p.is_file())
paths.update(str(p.resolve()) for p in G.rglob('*') if p.is_file())
paths.update(str(p.resolve()) for p in (R/'diagnostics/simplex-core-architecture').glob('S5-PRECISION-JOURNAL*.md'))
paths.update(str((R/'docs/superpowers/plans'/n).resolve()) for n in ['2026-10-13-precision-journal-interruption-test-preparation.md','2026-10-13-precision-journal-interruption-test-integration.md'])
inv={p:sha(p) for p in sorted(paths)}
out('evidence.json',{'checks':checks,'structural_red_missing':red,'all_passed':all(checks.values()) and all(red.values()),'prefix_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':sha(H/'candidate.jl'),'time_ns':time.time_ns(),'scope':'OFFLINE ONLY; no Julia syntax/runtime test','copies_per_case':34,'copied_entries_per_case':85,'sha256':inv})
print(json.dumps({'checks':checks,'pins':len(inv)}));raise SystemExit(0 if all(checks.values()) and all(red.values()) else 1)
