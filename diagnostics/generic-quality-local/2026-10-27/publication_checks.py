from pathlib import Path

def verify_tested_trees(master,stage,pins,need,sha):
    for tree in ['src','test']:
        actual={str(p.relative_to(master)) for p in (master/tree).rglob('*') if p.is_file()}
        tested={str(p.relative_to(stage)) for p in (stage/tree).rglob('*') if p.is_file()}
        bound={str(Path(p).relative_to(master)):v for p,v in pins['inventory'].items() if Path(p).is_relative_to(master/tree)}
        need(actual==tested==set(bound),'complete actual/tested/pinned tree membership '+tree)
        for name in actual:
            p=master/name;v=bound[name]
            need(str(p.resolve(strict=True))==v['resolved'],'actual source resolution '+name)
            need(sha(p)==sha(stage/name)==v['sha256'],'actual source still equals tested/pinned '+name)

def verify_historical_maps(root,master,main_index,base,names,hist,continuation,protected,baseline,need,sha):
    need(hist['master_before']==base,'exact old master ref')
    need(continuation['master_source_before']==hist['source_before'],'exact source map preservation')
    need(continuation['master_index_before']==hist['master_index_before'],'exact index map preservation')
    expected={str(master/name):name for name in names if name in baseline}
    need(set(hist['source_before'])==set(expected),'exact changed existing source map keys')
    for actual,name in expected.items():
        v=hist['source_before'][actual];before=root/'baseline'/name
        need(v['before']==str(before) and v['sha256']==baseline[name],'exact baseline before mapping '+actual)
        need(sha(before)==v['sha256'],'preserved before source bytes '+actual)
    need(set(hist['master_index_before'])=={main_index},'exact original index path')
    v=hist['master_index_before'][main_index];before=root/'before-master/master.index'
    need(v['before']==str(before),'exact original index before path')
    need(v['sha256']==protected['indexes'][main_index]==sha(before),'preserved original index bytes')
