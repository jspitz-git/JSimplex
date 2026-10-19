from pathlib import Path
import hashlib,json
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');q=r/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-PLAN';s=r/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md'
with (q/'spec.before-lookup-clarification.md').open('xb') as f:f.write(s.read_bytes())
t=s.read_text();old='Commit-support counting is another O(h*w) pass.';new='Commit-support counting and recomputed packed interval positions cost another O(w log n+h*w) pass; no per-column offsets are retained in the two-mask workspace.'
if t.count(old)!=1:raise RuntimeError('unique correction')
s.write_text(t.replace(old,new))
with (q/'LOOKUP-CLARIFICATION.md').open('x') as f:f.write('# Final lookup accounting correction\n\nThe reviewer requested charging repeated interval lookups during support counting/commit. The spec now explicitly budgets O(w log n+h*w); aggregate complexity and algorithm/gates are unchanged. The old spec bindings in author.json and review-fix.json map ONLY to spec.before-lookup-clarification.md on exact hash equality. Their other bindings are unchanged. Those records remain frozen, not retroactively updated.\n')
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
checks={}
for file in ['author.json','review-fix.json']:
 j=json.loads((q/file).read_text());checks[file]=all(sha(q/'spec.before-lookup-clarification.md' if Path(n)==s else Path(n))==h for n,h in j['sha256'].items())
checks['exact_text_correction']=s.read_text()==(q/'spec.before-lookup-clarification.md').read_text().replace(old,new)
with (q/'lookup-fix.py').open('xb') as f:f.write(Path(__file__).read_bytes())
with (q/'author-final.json').open('x') as f:json.dump({'all_passed':all(checks.values()),'checks':checks,'sha256':{str(x):sha(x) for x in [s,q/'spec.before-lookup-clarification.md',q/'LOOKUP-CLARIFICATION.md',q/'lookup-fix.py',q/'author.json',q/'review-fix.json']},'mapping':'Only previous spec bindings map to spec.before-lookup-clarification.md'},f,indent=2)
print(checks)
if not all(checks.values()):raise SystemExit(1)
