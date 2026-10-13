"""Exclusive actual read-time mandatory inventory; no Julia invocation."""
from common import *
assert current_refs()==INITIAL_REFS and sha(R/REL)==OLD and sha(M/REL)==OLD
host=absent();assert not host['matches'];host.update(refs=current_refs(),user_hashes=read(H.parent/'S5-Y/host.json')['user_hashes'])
assert all(sha(k)==v for k,v in host['user_hashes'].items());dump(H/'host-before.json',host)
# Required paths are explicit union of already enumerated lineage and newly authored files.
# Historical manifests remain unchanged. Their own path bytes are freshly bound here.
paths=set(read(H.parent/'S5-Y/required-paths.json')['sha256'])
paths|=set(read(H.parent/'S5-Z/pins-reviewed.json')['sha256'])
paths|={str(p) for name in ('S5-Y','S5-Z') for p in (H.parent/name).rglob('*') if p.is_file()}
paths|={str(p) for p in H.iterdir() if p.is_file() and not p.name.endswith('.pending')}
paths|=set(map(str,essentials()))
for p in (R,M):
 paths|={str(p/n) for n in ('Project.toml','Manifest.toml','LocalPreferences.toml','.vscode/settings.json')}
assert all(Path(p).is_file() for p in paths)
dump(H/'required-paths.json',dict(sha256={p:sha(p) for p in sorted(paths)},scope='Concrete mandatory pre-edit inventory; only exact actual-test stage hash overrides are permitted.'))
print(len(paths),'required paths')
