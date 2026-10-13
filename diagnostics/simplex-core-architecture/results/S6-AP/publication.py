"""Exclusive publication checks and exact index manifest; commit/push are separate."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def sh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads((H/'closure.json').read_text());c={'closure_PASS':d['all_passed'] is True and all(d['checks'].values()),'closure_bindings':all(sh(p)==v for p,v in d['sha256'].items())}
base=['diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','diagnostics/simplex-core-architecture/S6-TEST-MPS-FAILURE-PROVENANCE.md','diagnostics/simplex-core-architecture/S6-TEST-MPS-FAILURE-PROVENANCE-REVIEW.md','docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md']
tracked=set(git('diff','--name-only','HEAD').splitlines());c['only_expected_tracked']=tracked==set(base[:2])
authored=base+[str(p.relative_to(R)) for p in H.rglob('*') if p.is_file() and p.suffix=='.py']
# Tracked authored files checked by git; new authored text rejects trailing spaces separately.
c['authored_whitespace']=subprocess.run(['git','diff','--check','--',*base],capture_output=True).returncode==0 and all(all(line.rstrip(' \t')==line for line in (R/p).read_text().splitlines()) for p in authored)
c['raw_bytes_preserved']=sh(H/'user-failure.log')=='22da06e3955a94ffa25fc1f0a0630e933c124aa4a137a25e159b57877030e115'
c['master_unchanged']=git('-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD')=='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
with (H/'publication-check.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),closure_sha256=sh(H/'closure.json'),verbatim_policy='Raw CRLF user log, Windows snapshots and preserved continuation bytes are retained exactly; authored source/text is checked separately.'),f,indent=2);f.write('\n')
assert all(c.values()),c
paths=base+[str(p.relative_to(R)) for p in sorted(H.rglob('*')) if p.is_file()]
assert not git('diff','--cached','--name-only'),'preexisting staged changes'
subprocess.run(['git','add','--',*paths],check=True)
staged=git('diff','--cached','--name-only').splitlines();assert set(staged)==set(paths)
blobs={p:hashlib.sha256(subprocess.check_output(['git','show',':'+p])).hexdigest() for p in staged}
assert all(sh(R/p)==v for p,v in blobs.items())
manifest=str((H/'staged-files.json').relative_to(R));expected=sorted(staged+[manifest])
with (H/'staged-files.json').open('x') as f:json.dump(dict(sha256=blobs,complete_staged_names=expected,self_path=manifest,self_hash_excluded=True),f,indent=2);f.write('\n')
subprocess.run(['git','add','--',manifest],check=True)
assert sorted(git('diff','--cached','--name-only').splitlines())==expected
assert all(hashlib.sha256(subprocess.check_output(['git','show',':'+p])).hexdigest()==v for p,v in blobs.items())
assert subprocess.check_output(['git','show',':'+manifest])==(R/manifest).read_bytes()
print(json.dumps(dict(checks=c,EXACT_COMPLETE_names=len(expected),listed_blobs=len(blobs))))
