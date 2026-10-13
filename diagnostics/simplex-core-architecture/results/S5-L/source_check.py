"""Exclusive offline S5-L text/provenance/schema checks; no Julia parser."""
from pathlib import Path
import hashlib,json,re,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';L=D/'results/S5-L';K=L.parent/'S5-K'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
x=read(L/'source-provenance.json');c=(L/'candidate.jl').read_text();s=(R/'test/adaptive_pricing_lifecycle_tests.jl').read_text();k=read(K/'evidence.json')
checks_text=c.split('    checks = (',1)[1].split('\n    )',1)[0];names=re.findall(r'^        (\w+)=',checks_text,re.M)
obs=c.split('    observations = (',1)[1].split('\n    return checks',1)[0];observations=re.findall(r'(\w+)=',obs)
callback=c[c.index('function observe_pending!'):c.index('selected_owners(ws)')]
fields=['active','algorithm','weight_quality','framework_valid','needs_reset','cooldown_until','observations','last_monitor','last_observation','pricing_passes','validated_weights','rejected_weights','switches','resets','return_mode','temporary','trial_until','progress_windows','last_transition']
price=(R/'src/simplex_pricing.jl').read_text().split('end',1)[0];actualfields=re.findall(r'^    (\w+)::',price,re.M)
dedent=lambda t:''.join(line[4:] if line.startswith('    ') else line for line in t.splitlines(keepends=True))
checks={
 'K118_unchanged':len(k['sha256'])==118 and all(sha(p)==v for p,v in k['sha256'].items()),
 'fixture_source_unchanged':sha(R/'test/adaptive_pricing_lifecycle_tests.jl')==x['source_sha256'],
 'three_exact_helpers':len(x['helpers'])==3 and all(h['source_text'] in s and c.count(h['source_text'])==1 and hashlib.sha256(h['source_text'].encode()).hexdigest()==h['sha256'] for h in x['helpers']),
 'two_exact_setup_blocks':all(x[q] in s and c.count(dedent(x[q]))==1 for q in ('setup1_original','setup2_original')),
 'candidate_and_prepare_bound':sha(L/'candidate.jl')==x['candidate_sha256'] and sha(L/'prepare.py')==x['prepare_sha256'],
 'one_setup_one_handoff':c.count('JSimplex.initialize_workspace(')==1 and c.count('JSimplex.make_dual_feasible!(')==1,
 'no_old_testsets_or_weight_helper':'@testset' not in c and 'check_basis_weights' not in c,
 'no_extra_backend_solve_calls':all(t not in c for t in ('forward_solve!','transpose_solve!','refactorize!','solve(problem')),
 'source_root_discriminator':'state.progress.diagnostics.observer.live === probe.live' in callback,
 'published_live_factor_discriminator':'state === probe.live' in callback and 'state.factorization === probe.trial.factorization' in callback and 'state.factorization !== probe.entry_factor' in callback,
 'callback_constant_metadata':all(t not in callback for t in ('copy(','push!','for ','while ','all(','selected_owners')),
 'one_sentinel_identity':'outcome.cause === probe.sentinel' in c and 'throw(probe.sentinel)' in c,
 'three_entry_copies':c.count('copy(')==3,
 'forty_unique_predicates':len(names)==len(set(names))==40,
 'fifteen_observations':len(observations)==len(set(observations))==15,
 'nineteen_pricing_fields':actualfields==fields,
 'raw_before_assertion':c.index('TOML.print(io,Dict')<c.index('all(values(checks)) || error'),
 'bounded_ring_no_copy':'mod1(d.next_event-1,64)' in c and 'recent_events(' not in c,
 'failure_scope_cost':'entry_costs_preserved=isequal(ws.costs,entry.costs)' in c and 'preserve output and stop' in c,
 'not_launched':'UNEXECUTED' in c and not any(L.glob('*.toml')),
}
paths=set(map(Path,k['sha256']));paths.update(p for p in K.rglob('*') if p.is_file());paths.update(p for p in L.iterdir() if p.is_file())
paths.update([D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-ORACLE-REVIEW.md',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-qualification.md'])
e={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'sha256':{str(p):sha(p) for p in sorted(paths)},'candidate_checks':names,'candidate_observations':observations,'pricing_fields':fields,'scope':'Offline source text checks, not Julia syntax validation or observed runtime predicates.'}
with (L/'evidence.json').open('x') as f:json.dump(e,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':e['all_passed'],'pins':len(paths)}));raise SystemExit(0 if e['all_passed'] else 1)
