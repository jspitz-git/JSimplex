"""Strict Test result schema; no execution or numerical imports."""
from common import *
def raw_ok(raw,c):
 try:
  require(set(raw)=={'stage','source','Julia_version','before_precision','before_rounding','after_precision','after_rounding','ambient_ok','files','errors','all_passed'},'raw keys')
  require(raw['stage']==c['stage'] and raw['source']==str(Path(c['root'])/'src/JSimplex.jl') and raw['Julia_version']=='1.13.0','source/stage/runtime')
  require(raw['errors']==[] and raw['ambient_ok'] is True and type(raw['before_precision']) is int and raw['before_precision']>0 and raw['before_precision']==raw['after_precision'] and raw['before_rounding']==raw['after_rounding'],'ambient/errors')
  require(raw['all_passed'] is (c['stage']!='red'),'aggregate')
  require(type(raw['files']) is list and len(raw['files'])==len(c['files']),'files')
  for f,path in zip(raw['files'],c['files']):
   require(set(f)=={'file','tree','counts'} and f['file']==path,'file schema')
   t=f['tree'];expected=c['expected'][path]
   require(set(t)=={'name','counts','nonpasses','children'} and t['name']==path and type(t['counts']) is list and all(type(x) is int for x in t['counts']) and t['counts']==[0,0,0,0] and t['nonpasses']==[] and len(t['children'])==len(expected),'file tree')
   total=[0,0,0,0]
   for child,e in zip(t['children'],expected):
    require(set(child)=={'name','counts','nonpasses','children'} and child['name']==e['name'] and child['children']==[],'testset schema')
    counts=child['counts'];require(type(counts) is list and len(counts)==4 and all(type(x) is int and x>=0 for x in counts) and counts==e['counts'],'counts')
    total=[x+y for x,y in zip(total,counts)]
    require(len(child['nonpasses'])==sum(counts[1:]),'nonpass count')
    for fail in child['nonpasses']:
     require(c['stage']=='red' and set(fail)=={'kind','expression','file','line','display'} and type(fail['kind']) is int and fail['kind']==2 and fail['file']==path and type(fail['line']) is int and fail['line']==39 and 'row.reads' in fail['expression'] and 'vcat' in fail['expression'] and bool(fail['display']),'unexpected failure')
   require(type(f['counts']) is list and len(f['counts'])==4 and all(type(x) is int for x in f['counts']) and f['counts']==total,'file aggregate')
  return True
 except (KeyError,TypeError,ValueError,AttributeError):return False
