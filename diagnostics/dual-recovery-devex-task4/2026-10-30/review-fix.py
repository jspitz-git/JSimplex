from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-task4/2026-10-30')
def fresh(n,b):
 with (D/n).open('xb') as f:f.write(b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for a,b in [('/tmp/devex-task4-preparation-review.md','REVIEW-INITIAL.md'),('/tmp/devex-task4-preparation-review.json','review-initial.json'),('/tmp/devex-task4-independent-sourcechecks.json','reviewer-initial-sourcechecks.json')]:fresh(b,Path(a).read_bytes())
fresh('ADMISSION-PREPARATION.before-review.md',(D/'ADMISSION-PREPARATION.md').read_bytes())
# Prospective Python regression checks are saved before their gate helper.
tests='''"""New offline binding regressions only; no main/guard/Julia invocation."""
import unittest,tempfile,sys,importlib.util,importlib.machinery
from pathlib import Path
import common as C
import binding_checks as B
D=Path(__file__).resolve().parent
class BindingTests(unittest.TestCase):
 def test_interpreter_valid_and_wrong_path(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'python';p.write_bytes(b'bound interpreter');other=Path(tmp)/'other';other.write_bytes(p.read_bytes())
   seal={'guard_python':str(p)};pins={'inventory':{str(p):{'resolved':str(p.resolve()),'sha256':C.sha(p)}}}
   B.interpreter(seal,pins,str(p))
   with self.assertRaises(ValueError):B.interpreter(seal,pins,str(other))
   p.write_bytes(b'changed')
   with self.assertRaises(ValueError):B.interpreter(seal,pins,str(p))
   with self.assertRaises(ValueError):B.interpreter({'guard_python':True},pins,str(p))
 def test_changed_interpreter_resolution(self):
  with tempfile.TemporaryDirectory() as tmp:
   a=Path(tmp)/'a';b=Path(tmp)/'b';p=Path(tmp)/'python'
   a.write_bytes(b'same');b.write_bytes(b'same');p.symlink_to(a)
   seal={'guard_python':str(p)};pins={'inventory':{str(p):{'resolved':str(a.resolve()),'sha256':C.sha(p)}}}
   B.interpreter(seal,pins,str(p));p.unlink();p.symlink_to(b)
   with self.assertRaises(ValueError):B.interpreter(seal,pins,str(p))
 def test_head_at_every_boundary(self):
  seal={'head':'a'*40};ad={'head':'a'*40};B.head(seal,ad,'a'*40)
  with self.assertRaises(ValueError):B.head(seal,ad,'b'*40)
  with self.assertRaises(ValueError):B.head(seal,{'head':'b'*40},'a'*40)
  with self.assertRaises(ValueError):B.head(seal,ad,True)
 def test_auditor_bound_before_shadow_directory(self):
  # Definitions-only import. This would fail for the original late import.
  spec=importlib.util.spec_from_file_location('task4_reviewed_launch_definitions',D/'launch-reviewed.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as tmp:
   shadow=Path(tmp)/'audit.py';shadow.write_text('raise RuntimeError("unexpected shadow execution")\\n')
   old=importlib.machinery.PathFinder.find_spec('audit',[tmp,str(D)])
   self.assertEqual(Path(old.origin),shadow)
   sys.path.insert(0,tmp)
   try:self.assertEqual(Path(module.audit.__file__).resolve(),(D/'audit_reviewed.py').resolve())
   finally:sys.path.pop(0)
  self.assertEqual(module.audit.__name__,'audit_reviewed')
if __name__=='__main__':unittest.main()
'''
fresh('binding_tests.py',tests.encode())
helper='''"""Cold admission checks; no reservation or launch side effects."""
from pathlib import Path
import common as C

def interpreter(seal,pins,current):
 C.require(type(current) is str and type(seal.get('guard_python')) is str,'interpreter type')
 absolute=str(Path(current).absolute())
 C.require(absolute==seal['guard_python'],'launch interpreter differs from phase seal')
 item=pins['inventory'].get(absolute)
 C.require(isinstance(item,dict) and str(Path(current).resolve(strict=True))==item.get('resolved') and C.sha(current)==item.get('sha256'),'unpinned or changed interpreter')

def head(seal,ad,current):
 C.require(type(current) is str and type(seal.get('head')) is str and type(ad.get('head')) is str and len(current)==40 and current==seal['head']==ad['head'],'admitted HEAD changed')
'''
fresh('binding_checks.py',helper.encode())
s=(D/'seal.py').read_text();s=s.replace("seal=dict(phase=phase,head=", "seal=dict(guard_python=str(Path(sys.executable).absolute()),phase=phase,head=")
fresh('seal-reviewed.py',s.encode())
s=(D/'launch.py').read_text();s=s.replace('import common as C','import common as C\nimport binding_checks as B\nimport audit_reviewed as audit')
s=s.replace("C.phase_ok(phase);out=C.RUN/phase;seal=C.read(out/'seal.json');ad=C.read(admission_path)","C.phase_ok(phase);out=C.RUN/phase;seal=C.read(out/'seal.json');ad=C.read(admission_path)\n pins=C.read(out/'pins.json');B.interpreter(seal,pins,sys.executable)\n C.require(Path(audit.__file__).resolve()==(C.D/'audit_reviewed.py').resolve(),'wrong auditor source')")
s=s.replace("h=C.host();C.fresh(out/'prelaunch-host.json',h)","h=C.host();C.fresh(out/'prelaunch-host.json',h);B.head(seal,ad,h['refs']['HEAD'])")
s=s.replace("pins=C.read(out/'pins.json');C.require(all(","C.require(all(")
s=s.replace("post=C.host(extra);C.fresh(out/'postflight.json',post)","post=C.host(extra);C.fresh(out/'postflight.json',post);B.head(seal,ad,post['refs']['HEAD'])")
s=s.replace(' import audit\n audit.audit_phase(phase)',' audit.audit_phase(phase)')
fresh('launch-reviewed.py',s.encode())
s=(D/'audit.py').read_text().replace('import common as C','import common as C\nimport binding_checks as B')
s=s.replace("pins=C.read(out/'pins.json');C.require", "pins=C.read(out/'pins.json');B.interpreter(seal,pins,sys.executable)\n for admitted_head in (C.read(out/'prelaunch-host.json')['refs']['HEAD'],C.read(out/'postflight.json')['refs']['HEAD'],C.git('rev-parse','HEAD')):B.head(seal,ad,admitted_head)\n C.require")
fresh('audit_reviewed.py',s.encode())
s=(D/'offline_tests.py').read_text().replace('import audit\n','import audit_reviewed as audit\n');fresh('offline_tests-reviewed.py',s.encode())
s=(D/'ADMISSION-PREPARATION.md').read_text();s=s.replace('seal.py','seal-reviewed.py').replace('launch.py','launch-reviewed.py').replace('audit.py','audit_reviewed.py')
s=s.replace('Time between independent admissions is excluded;', 'Offline sealing, initial preflight, independent admission review and final Python auditing are excluded from the guarded-time sum; time between independent admissions is excluded;')
s+='''\n## Preserved initial review and canonical corrections\n\nThe initial preparation was rejected for three binding gaps, preserved in REVIEW-INITIAL.md/review-initial.json. Canonical tools are now seal-reviewed.py, launch-reviewed.py, audit_reviewed.py and binding_checks.py; common.py, guards, Julia entries, overlays, test files, numerical expectations and contract.json remain byte-identical. Initial seal.py/launch.py/audit.py/offline_tests.py/source-check.json remain frozen and must never be launched as numerical continuations. The source-check/initial-review ADMISSION-PREPARATION.md pins map ONLY to ADMISSION-PREPARATION.before-review.md.\n\nF1: seal explicitly records its absolute guard_python; launcher and auditor require the actual interpreter's exact path, resolved target and SHA to match that inventory entry before launch/after exit. F2: launcher binds audit_reviewed at definition import before adding guard/ to sys.path and checks its exact resolved source file; it no longer performs a late unqualified import. F3: launcher enforces the admitted HEAD at its fresh prelaunch and saved postflight; auditor checks saved prelaunch/postflight plus current HEAD against both admission and seal. New offline binding_tests.py exercises matching and mismatched interpreter path/hash/resolution, matching/moved/malformed HEAD, and a definitions-only launcher import with an inert shadow audit.py. The launcher main, guard and Julia are not run by these tests. Existing auditor type/bit/pair tests run through a separate canonical offline test copy; no old script is rerun.\n\nThe added work is cold scalar/path/hash/ref verification and one already-required interpreter file digest, with no numerical hot-path or retained production-memory change. Fresh concrete numerical review still binds the entire publication expected_names (including all canonical executable dependencies) before any process is launched. This final preparation acceptance is not that numerical admission.\n'''
(D/'ADMISSION-PREPARATION.md').write_text(s)
checks={'Julia_drivers_unchanged':True,'single_seal_interpreter_field':s is not None,'intended_auditor_early_bound':'import audit_reviewed as audit' in (D/'launch-reviewed.py').read_text() and ' import audit\n' not in (D/'launch-reviewed.py').read_text(),'pre_and_post_head_checks':(D/'launch-reviewed.py').read_text().count('B.head(')==2,'audit_all_head_boundaries':'for admitted_head in (' in (D/'audit_reviewed.py').read_text()}
r=json.loads((D/'review-initial.json').read_text())
for n in ('red.jl','green.jl','cost.jl','endpoint.jl','common.py','seal.py','launch.py','audit.py','contract.json'):
 checks['original_frozen:'+n]=sha(D/n)==r['bindings'][str(D/n)]
checks['before_document_exact']=sha(D/'ADMISSION-PREPARATION.before-review.md')==r['bindings'][str(D/'ADMISSION-PREPARATION.md')]
fresh('review-fix.json',(json.dumps(dict(accepted=all(checks.values()),scope='source-only admission binding correction; no Julia',checks=checks,bindings={str(D/n):sha(D/n) for n in ('binding_checks.py','binding_tests.py','seal-reviewed.py','launch-reviewed.py','audit_reviewed.py','offline_tests-reviewed.py','ADMISSION-PREPARATION.md','ADMISSION-PREPARATION.before-review.md','source-check.json','REVIEW-INITIAL.md','review-initial.json')}),indent=2)+'\n').encode())
if not all(checks.values()):raise RuntimeError(checks)
print(json.dumps(dict(accepted=True,checks=len(checks))))
