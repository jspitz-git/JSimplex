from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-C';B=D.parent/'S2-B'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
mapper={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):D/'STATUS.md.before-S2-C',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):D/'roadmap.md.before-S2-C'}
old=load(B/'closure.json');pins=load(D/'pins.json');author=load(D/'author-check.json');host=load(D/'pre-continuation-host.json')
review=(D/'review.md').read_text()
checks={
 'original_closure25_preserved':load(D/'closure.json')['all_passed'] and len(load(D/'closure.json')['sha256'])==25 and all(sha(D/'roadmap.md.before-whitespace' if p==str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md') else Path(p))==h for p,h in load(D/'closure.json')['sha256'].items()),
 'original_publication_false_preserved':not load(D/'publication.json')['all_passed'],
 'whitespace_fix4':load(D/'whitespace-fix.json')['all_passed'] and all(sha(Path(p))==h for p,h in load(D/'whitespace-fix.json')['sha256'].items()),
 'publication_correction_accepted':'ACCEPTED S2-C publication whitespace correction.' in (D/'publication-review.md').read_text(),
 'source21':load(D/'source-check.json')['all_passed'],
 'full535_pins':len(pins)==535 and all(sha(Path(p))==h for p,h in pins.items()),
 'author6':author['all_passed'] and all(sha(Path(p))==h for p,h in author['sha256'].items()),
 'B24_preserved':len(old['sha256'])==24 and all(sha(mapper.get(p,Path(p)))==h for p,h in old['sha256'].items()),
 'fresh_host5':host['all_passed'] and len(host['groups'])==26,
 'review_accepted':'ACCEPTED for S2-C offline preparation only.' in review,
 'reviewer24_checks':load(D/'reviewer-check.json')['all_passed'] and all(load(D/'reviewer-check.json')['mechanical_checks'].values()),
 'reviewer24_bindings':len(load(D/'reviewer-check.json')['sha256'])==24 and all(sha(Path(p))==h for p,h in load(D/'reviewer-check.json')['sha256'].items()),
 'no_unresolved_findings':not any(load(D/'reviewer-check.json')['findings'].values()),
 'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='d02416c108f06fcd41d58e0a1980b70a51fef9ef',
 'HEAD_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='dee5b167c54daaaa1c2273729278da2a86c7880d',
 'actual_source_test_env_ci_unchanged':not subprocess.check_output(['git','diff','--name-only','master','--','src','test','.github','Project.toml'],text=True).strip(),
 'only_continuation_tracked_changes':set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())==set(str(Path(p).relative_to(R)) for p in mapper),
 'index_empty':not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip(),
 'next_offline_no_allowance':'Do not\nlaunch Julia as part of this S2-D preparation.' in (R/'docs/superpowers/plans/2026-10-13-price-audit-values-admission.md').read_text(),
}
paths=sorted(p for p in D.iterdir() if p.is_file())+[R/p for p in ['diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-VALUES-PREPARATION.md','diagnostics/simplex-core-architecture/S2-PRICE-AUDIT-VALUES-PREPARATION-REVIEW.md','diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','docs/superpowers/plans/2026-10-13-price-audit-values-admission.md']]
o={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in paths},'B_continuation_mapping':{p:str(v) for p,v in mapper.items()},'scope':'OFFLINE preparation only; no Julia or numerical allowance'}
with (D/'closure-final.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(o['sha256'])}));assert o['all_passed']
