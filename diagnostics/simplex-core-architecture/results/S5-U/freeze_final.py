"""Exclusive final requirement preparation after preserved second rejection."""
from common_final import *
assert not absent()['matches'];assert 'REJECTED' in (H/'admission-accepted-review.md').read_text()
old=read(H/'required-reviewed-paths.json')['sha256'];assert all(sha(k)==v for k,v in old.items());assert sha(R/REL)==sha(M/REL)==OLD
files=set(old)|set(map(str,essentials()))|{str(p) for p in H.rglob('*') if p.is_file()}
dump(H/'required-final-paths.json',dict(sha256={p:sha(p) for p in sorted(files)},planned_only_substitutions={str(R/REL):EXPECTED,str(M/REL):EXPECTED},scope='ROOT target only for GREEN, both targets for master; master additionally requires all23 immutable original/portable GREEN evidence paths.'))
print('Final required paths',len(files))
