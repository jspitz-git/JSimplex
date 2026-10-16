from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-ADAPTER-PREPARATION';C=R/'diagnostics/direct-bg-block-upper/reproduce'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=json.loads((E/'reviewer-final-check.json').read_text())
for p,h in f['sha256'].items():assert sha(Path(p))==h
m=json.loads((E/'stage-source-map.json').read_text());assert m['all_passed']
for p,h in m['sha256'].items():assert sha(Path(p))==h
paths={Path(p) for p in f['sha256'] if Path(p).is_relative_to(R)}|{Path(p) for p in m['sha256']}
paths.update(p for p in E.iterdir() if p.is_file() and (p.name.startswith('reviewer-') or p.name.startswith('independent-review-')))
paths.update(E/n for n in ('stage-source-map.json','stage-source-map.py','review-fix.py','review-fix.json','test-amendment.py','test-amendment.json','source-check-reviewed.json','source-check-reviewed.py','overlay-reviewed.json','adapter-inverse-reviewed.json'))
paths={p for p in paths if p.exists()}
o=json.loads((E/'overlay-reviewed.json').read_text());stage=Path(o['path'])
for n,h in o['sha256'].items():assert sha(stage/n)==h;paths.add(stage/n)
record={'verdict':'PASS (offline source preparation only)','unresolved_blocking_findings':0,'scope':'No Julia parsing/import/compilation/numerical execution; no Task3 admission. Comparator is the accepted staged DIRECT BG, not unmodified master dispatch.','sha256':{str(p.relative_to(R)):sha(p) for p in sorted(paths)}}
with (E/'reviewer-final-bindings.json').open('x') as out:json.dump(record,out,indent=2);out.write('\n')
print('PASS final relative-R bindings:',len(record['sha256']))
