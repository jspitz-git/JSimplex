"""One separate path-normalization correction; preserve failed closure and draft publication."""
from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=(E/'closure.py').read_text();before="def bindings(o,m=mapper):return all(sha(m.get(p,p))==h for p,h in o['sha256'].items())";after="def bindings(o,m=mapper):\n def mapped(p):\n  absolute=str(Path(p) if Path(p).is_absolute() else R/p)\n  return m.get(absolute,Path(absolute))\n return all(sha(mapped(p))==h for p,h in o['sha256'].items())"
if old.count(before)!=1 or old.count("E/'closure.json'")!=1:raise SystemExit('closure selector mismatch')
new=old.replace(before,after).replace("E/'closure.json'","E/'closure-final.json'")
with (E/'closure-final.py').open('x') as f:f.write(new)
p=(E/'publication.py').read_text()
if p.count("E/'closure.json'")!=1:raise SystemExit('publication selector mismatch')
with (E/'publication-reviewed.py').open('x') as f:f.write(p.replace("E/'closure.json'","E/'closure-final.json'"))
mapper={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):E/'STATUS.md.before-S2-E',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):E/'roadmap.md.before-S2-E'}
ns={'sha':sha,'mapper':mapper,'R':R,'Path':Path};exec(before,ns);pub=json.loads((D/'publication.json').read_text());red=ns['bindings'](pub);exec(after,ns);green=ns['bindings'](pub)
original=json.loads((E/'closure.json').read_text());mismatches=[p for p,h in pub['sha256'].items() if sha(Path(p))!=h]
checks={'original23of24_false_preserved':original['all_passed'] is False and len(original['checks'])==24 and sum(original['checks'].values())==23 and original['checks']['Dpublication6_128'] is False,'RED_old_relative_mapping_false':red is False,'GREEN_normalized_mapping_true':green is True,'only_two_relative_continuations_differ':set(mismatches)=={str(Path(p).relative_to(R)) for p in mapper},'old_absolute_mapping_unchanged':ns['bindings'](json.loads((D/'closure.json').read_text())),'source_change_only_binding_normalization_and_new_output':new.replace(after,before).replace("E/'closure-final.json'","E/'closure.json'")==old,'publication_change_only_new_closure_path':(E/'publication-reviewed.py').read_text().replace("E/'closure-final.json'","E/'closure.json'")==p}
paths=[E/n for n in ['closure.py','closure.json','closure-final.py','publication.py','publication-reviewed.py','closure-amendment.py']]+[D/'publication.json',E/'STATUS.md.before-S2-E',E/'roadmap.md.before-S2-E']
o={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in paths},'explanation':'Original closure stopped before staging/commit/push. D publication hashes use repository-relative paths; historical continuation map used absolute keys. Normalize the key only; both preserved before-E hashes match exactly. Original false closure remains unchanged; no numerical/auditor/postcheck rerun.'}
with (E/'closure-amendment.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(paths)}))
if not o['all_passed']:raise SystemExit(1)
