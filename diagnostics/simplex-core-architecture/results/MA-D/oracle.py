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

if __name__=='__main__':
    import json
    from pathlib import Path
    checks={
        'nearest_even_down':rounded(Q(9,8),3)==1,
        'nearest_even_up':rounded(Q(11,8),3)==Q(3,2),
        'directed_positive':rounded(Q(9,8),3,'up')==Q(5,4),
        'directed_negative':rounded(Q(-9,8),3,'down')==Q(-5,4),
        'toward_zero':rounded(Q(-9,8),3,'zero')==-1,
        'first_seed_unrounded':upper([1+power2(-130),1,0],[[(1,1),(2,0)]],[1],1,128)[0][0]==power2(-130),
        'premature_seed_differs':rounded(1+power2(-130),128)==1,
        'exact_rational':upper([Q(5,7),Q(2,3),Q(-1,5)],[[(1,Q(3,4)),(2,Q(2,9))]],[Q(4,11)],1)[0][0]==(Q(5,7)-Q(1,2)+Q(2,45))*Q(11,4),
    }
    with Path(__file__).with_name('oracle-checks.json').open('x') as f:
        json.dump({'all_passed':all(checks.values()),'checks':checks,'scope':'Python exact synthetic checks, no Julia/numerical solver'},f,indent=2);f.write('\n')
    print(checks)
    if not all(checks.values()):raise SystemExit(1)
