"""Finite unbounded-exponent sequential binary oracle; never parses Julia.
Signed zero, nonfinite values and MPFR exponent/flag boundaries require the
separate Julia reference regressions. Do not use this oracle for those cases.
"""
from fractions import Fraction as Q

def power2(e):
    return Q(2**e) if e >= 0 else Q(1,2**(-e))

def rounded(x,bits,mode='nearest'):
    x=Q(x)
    if bits<2 or mode not in ('nearest','up','down','zero'):
        raise ValueError('unsupported precision or rounding')
    if not x:return Q(0)
    sign=1 if x>0 else -1;a=abs(x)
    e=a.numerator.bit_length()-a.denominator.bit_length()
    if a<power2(e):e-=1
    unit=power2(e-bits+1);scaled=a/unit
    n,rem=divmod(scaled.numerator,scaled.denominator)
    if mode=='nearest':
        twice=2*rem
        n+=int(twice>scaled.denominator or (twice==scaled.denominator and n%2==1))
    elif rem and ((mode=='up' and sign>0) or (mode=='down' and sign<0)):
        n+=1
    return sign*n*unit

def upper(work,rows,diagonal,count,bits=None,mode='nearest'):
    out=list(map(Q,work));rnd=(lambda v:Q(v)) if bits is None else (lambda v:rounded(v,bits,mode))
    publications=[]
    for pivot in range(count-1,-1,-1):
        value=out[pivot]
        for index,coefficient in rows[pivot]:
            value=rnd(value-rnd(Q(coefficient)*out[index]))
        out[pivot]=rnd(value/Q(diagonal[pivot]))
        publications.append((pivot,out[pivot]))
    return out,publications

