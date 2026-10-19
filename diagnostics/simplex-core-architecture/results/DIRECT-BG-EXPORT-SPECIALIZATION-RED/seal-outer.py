"""UNEXECUTED. Only future explicit phase sealing; creates no numerical reservation."""
from pathlib import Path
import sys
Q=Path(__file__).resolve().parent
D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')
sys.path.insert(0,str(D))
from control import *
def main(phase):
 require(phase=='red300','Only authorized RED300');ready=rd(Q/'outer-ready.json');outer=ready['identity']
 require(guard.process_identity(outer['pid'])==outer and outer['pid']==outer['pgid']==outer['sid'],'Outer not alive/isolated')
 require(ready['script_sha256']==sha(Q/'outer.py') and ready['phase']==phase and ready['waiting_only'] is True,'Outer ready linkage')
 cfg=config(phase);validate_environment();files=preparation();validate_sources();extra,groups=predecessor(phase);h=full_host(groups)
 require(host_safe(h) and not guard.pressure(guard.memory()),'Host/process/resource refusal')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Diagnostic tracked changes')
 run=Path(cfg['run']);run.mkdir(parents=True,exist_ok=False)
 save(run/'host.json',h);save(run/'config.json',cfg)
 files=sorted(set(files+list(rd(D/'runtime-inputs-complete.json')['inventory'])+[str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in rd(D/'baseline.json')[label]]+[str(Path(cfg['stage'])/n) for n in rd(D/'stages.json')[cfg['mode']]['sha256']]+extra+[str(run/'host.json'),str(run/'config.json')]))
 extra_paths=rd(Q/'outer-required.json')['paths']
 require(all(Path(p).is_file() for p in extra_paths),'Outer inputs missing')
 files=sorted(set(files+extra_paths))
 # All production tracked bytes and immutable outer wrapper inputs pinned.
 trees=[cfg['stage'],str(C)]
 save(run/'sealed.json',dict(phase=phase,outer_identity=outer,head=h['head'],master=h['master'],boot_id=h['boot_id'],groups=h['groups'],config=cfg,files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=[]))
 print('SEALED exact BG specialization phase; fresh independent exact-stage admission required; NOT launched')
if __name__=='__main__':main(sys.argv[1])
