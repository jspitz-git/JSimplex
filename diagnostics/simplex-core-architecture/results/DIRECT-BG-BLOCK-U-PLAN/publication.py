from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent
def need(c,m):
    if not c:raise RuntimeError(m)
def git(*a):return subprocess.check_output(["git",*a],cwd=R).decode().strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((E/"closure.json").read_text());need(c["all_passed"],"Closure")
need(all(sha(R/k)==v for k,v in c["sha256"].items()),"Closure bindings")
need(not git("diff","--cached","--name-only"),"Index not empty")
paths=sorted([R/k for k in c["sha256"]]+[E/"closure.json",E/"publication.json"])
actual=set(p for p in E.iterdir() if p.is_file() and p.name!="host.json")|{R/"docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md",R/"docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md",E/"publication.json"}
need(set(paths)==actual,"Unexpected new file")
names=[str(p.relative_to(R)) for p in paths]
need(subprocess.run(["git","diff","--quiet","HEAD"],cwd=R).returncode==0,"Tracked content drift")
record=dict(all_passed=True,exact_names=names,sha256={str(p.relative_to(R)):sha(p) for p in paths if p.name!="publication.json"},scope="NEW planning files only; private host.json deliberately excluded. Self hash and every actual staged blob are recorded in ignored staged-receipt.json BEFORE commit.")
with (E/"publication.json").open("x") as f:json.dump(record,f,indent=2);f.write("\n")
subprocess.run(["git","add","--",*names],cwd=R,check=True)
need(git("diff","--cached","--name-only").splitlines()==names,"Exact staged names")
subprocess.run(["git","diff","--cached","--check"],cwd=R,check=True)
blobs={n:git("rev-parse",":"+n) for n in names}
need(all(blobs[n]==git("hash-object",n) for n in names),"Staged content")
need(all(x.startswith("A\t") for x in git("diff","--cached","--name-status").splitlines()),"Only new additions")
receipt=R/".superpowers/sdd/2026-10-16-direct-bg-block-upper/staged-receipt.json";receipt.parent.mkdir(parents=True,exist_ok=True)
with receipt.open("x") as f:json.dump(dict(all_passed=True,parent=git("rev-parse","HEAD"),exact_names=names,blobs=blobs,sha256={n:sha(R/n) for n in names}),f,indent=2);f.write("\n")
print(json.dumps(dict(all_passed=True,exact_files=len(names),receipt=str(receipt)),indent=2))
