"""Exclusive admission file-list preparation after offline tests; no Julia."""
from common import *
X=H.parent/'S5-X';D=H.parent.parent
paths={Path(k) for k in read(X/'evidence.json')['sha256']}
paths|={p for p in X.iterdir() if p.is_file()}
old=read(H.parent/'S5-U/master/pins.json')['inventory']
paths|={Path(k) for k in old if k.startswith('/home/jspitz/.julia/') or '/packages/' in k or '/artifacts/' in k}
paths|={H/'link_tests.py',H/'link-tests.json',Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/doc/julia/html/en/manual/command-line-interface.html'),Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/loading.jl')}
paths|=set(essentials())|{H/'synthetic-guard-refusal.log',H/'synthetic-guard-invocation.json',D/'S5-CRASH-FALLBACK-OBSERVER-PREPARATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-PREPARATION-REVIEW.md',R/'AGENTS.md',R/'Project.toml',M/'Project.toml',D/'STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
assert sha(C)==EXPECTED and refs()==REFS and not absent()['matches']
x=dict(sha256={str(p):sha(p) for p in sorted(paths)},scope='Required paths plus complete src/test trees; fresh read-time hashes, not cache-confinement proof.')
dump(H/'required-paths.json',x);print('Required fixed files',len(paths))
