"""One-shot offline planning closure; frozen evidence is read, never rerun."""
from pathlib import Path
import importlib.util,json,sys
D=Path(__file__).resolve().parent;R=D.parents[3]
P=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED')
sys.path.insert(0,str(P))
sp=importlib.util.spec_from_file_location('prior_control',P/'control.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
checks={}
def ck(v,n):checks[n]=bool(v)
review=c.rd(D/'review.json');src=c.rd(D/'source-check.json');ind=c.rd(D/'independent-check.json')
ck(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')=='BG export specialization plan','independent_acceptance')
ck(bool(review.get('sha256')) and c.bindings(review),'review_bindings')
amend=c.rd(D/'independent-amendment-check.json')
ck(amend['all_passed'] and all(amend['checks'].values()) and c.bindings(amend),'fresh_independent_amendment')
fix=c.rd(D/'review-fix.json');mapping=fix['historical_path_map']
def historical_bindings(j):return all(c.sha(Path(mapping.get(p,p)))==h for p,h in j['sha256'].items())
ck(src['all_passed'] and all(src['checks'].values()) and historical_bindings(src),'initial_author_bindings_mapped_to_preserved_text')
ck(ind['all_passed'] is False and [k for k,v in ind['checks'].items() if not v]==['plan_correctly_names_amended_import_source'] and historical_bindings(ind),'initial_single_rejection_preserved')
ck(fix['all_passed'] and all(fix['checks'].values()) and c.bindings(fix),'exact_lineage_amendment')
ck(c.rd(D/'review-rejected.json')['accepted'] is False and historical_bindings(c.rd(D/'review-rejected.json')),'original_rejected_review_preserved')
S=R/'docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md';Q=R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md'
ck(all(str(p) in review['sha256'] for p in [S,Q,D/'SELF-REVIEW.md']),'review_covers_final_texts')
h=c.full_host(c.rd(P/'runs/profile300/posthost.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(D/'host-closure.json',h)
entry=c.rd(D/'host.json')
ck(c.host_safe(h) and set(entry['groups'])<=set(h['groups']) and h['boot_id']==entry['boot_id'],'fresh_full_groups_sessions')
ck(h['head']==entry['head']=='39beb6ff4a9f287dbbfc4c2a3b821d47ce374d0d' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture','refs_unchanged')
ck(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'remote_refs_unchanged')
ck(not c.git('diff','--name-only','HEAD') and not c.git('diff','--cached','--name-only'),'tracked_files_and_index_unchanged')
ck(all(line in h['status'].splitlines() for line in entry['status'].splitlines()),'prior_untracked_preserved')
ck(not (R/'diagnostics/direct-bg-export-specialized').exists(),'no_new_candidate')
ck(c.bindings(c.rd(P/'publication.json')),'previous_publication_frozen')
names=c.rd(D/'publication-names-2.json')['names'];future={str((D/n).relative_to(R)) for n in ['closure-2.json','publication.json']}
actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [S,Q]}
ck(len(names)==len(set(names)) and actual==set(names)-future,'exact_new_files')
ck(all(n.startswith(str(D.relative_to(R))+'/') or n in [str(S.relative_to(R)),str(Q.relative_to(R))] for n in names),'planning_scope_only')
out=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Planning only; candidate and numerical work deferred to separate admitted tasks')
c.save(D/'closure-2.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Closure failed; preserve original')
