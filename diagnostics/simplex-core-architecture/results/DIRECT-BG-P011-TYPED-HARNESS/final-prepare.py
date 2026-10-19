"""New final offline preparation verification and manifest, not an old rerun."""
from pathlib import Path
import ast,json,hashlib,tomllib
import control as c,oracle as o
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
fix=c.rd(D/'review-fix-provenance.json');mapping=fix['before']
def historical_bindings(v):
 return all(sha(mapping[n]['preserved_path'] if n in mapping else n)==h for n,h in v.items())
initial=c.rd(D/'preparation-pins.json.before-review')
check('initial_234_inputs_preserved',len(initial['sha256'])==234 and historical_bindings(initial['sha256']))
rv=c.rd(D/'review.json.before-review')
check('initial_rejection_preserved',rv['accepted'] is False and len(rv['findings'])==1 and historical_bindings(rv['sha256']))
check('initial_evidence_preserved',historical_bindings(rv['evidence_sha256']))
check('initial_manifest_binding',rv['pins_sha256']==sha(D/'preparation-pins.json.before-review'))
check('initial_source_check_bindings',historical_bindings(c.rd(D/'source-check.json')['sha256']))
oldtests=c.rd(D/'tests.json')
check('initial_864_checks_preserved',oldtests['all_passed'] is True and oldtests['count']==864 and historical_bindings({str(D/n):h for n,h in oldtests['sha256'].items()}))
newtests=c.rd(D/'tests-reviewed.json')
check('new_894_checks_bound',newtests['all_passed'] is True and newtests['count']==894 and all(sha(D/n)==h for n,h in newtests['sha256'].items()))
check('correction_bindings',all(sha(n)==h for n,h in fix['after_sha256'].items()))
raw=Path(fix['historical_rendering_source'])
check('original_raw_rendering_bound',sha(raw)==fix['historical_rendering_sha256'] and tomllib.loads(raw.read_text())['records']['failures'][0]['detail']==o.RED_FAILURE_DETAIL==fix['expected_detail'])
check('no_byte_count_oracle','208' not in o.RED_FAILURE_DETAIL and ' == 0' in o.RED_FAILURE_DETAIL)
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
check('python_sources_parse',True)
check('driver_controls_unchanged',all(sha(D/n)==initial['sha256'][str(D/n)] for n in ['driver.jl','control.py','audit.py','seal.py','launch.py','outer.py','guard.py','supervisor.py','post-return.py','recorder.jl']))
check('no_action_paths',all(not (D/n).exists() for n in ['runs','outers','sealed.json','reservation.json']))
check('frozen_sources_current',all(sha(n)==h for n,h in initial['sha256'].items() if not n.startswith(str(D)+'/')))
save('review-fix-check.json',dict(all_passed=True,checks=checks,initial_mapping=mapping,sha256={str(p):sha(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ['review.json','review.md']}))
# Source checks above bind the before documents; append factual cost/fix notes now,
# then bind these final documents by the new manifest rather than altering old pins.
for n,extra in [('ADMISSION.md','\nTests-cost wraps tests(), including unit-1.toml serialization inside that function. Other payload serialization is outside its window. These partial cost records must not be added as independent components.\n'),('REPORT.md','\nCorrection verification: 894 new synthetic checks and 14 explicit source/preservation checks passed. The first offline amendment stopped before editing original files because it expected a trailing newline absent from the saved failure rendering; its script and failure record are preserved. The separate corrected amendment binds the exact 439-character rendering. Tests-cost includes unit-1.toml serialization; other payload serialization is outside that window.\n')]:
 p=D/n;p.write_text(p.read_text()+extra)
# New exact membership preserves all initial subjects and adds every new local
# evidence file except the final receipt/report and manifest (self-reference).
paths=set(Path(n) for n in initial['sha256'])
paths.update(p for p in D.iterdir() if p.is_file() and p.name not in ['preparation-pins.json','review.json','review.md'])
paths.add(raw)
required=D/'required-paths.json';required.write_text(json.dumps(dict(paths=sorted(str(p) for p in paths)),indent=2)+'\n')
if not all(p.is_file() and not p.is_symlink() for p in paths):raise RuntimeError('Missing/symlink input')
(D/'preparation-pins.json').write_text(json.dumps(dict(scope='P011 typed harness preparation only; reviewed offline correction; not launch pins',sha256={str(p):sha(p) for p in sorted(paths)}),indent=2)+'\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),manifest_inputs=len(paths))))
