from pathlib import Path
import json,hashlib,shutil,sys,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';F=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30';D=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30';T=Path('/tmp/dual-recovery-devex-green-fixtures-20261030')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
need(not D.exists(),'new directory required')
need(git('rev-parse','HEAD')=='a2f2415fcc6c9a018ae8209e28f517da1b23b688','HEAD changed')
frozen={}
for origin in (P,F):
 pub=json.loads((origin/'publication.json').read_text())
 for rel in pub['expected_names']:
  f=W/rel;frozen[str(f)]=sha(f)
need(len(frozen)==255,'unexpected frozen publication coverage')
D.mkdir(parents=True);root=D/'prepared';copies={}
def copy(src,dest):
 need(src.is_file() and not src.is_symlink(),'regular original required '+str(src))
 dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(src.read_bytes())
 need(sha(src)==sha(dest),'copy mismatch')
 copies[str(dest)]=dict(source=str(src),sha256=sha(src),bytes=src.stat().st_size)
for name in ('green.jl','endpoint.jl'):copy(P/name,root/name)
for p in sorted((P/'tests').rglob('*')):
 if p.is_file():copy(p,root/p.relative_to(P))
for p in sorted((P/'overlays/candidate').rglob('*')):
 if p.is_file():copy(p,root/p.relative_to(P))
target=root/'tests/fixtures/solver/netlib/adlittle.mps'
need(not target.exists(),'adlittle should be the only added file')
copy(W/'test/fixtures/solver/netlib/adlittle.mps',target)
for name in ('fixture_check.py','fixture_tests.py','fixture-manifest.json','offline-red.log','host.json','preflight.py'):
 copy(T/name,D/name)
copy(Path(__file__),D/'prepare.py')
need(all(sha(n)==h for n,h in frozen.items()),'old publication changed')
need(not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'),'tracked/index changed')
manifest=json.loads((D/'fixture-manifest.json').read_text())
need(len(list(root.rglob('*.mps')))==2,'unexpected fixture count')
need(len(list((root/'overlays/candidate/src').rglob('*.jl')))==71,'source count')
record=dict(accepted=True,scope='OFFLINE isolated fixture preparation only, no Julia or numerical admission',head=git('rev-parse','HEAD'),master=git('rev-parse','master'),copies=copies,frozen_previous_publications=frozen,prepared_file_count=len([p for p in root.rglob('*') if p.is_file()]),added_fixture=str(target),added_fixture_sha256=sha(target),original_programs_unchanged=manifest['programs'],runtime_unexecuted=True,prior_failed_green_accepted=False,consumed_seconds=527.9604928489425,unspent_shared_seconds=1272.0395071510575)
with (D/'staging.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,prepared_files=record['prepared_file_count'],copies=len(copies),frozen_previous_files=len(frozen),added_fixture_bytes=target.stat().st_size)))
