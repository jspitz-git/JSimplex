"""One-shot Task2 closure, after fresh final exact independent review; no Julia."""
from pathlib import Path
import json,hashlib,subprocess,sys
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce'
P=E.parent/'DIRECT-BG-DYNAMIC-U-PREPARATION';DP=E.parent/'DIRECT-BG-DYNAMIC-U-PLAN';D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def g(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
canonical=rd(E/'canonical.json');newfiles=canonical['new_candidate_files']
need(len(newfiles)==len(set(newfiles))==11,'Exact11new candidate files')
review=rd(E/'review.json');members={str(p) for p in E.iterdir() if p.is_file() and p.name!='review.json'}|{str(C/n) for n in newfiles}
need(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')=='direct BG dynamic U Task2 preparation','Review gate')
need(set(review['sha256'])==members and all(sha(Path(n))==h for n,h in review['sha256'].items()),'Review exact names/hash')
for n,h in rd(E/'entry.json')['sha256'].items():need(sha(Path(n))==h,'Prior evidence/plan drift')
for n,h in rd(DP/'helper-pins.json')['sha256'].items():need(sha(Path(n))==h,'Host helper drift')
for n,h in rd(P/'publication.json')['sha256'].items():need(sha(R/n)==h,'Frozen Task1 publication drift '+n)
o=rd(E/canonical['overlay']);O=Path(o['path'])
need({str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(o['sha256']),'Overlay names')
need(all(sha(O/n)==h for n,h in o['sha256'].items()),'Overlay hashes')
need(rd(E/canonical['author_checks'])['all_passed'],'Author supplement')
need(not rd(E/canonical['preserved_false_author'])['all_passed'],'Original FALSE preserved')
need(sha(C/canonical['candidate'])==sha(O/'src/dynamic-bg.jl') and sha(C/canonical['tests'])==sha(O/'test/dynamic-bg-tests.jl'),'Canonical source identity')
master='26e2291745999f485a74f643298ca997d65c7205';head='3b0aaf41e67fec3b0e0c60ece0faa6ba303f23b1';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
need(g('rev-parse','HEAD')==head and g('rev-parse','master')==master and g('rev-parse','HEAD',cwd=W)==master,'Refs')
remote=g('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');need(master+'\trefs/heads/master' in remote and head+'\trefs/heads/codex/simplex-core-architecture' in remote,'Remote refs')
need(not g('diff','--cached','--name-only') and not g('diff','--name-only'),'Index/tracked changes before continuation')
for root in (R,W):need(not g('diff','HEAD','--name-only','--','src','test','.github','Project.toml',cwd=root),'Tracked production drift')
sys.path.insert(0,str(D));from control import full_host
h=full_host(rd(E/'host.json')['groups']);need(not h['matches'],'Groups/sessions/Julia');save(E/'closure-host.json',h)
S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';maps=[]
for rec in [P/'closure.json',P/'publication.json']:
 for live,before in [(S,E/'STATUS.md.before-Task2'),(ROAD,E/'roadmap.md.before-Task2')]:
  key=str(live.relative_to(R));v=rd(rec)['sha256'][key];need(sha(live)==sha(before)==v,'Continuation drift');maps.append(dict(record=str(rec.relative_to(R)),key=key,sha256=v,preserved=str(before.relative_to(R))))
save(E/'continuation-mappings.json',maps)
text=(E/'continuation-text.md').read_text();s=S.read_text();marker='## Exact next action\n';need(s.count(marker)==1,'STATUS marker');i=s.index(marker)+len(marker);S.write_text(s[:i]+'\n'+text+'\n### Historical prior continuation (superseded)\n'+s[i:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Direct BG dynamic U Task2 offline adapter preparation (2026-10-16)\n\n'+text)
paths=sorted([p for p in E.iterdir() if p.is_file()]+[C/n for n in newfiles]+[S,ROAD])
save(E/'closure.json',dict(all_passed=True,checks=dict(exact_final_review=True,prior_evidence_plan_bound=True,canonical_overlay_identity=True,original_failures_preserved=True,production_tracked_diff_clear=True,local_remote_refs_unchanged=True,fresh_groups_sessions_clear=True,prior_maps4=len(maps)==4,offline_only=True),sha256={str(p.relative_to(R)):sha(p) for p in paths}))
print('Task2 closure9PASS',len(paths),'bindings')
