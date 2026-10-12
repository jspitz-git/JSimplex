"""Exclusive offline preparation, no Julia and no old script execution."""
from pathlib import Path
import hashlib,json,tomllib,ast,html,re,time
R=Path.cwd();I=Path(__file__).resolve().parent;H=I.parent/'S5-H';G=I.parent/'S5-G'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
e=json.loads((H/'evidence.json').read_text());expected=tomllib.loads((I/'expected.toml').read_text());s=(H/'append.jl').read_text();x=s;patches=tomllib.loads((I/'insertions.toml').read_text())['insertions']
for p in patches:
 assert x.count(p['anchor'])==1;x=x.replace(p['anchor'],p['insert']+p['anchor'])
for p in reversed(patches):x=x.replace(p['insert']+p['anchor'],p['anchor'])
for n in ['launcher.py','audit.py']:ast.parse((I/n).read_text())
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu');doc=(runtime/'share/doc/julia/html/en/manual/command-line-interface.html').read_text();row=next(html.unescape(re.sub('<[^>]+>',' ',v)) for v in doc.split('<tr>') if '--compiled-modules' in v)
loader=(runtime/'share/julia/base/loading.jl').read_text();start=loader.index('    if JLOptions().use_compiled_modules == 1',loader.index('function __require_prelocked'));end=loader.index('\n    end',start)+8
checks={'H780_all_unchanged':all(sha(p)==v for p,v in e['sha256'].items()),'candidate_and_prefix':sha(H/'candidate.jl')==expected['candidate'] and sha(R/'test/simplex_precision_state_tests.jl')==expected['prefix'],'inverse_three_insertions':x==s and len(patches)==3,'new_python_syntax':True,'existing_mode_documented':'disallows creation of new precompile files' in row,'loader_compilecache_guard':'return compilecache(pkg, path;' in loader[start:end],'G_false_audit_preserved':not json.loads((G/'audit.json').read_text())['all_passed'],'G_separate_supplement_pass':json.loads((G/'outcome-supplement.json').read_text())['all_passed']}
paths=set(e['sha256'])|{str(p.resolve()) for p in I.iterdir() if p.is_file()}|{str(H/'closure.json'),str(H/'evidence.json'),str(R/'diagnostics/simplex-core-architecture/S5-PRECISION-JOURNAL-INTERRUPTION-TEST-PREPARATION-REVIEW.md'),str(runtime/'share/julia/stdlib/v1.13/Test/src/Test.jl')}
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'cli_row':row.strip(),'loader_excerpt':loader[start:end],'sha256':{p:sha(p) for p in sorted(paths)}}
with (I/'preparation.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pins':len(paths)}));raise SystemExit(0 if x['all_passed'] else 1)
