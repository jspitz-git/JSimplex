from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-specialized/reproduce';OLD=R/'diagnostics/direct-bg-export-workspace/reproduce';G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ren(s):return s.replace('_bgx_','_bgxs_').replace('BGExport','BGSpecializedExport').replace('_BGXBuildOwner','_BGXSBuildOwner')
C.mkdir(parents=True)
records={}
for name in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl']:
 src=OLD/name if name!='import-tests.jl' else R/'diagnostics/direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl'
 if sha(src)!=json.loads((G/'runs/green2-300/sealed.json').read_text())['inventory'][str(src)]['sha256']:raise RuntimeError('Test source drift')
 with (C/name).open('x') as f:f.write(ren(src.read_text()))
 records[name]={'source':str(src),'original_sha256':sha(src),'candidate_sha256':sha(C/name)}
with (C/'boundary-tests.jl').open('xb') as f:f.write((D/'boundary-tests.input.jl').read_bytes())
record={'test_lineage':records,'boundary_sha256':sha(C/'boundary-tests.jl'),'candidate_absent':all(not (C/(n+'.jl')).exists() for n in ['workspace','export','import','factor']),'execution':'NONE; test definitions prepared before candidate'}
with (D/'tests-prepared.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
