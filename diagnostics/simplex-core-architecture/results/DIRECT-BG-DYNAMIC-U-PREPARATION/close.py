"""One-shot Task1 closure, executed only after exact final independent review."""
from pathlib import Path
import json,hashlib,subprocess,sys
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce';P=E.parent/'DIRECT-BG-DYNAMIC-U-PLAN';D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def g(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
review=rd(E/'review.json');members={str(p) for p in E.iterdir() if p.is_file() and p.name!='review.json'}|{str(p) for p in C.iterdir() if p.is_file()}
need(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')=='direct BG dynamic U Task1 preparation','Review gate')
need(set(review['sha256'])==members and all(sha(Path(n))==h for n,h in review['sha256'].items()),'Review exact names/hash')
for n,h in rd(E/'entry.json')['sha256'].items():need(sha(Path(n))==h,'Accepted plan drift')
for n,h in rd(P/'helper-pins.json')['sha256'].items():need(sha(Path(n))==h,'Host helper drift')
canonical=rd(E/'canonical.json');o=rd(E/canonical['overlay']);O=Path(o['path'])
need({str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(o['sha256']),'Overlay names')
need(all(sha(O/n)==h for n,h in o['sha256'].items()),'Overlay hashes')
need(rd(E/canonical['author_checks'])['all_passed'],'Author checks')
need(sha(C/canonical['candidate'])==sha(O/'src/slot-upper.jl') and sha(C/canonical['tests'])==sha(O/'test/slot-upper-tests.jl'),'Canonical source identity')
master='26e2291745999f485a74f643298ca997d65c7205';head='2ad323617d16a26289ed05a9afac3fbe27b0133e';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
need(g('rev-parse','HEAD')==head and g('rev-parse','master')==master and g('rev-parse','HEAD',cwd=W)==master,'Refs')
remote=g('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');need(master+'\trefs/heads/master' in remote and head+'\trefs/heads/codex/simplex-core-architecture' in remote,'Remote refs')
for root in (R,W):need(not g('diff','HEAD','--name-only','--','src','test','.github','Project.toml',cwd=root),'Tracked source/test/CI/project drift')
sys.path.insert(0,str(D));from control import full_host
h=full_host(rd(E/'host.json')['groups']);need(not h['matches'],'Groups/Julia');save(E/'closure-host.json',h)
S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';maps=[]
for rec in [P/'closure.json',P/'publication.json']:
 for live,before in [(S,E/'STATUS.md.before-Task1'),(ROAD,E/'roadmap.md.before-Task1')]:
  key=str(live.relative_to(R));v=rd(rec)['sha256'][key];need(sha(live)==sha(before)==v,'Continuation drift');maps.append(dict(record=str(rec.relative_to(R)),key=key,sha256=v,preserved=str(before.relative_to(R))))
save(E/'continuation-mappings.json',maps)
text=(E/'continuation-text.md').read_text();s=S.read_text();marker='## Exact next action\n';need(s.count(marker)==1,'STATUS marker');i=s.index(marker)+len(marker);S.write_text(s[:i]+'\n'+text+'\n### Historical prior continuation (superseded)\n'+s[i:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Direct BG dynamic U Task1 offline preparation (2026-10-16)\n\n'+text)
paths=sorted([p for p in E.iterdir() if p.is_file()]+[p for p in C.iterdir() if p.is_file()]+[S,ROAD])
save(E/'closure.json',dict(all_passed=True,checks=dict(exact_review=True,accepted_plan_bound=True,canonical_overlay_bound=True,source_test_CI_tracked_diff_clear=True,refs_remote_unchanged=True,groups_sessions_clear=True,prior_maps4=len(maps)==4,offline_only=True),sha256={str(p.relative_to(R)):sha(p) for p in paths}))
print('Task1 closure8PASS',len(paths),'bindings')
