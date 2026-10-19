"""Text-only scope contract, not a Julia parse or runtime test."""
from pathlib import Path
INSERT='const _BGB_ZERO_COUNTS = ntuple(_ -> 0, Val(20))\n'
REPLACEMENTS=[('BGPanelCounts() = BGPanelCounts(ntuple(_ -> 0,20))','BGPanelCounts() = BGPanelCounts(_BGB_ZERO_COUNTS)'),('counts(::BGNoCounts) = ntuple(_->0,20)','counts(::BGNoCounts) = _BGB_ZERO_COUNTS'),('BGPanelDecision(r,b,ok,ok ? :eligible : :dimensions,true,ntuple(_->0,20))','BGPanelDecision(r,b,ok,ok ? :eligible : :dimensions,true,_BGB_ZERO_COUNTS)')]
def checks(text):
 return {'private_static_constant':text.count(INSERT)==1,**{f'replacement_{i}':text.count(new)==1 and old not in text for i,(old,new) in enumerate(REPLACEMENTS,1)}}
def inverse(text):
 text=text.replace(INSERT,'',1)
 for old,new in REPLACEMENTS:text=text.replace(new,old,1)
 return text
