import math

def valid_outcome(d):
    assert math.isfinite(d['seconds']) and d['seconds']>0
    assert math.isfinite(d['loop']) and 0<=d['loop']<=d['seconds']
    if d['status']!='OPTIMAL':
        return False
    assert d['original_feasible'] is True
    assert d['certificate_last'] is True and d['certificate_true']>0
    return True
