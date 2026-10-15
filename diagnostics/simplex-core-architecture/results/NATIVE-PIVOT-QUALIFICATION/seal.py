"""UNEXECUTED: build one fresh stage and seal for independent exact-stage review.
No Julia, output reservation or admission is created by this program.
"""
from control import *
import guard

def main(phase):
 cfg=config(phase);validate_environment()
 pins=D/'preparation-pins.json';z=rd(pins)
 verify_review(rd(D/'review.json'),pins,list(z['sha256'])+[str(pins)],'offline preparation')
 require(bindings(z),'Preparation changed')
 extra,groups=predecessor(phase);h=full_host(groups)
 require(not h['matches'] and h['master']==MASTER and h['boot_id']==rd(D/'host.json')['boot_id'],'Fresh refs/processes')
 require(subprocess.run(['git','merge-base','--is-ancestor',HEAD,'HEAD'],cwd=R).returncode==0,'Unrelated HEAD')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes')
 run=Path(cfg['run']);run.mkdir(parents=True,exist_ok=False)
 save(run/'host.json',h);save(run/'config.json',cfg)
 manifest=rd(PREV/'overlay-manifest.json')[cfg['arm']];target=Path(cfg['stage'])
 require(not target.exists() and not target.is_symlink(),'Existing stage')
 for e in manifest:
  d=Path(e['destination']);require(not d.is_absolute() and '..' not in d.parts and sha(e['source'])==e['sha256'],'Bad source/destination')
 target.mkdir(parents=True,exist_ok=False)
 for e in manifest:
  f=target/e['destination'];f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as w:w.write(Path(e['source']).read_bytes())
 staged=validate_stage(cfg)
 files=sorted(set(z['sha256'])|{str(pins),str(D/'review.json'),str(run/'host.json'),str(run/'config.json'),str(STATUS),str(ROAD)}|{str(p) for p in staged+extra})
 sealed=dict(phase=phase,head=h['head'],master=h['master'],boot_id=h['boot_id'],groups=h['groups'],files=files,trees=[str(target)],inventory=guard.inventory(files,[str(target)]),inputs=[],config=cfg)
 save(run/'sealed.json',sealed)
 print('SEALED, NOT LAUNCHED. Fresh independent exact-stage admission.json is required.')
if __name__=='__main__':main(sys.argv[1])
