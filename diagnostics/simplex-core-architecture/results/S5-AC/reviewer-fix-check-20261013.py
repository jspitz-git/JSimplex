"""New read-only narrow correction verification; does not execute other evidence."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();H=R/'diagnostics/simplex-core-architecture/results/S5-AC';D=H.parent.parent
seen={}
def h(p):
 p=Path(p);v=hashlib.sha256(p.read_bytes()).hexdigest();seen[str(p)]=v;return v
def j(p):h(p);return json.loads(Path(p).read_text())
f=j(H/'review-fix.json'); prior=j(H/'reviewer-check-20261013.json'); source=j(H/'source-check.json')
P=D/'S5-CLEANUP-ENTRY-REUSE-DECISION.md';B=H/(P.name+'.before-review');before=B.read_bytes();after=P.read_bytes()
old=b'if kernel_timing=true, FTRAN/BTRAN/pricing calls.'
new=b'if kernel_timing=true, FTRAN/BTRAN calls. The direct initial reduced-cost recomputation is not wrapped in the production pricing timer; S5-A counted that pricing request through its separate diagnostic wrapper.'
c={}
c['six_fix_bindings']=len(f['sha256'])==6 and all(h(p)==v for p,v in f['sha256'].items())
c['six_fix_checks']=len(f['checks'])==6 and f['all_passed'] is True and all(f['checks'].values())
c['exact_single_correction']=before.count(old)==1 and after==before.replace(old,new)
c['preserved_original']=h(B)==source['sha256'][str(P)]==prior['sha256'][str(P)]=='36e96502096ea0677fa13a4970c217b030375020202226d6b137ca054ac38ef7'
plan=R/'docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md'
c['unchanged_next_plan']=h(plan)==prior['sha256'][str(plan)]=='987e7f2a462c5b0d2d97bae05f2df4c24bee0f031d317d9801d8e0aee48c105f'
s=R/'src/simplex.jl';q=R/'src/simplex_recovery.jl';w=R/'.superpowers/simplex-core-architecture/S5-A/census-1-source/cleanup_entry_census.jl'
c['source_and_wrapper_preserved']=all(h(p)==prior['sha256'][str(p)] for p in (s,q,w))
st=s.read_text();rt=q.read_text();wr=w.read_text()
recompute=st[st.index('function recompute!('):st.index('recompute!(workspace::SimplexWorkspace, refactorize::Bool)')]
prices=st[st.index('function _recompute_reduced_costs!'):st.index('function recompute!(')]
checked=rt[rt.index('function _checked_basis_solve!'):rt.index('# Precision-specialized repair')]
c['two_timed_solves_direct_untimed_prices']=recompute.count('_checked_basis_solve!')==2 and '_recompute_reduced_costs!(workspace.reduced_costs, workspace, dual)' in recompute and ':pricing' not in recompute and '_timed_simplex' not in prices and '_timed_simplex(ws, transposed ? :btran : :ftran)' in checked
c['historical_diagnostic_wrapper']='"pricing_reconstructions"' in wr and '("simplex.jl","function _recompute_reduced_costs!",:(_ce_counts[3]+=1))' in wr
c['continuation_texts_unchanged']=all(h(p)==prior['sha256'][str(p)] for p in (D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'))
c['initial_rejection_preserved']=h(H/'review-initial.md')=='2998e892e468b8b2516865cc8e277a39ef22558e3fb0d012c29c95f6422c32e0' and 'Verdict: REJECTED' in (H/'review-initial.md').read_text()
c['tracked_delta_empty']=not subprocess.check_output(['git','diff','HEAD','--name-only'],text=True).strip()
h(H/'reviewer-read-failure.md');h(__file__)
with (H/'reviewer-fix-check-20261013.json').open('x') as out:json.dump({'checks':c,'all_passed':all(c.values()),'sha256':seen,'scope':'Narrow source/text/hash correction verification only; no frozen scripts or numerical execution'},out,indent=2);out.write('\n')
print(json.dumps({'checks':c,'all_passed':all(c.values()),'bindings':len(seen)}));assert all(c.values())
