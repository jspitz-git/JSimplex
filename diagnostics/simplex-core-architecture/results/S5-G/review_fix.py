"""One offline prelaunch correction; preserve initial source/hash evidence."""
from pathlib import Path
import json,hashlib,ast
H=Path(__file__).resolve().parent
for name in ('audit.py','independent_post.py'):
    with (H/(name+'.before-review')).open('xb') as f:f.write((H/name).read_bytes())
p=H/'audit.py';s=p.read_text()
old="and all(typed(fm[k],128) for k in ('objective_constant','progress_constant','options','policy'))"
new="and all(typed(fm[k],128) for k in ('objective_constant','progress_constant')) and all(typed(fm['options'][k],128) for k in ('primal_tolerance','dual_tolerance','zero_tolerance')) and all(typed(fm['policy'][k],128) for k in ('solve_tolerance','pivot_error_tolerance'))"
assert old in s;s=s.replace(old,new)
s=s.replace("    c('native_policy'", "    c('time_limit_float64',fm['options']['time_limit']==bm['options']['time_limit'] and typed(fm['options']['time_limit'],53))\n    c('native_policy'")
s=s.replace("return v in ('Inf','-Inf','NaN') and neg==(math.copysign(1,z)<0)","return v==('NaN' if math.isnan(z) else '-Inf' if z<0 else 'Inf') and neg==(math.copysign(1,z)<0) and x['precision']==53")
s=s.replace("if v in ('Inf','-Inf','NaN'):return x['bits']==''", "if v in ('Inf','-Inf','NaN'):return x['bits']=='' and (v=='NaN' or neg==(v=='-Inf'))")
p.write_text(s)
p=H/'independent_post.py';s=p.read_text()
insert='''expected_paths=set(pins['files'])
for tree in pins['trees']:
    root=Path(tree)
    assert root.is_dir() and not root.is_symlink()
    for q in root.rglob('*'):
        assert not (q.is_symlink() and (q.is_dir() or not q.exists()))
        if q.is_file():expected_paths.add(str(q))
'''
s=s.replace("checks={'all_launch_hashes'",insert+"checks={'inventory_membership':expected_paths==set(pins['inventory']),'all_launch_hashes'")
p.write_text(s)
# Execute only the new pure encoding predicate, not either result auditor/main.
def helper(text):
    tree=ast.parse(text);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='valid_scalar')
    import struct,math
    from fractions import Fraction
    env={'struct':struct,'math':math,'Fraction':Fraction}
    exec(compile(ast.Module(body=[f],type_ignores=[]),'encoding-predicate','exec'),env)
    return env['valid_scalar']
a=helper((H/'audit.py.before-review').read_text());b=helper((H/'audit.py').read_text())
wrong={'kind':'Float64','value':'NaN','precision':53,'negative':False,'bits':format(0x7ff0000000000000,'064b')}
wrong2={'kind':'BigFloat','value':'-Inf','precision':128,'negative':False,'bits':''}
red={'broad_precision':old in (H/'audit.py.before-review').read_text(),'nonfinite_mismatch_accepted':a(wrong),'bigfloat_sign_mismatch_accepted':a(wrong2),'membership_missing':'expected_paths' not in (H/'independent_post.py.before-review').read_text()}
green={'selective_precision':old not in (H/'audit.py').read_text() and "c('time_limit_float64'" in (H/'audit.py').read_text(),'nonfinite_rejected':not b(wrong),'bigfloat_sign_rejected':not b(wrong2),'membership_explicit':"expected_paths==set(pins['inventory'])" in (H/'independent_post.py').read_text()}
checks={'four_red_reproduced':all(red.values()),'four_green':all(green.values()),'positive_inf_valid':b(wrong|{'value':'Inf'}),'negative_inf_valid':b(wrong|{'value':'-Inf','negative':True,'bits':format(0xfff0000000000000,'064b')}),'nan_valid':b(wrong|{'bits':format(0x7ff8000000000000,'064b')})}
for n in ('audit.py','independent_post.py'):ast.parse((H/n).read_text())
bindings={str(H/n):hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ('audit.py','audit.py.before-review','independent_post.py','independent_post.py.before-review','review_fix.py')}
with (H/'review-fix.json').open('x') as f:json.dump({'red':red,'green':green,'checks':checks,'all_passed':all(checks.values()),'sha256':bindings},f,indent=2);f.write('\n')
print(json.dumps({'red':len(red),'green':len(green),'checks':checks}));assert all(checks.values())
