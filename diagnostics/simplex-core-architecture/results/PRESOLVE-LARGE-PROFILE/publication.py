from control import *
import subprocess
req(rd(D/'closure.json')['all_passed'],'closure')
req(all(sha(p)==v for p,v in rd(D/'closure.json')['sha256'].items()),'closure bindings')
req(git('diff','--cached','--name-only')=='','index not empty')
extra=[R/'diagnostics/simplex-core-architecture/PRESOLVE-LARGE-PASS-PROFILE.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
paths=sorted([p for p in D.rglob('*') if p.is_file()]+extra+[D/'publication.json',D/'publication-names.json'])
req(len(paths)==len(set(paths)),'duplicates');names=[str(p.relative_to(R)) for p in paths]
save(D/'publication-names.json',names)
existing=[p for p in paths if p!=D/'publication.json']
subprocess.run(['git','add','--',*[str(p.relative_to(R)) for p in existing]],cwd=R,check=True)
# Preserve exact source excerpts including EOF newlines; all other authored files clean.
rawnames=[str((D/n).relative_to(R)) for n in ('controller.jl','original-controller.jl')]
diff=subprocess.run(['git','diff','--cached','--check','--','.',*[f':(exclude){p}' for p in rawnames]],cwd=R,text=True,capture_output=True)
req(diff.returncode==0,'authored whitespace '+diff.stdout+diff.stderr)
rawdiff=subprocess.run(['git','diff','--cached','--check','--',*rawnames],cwd=R,text=True,capture_output=True)
req(rawdiff.returncode in (0,2) and all(not line or 'new blank line at EOF' in line or line.startswith('+') for line in rawdiff.stdout.splitlines()),'unexpected raw whitespace '+rawdiff.stdout)
blobs={str(p.relative_to(R)):git('rev-parse',':'+str(p.relative_to(R))) for p in existing}
req(all(blobs[str(p.relative_to(R))]==git('hash-object',str(p)) for p in existing),'staged bytes')
save(D/'publication.json',dict(all_passed=True,exact_names=names,staged_blobs_excluding_self=blobs,sha256={str(p):sha(p) for p in existing},raw_excerpt_diffcheck=dict(returncode=rawdiff.returncode,stdout=rawdiff.stdout,stderr=rawdiff.stderr),self_binding='Publication file blob verified separately in exact final index and committed tree.'))
subprocess.run(['git','add','--',str((D/'publication.json').relative_to(R))],cwd=R,check=True)
req(sorted(git('diff','--cached','--name-only').splitlines())==sorted(names),'exact complete index')
req(all(git('rev-parse',':'+str(p.relative_to(R)))==git('hash-object',str(p)) for p in paths),'final all index bytes')
print('Publication PASS; exact',len(paths),'names/blobs staged before commit')
