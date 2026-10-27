from pathlib import Path
import sys,json,shutil,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');sys.path.insert(0,str(D));import common as c
c.unchanged();oldpath=c.R/'diagnostics/dual-finite-validity/terminal-primal-repair/green-2/output/process.json';old=json.loads(oldpath.read_text())['child'];pid=77336;p=Path('/proc')/str(pid);st=(p/'stat').read_text().rsplit(')',1)[1].split();a=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
identity=dict(pid=pid,pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=a,boot_id=boot)
c.need(identity['pgid']==identity['sid']==pid and a==['/usr/libexec/wsl-pro-service'],'exact unrelated service');c.need(boot!=old['boot_id'] and identity['start_ticks']!=old['start_ticks'],'different boot and creation')
c.put('host-identity-allowance.json',dict(identities=[identity],historical_child=old,historical_record=str(oldpath),historical_sha256=c.sha(oldpath),reason='An unrelated system service reuses an old numerical group number across different boots; preserve exact boot/start/command identity, never exempt Julia or another process.'))
text=(D/'common.py').read_text();oldline="   need(pgid not in groups and sid not in groups,'historical group/session');need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+a[:1]),'Julia active')"
newlines="""   if pgid in groups or sid in groups:
    allowance=Path('"""+str(D/'host-identity-allowance.json')+"""')
    need(sha(allowance)=='"""+c.sha(D/'host-identity-allowance.json')+"""','fixed unrelated identity evidence')
    permitted=json.loads(allowance.read_text())['identities']
    actual=dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    need(actual in permitted,'historical group/session or changed unrelated process')
   need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+a[:1]),'Julia active')"""
c.need(text.count(oldline)==1,'one identity gate');new=text.replace(oldline,newlines);c.need(new.replace(newlines,oldline)==text,'host exact inverse');(D/'common_next.py').write_text(new)
for name in ['build-local-stage.py','prepare-local-arm.py']:shutil.copyfile('/tmp/'+name,D/('preflight-refused-'+name))
c.need(not (D/'RED').exists(),'no RED stage before preflight');shutil.move(str(D/'RED-run'),str(D/'RED-run.preflight-refused'))
c.put('preflight-refusal.json',dict(numerical_runs=0,stage_created=False,reason='strict historical numeric group77336 present as unrelated different-boot WSLservice; first build aborted beforecopy; dependent prepare mistakenly attempted afterwards and left only partial config, preserved.',original_scripts=[str(D/'preflight-refused-build-local-stage.py'),str(D/'preflight-refused-prepare-local-arm.py')],partial_directory=str(D/'RED-run.preflight-refused')))
for name in ['build-local-stage.py','prepare-local-arm.py']:
 path=Path('/tmp')/name;s=path.read_text().replace('import common as c','import common_next as c') if name=='build-local-stage.py' else path.read_text().replace("(D/'common.py').read_text()","(D/'common_next.py').read_text()")
 if name=='prepare-local-arm.py':s=s.replace("'changes.json','baseline-tree.json'","'changes.json','host-identity-allowance.json','common_next.py','baseline-tree.json'")
 path.write_text(s)
(D/'HOST-IDENTITY.md').write_text('''# Identity-safe historical group preflight

Two offline preparations were refused before any Julia or RED stage. The second was mistakenly dispatched after the first failure and left a partial directory; original scripts/config are preserved. Numeric PGID/SID77336 now belongs to /usr/libexec/wsl-pro-service. The archived numerical child77336 has boot4fde10f2/start3810211; current service has a different boot and start6151792. A numeric ID alone cannot identify an old run. No system service is killed.

New common_next.py preserves the old helper and every other gate. All historical group/session numbers are still examined. The sole allowed collision is the exact pinned (currentboot,pid,pgid,sid,start_ticks,command) service tuple; any different occupant or any Julia process is refused. Historical numerical identities remain absent. Fresh admission must verify this explicit source-bound refinement, current refs/source/index and memory before each launch. Do not claim literal absence of every numeric ID:77336 is present as the proven unrelated different-boot process. No numerical checks, memory limits or candidate bytes changed.
''')
shutil.copyfile(__file__,D/'prepare-host-identity.py');print('offline identity refinement prepared; noJulia; both refused drafts preserved')
