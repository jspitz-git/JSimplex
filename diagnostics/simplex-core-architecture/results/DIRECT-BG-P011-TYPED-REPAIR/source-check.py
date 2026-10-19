from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;R=D.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,text):
 if not ok:raise RuntimeError(text)
old=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl'
a=old.read_bytes();b=(D/'panel-tests.jl').read_bytes();h=(D/'helpers.jl').read_bytes();before=(D/'original-block.txt').read_bytes();after=(D/'replacement.txt').read_bytes()
checks={}
def check(k,v):checks[k]=bool(v);require(v,k)
check('helper_insert_unique',b.count(h)==1)
check('replacement_unique',b.count(after)==1)
check('whole_file_inverse',b.replace(h,b'',1).replace(after,before,1)==a)
ids=lambda s:re.findall(rb'@check(?:throws)? "(P\d+)"',s)
check('old_ids_order_preserved',[x for x in ids(b) if int(x[1:])<=94]==ids(a))
check('eight_new_ids',[x.decode() for x in ids(b) if int(x[1:])>94]==['P%03d'%i for i in range(95,103)])
check('no_duplicate_literal_ids',len(ids(b))==len(set(ids(b))))
check('no_captured_measurement_macro',b'@allocated' not in h and b'@allocations' not in h)
check('four_strict_zero_oracles',all(x in after for x in [b'p011.bytes == 0',b'p011.events == 0',b'p011.consumed_bytes == 0',b'p011.consumed_events == 0']))
check('reset_each_measured_consumption',h.count(b'sink[] = sentinel')==2)
check('no_include_time_probe_call',h.count(b'p011_probe(')==1)
check('all_input_hashes',all(sha(Path(p))==s for p,s in json.loads((D/'inputs.json').read_text()).items()))
check('candidate_exact_sha',sha(R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-CANDIDATE/panel.jl')=='19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295')
files=[p for p in sorted(D.iterdir()) if p.is_file()]
out={'scope':'Offline literal/edit-boundary checks only; Julia unexecuted','checks':checks,'all_passed':all(checks.values()),'bindings':{p.name:sha(p) for p in files}}
with (D/'source-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':out['all_passed'],'bindings':len(files)}))
