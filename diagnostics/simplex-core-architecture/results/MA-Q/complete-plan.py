from pathlib import Path
import hashlib,json
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-Q'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
review=json.loads((E/'review.json').read_text())
if review.get('accepted') is not True or review.get('findings'):raise SystemExit('Review not accepted/has findings')
for key,h in review['sha256'].items():
    if sha(key)!=h:raise SystemExit('Review binding mismatch: '+key)
files=[R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PLAN.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
names=['report.before-completion','STATUS.md.before-completion','roadmap.md.before-completion']
mapping={}
for p,n in zip(files,names):
    q=E/n
    with q.open('xb') as out:out.write(p.read_bytes())
    mapping[str(p)]={'preserved':str(q),'sha256':sha(q)}
p=files[0];s=p.read_text().replace('Status: plan prepared; independent review pending. No runtime qualification.', 'Status: design and plan accepted by independent review for MA-R offline preparation.\nNo runtime qualification or performance promotion.')
s=s.replace('- [New source checks](results/MA-Q/source-check.json)', '- [Independent review](results/MA-Q/review.md)\n- [New source checks](results/MA-Q/source-check.json)')
s+='''\nFresh independent gpt-6-astra review accepted the design and plan with no findings.\nIt verified all20new bindings and six predecessor mappings and inspected the actual\narithmetic, LU/permutation and triangular normalization sources. No unnecessary\nnew production work or retained memory is proposed under this private-product\nscope; the constant-time gate and one scratch remain prospective measured costs.\nReview acceptance permits MA-R offline preparation only. Reviewed pre-completion\nreport/STATUS/roadmap bytes are preserved and mapped in completion-map.json; final\nclosure binds completed text. No scripts or numerical evidence were rerun.\n'''
p.write_text(s)
p=files[1];s=p.read_text().replace('scratch in native DenseLU FTRAN/BTRAN. Independent review is pending; do not start\nMA-R until accepted.', 'scratch in native DenseLU FTRAN/BTRAN. Fresh independent gpt-6-astra review\naccepted the design and plan with no findings; next step is MA-R offline preparation.')
s=s.replace('MA-S numerical work requires its own immutable admission:', 'MA-Q completed source/design only:14source checks/20bindings and independent review.\nMA-S numerical work requires its own immutable admission:')
p.write_text(s)
p=files[2];s=p.read_text().replace('Independent MA-Q review is pending; MA-R may start only after acceptance. MA-R is\noffline candidate/reference/tests and a separate review.', 'Fresh independent MA-Q review accepted the design and plan with no findings.\nNext MA-R is offline candidate/reference/tests and a separate review.')
p.write_text(s)
obj={'scope':'Only review.json bindings of the three completion-wording paths map to these exact beforecopies. Source-check.json and all other review hashes remain unchanged. Older continuation maps unchanged.', 'mapping':mapping,'review_sha256':sha(E/'review.json')}
with (E/'completion-map.json').open('x') as out:json.dump(obj,out,indent=2);out.write('\n')
checks={
 'review_accepted_no_findings':review.get('accepted') is True and not review.get('findings'),
 'all20_source_bindings':all(sha(p)==h for p,h in json.loads((E/'source-check.json').read_text())['sha256'].items()),
 'review_bindings_preserved':all(sha(mapping[p]['preserved'] if p in mapping else p)==h for p,h in review['sha256'].items()),
 'three_beforecopies':len(mapping)==3 and all(sha(v['preserved'])==v['sha256'] for v in mapping.values()),
 'next_offline_only':all('MA-R' in p.read_text() for p in files) and 'No runtime qualification' in files[0].read_text(),
}
with (E/'completion-check.json').open('x') as out:json.dump({'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in files+[E/'complete-plan.py',E/'completion-map.json']}},out,indent=2);out.write('\n')
print(json.dumps(checks))
if not all(checks.values()):raise SystemExit(1)
