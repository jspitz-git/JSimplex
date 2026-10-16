"""One-shot new offline infrastructure and invertible diagnostic source/test overlay."""
from pathlib import Path
import json,hashlib,os,tomllib
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'NATIVE-PIVOT-COST-PREPARATION';P=D.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION';G=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,s):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(s)
def cp(src,n):
 with (D/n).open('xb') as f:f.write(src.read_bytes())
def save(n,z):put(n,json.dumps(z,indent=2)+'\n')
def require(x,m):
 if not x:raise RuntimeError(m)
for n in ['guard.py','supervisor.py','seal.py','launch.py','loaded-paths.json']:cp(C/n,n)
s=(C/'common.py').read_text().replace("PREV=Q.parent/'NATIVE-PIVOT-PREPARATION'","PREV=Q").replace("HEAD='294d4435e888577d90533b50c3c44da6702976e6'","HEAD='86e0397c882ff6628193cfa4c1d24a7c71ed7c3e'")
put('common.py',s)
s=(C/'control.py').read_text();a=s.index('OLD=');b=s.index('def validate_environment():')
s=s[:a]+'''PREPARATION=D.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION'
def config(phase):
 require(phase=='integration','Only new integration stage is prepared')
 stage=R/'.superpowers/native-pivot-integration/integration';run=D/'runs/integration';out=run/'output'
 command=['/bin/bash',WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'driver.jl'),str(out),phase,str(stage)]
 return dict(phase=phase,seconds=60,expected_exit=0,arm='candidate',stage=str(stage),run=str(run),output=str(out),command=command)
'''+s[b:]
a=s.index('def validate_prerequisites(');b=s.index('def full_host(',a)
s=s[:a]+'''def predecessor(phase):
 config(phase);P=PREPARATION;mp=P/'preparation-pins-reviewed.json';m=rd(mp);rp=P/'review-final.json';v=rd(rp)
 verify_review(v,mp,list(m['sha256'])+[str(mp.relative_to(R))],'offline integration preparation')
 require(bindings(m),'Preparation input drift')
 require(all(sha(path(n))==h for n,h in v['evidence_sha256'].items()),'Supplemental review drift')
 files={mp,rp}|{path(n) for n in m['sha256']}|{path(n) for n in v['evidence_sha256']}
 preserved={str(STATUS):D/'STATUS.md.before-driver',str(ROAD):D/'roadmap.md.before-driver'}
 for rec in [P/'closure.json',P/'publication.json']:
  z=rd(rec);require(z['all_passed'] is True,'Preparation publication not PASS');files.add(rec)
  for n,h in z['sha256'].items():
   p=path(n);p=preserved.get(str(p),p);require(sha(p)==h,'Preparation closure drift '+n);files.add(p)
 h=rd(P/'closure-host.json');require(not h['matches'] and len(h['groups'])==216,'Previous host closure')
 files.add(P/'closure-host.json')
 return sorted(files),h['groups']
'''+s[b:];put('control.py',s)
s=(C/'audit.py').read_text().replace('from oracle import test_results,cost_results','from oracle import test_results').replace(" if phase=='cost':names|={f'window-{i:03d}.toml' for i in range(1,89)}\n",'').replace("result=cost_results(raw,[tomllib.loads((out/f'window-{i:03d}.toml').read_text()) for i in range(1,89)]) if phase=='cost' else test_results(raw,phase)","result=test_results(raw,phase)")
put('audit.py',s)
# Apply only accepted source seams, then bind exact whole-file inverse.
m=json.loads((P/'overlay-manifest.json').read_text())['candidate'];ed=json.loads((P/'observer-seams.json').read_text());orig=Path(next(e['source'] for e in m if e['destination']=='src/factorization.jl'));s=orig.read_text()
for i in ed['application_order']:
 e=ed['edits'][i];require(s.count(e['before'])==e['count'],'Observer source anchor');s=s.replace(e['before'],e['after'])
put('observed-factorization.jl',s)
t=(P/'native_pivot_integration_tests.jl').read_text();edits=[('    result = solve(problem; options)\n','    result = solve(problem; options)\n    Main.NativePivotIntegrationProbe.result!(result)\n'),('            public_case(mode,symbol)\n','''            Main.NativePivotIntegrationProbe.begin_case!(string(mode,"/",symbol),symbol)
            try
                public_case(mode,symbol)
            finally
                Main.NativePivotIntegrationProbe.end_case!()
            end
'''),('    recovery_case()\n','''    Main.NativePivotIntegrationProbe.begin_case!("recovery",:threshold_one)
    try
        recovery_case()
    finally
        Main.NativePivotIntegrationProbe.end_case!()
    end
''')]
for before,after in edits:require(t.count(before)==1,'Test anchor');t=t.replace(before,after)
put('observed-tests.jl',t);save('test-inverse.json',dict(original=str(P/'native_pivot_integration_tests.jl'),edits=[dict(before=a,after=b) for a,b in edits]))
for e in m:
 if e['destination']=='src/factorization.jl':e.update(source=str(D/'observed-factorization.jl'),sha256=sha(D/'observed-factorization.jl'))
save('overlay-manifest.json',dict(candidate=m,scope='76files, same approved overlay except exact diagnostic factor seams. Testfile remains original; driver includes separate invertible observed test.'))
base=tomllib.loads((C/'runs/cost/output/raw.toml').read_text())['default_control'];save('controls-baseline.json',dict(default=base,source=str(C/'runs/cost/output/raw.toml'),source_sha256=sha(C/'runs/cost/output/raw.toml'),scope='Stored20 control bits, no runtime query'))
save('environment.json',{k:os.environ.get(k) for k in json.loads((C/'environment.json').read_text())})
# Reuse the accepted Test1.13 scoped recorder verbatim, not its old tests/driver.
x=(G/'test-driver.jl').read_text();a=x.index('module RecordedTests');b=x.index('function main()',a)
put('recorder.jl',x[a:b])
save('source-map.json',dict(byte_identical={n:str(C/n) for n in ['guard.py','supervisor.py','seal.py','launch.py','loaded-paths.json']},recorder_source=str(G/'test-driver.jl'),observer_source=str(orig),observer_seams=str(P/'observer-seams.json'),test_inverse=str(D/'test-inverse.json')))
print('Prepared isolated new driver infrastructure; no stage/seal/Julia')
