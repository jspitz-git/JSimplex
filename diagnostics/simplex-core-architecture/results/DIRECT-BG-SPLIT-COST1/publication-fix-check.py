"""Fresh independent publication-only inspection; no existing scripts executed."""
from pathlib import Path
import hashlib,json,subprocess,traceback
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST1';run=E.parent/'DIRECT-BG-SPLIT-COST-PREPARATION/runs/cost1-300'
checks={};details={}
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def git(*a):return subprocess.run(['git',*a],cwd=R,text=True,capture_output=True)
def save(v):
 with (E/'publication-fix-check.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
try:
 original=rd(E/'closure.json');names=rd(E/'publication-names.json')['names'];failure=rd(E/'publication-failure.json');csv=E/'summary.csv';csvname=str(csv.relative_to(R));missing=str((E/'publication.json').relative_to(R))
 ok(original['all_passed'] is True and len(original['checks'])==19 and all(original['checks'].values()) and len(original['sha256'])==236,'original19_236closure')
 ok(all(sha(R/n)==h for n,h in original['sha256'].items()),'all_original_closure_bytes_unchanged')
 review=rd(run/'result-review.json')
 ok(review['accepted'] is True and review['findings']==[] and review['performance_qualified'] is False,'diagnostic_acceptance_performance_rejection')
 ok(set(review['sha256'])=={str(p) for p in run.rglob('*') if p.is_file() and p!=run/'result-review.json'} and len(review['sha256'])==210 and all(sha(p)==h for p,h in review['sha256'].items()),'exact210_result_bindings')
 ok(len(review['evidence_sha256'])==23 and all(sha(p)==h for p,h in review['evidence_sha256'].items()),'all23_accepted_evidence_frozen')
 ok(len(names)==len(set(names))==238 and missing in names and not (R/missing).exists(),'original_missing_publication_preserved')
 staged=git('diff','--cached','--name-only');ok(staged.returncode==0 and set(staged.stdout.splitlines())==set(names)-{missing},'exact_original237_staged_paths')
 ok(all(git('rev-parse',':'+n).stdout.strip()==git('hash-object',n).stdout.strip() for n in names if n!=missing),'original_stage_matches_disk')
 raw=csv.read_bytes();ok(raw.count(b'\r\n')==raw.count(b'\r')==raw.count(b'\n')==9 and raw.endswith(b'\r\n'),'exact_nine_CRLF')
 ok(all(line.rstrip(b' \t')==line for line in raw.split(b'\r\n')),'no_trailing_spaces_tabs')
 ok(failure['original_publication_exit']==1 and failure['verification_returncode']==2 and failure['stderr']=='' and 'before publication.json/commit/push' in failure['stage'],'failure_stage_exit_preserved')
 expected=''.join(csvname+':'+str(i)+': trailing whitespace.\n+'+line.decode()+'\n' for i,line in enumerate(raw.split(b'\r\n')[:-1],1))
 ok(failure['stdout']==expected,'failure_exactly_nine_CR_diagnostics')
 other=git('diff','--cached','--check','--','.',':(exclude)'+csvname)
 onlycsv=git('-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',csvname)
 ok(other.returncode==0 and not other.stdout and not other.stderr,'fresh_default_check_all_other_files')
 ok(onlycsv.returncode==0 and not onlycsv.stdout and not onlycsv.stderr,'fresh_CR_at_EOL_check_CSV_only')
 source=(E/'publication-final.py').read_text()
 ok("old['sha256'].items()" in source and "review['sha256'].items()" in source and "review['accepted'] is True and review['findings']==[]" in source,'final_validates_closure_and_independent_review')
 ok("len(names)==len(set(names)) and actual==set(prior)" in source and "for root in (E,run)" in source,'final_exact_complete_new_scope')
 ok("set(oldnames)-{missing}" in source and "need(not (R/missing).exists()" in source,'final_preserves_original_failed_membership')
 ok("['git','diff','--cached','--check','--','.',':(exclude)'+csvname]" in source and "['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',csvname]" in source,'override_only_for_CSV')
 ok("raw.count(b'\\r\\n')==9" in source and "line.rstrip(b' \\t')==line" in source,'final_explicit_CRLF_only_guard')
 ok("git('hash-object',n)==v" in source and "git('rev-parse',':'+n)==git('hash-object',n)" in source and "open('x')" in source,'final_exact_blobs_exclusive_output')
 ok("'commit'" not in source and "'push'" not in source and 'julia' not in source.lower(),'final_has_no_commit_push_numerics')
 ok(not (E/'publication-final.json').exists() and not (E/'publication-names-final.json').exists(),'correction_not_yet_executed')
 ok(git('rev-parse','HEAD').stdout.strip()=='49b26f913df5497bafa8292529a872070864911c' and git('rev-parse','master').stdout.strip()=='26e2291745999f485a74f643298ca997d65c7205','refs_uncommitted_unchanged')
 details=dict(CRLF_rows=9,original_staged_paths=237,result_bindings=210,result_evidence_bindings=23,original_closure_bindings=236,git_other=dict(returncode=other.returncode,stdout=other.stdout,stderr=other.stderr),git_csv=dict(returncode=onlycsv.returncode,stdout=onlycsv.stdout,stderr=onlycsv.stderr))
 save(dict(accepted=True,checks=checks,check_count=len(checks),details=details,scope='Publication-only correction; no accepted artifact changed and no old scripts or numerics executed.'))
 print('PASS',len(checks),'publication-only checks')
except Exception:
 save(dict(accepted=False,checks=checks,check_count=len(checks),details=details,error=traceback.format_exc()));raise
