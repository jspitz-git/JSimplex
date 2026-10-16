"""OFFLINE ordinary overlay from exact master commit, never diagnostic src.

No package resolution, Julia loading, test invocation or environment copying.
The future launch admission supplies and binds the exact environment separately.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess
MASTER='26e2291745999f485a74f643298ca997d65c7205'
ANCHOR=b'include("huangfu_hall_factorization.jl")\n'
ADDITION=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
def digest(b):return hashlib.sha256(b).hexdigest()
def require(ok,message):
    if not ok:raise RuntimeError(message)
def prepare(destination,mode):
    require(mode in ('red','candidate'),'Invalid mode')
    repo=Path(__file__).resolve().parents[3]; output=Path(destination).resolve()
    require(not output.exists(),'Refusing existing destination')
    def git(*args):return subprocess.check_output(['git',*args],cwd=repo)
    require(git('rev-parse',MASTER+'^{commit}').decode().strip()==MASTER,'Master identity')
    names=git('ls-tree','-r','--name-only',MASTER,'--','src','Project.toml').decode().splitlines()
    require('src/JSimplex.jl' in names and 'Project.toml' in names,'Incomplete source tree')
    content={name:git('show',MASTER+':'+name) for name in names}
    require(all(name=='Project.toml' or name.startswith('src/') for name in names),'Unexpected source name')
    root=content['src/JSimplex.jl'];require(root.count(ANCHOR)==1 and ADDITION not in root,'Root inverse')
    implementation=Path(__file__).resolve().parent if mode=='candidate' else repo/'diagnostics/direct-lu-markowitz/reproduce'
    extra={name:(implementation/name).read_bytes() for name in ('factor-export.jl','direct-factor.jl')}
    # Complete validation/reads precede destination creation. No old tree is modified.
    output.mkdir(parents=True,exist_ok=False)
    for name,data in content.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    (output/'src/JSimplex.jl').write_bytes(root.replace(ANCHOR,ANCHOR+ADDITION))
    for name,data in extra.items():(output/'src'/name).write_bytes(data)
    manifest=dict(scope='UNEXECUTED; no environment or launch admission',master=MASTER,mode=mode,
        source_sha256={n:digest(b) for n,b in content.items()},
        implementation_sha256={str((implementation/n).relative_to(repo)):digest(b) for n,b in extra.items()},
        overlay_sha256={str(p.relative_to(output)):digest(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file()},
        changed_original_files=['src/JSimplex.jl'],added_source_files=['src/factor-export.jl','src/direct-factor.jl'],
        julia_executed=False,environment_copied=False)
    with (output/'overlay.json').open('x') as f:json.dump(manifest,f,indent=2);f.write('\n')
    return manifest
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('destination',type=Path);ap.add_argument('--mode',required=True,choices=['red','candidate'])
    args=ap.parse_args();m=prepare(args.destination,args.mode)
    print(json.dumps(dict(source_files=len(m['source_sha256']),mode=m['mode'],julia_executed=False)))
