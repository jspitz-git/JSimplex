"""Fresh source membership and precise report-claim checks, no project code execution."""
from pathlib import Path
import json,hashlib,subprocess,tomllib,traceback
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';P=D/'runs/cost1-300';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');checks={};facts={}
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root).decode().strip()
try:
 for label,root,count in [('diagnostic',R,514),('production',W,516)]:
  b=rd(D/'baseline.json')[label];ck(label+' exact members',len(b)==count and set(git(root,'ls-files','src','test','.github','Project.toml').splitlines())==set(b));ck(label+' current hashes',all(sha(root/n)==v for n,v in b.items()))
 ck('production master',git(W,'rev-parse','HEAD')==rd(P/'sealed.json')['master'])
 for n in ['preparation-pins.json','review.json','lineage.json']:
  j=rd(D/n);ck(n+' hashes',all(sha(Path(p))==v for p,v in j['sha256'].items()))
 ck('prep canonical count membership',len(rd(D/'preparation-pins.json')['sha256'])==91 and set(rd(D/'preparation-pins.json')['sha256'])==set(rd(D/'required-paths.json')['paths']))
 stage=rd(D/'stages.json')['cost'];root=Path(stage['path']);ck('stage exact75',len(stage['sha256'])==75 and set(stage['sha256'])=={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()})
 facts['resources']=rd(E/'result-review-checks.json')['facts']['resources'];resources=facts['resources'];report=(E/'REPORT.md').read_text()
 ck('resource report exact',resources==dict(samples=12,min_available_kib=22437856,max_swap_kib=0,child_maxrss_kib=668936,terminal=dict(available_kib=22965768,swap_used_kib=0)))
 ck('report hash source summary',rd(E/'summary-check.json')['report_sha256']==sha(E/'REPORT.md'))
 for cell,predicate,expected,side,gc in [(9,max,'94.120705','candidate',9.9653),(17,min,'0.068230','reference',2.9818)]:
  rows=[tomllib.loads((P/'output'/f'window-{cell}-{w}.toml').read_text()) for w in range(7,21)];pairs=[{r['side']:r for r in rows if r['pair']==k} for k in range(4,11)];q=predicate(pairs,key=lambda x:x['candidate']['seconds']/x['reference']['seconds']);ratio=q['candidate']['seconds']/q['reference']['seconds'];ck('outlier paired GC '+str(cell),f'{ratio:.6f}'==expected and abs(q[side]['gc_seconds']*1000-gc)<1e-10)
 facts['ratios']={}
 for backend in ['native','markowitz']:
  stats=[c['statistics'] for c in rd(E/'result-review-checks.json')['facts']['all_cell_statistics'] if c['backend']==backend]
  facts['ratios'][backend]=dict(minimum_paired_median=min(s['seconds']['paired_ratio']['median'] for s in stats),maximum_paired_median=max(s['seconds']['paired_ratio']['median'] for s in stats))
 ck('ordinary time medians also slower',all(c['statistics']['seconds']['candidate']['median']>c['statistics']['seconds']['reference']['median'] for c in rd(P/'audit.json')['cells']))
 ck('authorization exact base and first only',rd(E/'authorization.json')['base']==rd(P/'sealed.json')['head'] and 'One cost1-300 only' in rd(E/'authorization.json')['scope'])
 ck('closure publication not executed',all(not(E/n).exists() for n in ['closure.json','closure-host.json','continuation-mappings.json','publication-names.json','publication.json']))
 ck('continuation no two process claim','No cost2/retry/publicsolve.' in (E/'continuation-text.md').read_text() and 'requires separate authorization and fresh exact admission' in (E/'continuation-text.md').read_text())
except Exception:facts['error']=traceback.format_exc()
result=dict(all_passed=all(checks.values()) and 'error' not in facts,checks=checks,facts=facts)
with (E/'result-review-supplement.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
