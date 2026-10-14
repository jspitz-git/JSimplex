from control import *
P=D.with_name('PRESOLVE-EXACT-CACHE');B=R/'diagnostics/simplex-core-architecture';names=rd(D/'publication-names.json');selfname=str((D/'publication.json').relative_to(R));entry=rd(P/'host.json');closure=rd(D/'closure.json')
req(closure['all_passed'] is True and all(sha(p)==v for p,v in closure['sha256'].items()),'closure changed')
req(git('rev-parse','HEAD')==entry['refs']['head'] and git('rev-parse','master')==entry['refs']['master'],'refs')
expected={str(p.relative_to(R)) for root in (P,D) for p in root.rglob('*') if p.is_file()}|{'diagnostics/simplex-core-architecture/PRESOLVE-EXACT-CONVERSION-CACHE.md','diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',selfname}
req(set(names)==expected and len(names)==len(set(names)),'exact names completeness')
req(not git('diff','--cached','--name-only'),'stage not empty')
others=[n for n in names if n!=selfname];subprocess.run(['git','add','--',*others],cwd=R,check=True)
req(set(git('diff','--cached','--name-only').splitlines())==set(others),'stage names')
blobs={n:git('rev-parse',':'+n) for n in others};req(all(blobs[n]==git('hash-object','--',n) for n in others),'stage blobs')
# Whitespace-check authored docs/code, excluding literal frozen copies and raw.
authored=[n for n in others if n.endswith('.md') or Path(n).name=='driver.jl' or (n.endswith('.py') and Path(n).name not in ('guard.py','supervisor.py','entry.py'))]
r=subprocess.run(['git','diff','--cached','--check','--',*authored],cwd=R,capture_output=True,text=True);req(r.returncode==0 and not r.stdout and not r.stderr,'authored whitespace: '+r.stdout+r.stderr)
save(D/'publication.json',dict(all_passed=True,qualification_accepted=False,exact_names=names,staged_blobs_excluding_self=blobs,sha256={str(R/n):sha(R/n) for n in others},self_binding='publication.json cannot embed its own hash; final exact staged blob verification includes it before commit',checks=dict(closure=True,exact_names=True,complete=True,staged_blobs=True,authored_whitespace=True,source_unchanged=True)))
subprocess.run(['git','add','--',selfname],cwd=R,check=True)
req(set(git('diff','--cached','--name-only').splitlines())==set(names),'final exact staged names')
req(all(git('rev-parse',':'+n)==git('hash-object','--',n) for n in names),'final all staged blobs')
print('Publication PASS; EXACT',len(names),'staged names and blobs, including publication:',git('rev-parse',':'+selfname))
