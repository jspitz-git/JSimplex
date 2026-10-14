"""One-shot OFFLINE preparation closure. No Julia; not a numerical admission."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
C=R/'diagnostics/direct-lu-markowitz/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
base=json.loads((D/'baseline.json').read_text())
checks={}
checks['baseline_514_unchanged']=len(base['sha256'])==514 and all(sha(R/n)==h for n,h in base['sha256'].items())
checks['master_unchanged']=git('rev-parse','master')==base['master']
checks['head_is_preparation_parent']=git('rev-parse','HEAD')==base['head']
checks['plan_frozen']=sha(R/'docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md')=='fb0b3609260394b0719423301284a0713475af793db53e1a828c0dce12efb5d7'
checks['spec_frozen']=sha(R/'docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md')=='1f53fca7568e94a0302eb646b405715ac81e00121172f4e29e17b2f085f381fc'
initial=json.loads((D/'source-check-initial.json').read_text())
checks['initial_checks_preserved']=initial['all_passed'] and all(sha(D/'initial'/('report.md' if n.endswith('/DIRECT-LU-PREPARATION.md') else Path(n).name))==h if n.startswith('diagnostics/') else sha(R/n)==h for n,h in initial['sha256'].items())
checks['implementation_unchanged_after_review']=all((C/n).read_bytes()==(D/'initial'/n).read_bytes() for n in ['factor-export.jl','direct-factor.jl','fixtures.jl','red.jl','prepare-overlay.py'])
fix=json.loads((D/'review-fix.json').read_text())
checks['test_fix_bound']=fix['all_passed'] and sha(C/'correctness.jl')==fix['after_sha256'] and sha(D/'initial/correctness.jl')==fix['before_sha256']
continuation=json.loads((D/'continuation.json').read_text())
checks['four_prior_continuation_bindings']=len(continuation['mappings'])==4 and all(sha(R/v['preserved_path'])==v['sha256']==json.loads((R/v['record']).read_text())['sha256'][v['key']] for v in continuation['mappings'])
overlay=json.loads((D/'overlay-initial.json').read_text());O=Path(overlay['output_root'])
anchor=b'include("huangfu_hall_factorization.jl")\n';addition=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
checks['overlay_inverse_and_candidates']=all((O/n).read_bytes()==((R/n).read_bytes().replace(anchor,anchor+addition) if n=='src/JSimplex.jl' else (R/n).read_bytes()) for n in overlay['source_sha256'] if not n.startswith('candidate/')) and all((O/'src'/n).read_bytes()==(C/n).read_bytes() for n in ['factor-export.jl','direct-factor.jl'])
checks['no_overlay_user_environment']=not (O/'Manifest.toml').exists() and not (O/'LocalPreferences.toml').exists()
checks['no_later_stage_drivers']=not (C/'cost.jl').exists() and not (C/'solver-check.jl').exists()
review=(D/'review-final.md').read_text()
checks['review_accepts_offline']='ACCEPTED' in review and 'offline' in review.lower()
# Final read-file bindings must all resolve unchanged. Review initial binds the
# two preserved initial texts explicitly through the closure provenance below.
final=json.loads((D/'review-final-bindings.json').read_text())
checks['final_review_bindings']=all(sha(R/n)==h for n,h in final['sha256'].items())
initial_review=json.loads((D/'review-initial-bindings.json').read_text())
oldmap={'diagnostics/direct-lu-markowitz/reproduce/correctness.jl':D/'initial/correctness.jl','diagnostics/simplex-core-architecture/DIRECT-LU-PREPARATION.md':D/'initial/report.md'}
checks['initial_review_preserved_bindings']=all(sha(oldmap.get(n,R/n))==h for n,h in initial_review['sha256'].items())
host=json.loads((D/'host.json').read_text())
checks['fresh_preparation_host_clear']=bool(host['boot_id']) and len(host['groups'])==196 and host['matches']==[] and host['head']==base['head']
supplement=json.loads((D/'review-oracle-supplement.json').read_text())
checks['oracle_supplement_bindings']=supplement['decision']=='no_additional_finding_final_offline_acceptance_stands' and all(sha(Path(n))==h for n,h in supplement['sha256'].items())
checks['tracked_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R).returncode==0
paths=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in ['closure.json','publication.json'])+sorted(C.iterdir())+[R/'diagnostics/simplex-core-architecture/DIRECT-LU-PREPARATION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
result={'all_passed':all(checks.values()),'checks':checks,'scope':'Offline source/hash/inverse closure only; no executed Julia test or numerical acceptance','sha256':{str(p.relative_to(R)):sha(p) for p in paths},'initial_review_mapping':{'diagnostics/direct-lu-markowitz/reproduce/correctness.jl':str((D/'initial/correctness.jl').relative_to(R)),'diagnostics/simplex-core-architecture/DIRECT-LU-PREPARATION.md':str((D/'initial/report.md').relative_to(R))}}
with (D/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':checks,'bindings':len(result['sha256'])},indent=2))
if not result['all_passed']:raise SystemExit(1)
