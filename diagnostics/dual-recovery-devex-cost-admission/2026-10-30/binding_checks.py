"""Cold admission checks; no reservation or launch side effects."""
from pathlib import Path
import common as C

def interpreter(seal,pins,current):
 C.require(type(current) is str and type(seal.get('guard_python')) is str,'interpreter type')
 absolute=str(Path(current).absolute())
 C.require(absolute==seal['guard_python'],'launch interpreter differs from phase seal')
 item=pins['inventory'].get(absolute)
 C.require(isinstance(item,dict) and str(Path(current).resolve(strict=True))==item.get('resolved') and C.sha(current)==item.get('sha256'),'unpinned or changed interpreter')

def head(seal,ad,current):
 C.require(type(current) is str and type(seal.get('head')) is str and type(ad.get('head')) is str and len(current)==40 and current==seal['head']==ad['head'],'admitted HEAD changed')
