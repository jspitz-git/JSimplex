from pathlib import Path
import json,hashlib,stat,subprocess,re,html
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-U';J=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu');B=J/'share/julia/base';L=J/'share/julia/stdlib/v1.13';T=D/'results/S4-T';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):
 with (E/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
loading=(B/'loading.jl').read_text();pc=Path('/home/jspitz/.julia/packages/PrecompileTools/QUxvR/src/workloads.jl');docs=J/'share/doc/julia/html/en/manual/command-line-interface.html';doc=docs.read_text();rows=[html.unescape(re.sub('<[^>]+>',' ',r)) for r in re.findall(r'<tr>.*?</tr>',doc) if any(x in r for x in ['--compiled-modules','--pkgimages','--startup-file'])]
put('installed-option-docs.json',dict(path=str(docs),sha256=sha(docs),rows=rows,scope='Installed documentation; no Julia flag query or C option-parser execution'))
cache=Path('/home/jspitz/.julia/compiled/v1.13/JSimplex');items=[]
for p in sorted(cache.iterdir()):
 s=p.lstat();items.append(dict(name=p.name,size=s.st_size,mtime_ns=s.st_mtime_ns,mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid,gid=s.st_gid,inode=s.st_ino,kind='symlink' if p.is_symlink() else 'file' if p.is_file() else 'other'))
put('cache-metadata.json',dict(directory=str(cache),entries=items,scope='lstat/name metadata only; no cache contents read/hashed/deserialized, no file selected or runtime validity established'))
paths=[B/'loading.jl',B/'client.jl',B/'options.jl',docs,J/'bin/julia',J/'include/julia/julia.h',L/'LinearAlgebra/src/LinearAlgebra.jl',L/'LinearAlgebra/src/blas.jl',L/'SparseArrays/src/solvers/LibSuiteSparse.jl',L/'libblastrampoline_jll/src/libblastrampoline_jll.jl',L/'OpenBLAS_jll/src/OpenBLAS_jll.jl',L/'SuiteSparse_jll/src/SuiteSparse_jll.jl',pc,pc.parent/'PrecompileTools.jl',R/'src/JSimplex.jl',R/'src/precompile.jl',R/'Project.toml',R/'Manifest.toml',R/'LocalPreferences.toml']
# Save only necessary installed-source excerpts, with their complete-file read-time hashes.
segments={'loading.jl':[(1296,1310),(1435,1495),(2155,2195),(2710,2757),(2827,2845),(4176,4232),(4337,4367)],'client.jl':[]}
excerpts=[]
for name,ranges in segments.items():
 lines=(B/name).read_text().splitlines()
 for lo,hi in ranges:excerpts.append(dict(path=str(B/name),sha256=sha(B/name),first_line=lo,last_line=hi,text='\n'.join(lines[lo-1:hi])))
put('source-excerpts.json',excerpts)
checks={}
section=loading[loading.index('function __require_prelocked'):loading.index('# just load the file normally via include',loading.index('function __require_prelocked'))]
checks['strict_error_before_compile_branch']=section.index('use_compiled_modules == 3')<section.index('use_compiled_modules == 1') and 'Precompiled image $pkg not available' in section
checks['only_mode1_enters_compile_branch']='if JLOptions().use_compiled_modules == 1' in section
checks['source_fallback_after_strict_guard']='include(__toplevel__, path)' in loading[loading.index('# just load the file normally via include'):]
checks['documented_existing_strict_difference']=any('strict' in r and 'will error if no precompile file is found' in r for r in rows)
checks['touch_on_cache_success_attempt']='touch(path_to_try) # update timestamp of precompilation file' in loading
checks['read_only_touch_failure_caught']='file might be read-only and then we fail to update timestamp, which is fine' in loading
checks['serialized_dependency_init_warning']='this runs __init__ methods too early' in loading
checks['init_and_package_callbacks']='run_module_init(mod, i)' in loading and 'run_extension_callbacks(modkey)' in loading
checks['stale_cache_cpu_flags_preferences']='jl_match_cache_flags' in loading and 'check_clone_targets(clone_targets)' in loading and 'stale_prefs(prefs_blob)' in loading
la=(L/'LinearAlgebra/src/LinearAlgebra.jl').read_text();blas=(L/'LinearAlgebra/src/blas.jl').read_text();jll=(L/'libblastrampoline_jll/src/libblastrampoline_jll.jl').read_text();ss=(L/'SparseArrays/src/solvers/LibSuiteSparse.jl').read_text()
checks['LA_init_registers_callback']='libblastrampoline_jll.add_dependency!(OpenBLAS_jll, libopenblas, lbt_openblas_onload_callback)' in la
checks['installed_shim_invokes_callback']='on_load_callback()' in jll
checks['callback_forwards_checks_and_threads']='BLAS.lbt_forward_ccall' in la and 'BLAS.check()' in la and 'BLAS.lbt_set_num_threads(nthreads)' in la
checks['BLAS_check_is_config_validation']='function check()' in blas and 'config = LBTConfig(unsafe_load(ccall((:lbt_get_config' in blas
checks['SuiteSparse_once_deferred_allocator_setup']='Base.OncePerProcess{Nothing}() do' in ss and 'SuiteSparse_config_malloc_func_set(cglobal(:jl_malloc' in ss
checks['both_precompile_enabled_and_verbose']=pc.read_text().count('$PrecompileTools.workload_enabled(@__MODULE__)')==2 and pc.read_text().count('if $iscompiling || $PrecompileTools.verbose[]')==2
prior=json.loads((T/'source-contract.json').read_text());fix=json.loads((T/'review-fix.json').read_text())
checks['T604_603current_onepreserved']=len(prior['sha256'])==604 and all(sha(fix['before'][p]['preserved'] if p in fix['before'] else p)==v for p,v in prior['sha256'].items())
checks['T_corrected_report_hash']=all(sha(p)==v for p,v in fix['after'].items())
host=json.loads((E/'host-before.json').read_text());checks['user6_unchanged']=all(sha(p)==v for p,v in host['user_hashes'].items());checks['fullgroups_absent']=not host['matches'] and not host['pids_present'];checks['source_test_CI_equal_master']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
allpaths=set(prior['sha256']);allpaths.update(str(p.resolve()) for p in paths+list(T.iterdir())+list(E.iterdir()) if p.is_file())
obj=dict(checks=checks,all_passed=all(checks.values()),sha256={p:sha(p) for p in sorted(allpaths)},cache_entry_count=len(items),scope='Installed source/doc/metadata analysis ONLY, no runtime cache validity/initializer closure or bootstrap qualification',bootstrap_qualified=False,julia_calls=0,module_loads=0)
put('source-contract.json',obj);print(json.dumps(dict(checks=checks,hashes=len(allpaths),cache_entries=len(items),all_passed=obj['all_passed'])));assert obj['all_passed']
