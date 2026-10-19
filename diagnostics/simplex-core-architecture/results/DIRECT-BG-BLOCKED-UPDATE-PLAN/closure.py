from pathlib import Path
import sys,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST';Q=P.with_name('DIRECT-BG-BLOCKED-UPDATE-PLAN')
sys.path.insert(0,str(P));import control as c
S=R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md';T=R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md'
def bindings(file,mapping={}):
 j=c.rd(Q/file)
 return all(c.sha(mapping.get(c.path(n),c.path(n)))==h for n,h in j['sha256'].items())
h=c.full_host(c.rd(Q/'host-entry.json')['groups']);h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');c.save(Q/'host-closure.json',h)
v=c.rd(Q/'review.json');names=c.rd(Q/'publication-names.json')['paths'];expected=set(names)-{str((Q/'closure.json').relative_to(R)),str((Q/'publication.json').relative_to(R))}
actual={str(x.relative_to(R)) for x in Q.rglob('*') if x.is_file()}|{str(S.relative_to(R)),str(T.relative_to(R))}
checks={
'host':c.host_safe(h) and len(h['groups'])==268,
'refs':h['head']=='a1cc1d768100f199a3e315c89bf39a28651e8970' and h['master']==c.MASTER,
'remotes':h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],
'branch':c.git('branch','--show-current')=='codex/simplex-core-architecture',
'production_checkout':c.git('rev-parse','HEAD',cwd=c.W)==c.MASTER,
'no_tracked_changes':not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'),
'entry_bindings':bindings('entry.json'),
'author_pass':c.rd(Q/'author.json')['all_passed'] is True and c.rd(Q/'author-final.json')['all_passed'] is True,
'author_bindings':bindings('author.json',{S:Q/'spec.before-lookup-clarification.md'}) and bindings('author-final.json'),
'fix_bindings':bindings('review-fix.json',{S:Q/'spec.before-lookup-clarification.md'}),
'initial_review_preserved':v.get('accepted') is True and c.rd(Q/'review-initial.json')['accepted'] is False and bindings('review-initial.json',{S:Q/'spec.before-R2.md',T:Q/'plan.before-R2.md'}),
'review':v.get('accepted') is True and v.get('findings')==[] and v.get('scope')=='BG blocked U experimental plan' and bindings('review.json'),
'review_current_docs':all(str(x) in v['sha256'] or str(x.relative_to(R)) in v['sha256'] for x in [S,T,Q/'DECISIONS.md']),
'exact_package':actual==expected and len(names)==len(set(names)),
'no_julia_artifacts':not list(Q.rglob('*.jl')),
}
result={'all_passed':all(checks.values()),'checks':checks,'sha256':{n:c.sha(R/n) for n in sorted(actual)},'scope':'Documentation closure only; no Julia or numerical execution','historical_mappings':{'review-initial spec/plan':'spec.before-R2.md / plan.before-R2.md','author and review-fix spec':'spec.before-lookup-clarification.md','all other bindings':'original paths unchanged'}}
c.save(Q/'closure.json',result);print(json.dumps(checks));c.require(result['all_passed'],'Closure failed; no publication')
