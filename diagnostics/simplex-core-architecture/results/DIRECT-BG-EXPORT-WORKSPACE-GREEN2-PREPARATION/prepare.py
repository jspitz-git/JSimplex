"""New GREEN2 harness preparation only. Never executes Julia or old write scripts."""
from pathlib import Path
import sys,json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');E=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN')
sys.path.insert(0,str(O));import control as c
h=c.full_host(c.rd(O/'runs/green300/posthost.json')['groups']);h.update(memory=c.guard.memory(),status=c.git('status','--porcelain'),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
c.require(c.host_safe(h) and not c.guard.pressure(h['memory']) and not c.git('diff','--name-only','HEAD') and not c.git('diff','--cached','--name-only'),'Host/working tree')
c.preparation();c.validate_sources();c.require(c.bindings(c.rd(E/'closure.json')) and c.rd(E/'closure.json')['all_passed'],'Failed result closure')
c.save(D/'host.json',h)
C=R/'diagnostics/direct-bg-export-workspace/reproduce';F=R/'diagnostics/direct-bg-export-workspace-harness-fix/reproduce';F.mkdir(parents=True,exist_ok=False)
a='sum(n for (T,n) in a.requests if T===Float64)';b='sum((n for (T,n) in a.requests if T===Float64);init=0)'
s=(C/'import-tests.jl').read_text();c.require(s.count(a)==1,'Unique reducer');(F/'import-tests.jl').open('x').write(s.replace(a,b))
for n in ('guard.py','supervisor.py','launch.py','seal.py','audit.py','oracle.py','recorder.jl','red.jl','baseline.json','stages.json','environment.json','runtime-inputs-complete.json','loaded-paths.json','expected-tests.json','expected-tests.toml'):
 (D/n).open('xb').write((O/n).read_bytes())
s=(O/'driver.jl').read_text();s=s.replace(str(C/'import-tests.jl'),str(F/'import-tests.jl')).replace('"green300"','"green2-300"').replace('"green600"','"green2-600"');(D/'driver.jl').open('x').write(s)
c.save(D/'authorization.json',dict(user_request='Prosím dokonči testování a měření kandidáta autonomně.',scope='Separate minimal diagnostic test amendment and unique GREEN2 correctness attempt before any separately prepared/admitted cost run',no_old_retry=True,no_candidate_change=True,seconds=300))
c.save(D/'inverse.json',dict(original=str(C/'import-tests.jl'),amended=str(F/'import-tests.jl'),before=a,after=b,original_sha256=c.sha(C/'import-tests.jl'),amended_sha256=c.sha(F/'import-tests.jl'),copied_controls=[n for n in ('guard.py','supervisor.py','launch.py','seal.py','audit.py','oracle.py','recorder.jl','red.jl')],driver_replacements=[[str(C/'import-tests.jl'),str(F/'import-tests.jl')],['"green300"','"green2-300"'],['"green600"','"green2-600"']],expected_assertions=7935,original_failed_run=str(O/'runs/green300')))
print('Prepared distinct test-only amendment and controls; not sealed or launched')
