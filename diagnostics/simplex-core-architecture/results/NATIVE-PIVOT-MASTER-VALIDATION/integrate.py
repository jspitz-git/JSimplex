"""One exact authorized local fast-forward; preserve unrelated user files."""
from pathlib import Path
import sys
E=Path(__file__).resolve().parent;D=E.parent/'NATIVE-PIVOT-MASTER-READINESS';sys.path.insert(0,str(D))
from control import *
preparation();validate_environment();validate_production(False);h=full_host();require(not h['matches'],'Processes')
main=Path('/home/jspitz/JSimplex.jl');c=rd(D/'production-commit.json');before=rd(E/'main-before.json')
require(git('branch','--show-current',cwd=main)=='master' and git('rev-parse','HEAD',cwd=main)==BASE,'Main ref')
require(git('status','--porcelain=v1',cwd=main)==before['status'],'User status drift')
require(not git('diff','--cached','--name-only',cwd=main),'User index')
require(git('diff','--name-only',cwd=main).splitlines()==['.vscode/settings.json'],'Unexpected user change')
user={n:sha(main/n) for n in ['.vscode/settings.json','Manifest.toml','LocalPreferences.toml']}
for n in c['names']:
 require(n not in user,'Affected dirty path')
 if git('ls-tree',BASE,'--',n):require(git('hash-object','--',n,cwd=main)==git('rev-parse',BASE+':'+n),'Dirty affected path')
 else:require(not (main/n).exists(),'New destination exists')
save(E/'integration-before.json',dict(host=h,user_sha256=user,base=BASE,target=c['commit']))
subprocess.run(['git','merge','--ff-only',c['commit']],cwd=main,check=True)
require(git('rev-parse','HEAD',cwd=main)==git('rev-parse','master')==c['commit'],'Master result')
require(all(sha(main/n)==v for n,v in user.items()),'User bytes changed')
require(git('status','--porcelain=v1',cwd=main)==before['status'],'User status changed')
blobs={n:git('rev-parse','master:'+n) for n in c['names']}
require(all(git('hash-object','--',n,cwd=main)==v for n,v in blobs.items()),'Actual master bytes')
validate_production(True)
save(E/'integration.json',dict(all_passed=True,parent=BASE,master=c['commit'],names=c['names'],git_blobs=blobs,user_sha256=user,main_status=before['status'],sha256={str(main/n):sha(main/n) for n in c['names']}))
print('Local master fast-forward complete; exact10 blobs and user files preserved')
