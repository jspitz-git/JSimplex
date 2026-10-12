"""One-time offline preparation evidence. No Julia process or old script imports."""
from pathlib import Path
import hashlib,json,tomllib,html,re,ast,subprocess
ROOT=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
H=Path(__file__).resolve().parent;F=H.parent/'S5-F'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
pins=tomllib.loads((F/'source-pins-reviewed.toml').read_text())['sha256']
checks={'frozen176':len(pins)==176 and all(sha(p)==v for p,v in pins.items())}
for name in ('launcher.py','audit.py'):ast.parse((H/name).read_text());checks[name+'_python_syntax']=True
runtime=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu')
loader=(runtime/'share/julia/base/loading.jl').read_text()
doc=(runtime/'share/doc/julia/html/en/manual/command-line-interface.html').read_text()
row=next(html.unescape(re.sub('<[^>]+>',' ',x)).strip() for x in doc.split('<tr>') if '--compiled-modules' in x)
checks['existing_documented']='disallows creation of new precompile files' in row
start=loader.index('    if JLOptions().use_compiled_modules == 1',loader.index('function __require_prelocked'))
end=loader.index('\n    end',start)+8
excerpt=loader[start:end]
checks['new_compilecache_guard']='Precompilation.precompilepkgs' in excerpt and 'return compilecache(pkg, path;' in excerpt
checks['master']=subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='0eb75c3190096946b0e91e5360230ccd7166f298'
checks['src_test_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True)
checks['head']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='1a58293ba85a54bd9995e6e99bcc65d3ac6ac4ed'
checks['no_julia']=not [p for p in Path('/proc').glob('[0-9]*') if (p/'comm').exists() and (p/'comm').read_text().strip()=='julia']
# Read-time bindings: not launch pins. Updated texts, if any, will be separately bound.
bindings={str(p):sha(p) for p in (H/'launcher.py',H/'audit.py',H/'prelaunch.md',Path(__file__),runtime/'share/julia/base/loading.jl',runtime/'share/doc/julia/html/en/manual/command-line-interface.html')}
out={'checks':checks,'all_passed':all(checks.values()),'frozen_sha256':pins,'sha256':bindings,'doc_row':row,'loader_excerpt':excerpt}
with (H/'preparation.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'passed':out['all_passed'],'pins':len(pins)}))
assert out['all_passed']
