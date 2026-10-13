from pathlib import Path
import json,hashlib,ast
D=Path(__file__).resolve().parent;R=D.parents[3];s=(D/'closure-corrected.py').read_text();module=ast.parse(s);ns=dict(Path=Path,hashlib=hashlib,R=R)
for name in ['sha','validmap','review_admitted']:
 node=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),'pure-closure-functions','exec'),ns)
p=str(D/'closure-corrected.py');h=hashlib.sha256((D/'closure-corrected.py').read_bytes()).hexdigest();good=dict(accepted=True,unresolved_findings=[],sha256={p:h});fn=ns['review_admitted'];checks={'accepted_bound_positive':fn(good)}
for n,d in [('rejected',dict(good,accepted=False)),('findings',dict(good,unresolved_findings=['issue'])),('changed',dict(good,sha256={p:'0'*64})),('empty',dict(good,sha256={})),('missing',{}),('missing_file',dict(good,sha256={str(D/'absent.txt'):h}))]:checks[n]=not fn(d)
checks['canonical_review_mandatory']="for n in ['review-final.json','result-review.json','closure-review-final.json']:" in s and "checks[n+'_accepted']=review_admitted(d)" in s
checks['false_blocks_closure']="if not all(checks.values()):raise SystemExit(1)" in s and "all_passed=all(checks.values())" in s
checks['publisher_separate_PASS']= "require(c['all_passed'] is True and all(c['checks'].values()),'separate PASS closure')" in (D/'publication-corrected.py').read_text()
checks['history_restored']=json.loads((D/'continuation-fix.json').read_text())['all_passed'] is True
with (D/'closure-fix-tests.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['closure-corrected.py','publication-corrected.py','continuation-fix.py','continuation-fix.json',Path(__file__).name]},scope='Pure Python review-gate tests; no closure/publication/Julia execution.'),f,indent=2);f.write('\n')
print(sum(checks.values()),'/',len(checks))
if not all(checks.values()):raise SystemExit(1)
