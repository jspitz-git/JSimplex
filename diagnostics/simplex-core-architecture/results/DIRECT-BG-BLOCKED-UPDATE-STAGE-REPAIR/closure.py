"""Separate closure of offline stage repair; no Julia or earlier script execution."""
from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR');sys.path.insert(0,str(H));import control as c
checks={}
def ck(n,v):checks[n]=bool(v);c.require(v,n)
inputs=D/'review-inputs.json';v=c.rd(D/'review.json');m=c.rd(D/'stage.json');s=Path(m['stage'])
ck('independent_acceptance',v.get('accepted') is True and v.get('findings')==[])
ck('exact_review_membership',set(v['sha256'])==set(c.rd(inputs)['sha256'])|{str(inputs)})
ck('review_bindings',c.bindings(v))
if 'evidence_sha256' in v:ck('review_evidence',c.bindings(v,'evidence_sha256'))
ck('no_runtime_acceptance',all(v.get(k) is False for k in ['launch_admitted','runtime_acceptance','numerical_acceptance','performance_acceptance']))
ck('verification',c.rd(D/'verification.json')['all_passed'] is True and c.bindings(c.rd(D/'verification.json')))
ck('candidate_preserved',all(c.sha(n)==h for n,h in c.rd(D/'verification.json')['candidate_sha256'].items()))
ck('new_stage_exact',c.bindings(m) and set(m['stage_files'])=={str(p.relative_to(s)) for p in s.rglob('*') if p.is_file()})
ck('new_stage_no_symlinks',not s.is_symlink() and not any(p.is_symlink() for p in s.rglob('*')))
old=c.rd(H/'runs/red300/sealed.json');ck('old_seal_unchanged',c.guard.pins_match(old))
red=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');ck('failed_red_publication_unchanged',c.bindings(c.rd(red/'publication-final.json')))
ck('red_still_not_qualified',c.rd(H/'runs/red300/audit.json')['all_passed'] is False and not (H/'runs/red300/result-review.json').exists())
oldhost=c.rd(H/'runs/red300/outer-closure.json')['host'];h=c.full_host(oldhost['groups']);h['memory']=c.guard.memory();c.save(D/'host-closure.json',h)
ck('fresh_host_refs',c.host_safe(h) and h['head']==c.rd(D/'entry.json')['head'] and h['master']==m['master'] and h['boot_id']==c.rd(D/'host-entry.json')['boot_id'])
ck('no_visible_julia_prior_groups_sessions',h['matches']==[] and len(h['groups'])==271)
ck('clean_tracked_index',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('no_new_run_artifacts',not (H/'runs/green300').exists() and not any((D/n).exists() for n in ['runs','outers','reservation.json','sealed.json']))
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
ck('preserved_continuation',ledger.read_bytes()==(D/'progress.md.after-stage-repair').read_bytes() and (D/'progress.md.before-stage-repair').is_file())
names=c.rd(D/'publication-names.json')['paths'];actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}
ck('exact_package_names',actual==set(names)-{str((D/n).relative_to(R)) for n in ['closure.json','publication.json']} and len(names)==len(set(names)))
c.save(D/'closure.json',dict(all_passed=True,launch_admitted=False,checks=checks,sha256={n:c.sha(R/n) for n in sorted(actual)},scope=__doc__))
print('Offline closure PASS',len(checks),'checks',len(actual),'bindings')
