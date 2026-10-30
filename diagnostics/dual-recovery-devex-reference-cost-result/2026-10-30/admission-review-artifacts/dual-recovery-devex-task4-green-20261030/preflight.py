import sys,json,pathlib,subprocess,hashlib
W=pathlib.Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';T=pathlib.Path('/tmp/dual-recovery-devex-task4-green-20261030')
sys.path.insert(0,str(P));import common as C
expected='31415cc1eccc2d6c332ff14863e509f0d805c909'
post=C.read(W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30/postcheck.json')
h=C.host(post['checked_groups'])
C.require(h['refs']['HEAD']==expected,'unexpected diagnostic HEAD')
C.require(C.git('branch','--show-current')=='codex/native-quality-finite','wrong branch')
C.require(not C.git('diff','--cached','--name-only'),'nonempty index')
C.require(not C.git('diff','HEAD','--name-only'),'tracked worktree change')
refs=dict((r.split()[1],r.split()[0]) for r in C.git('ls-remote','origin','refs/heads/master','refs/heads/codex/native-quality-finite').splitlines())
C.require(refs['refs/heads/codex/native-quality-finite']==expected and refs['refs/heads/master']==C.MASTER,'remote refs')
used,previous=C.previous('green');C.require(used==33.35953255696222,'prior inclusive time mismatch')
C.require(not (C.RUN/'green').exists(),'GREEN already sealed or attempted')
C.require(not any((C.RUN/q).exists() for q in ('reference-cost','candidate-cost')),'later phases present')
old=[]
for pid,ticks in [(406098,32498885),(406119,32498907),(406120,32498924)]:
 try:a=C.identity(pid)
 except (FileNotFoundError,ProcessLookupError):a=None
 C.require(a is None or a['boot_id']!='781795f4-f7af-4c3b-9ce9-45c7cae76ecb' or a['start_ticks']!=ticks,'old identity still present')
 old.append(dict(pid=pid,start_ticks=ticks,original_boot='781795f4-f7af-4c3b-9ce9-45c7cae76ecb',current=a))
r=dict(accepted=True,host=h,remote_refs=refs,previous=previous,used_seconds=used,remaining_seconds=1800-used,old_identities=old,scope='fresh full prior730 groups AND sessions/noJulia, refs/resources; no launch',bindings={str(W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30/postcheck.json'):C.sha(W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30/postcheck.json')})
C.fresh(T/'preflight.json',r)
print(json.dumps(dict(accepted=True,groups=len(h['checked_groups']),boot=h['boot_id'],memory=h['memory'],refs=h['refs'],remaining=1800-used)))
