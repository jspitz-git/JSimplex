"""One-shot publication whitespace supplement; preserve frozen source bytes."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-N'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
initial=read(D/'publication.json');closure=read(D/'closure.json');pins=read(D/'pins.json')
paths=[D/'prepare-2.py',D/'prepare-3.py']
expected=''.join(str(p.relative_to(R))+':15: trailing whitespace.\n+ \n' for p in paths)
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
checks={
 'initial_failure_only_staged_whitespace':initial['all_passed'] is False and initial['checks']==dict(closure_pass=True,closure_bindings=True,exact_stage_before_self=True,staged_bytes_exact=True,staged_diff_clean=False),
 'exact_two_whitespace_diagnostics':r.returncode==2 and r.stdout==expected and not r.stderr,
 'two_lines_exact_single_space':all(p.read_bytes().splitlines()[14]==b' ' for p in paths),
 'both_sources_frozen_and_unchanged':all(sha(p)==pins['inventory'][str(p)]['sha256'] for p in paths),
 'original_closure_pass_and_bindings_current':closure['all_passed'] is True and all(closure['checks'].values()) and all(sha(p)==v for p,v in closure['sha256'].items()),
 'all_initial_publication_bytes_and_blobs_unchanged':all(sha(R/p)==v for p,v in initial['sha256'].items()) and all(subprocess.check_output(['git','rev-parse',':'+p],text=True).strip()==v for p,v in initial['staged_blobs'].items()),
}
v=dict(all_passed=all(checks.values()),checks=checks,expected_diagnostics=expected,git_check=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),sha256={str(p):sha(p) for p in [*paths,D/'pins.json',D/'closure.json',D/'publication.json',Path(__file__).resolve()]},scope='Only the exact two frozen single-space lines are preserved. No general whitespace exemption; initial FALSE publication remains unchanged.')
with (D/'publication-whitespace-supplement.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(v['all_passed'],'supplement failed')
