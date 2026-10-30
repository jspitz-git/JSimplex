import sys,json,pathlib,shutil
W=pathlib.Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';T=pathlib.Path('/tmp/dual-recovery-devex-task4-green-20261030');sys.path.insert(0,str(P));import common as C
R=C.RUN/'green';seal=C.read(R/'seal.json');adpath=pathlib.Path('/tmp/devex-task4-green-admission.json');ad=C.read(adpath)
C.require(ad['accepted'] is True and ad['scope']=='numerical_admission' and ad['phase']=='green','not admitted')
C.require(ad['head']==seal['head']==C.git('rev-parse','HEAD') and ad['command']==seal['command']==C.command('green'),'head/command')
C.require(ad['seal_sha256']==C.sha(R/'seal.json') and ad['pins_sha256']==C.sha(R/'pins.json')==seal['pins_sha256'],'seal/pins')
C.require(C.sha(ad['review_report'])==ad['review_report_sha256'],'report sha')
C.require(all(ad['checks'].values()),'review check not accepted')
C.require(all(C.sha(n)==v for n,v in ad['bindings'].items()),'review binding mismatch')
C.require(not (R/'attempt.json').exists(),'attempt consumed')
for source,name in [(adpath,'numerical-admission.json'),(pathlib.Path(ad['review_report']),'ADMISSION-REVIEW.md')]:
 dest=R/name
 with dest.open('xb') as f:f.write(source.read_bytes())
 C.require(C.sha(source)==C.sha(dest),'admission copy')
h=C.host(C.read(T/'preflight.json')['host']['checked_groups']);C.require(h['refs']['HEAD']==seal['head'],'fresh head')
C.fresh(T/'prelaunch-full-host.json',h)
print(json.dumps(dict(accepted=True,checks=len(ad['checks']),bindings=len(ad['bindings']),admission_sha256=C.sha(adpath),full_groups=len(h['checked_groups']),memory=h['memory'],boot=h['boot_id'])))
