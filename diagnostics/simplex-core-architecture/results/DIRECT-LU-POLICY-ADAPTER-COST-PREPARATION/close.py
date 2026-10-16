"""One-shot offline candidate closure after independent acceptance; no runtime qualification."""
from pathlib import Path
import json,hashlib,subprocess,sys
P=Path(__file__).resolve().parent;R=P.parents[3];D=P.parent/'NATIVE-PIVOT-MASTER-READINESS';V=P.parent/'DIRECT-LU-POLICY-ADAPTER-GREEN';sys.path.insert(0,str(P))
from control import full_host, preparation
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def need(v,m):
 if not v:raise RuntimeError(m)
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def g(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
preparation()  # Canonical exact membership, manifest hash and independent review BEFORE writes.
for label,root in [('diagnostic',R),('production',W)]:
 for n,h in rd(P/'baseline.json')[label].items():need(sha(root/n)==h,'Baseline drift '+label+'/'+n)
need(g('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205','Master drift')
need(g('ls-remote','origin','refs/heads/master').startswith(g('rev-parse','master')+'\t'),'Remote drift')
h=full_host(rd(P/'host.json')['groups']);need(not h['matches'],'Live groups/Julia');save(P/'closure-host.json',h)
S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';maps=[]
for rec in [V/'closure.json',V/'publication.json']:
 for live,before in [(S,P/'STATUS.md.before-cost'),(ROAD,P/'roadmap.md.before-cost')]:
  n=str(live.relative_to(R));value=rd(rec)['sha256'][n];need(sha(live)==sha(before)==value,'Continuation drift');maps.append(dict(record=str(rec.relative_to(R)),key=n,sha256=value,preserved=str(before.relative_to(R))))
save(P/'continuation-mappings.json',maps)
text=(P/'continuation-text.md').read_text();s=S.read_text();marker='## Exact next action\n';need(s.count(marker)==1,'STATUS marker');i=s.index(marker)+len(marker)
S.write_text(s[:i]+'\n'+text+'\n### Historical prior continuation (superseded)\n'+s[i:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Direct LU matched-policy cost preparation (2026-10-16)\n\n'+text.rstrip()+'\n')
files=sorted([q for q in P.rglob('*') if q.is_file()]+[S,ROAD])
save(P/'closure.json',dict(all_passed=True,checks=dict(review_accepted=True,review_bindings=True,diagnostic_source_unchanged=True,production_source_unchanged=True,master_remote_unchanged=True,host_groups_sessions_clear=True,prior_maps4=len(maps)==4,offline_preparation_only=True),sha256={str(q.relative_to(R)):sha(q) for q in files}))
print('Matched cost preparation closure8PASS',len(files),'bindings')
