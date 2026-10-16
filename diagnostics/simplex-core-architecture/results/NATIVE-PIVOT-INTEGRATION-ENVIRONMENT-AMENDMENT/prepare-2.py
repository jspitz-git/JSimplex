"""One-shot offline routing preparation. No stage, seal or Julia."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;R=E.parents[3];P=E.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
 with p.open('x') as f:f.write(s)
copy_names=['guard.py','supervisor.py','seal.py','launch.py','audit.py','oracle.py','loaded-paths.json','controls-baseline.json']
for n in copy_names:
 with (E/n).open('xb') as f:f.write((P/n).read_bytes())
old=(P/'common.py').read_text();new=old.replace('PREV=Q',"PREV=Q.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'").replace('86e0397c882ff6628193cfa4c1d24a7c71ed7c3e','5fd40966abc84be5bb88a789853273b41f754717')
write(E/'common.py',new)
old=(P/'control.py').read_text();new=old.replace("PREPARATION=D.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION'","DRIVER=D.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'\nPREPARATION=DRIVER")
new=new.replace("R/'.superpowers/native-pivot-integration/integration'","R/'.superpowers/native-pivot-integration-env1/integration'").replace("str(D/'driver.jl')","str(DRIVER/'driver.jl')")
a=new.index('def predecessor(phase):');z=new.index('def full_host(',a)
replacement="""def predecessor(phase):
 config(phase);P=DRIVER;mp=P/'preparation-pins.json';m=rd(mp);rp=P/'review-final.json';v=rd(rp)
 verify_review(v,mp,list(m['sha256'])+[str(mp)],'offline preparation')
 require(bindings(m),'Driver preparation input drift')
 require(all(sha(path(n))==h for n,h in v['evidence_sha256'].items()),'Supplemental driver review drift')
 files={mp,rp}|{path(n) for n in m['sha256']}|{path(n) for n in v['evidence_sha256']}
 preserved={str(STATUS):D/'STATUS.md.before-environment',str(ROAD):D/'roadmap.md.before-environment'}
 for rec in [P/'closure.json',P/'publication.json']:
  z=rd(rec);require(z['all_passed'] is True,'Driver publication not PASS');files.add(rec)
  for n,h in z['sha256'].items():
   p=path(n);p=preserved.get(str(p),p);require(sha(p)==h,'Driver closure drift '+n);files.add(p)
 h=rd(P/'closure-host.json');require(not h['matches'] and len(h['groups'])==216,'Previous driver closure')
 files.add(P/'closure-host.json')
 return sorted(files),h['groups']
"""
new=new[:a]+replacement+new[z:];write(E/'control.py',new)
save(E/'source-map.json',dict(byte_identical={n:dict(source=str(P/n),sha256=sha(E/n)) for n in copy_names},driver=str(P/'driver.jl'),driver_sha256=sha(P/'driver.jl'),observer_and_tests='Original accepted files in DRIVER, unchanged; no new Julia text',common_changes=['PREV targets immutable original overlay','HEAD advances to accepted driver publication'],control_changes=['DRIVER/PREPARATION target accepted driver preparation','new stage/output routing','original driver path','predecessor binds accepted1503 manifest/review and closure/publication with new before-environment mapping'],old_common_sha256=sha(P/'common.py'),old_control_sha256=sha(P/'control.py')))
# Correct the unexecuted command-vector selector in a new test source; original RED/source preserved.
t=(E/'offline-tests.py').read_text();require="c.guard_command(cfg,Path('/tmp/pins'),10)[5]=='52'"
if t.count(require)!=1:raise RuntimeError('test selector')
write(E/'offline-tests-final.py',t.replace(require,"c.guard_command(cfg,Path('/tmp/pins'),10)[6:8]==['--seconds','52']"))
save(E/'test-selector-note.json',dict(scope='Author source inspection before GREEN; no runtime failure',old='guard_command index5 is output path',new='indices6:8 are --seconds,52',original='offline-tests.py and offline-RED.json preserved; new offline-tests-final.py only selector correction'))
print(dict(byte_identical=len(copy_names),new_routing=True,no_stage=True))
