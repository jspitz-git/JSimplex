from pathlib import Path
import re,json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S4-S';sha=lambda b:hashlib.sha256(b).hexdigest();original=[]
def walk(rel,modified_root=None):
 out=[rel];text=modified_root if rel=='src/JSimplex.jl' and modified_root is not None else (R/rel).read_text()
 for name in re.findall(r'^include\("([^"\n]+)"\)',text,re.M):out+=walk(str(Path(rel).parent/name),modified_root)
 return out
original=walk('src/JSimplex.jl');root=(R/'src/JSimplex.jl').read_text();patches=[]
for name in ['LinearAlgebra','Logging','SparseArrays']:
 patches.append(dict(old=f'using {name}\n',new=f'const {name} = Main.JSimplex.{name}\nusing .{name}\n',count=1))
patches += [dict(old='import OrderedCollections\n',new='const OrderedCollections = Main.JSimplex.OrderedCollections\n',count=1),dict(old='using PrecompileTools: @setup_workload, @compile_workload\n',new='# S4-S: no PrecompileTools import in the isolated solver core.\n',count=1),dict(old='include("moi.jl")\n',new='# S4-S: MOI integration excluded from isolated public solve scope.\n',count=1),dict(old='include("precompile.jl")\n',new='# S4-S: package precompile workload excluded, not suppressed by mutable state.\n',count=1)]
modified=root
for p in patches:assert modified.count(p['old'])==1;modified=modified.replace(p['old'],p['new'])
back=modified
for p in reversed(patches):assert back.count(p['new'])==1;back=back.replace(p['new'],p['old'])
assert back==root
selected=walk('src/JSimplex.jl',modified);hh=(R/'src/huangfu_hall_factorization.jl').read_text();old='lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=false)';new='lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=_same_umfpack_pattern(F,convert(SparseMatrixCSC{Float64,Int},B)))';assert hh.count(old)==1;candidate=hh.replace(old,new);assert candidate.replace(new,old)==hh
methods=[]
for rel in original:
 text=(R/rel).read_text()
 for m in re.finditer(r'(?m)^(?:(?:Base\.)?@\w+\s+)*(?:function\s+)?((?:Base|MOI|LinearAlgebra|SparseArrays)\.(?!@))',text):
  tail=text[m.end():];start=tail.index('(')
  if tail.startswith(':('):start=tail.index('(',tail.index(')')+1)
  depth=0
  for j,c in enumerate(tail[start:],start):
   if c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:end=j+1;break
  sig=m.group(0)+tail[:end]
  owners=[x for x in ['Bound','_UnreliableBasisSolve','IndexedVector','MPSParseError','_UnitTransposeRHS','UpperRowIndices','DiagnosticObserverFailure','_PriceAuditMatrix','_PrimalActivityBounds','Optimizer'] if re.search(r'\b'+x+r'\b',sig)]
  assert len(owners)==1,(rel,sig,owners)
  methods.append(dict(source=rel,line=text.count('\n',0,m.start())+1,signature=sig,owner=owners[0],selected=rel in selected,classification='contains cloned nominal type; external generic receives disjoint new signature'))
entries=[]
for side,container in [('reference','S4HHReference'),('candidate','S4HHCandidate')]:
 for n,rel in enumerate(selected):
  body=modified if rel=='src/JSimplex.jl' else candidate if side=='candidate' and rel=='src/huangfu_hall_factorization.jl' else (R/rel).read_text()
  entries.append(dict(side=side,container=container,module=container+'.JSimplex',load_order=n,source=str(R/rel),relative_source=rel,proposed_destination=side+'/'+rel,source_sha256=sha((R/rel).read_bytes()),proposed_sha256=sha(body.encode()),proposed_bytes=len(body.encode())))
obj=dict(scope='OFFLINE PROPOSAL ONLY: no module loaded, no generated .jl tree installed',containers=['Main.S4HHReference','Main.S4HHCandidate'],preconditions=['Main.JSimplex is the already-resident pinned production module','four dependency module bindings identical to pinned resident production bindings','containers absent, fresh process, no repeated module loads','both side source trees exclusively materialized from this manifest before future launch'],original_load_order=original,selected_load_order=selected,excluded=[x for x in original if x not in selected],root_substitutions=patches,candidate_HH_substitution=dict(old=old,new=new,count=1),entries=entries,external_methods=methods,generated_enum_types=['TerminationStatus','ObjectiveSense','VariableDomain','VariableState'],generated_external_families=['Enums.namemap','Base.typemin','Base.typemax','Enums._enum_hash','Base.instances'],no_routing_renames=True,inverse_exact=True)
assert len(original)==70 and len(selected)==64 and len(methods)==62 and sum(m['selected'] for m in methods)==29
for filename,body in [('isolated-root.txt',modified),('candidate-hh.txt',candidate)]:
 with (E/filename).open('x') as f:f.write(body)
with (E/'manifest.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(dict(original_files=len(original),selected_per_side=len(selected),side_entries=len(entries),external_explicit=len(methods),selected_explicit=sum(m['selected'] for m in methods),root_patches=len(patches),candidate_patches=1,inverse_exact=True)))
