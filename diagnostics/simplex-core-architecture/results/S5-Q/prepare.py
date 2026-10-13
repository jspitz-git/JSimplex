"""Exclusive offline source-oracle preparation; no Julia or numerical fixture."""
from pathlib import Path
import json,hashlib,subprocess,time,re
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';Q=D/'results/S5-Q';P=Q.parent/'S5-P'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(n):return (R/n).read_text()
old=json.loads((P/'evidence.json').read_text());pc=json.loads((P/'closure.json').read_text());pi=json.loads((P/'independent.json').read_text());ph=json.loads((P/'host-before.json').read_text())
assert all(sha(p)==h for p,h in old['sha256'].items()) and all(sha(p)==h for p,h in pc['sha256'].items()) and all(sha(p)==h for p,h in pi['sha256'].items())
groups=set(ph['groups']);hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().strip().startswith('julia'):hits.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (OSError,ValueError,IndexError):pass
assert not hits
host=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=hits,user_hashes={p:sha(p) for p in ph['user_hashes']},refs={x:subprocess.check_output(['git','rev-parse',x],text=True).strip() for x in ['HEAD','master']},remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True),time_ns=time.time_ns())
with (Q/'host-before.json').open('x') as f:json.dump(host,f,indent=2);f.write('\n')
s=read('test/simplex_precision_tests.jl');start=s.index('            p=LinearProblem(sparse(T[2 1;1 3])');end=s.index('\n            ws.iterations=3;',start);setup=s[start:end]
with (Q/'existing-setup.txt').open('x') as f:f.write(setup+'\n')
# Source excerpt only. No substituted Julia fixture/candidate is created.
rowname='Transfer rebuilds the actual typed basis and retains cumulative work';rows=[]
for run in ['38142752357','38149970679']:
 meta=D/f'results/S6-A/ci-inventory-1-{run}-metadata.json';md=json.loads(meta.read_text());log=R/f'.superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{run}-failed.log';lines=log.read_text().splitlines();found=[(i+1,l) for i,l in enumerate(lines) if rowname in l and '|' in l];assert len(found)==1
 no,raw=found[0];clean=re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',raw);assert clean.split('|',1)[1].split()[:2]==['1504','1504'];historical=subprocess.check_output(['git','show',md['headSha']+':test/simplex_precision_tests.jl']);assert historical==(R/'test/simplex_precision_tests.jl').read_bytes()
 rows.append(dict(run=run,head=md['headSha'],conclusion=md['conclusion'],line=no,raw=raw,normalized=clean,passed=1504,total=1504,whole_file_equal=True,sha256=sha(R/'test/simplex_precision_tests.jl')))
a=read('src/simplex_start.jl');r=read('src/simplex_recovery.jl');j=read('src/simplex.jl');n=read('src/simplex_numerics.jl');d=read('src/simplex_diagnostics.jl');du=read('src/dual_simplex.jl');pr=read('src/simplex_pricing.jl')
body=r[r.index('function _remember_verified_basis!'):r.index('function _store_basis_checkpoint!')]
checks={
 'prior157_and_closure25_and_author7':len(old['sha256'])==157 and len(pc['sha256'])==25 and len(pi['sha256'])==7,
 'existing_Float64_PFI_native_combination':'(Float64,BigFloat,128)' in s and 'update in (:pfi,' in s and 'backend in (:native,:markowitz)' in s,
 'existing_recovery_true_refinement_default':'recovery=true,' in setup and 'solve_refinement=' not in setup and 'numerical_profile=' not in setup,
 'native_profile_disables_refinement':'numerical_profile::Symbol=:native' in n and 'solve_refinement::Bool=(numerical_profile == :checked)' in n,
 'source_setup_verbatim':(Q/'existing-setup.txt').read_text().rstrip('\n')==setup,
 'observer_then_immediate_stop_then_store':body.index('_recovery_observer!')<body.index('stop() && return false',body.index('_recovery_observer!'))<body.index('_store_basis_checkpoint!'),
 'checkpoint_copy_before_observer':body.index('checkpoint = checkpoint_basis(ws)')<body.index('_recovery_observer!'),
 'record_after_store':body.index('_store_basis_checkpoint!')<body.index('_record_recovery!'),
 'default_recompute_before_initial_event':'recompute!(workspace)\n    _simplex_event!(workspace, :refactor_initial)' in j,
 'refactor_counter_before_other_event':'workspace.refactorizations += 1\n        _simplex_event!(workspace, diagnostic_reason)' in j,
 'imported_invalidation_before_recompute':'_invalidate_basis_checkpoints!(ws)\n        recompute!(ws;refactorize=true,caller_guard=guard)' in a,
 'ordinary_observer_not_stage':'ws.progress.diagnostics.observer isa _StageObserver' in read('src/simplex_pivot.jl'),
 'guard_original_exception':'stop.exception = exception\n        rethrow()' in du,
 'no_refinement_callback_with_false':'policy.solve_refinement || return true' in r,
 'recompute_recovery_conditional':'isempty(workspace.factorization.updates)' in j and '_remember_verified_basis!(workspace,_basis_solve_stop(workspace,caller_guard))' in j,
 'selected_no_auto_pricing_state':'pricing=:devex' in setup and 'isnothing(state) && return nothing' in pr,
 'record_event_separate_from_checkpoint_observer':'_record_recovery!(diagnostics::SimplexDiagnostics,reason) = record_event!(diagnostics,reason)' in r,
 'historical1504_each_failed_run':len(rows)==2 and all(x['passed']==1504 and x['whole_file_equal'] for x in rows),
}
oracle={
 'state':'OFFLINE PROSPECTIVE ONLY; no fixture or driver created',
 'existing_source':'test/simplex_precision_tests.jl::Transfer rebuilds the actual typed basis and retains cumulative work',
 'selection':{'T':'Float64','update':'pfi','backend':'native','scope':'existing setup only; no transfer_precision, crash_basis, solve, success control, resume or loop'},
 'adaptation':'Retain model/basis/options/policy values exactly. Replace progress diagnostics Nothing with an ordinary observer, retain original time_ns start/objective/scaling/offsets7/11; opt in to existing kernel timing. Add explicit throwing stop and original sentinel. No numerical-policy flag is changed.',
 'discriminator':['Default :checkpoint before :refactor_initial is counted but cannot arm.','Exactly one :refactor_initial latches workspace and default Basis vector owners.','Exactly one :refactor_other on that workspace with local refactorizations1 marks imported stage and latches imported Basis owners.','Only subsequent :checkpoint on the same workspace after both latches arms the stop.','The immediate following stop call throws the same sentinel; unexpected order/duplicate/missing target fails qualification.'],
 'selected_assertions':['No workspace return; caught exception === sentinel and guard.exception === sentinel if guard is explicitly retained.','One initial latch, one imported latch, one selected checkpoint observer, one throw; no extra calls after throw.','Two explicit stop calls total under unchanged recovery-true/refinement-false policy: first before imported checkpoint quality, second after its observer.','Caller basis owners and two saved vector values unchanged; imported owners distinct from both caller and default owners.','Retained workspace.problem === original problem; progress diagnostics/objective/scaling references retained; start_ns and offsets7/11 unchanged.','Local iterations0/refactorizations1 at throw and unwind; no mutation of external immutable progress fields inferred from diagnostic changes.','Imported checkpoint history empty after invalidation and throwing second stop; phase_generation1; earlier default checkpoint was recorded once but is no longer in local history.','Recorded checkpoint count remains1; refactor_initial1/refactor_other1; selected observer count is not a second recorded checkpoint.','Four observer callbacks expected on admitted successful-prefix path: defaultcheckpoint,initial,other,importedcheckpoint; three recorded events, final refactor_other.','Counted FTRAN2/BTRAN2/refactorization1 at throw and unwind; correction/correction_attempt0. Hypersparse counters are not asserted zero and base factory work is additional.','Prospective setup/policy/options/scalar/source selection must bind actual later source; any mismatch preserves failure and stops.'],
 'observation_cost':{'input_basis_copies':2,'copied_entries':'m+v = 6 for existing m2,n2','reference_roles':9,'roles':['workspace','default_indices','default_states','imported_indices','imported_states','caller_indices','caller_states','sentinel','guard'],'scalar_bookkeeping':'fixed observer/stop/latch/throw counters, armed/order flags, selected work/event-count scalars at throw; no vector callback scans/copies or growing ledgers','retention':'roles do not count caller model/progress/diagnostics/closure/container aliases or cap retained factor/scratch/cache graph'},
 'conditional_work':{'default_factory_entries':1,'imported_refactor_entries':1,'counted_FTRAN_entries':2,'counted_BTRAN_entries':2,'optional_refinement_correction_entries':0,'checkpoint_constructions':2,'checkpoint_copied_containers':10,'checkpoint_copied_entries':'2*(m+4v)=36','checkpoint_quality_entries':'up to4 across default/imported checkpoint checks; no final outer reliability because stop throws first','final_outer_devex_reset':'unreached; imported refactor devex reset already occurred','limitations':'source-level conditional path, not observed PREforward/native/import accounting; hypersparse support/metadata/factor orientation/backend work additional'},
 'failure_policy':'Any future missing/duplicate/unreached discriminator, syntax/import/resource/numerical/assertion/cost mismatch must be preserved and stopped, without retry, fixture tuning or defect inference. No future attempt admitted here.',
 'limits':['Retained workspace mutable until unwind; no full-state/event trajectory or rollback.','No original certificate transfer, reliability/feasibility implication, observer neutrality or actual clock expiry.','Default/native stop semantics unchanged; original setup default time limit Inf retained.']}
with (Q/'oracle.json').open('x') as f:json.dump(oracle,f,indent=2);f.write('\n')
paths={Path(p) for p in old['sha256']}|{Path(p) for p in pi['sha256']}|{p for p in P.rglob('*') if p.is_file()}|{Path(__file__).resolve(),Q/'host-before.json',Q/'existing-setup.txt',Q/'oracle.json',R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-oracle.md',D/'S5-BASIS-INITIALIZATION-CONTRACT-REVIEW.md'}
out=dict(all_passed=all(checks.values()),checks=checks,rows=rows,sha256={str(p):sha(p) for p in sorted(paths)},time_ns=time.time_ns())
with (Q/'evidence.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pins':len(paths)}));assert out['all_passed']
