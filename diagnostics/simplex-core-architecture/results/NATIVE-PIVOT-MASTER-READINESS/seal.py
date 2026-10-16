"""UNEXECUTED. Refuses before actual master FF; creates no numerical reservation."""
from control import *
def main(phase):
 cfg=config(phase);validate_environment();files=preparation();prod=validate_production();extra,groups=predecessor(phase);h=full_host(groups)
 require(not h['matches'] and not guard.pressure(guard.memory()),'Host/process/resource refusal')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Diagnostic tracked changes')
 run=Path(cfg['run']);run.mkdir(parents=True,exist_ok=False)
 save(run/'host.json',h);save(run/'config.json',cfg)
 files=sorted(set(files+list(rd(D/'runtime-inputs.json')['inventory'])+[str(p) for p in prod]+extra+[str(run/'host.json'),str(run/'config.json')]))
 # All production tracked bytes individually pinned; no .git tree/cache snapshot.
 trees=[str(Path(cfg['stage'])/'src'),str(Path(cfg['stage'])/'test')]
 save(run/'sealed.json',dict(phase=phase,head=h['head'],master=h['master'],boot_id=h['boot_id'],groups=h['groups'],config=cfg,files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=[]))
 print('SEALED actual master; fresh independent exact-stage admission required; NOT launched')
if __name__=='__main__':main(sys.argv[1])
