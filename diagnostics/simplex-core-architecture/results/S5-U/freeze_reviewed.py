"""Exclusive corrected requirement preparation; no old script execution."""
from common_reviewed import *
assert not absent()['matches']
assert 'REJECTED' in (H/'admission-review.md').read_text()
old=read(H/'required-paths.json')['sha256'];assert all(sha(k)==v for k,v in old.items())
assert sha(R/REL)==sha(M/REL)==OLD
files=set(old)|set(map(str,essentials()))|{str(p) for p in H.rglob('*') if p.is_file()}
dump(H/'required-reviewed-paths.json',dict(sha256={p:sha(p) for p in sorted(files)},planned_only_substitutions={str(R/REL):EXPECTED,str(M/REL):EXPECTED},scope='Only ROOT target test for GREEN, both target test paths for master. Original rejected evidence preserved.'))
print('Reviewed required paths',len(files))
