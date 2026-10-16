"""Reviewed one-shot publication-only supplement; never reruns original closure/publication."""
from pathlib import Path
import json,hashlib,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def g(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
a=rd(E/'publication-amendment-review.json')
need(a['accepted'] is True and a['findings']==[],'Amendment review')
C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
newfiles=rd(E/'canonical.json')['new_candidate_files']
review_members={str(p) for p in E.iterdir() if p.is_file() and p.name!='publication-amendment-review.json'}|{str(C/n) for n in newfiles}|{str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
need(set(a['sha256'])==review_members,'Amendment exact review membership')
for n,h in a['sha256'].items():need(sha(Path(n))==h,'Amendment review drift')
c=rd(E/'closure.json');need(c['all_passed'],'Original closure')
for n,h in c['sha256'].items():need(sha(R/n)==h,'Original closure drift')
r=rd(E/'review.json');need(r['accepted'] is True and r['findings']==[],'Original final review')
for n,h in r['sha256'].items():need(sha(Path(n))==h,'Original final review drift')
p=rd(E/'publication-failure.json');need(not (E/'publication.json').exists(),'Historical publication outcome')
need(g('diff','--cached','--name-only').splitlines()==p['staged_names'],'Original stage membership')
for n,b in p['git_blobs'].items():need(g('rev-parse',':'+n)==g('hash-object','--',n)==b,'Original stage blob')
need(not g('diff','--name-only'),'Unstaged tracked changes')
head='3b0aaf41e67fec3b0e0c60ece0faa6ba303f23b1';master='26e2291745999f485a74f643298ca997d65c7205'
need(g('rev-parse','HEAD')==head and g('rev-parse','master')==master,'Refs')
remote=g('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');need(master+'\trefs/heads/master' in remote and head+'\trefs/heads/codex/simplex-core-architecture' in remote,'Remote refs')
paths=sorted([p for p in E.iterdir() if p.is_file()]+[R/'diagnostics/direct-bg-dynamic-upper/reproduce'/n for n in rd(E/'canonical.json')['new_candidate_files']]+[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'])
with (E/'closure-supplement.json').open('x') as f:json.dump(dict(all_passed=True,checks=dict(accepted_amendment=True,closure57_unchanged=True,review52_unchanged=True,original_stage59_blobs=True,tracked_no_new_change=True,refs_remote_unchanged=True,failed_outcome_preserved=True),sha256={str(p.relative_to(R)):sha(p) for p in paths}),f,indent=2);f.write('\n')
print('Task2 publication closure supplement7PASS',len(paths),'bindings')
