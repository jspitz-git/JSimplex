from pathlib import Path
import json,hashlib,time,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def put(p,o):
 with Path(p).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
old=json.loads((D/'admission-pins-reviewed.json').read_text())['inventory']
if not all(sha(p)==v['sha256'] for p,v in old.items()):raise SystemExit('prepared input changed')
paths={Path(p) for p in old}|{p for p in D.rglob('*') if p.is_file()}|{p for p in E.rglob('*') if p.is_file()}|{R/'docs/superpowers/plans/2026-10-13-price-audit-values-qualification.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-ADMISSION-PREPARATION-REVIEW.md'}
inv={str(p):{'sha256':sha(p),'resolved':str(p.resolve(strict=True))} for p in sorted(paths)}
put(D/'launch-pins.json',{'files':sorted(inv),'trees':[],'inputs':[],'inventory':inv,'created':time.time(),'scope':'S2-E single reviewed numerical attempt, exact frozen S2-D command paths'})
W=Path('/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh');out=R/'.superpowers/simplex-core-architecture/S2-D/qualification-1'
command=['/bin/bash',str(W),'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(D/'overlay'),str(D/'driver-reviewed.jl'),str(out/'raw')]
bundle={str(p):sha(p) for p in paths};bundle[str(D/'launch-pins.json')]=sha(D/'launch-pins.json')
a={'accepted':True,'numerical_allowance':True,'unresolved_findings':[],'attempts':1,'stage':'S2-D-qualification-1','logical_stage':'S2-E','command':command,'output':str(out),'refs':{str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in [R,Path('/home/jspitz/JSimplex.jl')]},'pins_sha256':sha(D/'launch-pins.json'),'sha256':bundle,'human_authorization':str(E/'human-authorization.md'),'limits':{'seconds':180,'julia_threads':1,'blas_threads':1,'heap_gib':2,'vm_gib':8,'available_ram_floor_gib':6,'swap_max_gib':1},'work':{'regression_pass':655,'child_pass':[90,40,416,34,16,31,28],'fixtures':8,'cost_setups':8,'warm_pairs_per_fixture':4,'measured_pairs_per_fixture':8,'windows':192,'whole_audits':3072,'audits_per_side':1536},'retry':False,'promotion':False}
put(E/'allowance-proposal.json',a)
put(E/'admission-preparation.json',{'all_passed':True,'launch_inventory_count':len(inv),'contains_original801':set(old).issubset(inv),'new_numerical_calls':0,'sha256':{str(p):sha(p) for p in [E/'prepare-admission.py',E/'seal.py',E/'human-authorization.md',E/'entry.json',D/'launch-pins.json',E/'allowance-proposal.json']}})
print('Launch inventory:',len(inv),'proposal only; no allowance/launch yet')
