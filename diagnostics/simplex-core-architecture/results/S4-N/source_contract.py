from pathlib import Path
import hashlib,json,re,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-N'
S=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers')
checks={}
def ck(k,v):checks[k]=bool(v)
def body(t,n):return re.search(r'^\w+ <'+n+r'>:\n.*?(?=\n\n)',t,re.M|re.S).group()
u=(E/'libumfpack.so.6.3.5.disassembly.txt').read_text();c=(E/'libsuitesparseconfig.so.7.10.1.disassembly.txt').read_text();init=(S/'LibSuiteSparse.jl').read_text();wrap=(S/'wrappers.jl').read_text();own=(S/'umfpack.jl').read_text();ss=(E/'upstream-SuiteSparse_config-SuiteSparse_config.c').read_text()
ck('installed_malloc_branch','<SuiteSparse_malloc@plt>' in body(u,'umf_l_malloc'))
ck('installed_realloc_raw_branch','<SuiteSparse_config_realloc@plt>' in body(u,'umf_l_realloc'))
ck('installed_free_branch','<SuiteSparse_free@plt>' in body(u,'umf_l_free'))
ck('installed_malloc_indirect','blr' in body(c,'SuiteSparse_malloc'))
ck('installed_realloc_offset16','[x2, #16]' in body(c,'SuiteSparse_config_realloc'))
ck('installed_free_offset24','[x1, #24]' in body(c,'SuiteSparse_free'))
ck('installed_setter_store','str\tx0' in body(c,'SuiteSparse_config_malloc_func_set'))
ck('julia_once_init','Base.OncePerProcess{Nothing}' in init)
ck('julia_all_four_callbacks',all(f'SuiteSparse_config_{x}_func_set(cglobal(:jl_{x}, Ptr{{Cvoid}}))' in init for x in ['malloc','calloc','realloc','free']))
ck('get_set_four_bindings',all(f'function SuiteSparse_config_{x}_func_{a}(' in wrap for x in ['malloc','calloc','realloc','free'] for a in ['get','set']))
ck('source_static_config','static struct SuiteSparse_config_struct SuiteSparse_config' in ss)
ck('source_raw_realloc','return (SuiteSparse_config.realloc_func (p, s))' in ss)
ck('source_start_default','SuiteSparse_config.malloc_func  = malloc' in ss)
ck('source_finalizers',all(x in own for x in ['umfpack_free_numeric(num, Tv, Ti)','num.p = C_NULL','umfpack_free_symbolic(sym, Tv, Ti)','sym.p = C_NULL']))
ck('reuse_still_false','lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=false)' in (R/'src/huangfu_hall_factorization.jl').read_text())
ck('production_tests_ci_match_master',subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b'')
host=json.loads((E/'host-before.json').read_text());ck('host_preflight_no_processes',host['matches']==[])
ck('preflight_refs_agree',all(x in host['remote'] for x in host['refs'].splitlines()))
ck('user_hashes_unchanged',all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in host['user_hashes'].items()))
old=json.loads((D/'results/S4-M/cost-1-pins.json').read_text());print('old keys',old.keys())
files=set(old['files'])|{str(x) for x in S.glob('*.jl')}
files|={str(x) for x in E.iterdir() if x.is_file()}
files|={str(D/'S4-NATIVE-ACCOUNTING-FEASIBILITY.md'),str(R/'docs/superpowers/plans/2026-10-12-hh-native-accounting-feasibility.md'),str(R/'docs/superpowers/plans/2026-10-12-hh-allocation-counter-attribution.md'),str(E/'source_contract.py')}
inv={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(files)}
ck('upstream_downloads_hash_match',all(hashlib.sha256((E/x['file']).read_bytes()).hexdigest()==x['sha256'] for x in json.loads((E/'upstream-provenance.json').read_text()) if 'file' in x))
# Read-time provenance, no launch is performed by N.
res={'checks':checks,'all_passed':all(checks.values()),'sha256':inv,'hash_scope':'Read-time source/evidence inventory; no Julia launch pins','native_calls':0,'julia_launches':0}
with (E/'source-contract.json').open('x') as f:json.dump(res,f,indent=2);f.write('\n')
print(len(checks),'checks',len(inv),'hashes',res['all_passed']);assert res['all_passed']
